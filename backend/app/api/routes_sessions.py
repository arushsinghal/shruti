import hashlib
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from app.schemas.consultation import ConsultationSession, CreateSessionRequest, ModeEnum
from app.storage.repository import SessionRepository
from app.api.routes_auth import get_current_user

router = APIRouter()
repo = SessionRepository()


class GrantConsentRequest(BaseModel):
    consent_mode: str = "verbal"
    consent_text_version: str = "v1"


@router.post("/sessions", response_model=ConsultationSession, status_code=201)
async def create_session(
    body: CreateSessionRequest = CreateSessionRequest(),
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Initializes a new clinical consultation session. Research prototype only — output requires physician review."""
    from app.api.routes_billing import check_can_create_session, increment_trial_usage
    user_id = str(current_user["id"])
    await check_can_create_session(user_id)
    session = await repo.create_session(
        user_id=user_id,
        patient_name=body.patient_name,
        doctor_name=body.doctor_name,
        abha_number=body.abha_number,
        pmjay_beneficiary=body.pmjay_beneficiary,
        specialty=body.specialty,
        cloud_ai_consent=body.cloud_ai_consent,
        mode=body.mode,
        patient_phone=body.patient_phone,
        patient_age=body.patient_age,
        patient_sex=body.patient_sex,
        whatsapp_number=body.whatsapp_number,
    )
    await increment_trial_usage(user_id)
    return session


class IntakeRequest(BaseModel):
    patient_name: str
    patient_phone: str
    patient_age: str = ""
    patient_sex: str = ""
    chief_complaint: str = ""
    whatsapp_number: str = ""  # Often differs from patient_phone in India; falls back to patient_phone if blank.


@router.post("/sessions/intake", response_model=ConsultationSession, status_code=201)
async def assistant_intake(
    body: IntakeRequest,
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Assistant registers a patient before the doctor consultation.

    Creates a session owned by the clinic's doctor (not the assistant) so it
    appears in the doctor's dashboard immediately. Requires the caller to be
    an assistant with a linked clinic."""
    from app.storage.db import db_connect as _db_connect
    if current_user.get("role") != "assistant":
        raise HTTPException(status_code=403, detail="Only assistants can use the intake route.")

    assistant_id = str(current_user["id"])
    async with _db_connect() as db:
        async with db.execute(
            """SELECT c.owner_user_id, c.id FROM clinics c
               JOIN clinic_members cm ON cm.clinic_id = c.id
               WHERE cm.user_id = ? AND c.owner_user_id != ?
               LIMIT 1""",
            (assistant_id, assistant_id),
        ) as cursor:
            row = await cursor.fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="You are not linked to a clinic yet.")

    doctor_user_id = str(row[0])
    clinic_id = str(row[1])
    notes = body.chief_complaint.strip() or None

    session = await repo.create_session(
        user_id=doctor_user_id,
        patient_name=body.patient_name.strip(),
        patient_phone=body.patient_phone.strip(),
        patient_age=body.patient_age.strip() or None,
        patient_sex=body.patient_sex.strip() or None,
        cloud_ai_consent=False,
        mode="health",
        clinic_id=clinic_id,
        initiated_by="assistant",
        whatsapp_number=body.whatsapp_number.strip() or None,
    )
    # Store chief complaint in transcript field as a hint for the doctor
    if notes:
        async with _db_connect() as db:
            await db.execute(
                "UPDATE sessions SET transcript = ? WHERE id = ?",
                (f"[Chief complaint: {notes}]", session.id),
            )
            await db.commit()
        session.transcript = f"[Chief complaint: {notes}]"
    return session


@router.get("/sessions", response_model=list[ConsultationSession])
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> list[ConsultationSession]:
    """Retrieves metadata of recent consultation sessions for deployment monitoring. Research prototype only — output requires physician review."""
    # TODO: push limit/offset into the SQL query (repository.list_sessions) to avoid
    # loading all rows into memory. Current approach slices in Python, which is safe for
    # early deployments (<500 sessions) but becomes a full-table scan as volume grows.
    # Next step: add LIMIT/OFFSET to the SELECT in repository.py and thread the params through.
    if current_user.get("role") == "assistant":
        sessions = await repo.get_sessions_for_assistant(str(current_user["id"]))
    else:
        sessions = await repo.get_sessions_for_user(str(current_user["id"]))
    return sessions[offset : offset + limit]


def _soap_is_empty(soap) -> bool:
    """True if SOAP has only default placeholder text (never been populated from facts)."""
    if not soap:
        return True
    if isinstance(soap, str):
        try:
            soap = json.loads(soap)
        except Exception:
            return True
    defaults = {
        "No subjective complaints noted.",
        "No objective vitals recorded.",
        "Assessment not documented in transcript.",
        "Follow-up: as advised by physician.",
        "",
    }
    s = str(soap.get("S") or soap.get("subjective") or "").strip()
    return s in defaults


async def _backfill_soap_if_empty(session) -> None:
    """For health sessions with extracted facts but empty SOAP, regenerate using opt-out model."""
    if not session.mode or str(session.mode) != "health":
        return
    if not _soap_is_empty(session.soap_note):
        return
    memory_state = session.memory_state or {}
    raw_facts = memory_state.get("_extracted_facts") or []
    if not raw_facts:
        return

    from app.services import provenance as _prov
    from app.services.memory_context import MemoryContextService
    from app.services.soap_generator import SOAPGeneratorService
    from app.schemas.consultation import ExtractedFact

    _memory = MemoryContextService()
    _soap_gen = SOAPGeneratorService()

    facts = []
    for item in raw_facts:
        try:
            facts.append(ExtractedFact(**item) if isinstance(item, dict) else item)
        except Exception:
            continue
    if not facts:
        return

    non_rejected = _prov.facts_from_non_rejected(facts)
    full_state = _memory.resolve_memory([non_rejected])
    new_soap = _soap_gen.generate_soap(full_state)
    session.soap_note = new_soap
    session.clinical_facts = non_rejected
    session.memory_state = {**full_state, "_extracted_facts": raw_facts}
    await repo.update_session(session)


@router.get("/sessions/{session_id}", response_model=ConsultationSession)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Retrieves a single consultation session metadata by ID. Research prototype only — output requires physician review."""
    session = await repo.get_session_for_actor(session_id, current_user)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await _backfill_soap_if_empty(session)
    return session


@router.patch("/sessions/{session_id}/consent", response_model=ConsultationSession)
async def grant_consent(
    session_id: str,
    request: Request,
    body: GrantConsentRequest = GrantConsentRequest(),
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Records that the doctor has confirmed patient consent before this session's audio upload.
    Must be called before audio upload or clinical processing are permitted."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.cloud_ai_consent = True
    await repo.update_session(session)

    # Capture Consent Audit Logs
    timestamp = datetime.utcnow().isoformat()
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    # Hashing payload
    payload = {
        "consent_mode": body.consent_mode,
        "consent_text_version": body.consent_text_version,
        "session_id": session_id,
        "timestamp": timestamp,
        "user_id": user_id,
    }
    canonical_payload_json = json.dumps(payload, sort_keys=True)
    consent_hash = hashlib.sha256(canonical_payload_json.encode("utf-8")).hexdigest()

    await repo.log_consent(
        session_id=session_id,
        user_id=user_id,
        consent_mode=body.consent_mode,
        consent_text_version=body.consent_text_version,
        consent_payload_json=canonical_payload_json,
        consent_hash=consent_hash,
        timestamp=timestamp,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    reloaded_session = await repo.get_session(session_id, user_id)
    return reloaded_session or session


# ---------------------------------------------------------------------------
# Legal export — court-admissible PDF with provenance chain
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/legal-export")
async def legal_export(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return court-admissible PDF with transcript hash + evidence chain."""
    import hashlib
    import io
    import json as _json
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    from app.storage.db import db_connect

    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    transcript = session.transcript or ""
    transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    exported_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    soap: dict = {}
    if session.soap_note:
        try:
            soap = _json.loads(session.soap_note) if isinstance(session.soap_note, str) else (session.soap_note or {})
        except Exception:
            pass

    facts: dict = {}
    if session.clinical_facts:
        try:
            facts = _json.loads(session.clinical_facts) if isinstance(session.clinical_facts, str) else (session.clinical_facts or {})
        except Exception:
            pass

    consent_records: list = []
    async with db_connect() as db:
        async with db.execute(
            "SELECT consent_mode, consent_text_version, consent_hash, timestamp FROM consent_audit_log WHERE session_id=? ORDER BY timestamp",
            (session_id,),
        ) as cur:
            rows = await cur.fetchall()
        for r in rows:
            consent_records.append({"mode": r[0], "version": r[1], "hash": r[2], "timestamp": r[3]})

    # Build canonical JSON for payload hash
    payload = {
        "session_id": session_id,
        "doctor_name": session.doctor_name or "",
        "patient_name": session.patient_name or "Anonymous",
        "created_at": str(session.created_at),
        "exported_at": exported_at,
        "transcript_sha256": transcript_hash,
        "transcript_length_chars": len(transcript),
        "soap_note": soap,
        "extracted_facts": facts,
        "consent_audit": consent_records,
    }
    payload_str = _json.dumps(payload, sort_keys=True, ensure_ascii=False)
    record_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    pdf_bytes = _build_legal_pdf(
        session_id=session_id,
        doctor_name=session.doctor_name or "Unknown",
        patient_name=session.patient_name or "Anonymous",
        created_at=str(session.created_at),
        exported_at=exported_at,
        transcript=transcript,
        transcript_hash=transcript_hash,
        record_hash=record_hash,
        soap=soap,
        facts=facts,
        consent_records=consent_records,
    )

    filename = f"lipi-legal-{session_id[:8]}-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_legal_pdf(
    *,
    session_id: str,
    doctor_name: str,
    patient_name: str,
    created_at: str,
    exported_at: str,
    transcript: str,
    transcript_hash: str,
    record_hash: str,
    soap: dict,
    facts: dict,
    consent_records: list,
) -> bytes:
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Lipi Legal Export — {session_id[:8]}",
        author="Lipi Health",
        subject="Court-Admissible Clinical Record",
    )

    W = A4[0] - 5 * cm  # usable width

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=4, textColor=colors.HexColor("#334155"))
    BODY = ParagraphStyle("BODY", parent=styles["Normal"], fontSize=9, leading=14, textColor=colors.HexColor("#334155"))
    MONO = ParagraphStyle("MONO", parent=styles["Code"], fontSize=7.5, leading=12, fontName="Courier", textColor=colors.HexColor("#475569"), wordWrap="CJK")
    SMALL = ParagraphStyle("SMALL", parent=styles["Normal"], fontSize=7.5, leading=11, textColor=colors.HexColor("#64748b"))
    WARN = ParagraphStyle("WARN", parent=styles["Normal"], fontSize=8, leading=12, textColor=colors.HexColor("#b45309"), backColor=colors.HexColor("#fef3c7"))
    CENTER = ParagraphStyle("CENTER", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#64748b"))

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Lipi Health — Court-Admissible Clinical Record", H1))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3 * cm))

    meta_data = [
        ["Session ID", session_id],
        ["Patient", patient_name],
        ["Doctor", doctor_name],
        ["Consultation date", created_at],
        ["Export timestamp", exported_at],
    ]
    meta_table = Table([[Paragraph(k, SMALL), Paragraph(v, BODY)] for k, v in meta_data],
                       colWidths=[4 * cm, W - 4 * cm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Integrity disclaimer ─────────────────────────────────────────────
    story.append(Paragraph(
        "<b>IMPORTANT:</b> This document is generated by Lipi Health, a clinical documentation "
        "assistant. It is NOT a certified medical device output. The SHA-256 hashes below provide "
        "cryptographic evidence of record integrity — any post-export modification will produce a "
        "different hash. This document requires physician attestation before use in legal proceedings.",
        WARN,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ── SOAP Note ────────────────────────────────────────────────────────
    story.append(Paragraph("SOAP Note", H2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2 * cm))
    for key, label in [("S", "Subjective"), ("O", "Objective"), ("A", "Assessment"), ("P", "Plan")]:
        val = soap.get(key) or soap.get(label.lower()) or ""
        if val:
            story.append(Paragraph(f"<b>{label} ({key}):</b> {val}", BODY))
            story.append(Spacer(1, 0.15 * cm))

    # ── Extracted Clinical Facts ──────────────────────────────────────────
    story.append(Paragraph("Extracted Clinical Facts", H2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2 * cm))
    fact_sections = [
        ("Symptoms", facts.get("symptoms") or []),
        ("Diagnoses", facts.get("diagnoses") or []),
        ("Medications", [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in (facts.get("medications") or [])]),
        ("Investigations", facts.get("investigations") or []),
        ("Vitals", facts.get("vitals") or []),
        ("Allergies", facts.get("allergies") or []),
        ("Follow-up", facts.get("follow_up") or []),
    ]
    for label, items in fact_sections:
        if items:
            story.append(Paragraph(f"<b>{label}:</b> {', '.join(str(i) for i in items)}", BODY))
            story.append(Spacer(1, 0.1 * cm))

    # ── Consent Audit ────────────────────────────────────────────────────
    if consent_records:
        story.append(Paragraph("Consent Audit Log", H2))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 0.2 * cm))
        consent_rows = [["Mode", "Version", "Hash (truncated)", "Timestamp"]] + [
            [r.get("mode", ""), r.get("version", ""), (r.get("hash") or "")[:20] + "…", r.get("timestamp", "")]
            for r in consent_records
        ]
        ct = Table(consent_rows, colWidths=[2.5 * cm, 2 * cm, 4.5 * cm, W - 9 * cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(ct)

    # ── Transcript ───────────────────────────────────────────────────────
    story.append(Paragraph("Verbatim Transcript", H2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2 * cm))
    if transcript:
        # Chunk transcript to avoid single oversized paragraph
        chunk_size = 1000
        for i in range(0, len(transcript), chunk_size):
            chunk = transcript[i:i + chunk_size].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(chunk, MONO))
    else:
        story.append(Paragraph("<i>No transcript recorded.</i>", SMALL))
    story.append(Spacer(1, 0.4 * cm))

    # ── Integrity Hashes ─────────────────────────────────────────────────
    story.append(KeepTogether([
        Paragraph("Cryptographic Integrity", H2),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")),
        Spacer(1, 0.2 * cm),
        Paragraph("<b>Transcript SHA-256</b> (covers verbatim transcript text only):", SMALL),
        Paragraph(transcript_hash, MONO),
        Spacer(1, 0.2 * cm),
        Paragraph("<b>Record SHA-256</b> (covers all fields above — session ID, SOAP, facts, consent audit):", SMALL),
        Paragraph(record_hash, MONO),
        Spacer(1, 0.3 * cm),
        Paragraph(
            "To verify integrity: recompute SHA-256 of the stored transcript and compare to the "
            "Transcript SHA-256 above. A mismatch indicates post-export modification.",
            SMALL,
        ),
    ]))

    # ── Footer on each page ──────────────────────────────────────────────
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(2.5 * cm, 1.5 * cm, f"Lipi Health — Session {session_id[:8]} — Exported {exported_at}")
        canvas.drawRightString(A4[0] - 2.5 * cm, 1.5 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Learning counter — per-doctor flywheel stats
# ---------------------------------------------------------------------------

@router.get("/learning/stats")
async def learning_stats(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Return the doctor's learning flywheel stats for dashboard display."""
    from app.storage.db import db_connect

    user_id = str(current_user["id"])
    async with db_connect() as db:
        async with db.execute(
            "SELECT COUNT(*), SUM(confirmations), SUM(rejections) FROM extraction_knowledge WHERE confirming_users LIKE ?",
            (f"%{user_id}%",),
        ) as cur:
            row = await cur.fetchone()

        async with db.execute(
            "SELECT COUNT(*) FROM extraction_knowledge WHERE status='promoted' AND confirming_users LIKE ?",
            (f"%{user_id}%",),
        ) as cur:
            promoted_row = await cur.fetchone()

    total = int(row[0] or 0)
    confirmations = int(row[1] or 0)
    rejections = int(row[2] or 0)
    promoted = int(promoted_row[0] if promoted_row else 0)

    return {
        "total_learned": total,
        "confirmations": confirmations,
        "rejections": rejections,
        "promoted_to_global": promoted,
        "accuracy_pct": round(confirmations / max(confirmations + rejections, 1) * 100, 1),
    }


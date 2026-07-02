"""
WhatsApp inbound webhook handler (Twilio).

Demo story: doctor sends a voice note → Lipi transcribes, extracts, queues assistant
tasks, and replies with the SOAP summary — all within ~15 seconds, no app login needed.

Phone → doctor mapping (in priority order):
  1. WHATSAPP_DEMO_PHONE_MAP env var (JSON: {"91XXXXXXXXXX": "user_id"})
  2. doctor_profiles.whatsapp_phone column (set via PUT /api/auth/doctor-profile)

Twilio signature validation is skipped when TWILIO_AUTH_TOKEN is empty (local dev /
mock mode). In production, set all three Twilio env vars and Twilio will call this
endpoint; you must configure the webhook URL in the Twilio console to:
  https://<your-domain>/api/whatsapp/webhook
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Request, Response

from jose import jwt as jose_jwt

from app.schemas.consultation import ModeEnum, StatusEnum
from app.services.cds_engine import CDSEngineService
from app.services.clinical_extractor import ClinicalExtractorService
from app.services.memory_context import MemoryContextService
from app.services.sarvam_asr import SarvamASRService
from app.services.soap_generator import SOAPGeneratorService
from app.services.whatsapp_service import WhatsAppService
from app.storage.db import db_connect
from app.storage.repository import SessionRepository
from app.utils.config import settings

from app.services.follow_up_scheduler import (
    get_pending_interaction,
    handle_haan,
    handle_nahi,
    mark_interaction_responded,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_extractor = ClinicalExtractorService()
_memory = MemoryContextService()
_soap_gen = SOAPGeneratorService()
_cds_engine = CDSEngineService()
_asr = SarvamASRService()
_repo = SessionRepository()

_TWIML_ACK = '<?xml version="1.0"?><Response><Message>📋 Processing your consultation... I\'ll send the note in a moment.</Message></Response>'
_TWIML_EMPTY = '<?xml version="1.0"?><Response></Response>'
_TWIML_HELP = (
    '<?xml version="1.0"?><Response><Message>'
    "Send a voice note of your consultation and I'll extract the SOAP note, "
    "queue lab orders, and set up follow-ups for your assistant automatically.\n\n"
    "Reply *status* for your last session summary."
    '</Message></Response>'
)


# ---------------------------------------------------------------------------
# Phone → user lookup
# ---------------------------------------------------------------------------

async def _get_user_clinic_id(user_id: str) -> Optional[str]:
    """Return the clinic_id for a user, or None if not in any clinic."""
    from app.storage.db import db_connect as _db_connect
    async with _db_connect() as db:
        async with db.execute(
            "SELECT clinic_id FROM clinic_members WHERE user_id=? LIMIT 1",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


def _normalize_phone(raw: str) -> str:
    """Strip 'whatsapp:' prefix and non-digit chars except leading +."""
    phone = raw.replace("whatsapp:", "").strip()
    digits = "".join(c for c in phone if c.isdigit())
    return digits  # e.g. "919876543210"


async def _lookup_user_by_phone(phone_digits: str) -> Optional[dict]:
    """Return {"id": str, "name": str} for the doctor owning this WhatsApp number."""
    # 1. Check env-var demo map first (fast path for demo / dev)
    if settings.whatsapp_demo_phone_map:
        try:
            demo_map: dict = json.loads(settings.whatsapp_demo_phone_map)
            if phone_digits in demo_map:
                user_id = str(demo_map[phone_digits])
                async with db_connect() as db:
                    async with db.execute(
                        "SELECT full_name FROM users WHERE id = ?", (int(user_id),)
                    ) as cur:
                        row = await cur.fetchone()
                name = row[0] if row else "Doctor"
                return {"id": user_id, "name": name}
        except Exception as exc:
            logger.warning("whatsapp_demo_phone_map parse error: %s", exc)

    # 2. Look up by doctor_profiles.whatsapp_phone
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT dp.user_id, u.full_name
            FROM doctor_profiles dp
            JOIN users u ON u.id = dp.user_id
            WHERE dp.whatsapp_phone = ?
            """,
            (phone_digits,),
        ) as cur:
            row = await cur.fetchone()

    if row:
        return {"id": str(row[0]), "name": row[1] or "Doctor"}
    return None


# ---------------------------------------------------------------------------
# Twilio signature validation
# ---------------------------------------------------------------------------

def _valid_twilio_signature(request_url: str, form_data: dict, sig_header: str) -> bool:
    token = settings.twilio_auth_token
    if not token:
        return True  # mock / dev mode — skip validation
    params_str = "".join(k + v for k, v in sorted(form_data.items()))
    digest = hmac.new(
        token.encode("utf-8"),
        (request_url + params_str).encode("utf-8"),
        hashlib.sha1,
    ).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, sig_header)


# ---------------------------------------------------------------------------
# WhatsApp reply formatter
# ---------------------------------------------------------------------------

def _generate_doctor_sign_url(session_id: str, user_id: str) -> str:
    """Create a 24-hour no-login signing link for the doctor."""
    import datetime as _dt
    expires = _dt.datetime.now(_dt.timezone.utc) + timedelta(hours=24)
    sign_payload = {
        "sub": session_id,
        "session_id": session_id,
        "user_id": str(user_id),
        "scope": "doctor_session_sign",
        "exp": expires,
    }
    token = jose_jwt.encode(sign_payload, settings.secret_key, algorithm=settings.algorithm)
    base = settings.app_base_url.rstrip("/")
    return f"{base}/sign/{token}"


def _format_soap_reply(soap: dict, facts: dict, session_id: str, doctor_name: str, user_id: str = "") -> str:
    lines = [f"✅ *Consultation captured* — {doctor_name}", ""]

    # Assessment
    assessment = ""
    if isinstance(soap, dict):
        assessment = (
            soap.get("A")
            or soap.get("assessment")
            or soap.get("Assessment")
            or soap.get("a")
            or ""
        )
        if isinstance(assessment, dict):
            assessment = assessment.get("diagnosis") or assessment.get("text") or str(assessment)
    if assessment:
        lines += ["📋 *Assessment*", str(assessment).strip(), ""]

    # Plan
    plan = ""
    if isinstance(soap, dict):
        plan = soap.get("P") or soap.get("plan") or soap.get("Plan") or soap.get("p") or ""
        if isinstance(plan, dict):
            plan = plan.get("text") or plan.get("medications") or str(plan)
    if plan:
        lines += ["💊 *Plan*", str(plan).strip(), ""]

    # Assistant tasks
    task_lines = []
    medications = facts.get("medications") or []
    if medications:
        task_lines.append("1. Send prescription ← ready to dispatch")
    investigations = facts.get("investigations") or []
    if investigations:
        inv_str = ", ".join(str(i) for i in investigations[:4])
        suffix = f" +{len(investigations) - 4} more" if len(investigations) > 4 else ""
        task_lines.append(f"2. Order labs: {inv_str}{suffix}")
    follow_up = facts.get("follow_up")
    if follow_up:
        fu_text = follow_up[0] if isinstance(follow_up, list) else str(follow_up)
        task_lines.append(f"3. Schedule follow-up: {fu_text}")

    if task_lines:
        lines += ["📝 *Tasks for assistant*"] + task_lines + [""]

    # Sign link — no-login mobile page if user_id is available, else fall back to dashboard
    if user_id:
        sign_url = _generate_doctor_sign_url(session_id, user_id)
        lines.append(f"✍️ Sign: {sign_url}")
    else:
        base = settings.app_base_url.rstrip("/")
        lines.append(f"Review: {base}/review/{session_id}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Background task: text transcript pipeline (no ASR step)
# ---------------------------------------------------------------------------

async def _stamp_session(session_id: str, **fields: str) -> None:
    """Update one or more timestamp/status columns on a session row."""
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [session_id]
    try:
        async with db_connect() as db:
            await db.execute(f"UPDATE sessions SET {cols} WHERE id = ?", vals)
            await db.commit()
    except Exception as exc:
        logger.warning("_stamp_session failed: %s", exc)


async def _run_text_pipeline(
    from_phone: str,
    transcript: str,
    user_id: str,
    user_name: str,
) -> None:
    """Same as _run_whatsapp_pipeline but accepts a typed transcript — skips ASR."""
    try:
        received_at = datetime.utcnow().isoformat()
        clinic_id = await _get_user_clinic_id(user_id)
        session = await _repo.create_session(
            user_id=user_id,
            doctor_name=user_name,
            cloud_ai_consent=True,
            mode=ModeEnum.health,
            initiated_by="whatsapp",
            clinic_id=clinic_id,
        )
        session_id = session.id
        await _stamp_session(session_id, received_at=received_at)

        session.transcript = transcript
        session.status = StatusEnum.transcribed
        await _repo.update_session(session)

        facts = _extractor.extract(transcript)
        state = _memory.resolve_memory([facts])
        soap = await _soap_gen.generate_soap_async(state)
        cds = _cds_engine.generate_cds(state)

        session.clinical_facts = facts
        session.memory_state = state
        session.soap_note = soap
        session.cds_suggestions = cds
        session.status = StatusEnum.complete
        await _repo.update_session(session)

        await _auto_create_tasks(session_id, user_id, facts)
        await _write_billing_record(session_id, user_id)

        if settings.hold_for_review:
            await _stamp_session(session_id, hold_for_review="1")
            logger.info("Text pipeline held for review: session=%s", session_id)
            return

        reply = _format_soap_reply(soap, facts, session_id, user_name, user_id)
        await WhatsAppService.send_text_message(from_phone, reply)
        await _stamp_session(session_id, delivered_at=datetime.utcnow().isoformat())

        has_labs = bool(facts.get("investigations"))
        has_followup = bool(facts.get("follow_up"))
        if has_labs or has_followup:
            nudge_parts = []
            if has_followup:
                nudge_parts.append("follow-up reminder")
            if has_labs:
                nudge_parts.append("lab orders")
            nudge = (
                f"📲 Patient ko seedha {' aur '.join(nudge_parts)} bhejna hai?\n\n"
                f"Reply karein: *P +91XXXXXXXXXX*"
            )
            await WhatsAppService.send_text_message(from_phone, nudge)

        logger.info("Text pipeline complete: session=%s user=%s", session_id, user_id)

    except Exception as e:
        logger.error("Text pipeline error: %s", e, exc_info=True)
        try:
            await WhatsAppService.send_text_message(
                from_phone, "⚠️ Something went wrong. Please try again."
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Background task: full pipeline
# ---------------------------------------------------------------------------

async def _run_whatsapp_pipeline(
    from_phone: str,
    media_url: str,
    user_id: str,
    user_name: str,
) -> None:
    tmp_path: Optional[str] = None
    received_at = datetime.utcnow().isoformat()
    try:
        # Download audio from Twilio
        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        audio_bytes: Optional[bytes] = None

        if media_url:
            try:
                auth = (sid, token) if sid and token else None
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(media_url, auth=auth)
                    resp.raise_for_status()
                    audio_bytes = resp.content
            except Exception as e:
                logger.error("WhatsApp audio download failed: %s", e)
                await WhatsAppService.send_text_message(
                    from_phone, "⚠️ Could not download audio. Please try again."
                )
                return

        # Save to temp OGG file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
            if audio_bytes:
                tmp.write(audio_bytes)

        # Create session (auto-consent: doctor opted in by sending the voice note)
        clinic_id = await _get_user_clinic_id(user_id)
        session = await _repo.create_session(
            user_id=user_id,
            doctor_name=user_name,
            cloud_ai_consent=True,
            mode=ModeEnum.health,
            initiated_by="whatsapp",
            clinic_id=clinic_id,
        )
        session_id = session.id
        await _stamp_session(session_id, received_at=received_at)

        # Transcribe
        if not audio_bytes or settings.allow_stub_asr or not settings.sarvam_api_key:
            transcript = (
                "Patient presents with fever for 3 days, 101°F. "
                "Prescribed paracetamol 500mg twice daily for 5 days. "
                "CBC and CRP ordered. Review in 3 days if not improving."
            )
        else:
            session.audio_file_path = tmp_path
            session.status = StatusEnum.audio_uploaded
            await _repo.update_session(session)
            try:
                result = await _asr.transcribe(tmp_path, "hi-IN")
                transcript = result["transcript"]
            except Exception as e:
                logger.error("WhatsApp ASR failed for session %s: %s", session_id, e)
                await WhatsAppService.send_text_message(
                    from_phone, "⚠️ Transcription failed. Please re-record and try again."
                )
                return

        session.transcript = transcript
        session.status = StatusEnum.transcribed
        await _repo.update_session(session)

        # Clinical extraction pipeline (deterministic, zero-LLM) + Gemini SOAP prose
        facts = _extractor.extract(transcript)
        state = _memory.resolve_memory([facts])
        soap = await _soap_gen.generate_soap_async(state)
        cds = _cds_engine.generate_cds(state)

        session.clinical_facts = facts
        session.memory_state = state
        session.soap_note = soap
        session.cds_suggestions = cds
        session.status = StatusEnum.complete
        await _repo.update_session(session)

        # Auto-create assistant tasks + billing record
        await _auto_create_tasks(session_id, user_id, facts)
        await _write_billing_record(session_id, user_id)

        # Hold for QC review if enabled (default: off — demo-safe)
        if settings.hold_for_review:
            await _stamp_session(session_id, hold_for_review="1")
            logger.info("WhatsApp pipeline held for review: session=%s", session_id)
            return

        # Send SOAP summary back to doctor
        reply = _format_soap_reply(soap, facts, session_id, user_name, user_id)
        await WhatsAppService.send_text_message(from_phone, reply)
        await _stamp_session(session_id, delivered_at=datetime.utcnow().isoformat())

        # If labs or follow-up were found, ask doctor for patient phone
        has_labs = bool(facts.get("investigations"))
        has_followup = bool(facts.get("follow_up"))
        if has_labs or has_followup:
            nudge_parts = []
            if has_followup:
                nudge_parts.append("follow-up reminder")
            if has_labs:
                nudge_parts.append("lab orders")
            nudge = (
                f"📲 Patient ko seedha {' aur '.join(nudge_parts)} bhejna hai?\n\n"
                f"Reply karein: *P +91XXXXXXXXXX*"
            )
            await WhatsAppService.send_text_message(from_phone, nudge)

        logger.info("WhatsApp pipeline complete: session=%s user=%s", session_id, user_id)

    except Exception as e:
        logger.error("WhatsApp pipeline unhandled error: %s", e, exc_info=True)
        try:
            await WhatsAppService.send_text_message(
                from_phone, "⚠️ Something went wrong. Please try again or log in to Lipi to review."
            )
        except Exception:
            pass
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


async def _write_billing_record(session_id: str, user_id: str) -> None:
    """Write a per-consultation fee record to consultation_billing — distinct from
    billing_records, which tracks Lipi's own SaaS/plan billing. `id` is an
    auto-increment integer PK — never supply a UUID for it.
    """
    from datetime import datetime
    amount = settings.consultation_fee_rupees or 0
    if amount <= 0:
        return
    try:
        async with db_connect() as db:
            async with db.execute(
                "SELECT 1 FROM consultation_billing WHERE session_id = ?", (session_id,)
            ) as cur:
                if await cur.fetchone():
                    return
            await db.execute(
                "INSERT INTO consultation_billing (session_id, user_id, amount, currency, notes, created_at) "
                "VALUES (?, ?, ?, 'INR', 'WhatsApp consultation', ?)",
                (session_id, user_id, amount, datetime.utcnow()),
            )
            await db.commit()
    except Exception as exc:
        logger.warning("Billing record write failed: %s", exc)


async def _auto_create_tasks(session_id: str, user_id: str, facts: dict) -> None:
    """Mirror of routes_notes._auto_create_tasks — avoids circular import."""
    import uuid
    from datetime import datetime

    now = datetime.utcnow().isoformat()
    rows = []

    investigations = facts.get("investigations") or []
    if investigations:
        titles = ", ".join(str(i) for i in investigations[:3])
        suffix = f" (+{len(investigations)-3} more)" if len(investigations) > 3 else ""
        rows.append((str(uuid.uuid4()), session_id, user_id, "order_investigations",
                     f"Order investigations: {titles}{suffix}", now))

    follow_up = facts.get("follow_up")
    if follow_up:
        fu_text = follow_up[0] if isinstance(follow_up, list) else str(follow_up)
        rows.append((str(uuid.uuid4()), session_id, user_id, "follow_up",
                     f"Schedule follow-up: {fu_text}", now))

    allergies = facts.get("allergies") or []
    if allergies:
        allergy_text = ", ".join(str(a) for a in allergies[:2])
        rows.append((str(uuid.uuid4()), session_id, user_id, "document_allergy",
                     f"Document allergy in chart: {allergy_text}", now))

    rows.append((str(uuid.uuid4()), session_id, user_id, "review_prescription",
                 "Review and share prescription with patient", now))

    async with db_connect() as db:
        for row in rows:
            await db.execute(
                "INSERT INTO assistant_tasks (id, session_id, user_id, task_type, title, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'open', ?) ON CONFLICT (id) DO NOTHING",
                row,
            )
        await db.commit()


# ---------------------------------------------------------------------------
# Patient message handler (intake flow + appointment booking)
# ---------------------------------------------------------------------------

async def _handle_patient_message(from_digits: str, from_phone: str, body: str) -> str:
    """Route inbound message from a non-doctor phone."""
    from app.services.patient_intake import get_active_intake, start_intake, advance_intake
    from app.services.appointment_booking import get_available_slots, book_appointment

    body_lower = body.lower().strip()

    # Appointment booking trigger
    if any(kw in body_lower for kw in ("book", "appointment", "appoint", "slot", "date", "milna", "booking")):
        # Check if they have an active intake with a clinic linked
        intake = await get_active_intake(from_digits)
        if intake and intake.get("clinic_user_id"):
            slots = await get_available_slots(intake["clinic_user_id"])
            if slots:
                lines = ["📅 *Available appointment slots:*\n"]
                for i, s in enumerate(slots, 1):
                    lines.append(f"{i}. {s['label']}")
                lines.append("\nSlot number reply karein (jaise: *1*)")
                return "\n".join(lines)
            return "Abhi koi slot available nahi hai. Seedhe clinic call karein. 📞"
        return "Pehle apna intake form bharo ya clinic code batao. Type karein *hi* to start."

    # Slot selection (digit reply after seeing slot list)
    if body_lower in ("1", "2", "3", "4", "5"):
        intake = await get_active_intake(from_digits)
        if intake and intake.get("clinic_user_id"):
            slots = await get_available_slots(intake["clinic_user_id"])
            idx = int(body_lower) - 1
            if 0 <= idx < len(slots):
                patient_name = intake.get("patient_name") or "Patient"
                complaint = intake.get("chief_complaint") or ""
                appt_id = await book_appointment(
                    intake["clinic_user_id"], from_digits, patient_name,
                    slots[idx]["datetime"], complaint,
                )
                return (
                    f"✅ *Appointment confirmed!*\n\n"
                    f"📅 {slots[idx]['label']}\n\n"
                    f"Appointment ID: `{appt_id[:8]}`\n"
                    f"Clinic mein waqt par aayein. 🏥"
                )

    # Check for active intake session
    intake = await get_active_intake(from_digits)
    if intake:
        return await advance_intake(intake, body, from_phone)

    # Fresh patient — start intake if they greet
    greetings = ("hi", "hello", "helo", "namaste", "hey", "hii", "hy", "start", "help")
    if body_lower in greetings or len(body_lower) < 8:
        return await start_intake(from_digits)

    return (
        "Namaste! 🙏 Apne doctor ke paas jane se pehle brief bhejein.\n\n"
        "Type karein *hi* to start."
    )


# ---------------------------------------------------------------------------
# Doctor sending patient phone: "P +91XXXXXXXXXX"
# ---------------------------------------------------------------------------

async def _handle_doctor_patient_phone(doctor_user_id: str, patient_phone_digits: str, doctor_wa_phone: str) -> None:
    """
    Doctor replied with patient phone after receiving SOAP summary.
    Find their most recent session (last 24h), update patient_phone, and trigger dispatch.
    """
    from app.services.follow_up_scheduler import schedule_follow_up
    from app.services.diagnostic_dispatch import dispatch_lab_order_to_patient

    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    async with db_connect() as db:
        async with db.execute(
            "SELECT id, clinical_facts, patient_name, doctor_name FROM sessions WHERE user_id=? AND created_at>=? ORDER BY created_at DESC LIMIT 1",
            (doctor_user_id, cutoff),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            await WhatsAppService.send_text_message(
                doctor_wa_phone, "Pichle 24 ghante mein koi session nahi mila. Pehle ek consultation start karein."
            )
            return

        session_id, facts_json, patient_name, doctor_name = row

        await db.execute(
            "UPDATE sessions SET patient_phone=? WHERE id=?",
            (patient_phone_digits, session_id),
        )
        await db.commit()

    facts = json.loads(facts_json) if facts_json else {}
    triggered = []

    follow_up = facts.get("follow_up")
    if follow_up:
        fu_text = follow_up[0] if isinstance(follow_up, list) else str(follow_up)
        try:
            await schedule_follow_up(session_id, doctor_user_id, patient_phone_digits, patient_name, doctor_name or "", fu_text)
            triggered.append("follow-up reminder")
        except Exception as exc:
            logger.warning("Patient phone follow-up trigger failed: %s", exc)

    investigations = facts.get("investigations") or []
    if investigations:
        try:
            await dispatch_lab_order_to_patient(session_id, doctor_user_id, patient_phone_digits, patient_name, doctor_name or "", investigations)
            triggered.append("lab orders")
        except Exception as exc:
            logger.warning("Patient phone lab dispatch failed: %s", exc)

    if triggered:
        done_str = " aur ".join(triggered)
        await WhatsAppService.send_text_message(
            doctor_wa_phone, f"✅ Patient ko {done_str} bhej diye (…{patient_phone_digits[-4:]})."
        )
    else:
        await WhatsAppService.send_text_message(
            doctor_wa_phone, "Phone save ho gaya, lekin koi follow-up ya labs nahi mili is session mein."
        )


# ---------------------------------------------------------------------------
# Patient reply dispatcher
# ---------------------------------------------------------------------------

async def _handle_patient_reply(body: str, interaction: dict) -> str:
    """Route a patient's text reply to the correct handler based on interaction type."""
    normalized = body.strip().lower()
    itype = interaction["type"]
    ref_id = interaction["reference_id"]
    doctor_user_id = interaction["doctor_user_id"]

    if itype == "follow_up_confirm":
        if normalized in ("haan", "han", "ha", "yes", "y", "ok", "okay", "हाँ", "हां"):
            return await handle_haan(ref_id, doctor_user_id)
        elif normalized in ("nahi", "nhi", "no", "n", "नहीं", "nahi"):
            return await handle_nahi(ref_id)
        else:
            # Unrecognized reply — re-prompt
            return (
                "Samajh nahi aaya 🙏\n\n"
                "Reply karein *HAAN* agar aap aa sakte hain, "
                "ya *NAHI* agar aapko reschedule karna hai."
            )
    else:
        return "Aapka reply mil gaya. Clinic se jald hi contact karenge. 🙏"


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Twilio inbound WhatsApp webhook. Expects application/x-www-form-urlencoded."""
    form = await request.form()
    form_data = dict(form)

    # Validate Twilio signature (skipped in mock mode)
    sig = request.headers.get("X-Twilio-Signature", "")
    request_url = str(request.url)
    if not _valid_twilio_signature(request_url, form_data, sig):
        logger.warning("WhatsApp webhook: invalid Twilio signature from %s", request.client)
        return Response(content=_TWIML_EMPTY, media_type="text/xml", status_code=403)

    from_raw = form_data.get("From", "")
    from_phone = from_raw.replace("whatsapp:", "").strip()
    from_digits = _normalize_phone(from_raw)
    body = form_data.get("Body", "").strip().lower()
    num_media = int(form_data.get("NumMedia", 0))
    media_url = form_data.get("MediaUrl0", "")
    media_type = form_data.get("MediaContentType0", "")

    logger.info("WhatsApp inbound: from=%s media=%d type=%s", from_phone, num_media, media_type)

    # Handle help text
    if num_media == 0 and body in ("help", "hi", "hello", "start", ""):
        return Response(content=_TWIML_HELP, media_type="text/xml")

    # Doctor sending patient phone: "P +91XXXXXXXXXX" or "patient +91XXXXXXXXXX"
    if num_media == 0 and body and (body.lower().startswith("p ") or body.lower().startswith("patient ")):
        raw_phone = body.split(None, 1)[1] if " " in body else ""
        phone_digits = "".join(c for c in raw_phone if c.isdigit())
        if len(phone_digits) >= 10:
            doc = await _lookup_user_by_phone(from_digits)
            if doc:
                import asyncio
                asyncio.create_task(_handle_doctor_patient_phone(doc["id"], phone_digits, from_phone))
                return Response(content=_TWIML_EMPTY, media_type="text/xml")

    # Check if this is a patient replying to a pending interaction (HAAN / NAHI)
    if num_media == 0 and body:
        interaction = await get_pending_interaction(from_digits)
        if interaction:
            reply_text = await _handle_patient_reply(body, interaction)
            await mark_interaction_responded(interaction["id"])
            safe = reply_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return Response(
                content=f'<?xml version="1.0"?><Response><Message>{safe}</Message></Response>',
                media_type="text/xml",
            )

    # Look up doctor — if not found, route as patient (intake or appointment booking)
    user = await _lookup_user_by_phone(from_digits)
    if not user:
        if num_media == 0 and body:
            reply_text = await _handle_patient_message(from_digits, from_phone, body)
        else:
            reply_text = "Namaste! 🙏 Text message bhejein — voice notes sirf doctors ke liye hain."
        safe = reply_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Response(
            content=f'<?xml version="1.0"?><Response><Message>{safe}</Message></Response>',
            media_type="text/xml",
        )

    # Doctor sent a bare phone number → patient dispatch shortcut (no "P " prefix needed)
    if num_media == 0:
        raw_body_strip = form_data.get("Body", "").strip()
        _digs = "".join(c for c in raw_body_strip if c.isdigit())
        _stripped_for_phone = raw_body_strip.replace("+", "").replace(" ", "").replace("-", "")
        if len(_digs) >= 10 and _stripped_for_phone == _digs:
            import asyncio
            asyncio.create_task(_handle_doctor_patient_phone(user["id"], _digs, from_phone))
            return Response(
                content=f'<?xml version="1.0"?><Response><Message>📤 Sending to patient (…{_digs[-4:]})…</Message></Response>',
                media_type="text/xml",
            )

    # Text-only message — if long enough treat as typed transcript, else show help
    if num_media == 0:
        raw_body = form_data.get("Body", "").strip()
        if len(raw_body) >= 20:
            background_tasks.add_task(
                _run_text_pipeline,
                from_phone=from_phone,
                transcript=raw_body,
                user_id=user["id"],
                user_name=user["name"],
            )
            return Response(
                content='<?xml version="1.0"?><Response><Message>📋 Processing your consultation… I\'ll send the note in a moment.</Message></Response>',
                media_type="text/xml",
            )
        return Response(content=_TWIML_HELP, media_type="text/xml")

    # Voice / audio message — kick off pipeline in background, ACK immediately
    is_audio = media_type.startswith("audio/") or media_type.startswith("video/")
    if not is_audio:
        return Response(
            content='<?xml version="1.0"?><Response><Message>Please send a voice note of the consultation.</Message></Response>',
            media_type="text/xml",
        )

    background_tasks.add_task(
        _run_whatsapp_pipeline,
        from_phone=from_phone,
        media_url=media_url,
        user_id=user["id"],
        user_name=user["name"],
    )

    return Response(content=_TWIML_ACK, media_type="text/xml")


@router.get("/whatsapp/webhook")
async def whatsapp_webhook_verify(request: Request) -> Response:
    """Twilio sometimes sends a GET to verify the endpoint on first setup. Return 200."""
    return Response(content=_TWIML_EMPTY, media_type="text/xml")

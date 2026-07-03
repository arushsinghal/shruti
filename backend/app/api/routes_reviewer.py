"""Internal QC reviewer dashboard API.

Reviewers see WhatsApp-originated sessions, can edit facts/SOAP, approve (sends sign link
to doctor) or reject (flags for re-transcription). When HOLD_FOR_REVIEW=False (default),
sessions are already sent to doctor — dashboard is read-only monitoring. When True,
reviewer approval triggers delivery.
"""
import json
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.services.icd10_map import annotate_diagnoses
from app.services.whatsapp_service import WhatsAppService
from app.storage.db import db_connect
from app.utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _json_parse(v):
    if not v:
        return {}
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return {}


def _confidence_scores(facts: dict) -> dict:
    """
    Heuristic confidence per extracted fact.
    High confidence: vitals (structured regex), exact keyword diagnoses.
    Medium: medications, investigations.
    Lower: inferred diagnoses, fuzzy matches.
    Will be replaced by per-extraction tracking once the extractor instruments itself.
    """
    scores: dict[str, float] = {}
    for dx in facts.get("diagnoses") or []:
        scores[f"dx:{dx}"] = 0.85
    for med in facts.get("medications") or []:
        name = med if isinstance(med, str) else med.get("name", str(med))
        scores[f"med:{name}"] = 0.88
    for vital in facts.get("vitals") or []:
        scores[f"vital:{vital}"] = 0.92
    for inv in facts.get("investigations") or []:
        scores[f"inv:{inv}"] = 0.80
    for sx in facts.get("symptoms") or []:
        scores[f"sx:{sx}"] = 0.75
    return scores


# ---------------------------------------------------------------------------
# Review queue
# ---------------------------------------------------------------------------

@router.get("/internal/review-queue")
async def get_review_queue(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Returns recent WhatsApp-originated sessions.
    When HOLD_FOR_REVIEW=True: only held sessions.
    When False: last 50 sessions for monitoring.
    """
    async with db_connect() as db:
        if settings.hold_for_review:
            query = """
                SELECT id, patient_name, doctor_name, created_at,
                       received_at, delivered_at, signed_at,
                       hold_for_review, reviewer_action, status
                FROM sessions
                WHERE initiated_by = 'whatsapp' AND hold_for_review = 1
                ORDER BY received_at DESC NULLS LAST, created_at DESC
                LIMIT ?
            """
        else:
            query = """
                SELECT id, patient_name, doctor_name, created_at,
                       received_at, delivered_at, signed_at,
                       hold_for_review, reviewer_action, status
                FROM sessions
                WHERE initiated_by = 'whatsapp'
                ORDER BY created_at DESC
                LIMIT ?
            """
        async with db.execute(query, (limit,)) as cur:
            rows = await cur.fetchall()

    sessions = []
    for r in rows:
        recv = r[4]
        deliv = r[5]
        sla_seconds = None
        if recv and deliv:
            try:
                t0 = datetime.fromisoformat(recv.rstrip("Z"))
                t1 = datetime.fromisoformat(deliv.rstrip("Z"))
                sla_seconds = int((t1 - t0).total_seconds())
            except Exception:
                pass

        sessions.append({
            "id": r[0],
            "patient_name": r[1] or "Unknown",
            "doctor_name": r[2] or "—",
            "created_at": r[3],
            "received_at": recv,
            "delivered_at": deliv,
            "signed_at": r[6],
            "held": bool(r[7]),
            "reviewer_action": r[8],
            "status": r[9],
            "sla_seconds": sla_seconds,
        })

    return {
        "hold_mode": settings.hold_for_review,
        "count": len(sessions),
        "sessions": sessions,
    }


@router.get("/internal/review-queue/{session_id}")
async def get_review_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Full session detail for the reviewer: transcript, facts, SOAP, confidence scores."""
    async with db_connect() as db:
        async with db.execute(
            """SELECT id, patient_name, doctor_name, transcript,
                      clinical_facts, soap_note, received_at, delivered_at,
                      signed_at, hold_for_review, reviewer_action, reviewer_note,
                      patient_phone, status, user_id
               FROM sessions WHERE id = ?""",
            (session_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    facts = _json_parse(row[4])
    soap = _json_parse(row[5])
    diagnoses_annotated = annotate_diagnoses(facts.get("diagnoses") or [])
    confidence = _confidence_scores(facts)

    return {
        "id": row[0],
        "patient_name": row[1] or "Unknown",
        "doctor_name": row[2] or "—",
        "transcript": row[3] or "",
        "facts": facts,
        "soap": soap,
        "diagnoses_annotated": diagnoses_annotated,
        "confidence": confidence,
        "received_at": row[6],
        "delivered_at": row[7],
        "signed_at": row[8],
        "held": bool(row[9]),
        "reviewer_action": row[10],
        "reviewer_note": row[11],
        "patient_phone": row[12],
        "status": row[13],
        "doctor_user_id": row[14],
    }


class EditRequest(BaseModel):
    facts: dict | None = None
    soap: dict | None = None
    reviewer_note: str = ""


class ApproveRequest(BaseModel):
    reviewer_note: str = ""
    doctor_phone: str = ""


@router.put("/internal/review-queue/{session_id}/edit")
async def edit_session(
    session_id: str,
    body: EditRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update facts and/or SOAP before approving."""
    reviewer_id = str(current_user["id"])
    updates: list[tuple] = []
    params: list = []

    if body.facts is not None:
        updates.append("clinical_facts = ?")
        params.append(json.dumps(body.facts))
    if body.soap is not None:
        updates.append("soap_note = ?")
        params.append(json.dumps(body.soap))
    if body.reviewer_note:
        updates.append("reviewer_note = ?")
        params.append(body.reviewer_note)
    updates.append("reviewer_id = ?")
    params.append(reviewer_id)

    if not updates:
        return {"success": True, "message": "Nothing to update"}

    params.append(session_id)
    async with db_connect() as db:
        await db.execute(
            f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    return {"success": True}


@router.post("/internal/review-queue/{session_id}/approve")
async def approve_session(
    session_id: str,
    body: ApproveRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Approve session: mark reviewed, send sign link to doctor's WhatsApp.
    Works in both hold and non-hold mode.
    """
    reviewer_id = str(current_user["id"])
    now = datetime.now(timezone.utc).isoformat()

    async with db_connect() as db:
        async with db.execute(
            """SELECT soap_note, clinical_facts, doctor_name, user_id,
                      patient_phone, hold_for_review, delivered_at
               FROM sessions WHERE id = ?""",
            (session_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    soap = _json_parse(row[0])
    facts = _json_parse(row[1])
    doctor_name = row[2] or "Doctor"
    doctor_user_id = row[3]
    patient_phone = row[4]
    held = bool(row[5])
    already_delivered = bool(row[6])

    # Generate sign URL
    sign_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    sign_payload = {
        "sub": session_id,
        "session_id": session_id,
        "user_id": str(doctor_user_id),
        "scope": "doctor_session_sign",
        "exp": sign_expires,
    }
    sign_token = jwt.encode(sign_payload, settings.secret_key, algorithm=settings.algorithm)
    base = settings.app_base_url.rstrip("/")
    sign_url = f"{base}/sign/{sign_token}"

    # Build reply (brief version for re-send)
    assessment = ""
    if isinstance(soap, dict):
        assessment = soap.get("A") or soap.get("assessment") or soap.get("Assessment") or ""
        if isinstance(assessment, dict):
            assessment = assessment.get("diagnosis") or assessment.get("text") or str(assessment)

    msg_lines = [f"✅ *Note ready for review* — {doctor_name}", ""]
    if assessment:
        msg_lines += [f"📋 {str(assessment).strip()[:200]}", ""]
    msg_lines.append(f"✍️ Sign: {sign_url}")
    message = "\n".join(msg_lines)

    # Send to doctor's WhatsApp
    doctor_phone = body.doctor_phone
    if not doctor_phone:
        # Look up from doctor profile
        try:
            async with db_connect() as db:
                async with db.execute(
                    "SELECT whatsapp_phone FROM doctor_profiles WHERE user_id = ?",
                    (str(doctor_user_id),),
                ) as cur:
                    prow = await cur.fetchone()
                    if prow:
                        doctor_phone = prow[0] or ""
        except Exception:
            pass

    wa_result = {"success": False, "error": "no_phone"}
    if doctor_phone:
        wa_result = await WhatsAppService.send_text_message(doctor_phone, message)

    # Mark delivered
    async with db_connect() as db:
        await db.execute(
            """UPDATE sessions
               SET hold_for_review = 0, reviewer_action = 'approved',
                   reviewer_id = ?, reviewer_note = ?, delivered_at = ?
               WHERE id = ?""",
            (reviewer_id, body.reviewer_note or "", now, session_id),
        )
        await db.commit()

    return {
        "success": True,
        "sign_url": sign_url,
        "whatsapp_sent": wa_result.get("success", False),
        "doctor_phone": doctor_phone,
    }


@router.post("/internal/review-queue/{session_id}/reject")
async def reject_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Mark session as needing re-transcription."""
    reviewer_id = str(current_user["id"])
    async with db_connect() as db:
        await db.execute(
            """UPDATE sessions
               SET reviewer_action = 'rejected', reviewer_id = ?, hold_for_review = 0
               WHERE id = ?""",
            (reviewer_id, session_id),
        )
        await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Ops dashboard stats
# ---------------------------------------------------------------------------

@router.get("/internal/ops-stats")
async def get_ops_stats(current_user: dict = Depends(get_current_user)) -> dict:
    """Rolling stats for the ops dashboard."""
    from datetime import date, timedelta

    today = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    month_start = date.today().replace(day=1).isoformat()

    stats: dict = {
        "hold_mode": settings.hold_for_review,
        "today": {},
        "week": {},
        "month": {},
        "sla": {},
        "quality": {},
        "queue": {},
    }

    try:
        async with db_connect() as db:
            # Session counts
            for period_key, start in [("today", today), ("week", week_start), ("month", month_start)]:
                async with db.execute(
                    "SELECT COUNT(*) FROM sessions WHERE initiated_by='whatsapp' AND created_at >= ?",
                    (start,),
                ) as cur:
                    stats[period_key]["total"] = (await cur.fetchone())[0]

                async with db.execute(
                    "SELECT COUNT(*) FROM sessions WHERE initiated_by='whatsapp' AND signed_at IS NOT NULL AND created_at >= ?",
                    (start,),
                ) as cur:
                    stats[period_key]["signed"] = (await cur.fetchone())[0]

                async with db.execute(
                    "SELECT COUNT(*) FROM sessions WHERE initiated_by='whatsapp' AND delivered_at IS NOT NULL AND created_at >= ?",
                    (start,),
                ) as cur:
                    stats[period_key]["delivered"] = (await cur.fetchone())[0]

            # SLA: avg delivery time (received_at → delivered_at) over last 24h
            async with db.execute(
                """SELECT received_at, delivered_at FROM sessions
                   WHERE initiated_by='whatsapp' AND received_at IS NOT NULL
                     AND delivered_at IS NOT NULL AND created_at >= ?""",
                (today,),
            ) as cur:
                rows = await cur.fetchall()

            sla_values = []
            sla_breaches = 0
            for r in rows:
                try:
                    t0 = datetime.fromisoformat(r[0].rstrip("Z"))
                    t1 = datetime.fromisoformat(r[1].rstrip("Z"))
                    secs = int((t1 - t0).total_seconds())
                    sla_values.append(secs)
                    if secs > 300:  # > 5 minutes = breach
                        sla_breaches += 1
                except Exception:
                    pass

            stats["sla"]["avg_seconds_24h"] = int(sum(sla_values) / len(sla_values)) if sla_values else None
            stats["sla"]["breach_count_24h"] = sla_breaches
            stats["sla"]["sample_count"] = len(sla_values)
            stats["sla"]["target_seconds"] = 180  # 3 minutes

            # Queue
            async with db.execute(
                "SELECT COUNT(*) FROM sessions WHERE initiated_by='whatsapp' AND hold_for_review = 1",
            ) as cur:
                stats["queue"]["held"] = (await cur.fetchone())[0]

            # Quality: reviewer edits vs approves
            async with db.execute(
                """SELECT reviewer_action, COUNT(*) FROM sessions
                   WHERE reviewer_action IS NOT NULL AND created_at >= ?
                   GROUP BY reviewer_action""",
                (week_start,),
            ) as cur:
                action_rows = await cur.fetchall()
            action_map = {r[0]: r[1] for r in action_rows}
            approved = action_map.get("approved", 0)
            rejected = action_map.get("rejected", 0)
            total_reviewed = approved + rejected
            stats["quality"]["approved_this_week"] = approved
            stats["quality"]["rejected_this_week"] = rejected
            stats["quality"]["approval_rate"] = round(approved / total_reviewed, 2) if total_reviewed else None

    except Exception as exc:
        logger.warning("ops-stats query error: %s", exc)

    return stats

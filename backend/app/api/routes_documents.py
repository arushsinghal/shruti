"""Document generation endpoints — prescription, referral, OPD register, TPA claim."""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.services.pdf_generator import (
    build_opd_register_pdf,
    build_prescription_pdf,
    build_referral_pdf,
    build_tpa_claim_pdf,
)
from app.storage.db import db_connect
from app.storage.repository import SessionRepository

router = APIRouter()
_repo = SessionRepository()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_session_or_404(session_id: str, user_id: str):
    session = await _repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _get_doctor_profile(user_id: str) -> dict:
    param = int(user_id) if str(user_id).isdigit() else user_id
    async with db_connect() as db:
        try:
            async with db.execute(
                "SELECT full_name, nmc_number, specialization FROM users WHERE id=?",
                (param,),
            ) as cur:
                row = await cur.fetchone()
            if not row:
                return {"name": "Unknown", "nmc": "", "specialization": ""}
            return {"name": row[0] or "Unknown", "nmc": row[1] or "", "specialization": row[2] or ""}
        except Exception:
            async with db.execute(
                "SELECT full_name FROM users WHERE id=?",
                (param,),
            ) as cur:
                row = await cur.fetchone()
            return {"name": (row[0] if row else None) or "Unknown", "nmc": "", "specialization": ""}


async def _get_clinic_info(user_id: str) -> dict:
    try:
        async with db_connect() as db:
            async with db.execute(
                """
                SELECT c.name, c.address, c.phone
                FROM clinics c
                JOIN clinic_members cm ON cm.clinic_id = c.id
                WHERE cm.user_id = ?
                LIMIT 1
                """,
                (str(user_id),),
            ) as cur:
                row = await cur.fetchone()
    except Exception:
        return {"name": "My Clinic", "address": "", "phone": ""}
    if not row:
        return {"name": "My Clinic", "address": "", "phone": ""}
    return {"name": row[0] or "My Clinic", "address": row[1] or "", "phone": row[2] or ""}


def _stream_pdf(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _date_str(session) -> str:
    try:
        return str(session.created_at)[:10]
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 1. Prescription
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/prescription")
async def download_prescription(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate a formatted prescription PDF from the completed session."""
    user_id = str(current_user["id"])
    session = await _get_session_or_404(session_id, user_id)
    doctor = await _get_doctor_profile(user_id)
    clinic = await _get_clinic_info(user_id)

    pdf = build_prescription_pdf(
        session_id=session_id,
        patient_name=session.patient_name or "—",
        patient_age=getattr(session, "patient_age", None) or "—",
        patient_sex=getattr(session, "patient_sex", None) or "—",
        doctor_name=session.doctor_name or doctor["name"],
        doctor_nmc=doctor["nmc"],
        doctor_specialization=doctor.get("specialization", ""),
        clinic_name=clinic["name"],
        clinic_address=clinic["address"],
        clinic_phone=clinic["phone"],
        soap_raw=session.soap_note,
        facts_raw=session.clinical_facts,
        date_str=_date_str(session),
    )
    fname = f"prescription-{session_id[:8]}-{_date_str(session)}.pdf"
    return _stream_pdf(pdf, fname)


# ---------------------------------------------------------------------------
# 2. Referral Letter
# ---------------------------------------------------------------------------

class ReferralRequest(BaseModel):
    to_doctor: str
    to_specialty: str = ""
    reason: str = ""
    urgency: str = "routine"  # "routine" | "urgent"


@router.post("/sessions/{session_id}/referral")
async def generate_referral(
    session_id: str,
    body: ReferralRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a referral letter PDF for the session."""
    user_id = str(current_user["id"])
    session = await _get_session_or_404(session_id, user_id)
    doctor = await _get_doctor_profile(user_id)
    clinic = await _get_clinic_info(user_id)

    pdf = build_referral_pdf(
        session_id=session_id,
        patient_name=session.patient_name or "—",
        patient_age=getattr(session, "patient_age", None) or "—",
        patient_sex=getattr(session, "patient_sex", None) or "—",
        doctor_name=session.doctor_name or doctor["name"],
        doctor_nmc=doctor["nmc"],
        clinic_name=clinic["name"],
        clinic_phone=clinic["phone"],
        to_doctor=body.to_doctor,
        to_specialty=body.to_specialty,
        reason=body.reason,
        urgency=body.urgency,
        soap_raw=session.soap_note,
        facts_raw=session.clinical_facts,
        date_str=_date_str(session),
    )
    fname = f"referral-{session_id[:8]}-{_date_str(session)}.pdf"
    return _stream_pdf(pdf, fname)


# ---------------------------------------------------------------------------
# 3. OPD Register
# ---------------------------------------------------------------------------

@router.get("/clinic/opd-register")
async def opd_register_pdf(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an OPD register PDF for a given date (YYYY-MM-DD).
    Defaults to today. Covers all sessions for the user's clinic.
    """
    user_id = str(current_user["id"])
    target_date = date or datetime.utcnow().strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    day_start = dt.strftime("%Y-%m-%d") + "T00:00:00"
    day_end = (dt + timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00"

    clinic = await _get_clinic_info(user_id)

    async with db_connect() as db:
        # Include sessions from this user OR any clinic member
        async with db.execute(
            """
            SELECT s.id, s.patient_name, s.patient_age, s.patient_sex,
                   s.doctor_name, s.created_at, s.clinical_facts, s.status
            FROM sessions s
            WHERE s.created_at >= ? AND s.created_at < ?
              AND (
                s.user_id = ?
                OR s.user_id IN (
                    SELECT cm2.user_id FROM clinic_members cm2
                    JOIN clinic_members cm1 ON cm1.clinic_id = cm2.clinic_id
                    WHERE cm1.user_id = ?
                )
              )
            ORDER BY s.created_at
            """,
            (day_start, day_end, user_id, user_id),
        ) as cur:
            rows = await cur.fetchall()

    sessions = [
        {
            "id": r[0],
            "patient_name": r[1],
            "patient_age": r[2],
            "patient_sex": r[3],
            "doctor_name": r[4],
            "created_at": str(r[5]),
            "clinical_facts": r[6],
            "status": r[7],
        }
        for r in rows
    ]

    pdf = build_opd_register_pdf(
        sessions=sessions,
        date_label=dt.strftime("%d %B %Y"),
        clinic_name=clinic["name"],
    )
    fname = f"opd-register-{target_date}.pdf"
    return _stream_pdf(pdf, fname)


# ---------------------------------------------------------------------------
# 4. TPA / Insurance Claim
# ---------------------------------------------------------------------------

class TpaClaimRequest(BaseModel):
    policy_number: str = ""
    insurer_name: str = ""
    tpa_name: str = ""


@router.post("/sessions/{session_id}/tpa-claim")
async def generate_tpa_claim(
    session_id: str,
    body: TpaClaimRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a pre-filled TPA insurance claim PDF for the session."""
    user_id = str(current_user["id"])
    session = await _get_session_or_404(session_id, user_id)
    doctor = await _get_doctor_profile(user_id)
    clinic = await _get_clinic_info(user_id)

    # Fetch billing records for itemized bill
    billing_rows: list[dict] = []
    async with db_connect() as db:
        async with db.execute(
            "SELECT amount, currency, notes FROM consultation_billing WHERE session_id=?",
            (session_id,),
        ) as cur:
            for r in await cur.fetchall():
                billing_rows.append({"amount": r[0], "currency": r[1], "notes": r[2]})

    from app.utils.config import settings
    consultation_fee = settings.consultation_fee_rupees or 0

    pdf = build_tpa_claim_pdf(
        session_id=session_id,
        patient_name=session.patient_name or "—",
        patient_age=getattr(session, "patient_age", None) or "—",
        patient_sex=getattr(session, "patient_sex", None) or "—",
        policy_number=body.policy_number,
        insurer_name=body.insurer_name,
        tpa_name=body.tpa_name,
        doctor_name=session.doctor_name or doctor["name"],
        doctor_nmc=doctor["nmc"],
        clinic_name=clinic["name"],
        clinic_address=clinic["address"],
        consultation_fee=consultation_fee,
        soap_raw=session.soap_note,
        facts_raw=session.clinical_facts,
        billing_rows=billing_rows,
        date_str=_date_str(session),
    )
    fname = f"tpa-claim-{session_id[:8]}-{_date_str(session)}.pdf"
    return _stream_pdf(pdf, fname)

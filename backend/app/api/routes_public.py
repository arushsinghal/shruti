"""Public unauthenticated routes for patient prescription retrieval."""
import json
import uuid
from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from jose import JWTError, ExpiredSignatureError, jwt

from app.storage.db import db_connect
from app.storage.repository import SessionRepository
from app.utils.config import settings
from app.utils.rate_limit import check_rate_limit
from app.services.prescription_renderer import render_prescription_html
from app.services.pdf_generator import build_prescription_pdf
from app.services.whatsapp_service import WhatsAppService
from app.services.icd10_map import annotate_diagnoses
from app.services.investigation_order_renderer import render_investigation_order_html

logger = logging.getLogger(__name__)
router = APIRouter()
repo = SessionRepository()


class VerifyAccessRequest(BaseModel):
    patient_name: str = ""
    initials: str = ""
    year_of_birth: str = ""


def _normalize(s: str) -> str:
    """Lowercase, strip all punctuation/whitespace to compare string keys stably."""
    return "".join(c.lower() for c in s if c.isalnum())


def _get_initials(name: str) -> str:
    """Extract initials from a full name string."""
    parts = [p.strip().lower() for p in name.split() if p.strip()]
    return "".join(p[0] for p in parts)


def _json_loads(value: Any) -> Any:
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _find_birth_years(value: Any) -> set[str]:
    """Best-effort lookup for DOB/year fields if future sessions store them."""
    years: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key_norm = _normalize(str(key))
            if key_norm in {"yearofbirth", "birthyear", "patientyearofbirth"}:
                year = "".join(c for c in str(item) if c.isdigit())
                if len(year) == 4:
                    years.add(year)
            if key_norm in {"dob", "dateofbirth", "patientdob"}:
                digits = "".join(c for c in str(item) if c.isdigit())
                for idx in range(max(len(digits) - 3, 0)):
                    candidate = digits[idx: idx + 4]
                    if candidate.startswith(("19", "20")):
                        years.add(candidate)
            years.update(_find_birth_years(item))
    elif isinstance(value, list):
        for item in value:
            years.update(_find_birth_years(item))
    return years


def _decode_share_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="This prescription link has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid prescription link")

    if payload.get("scope") != "patient_prescription_share":
        raise HTTPException(status_code=401, detail="Invalid prescription link")
    session_id = payload.get("session_id") or payload.get("sub")
    if not session_id:
        raise HTTPException(status_code=401, detail="Invalid prescription link")
    payload["session_id"] = session_id
    return payload


def _decode_download_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=410,
            detail="Temporary download token expired. Please verify your details again.",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Access unauthorized")

    if payload.get("scope") != "patient_prescription_download" or not payload.get("verified"):
        raise HTTPException(status_code=401, detail="Access unauthorized")
    session_id = payload.get("session_id") or payload.get("sub")
    doctor_user_id = payload.get("doctor_user_id")
    if not session_id or not doctor_user_id:
        raise HTTPException(status_code=401, detail="Access unauthorized")
    payload["session_id"] = session_id
    return payload


@router.post("/public/verify-access/{token}")
async def verify_patient_access(token: str, body: VerifyAccessRequest, request: Request):
    """Validates the signed share token and verifies the patient identity matches the record."""
    check_rate_limit(
        request,
        f"public_verify:{token[:16]}",
        max_attempts=settings.public_rate_limit_max_attempts,
        window_seconds=settings.public_rate_limit_window_seconds,
    )
    payload = _decode_share_token(token)
    session_id = payload["session_id"]

    async with db_connect() as db:
        async with db.execute(
            "SELECT patient_name, user_id, clinical_facts, memory_state FROM sessions WHERE id = ?",
            (session_id,)
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Prescription session not found")

    db_patient_name = row[0] or ""
    doctor_user_id = row[1]
    clinical_facts = _json_loads(row[2])
    memory_state = _json_loads(row[3])

    expected_birth_years = _find_birth_years(clinical_facts) | _find_birth_years(memory_state)

    # Task 21: if the session has no patient identity data at all, the link
    # was shared without any verifiable identity info — block gracefully.
    if not db_patient_name and not expected_birth_years:
        raise HTTPException(
            status_code=422,
            detail=(
                "This prescription link has no patient identity information on record "
                "and cannot be verified. Please contact the clinic."
            ),
        )

    # Verify patient identity if a name is recorded in the session
    if db_patient_name:
        db_norm = _normalize(db_patient_name)
        input_norm = _normalize(body.patient_name)
        db_init = _get_initials(db_patient_name)
        input_init = _normalize(body.initials) or _get_initials(body.patient_name)

        full_name_matched = len(input_norm) >= 4 and db_norm == input_norm
        initials_matched = len(db_init) >= 2 and len(input_init) >= 2 and input_init == db_init
        name_matched = full_name_matched or initials_matched
    else:
        name_matched = False

    supplied_birth_year = "".join(c for c in body.year_of_birth if c.isdigit())
    birth_year_matched = bool(
        supplied_birth_year and len(supplied_birth_year) == 4 and supplied_birth_year in expected_birth_years
    )

    if expected_birth_years:
        verified = name_matched and birth_year_matched
    else:
        verified = name_matched

    if not verified:
        raise HTTPException(
            status_code=403,
            detail="Verification failed: patient identity details do not match our records.",
        )

    # Generate a short-lived download token (5 minutes validity)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=5)
    download_payload = {
        "sub": session_id,
        "session_id": session_id,
        "doctor_user_id": doctor_user_id,
        "scope": "patient_prescription_download",
        "verified": True,
        "iat": now,
        "exp": expires,
    }
    download_token = jwt.encode(download_payload, settings.secret_key, algorithm=settings.algorithm)

    return {"success": True, "download_token": download_token}


@router.get("/public/download/{download_token}", response_class=HTMLResponse)
async def download_prescription_public(download_token: str):
    """Serves the printable prescription HTML layout if the temporary verified token is valid."""
    payload = _decode_download_token(download_token)
    session_id = payload["session_id"]
    doctor_user_id = payload["doctor_user_id"]

    # Task 22: verify session ownership before rendering to prevent token reuse attacks
    async with db_connect() as db:
        async with db.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, str(doctor_user_id)),
        ) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=403, detail="Session not found or access denied")

    try:
        html = await render_prescription_html(session_id, doctor_user_id)
        await repo.log_usage_event(
            "patient_prescription_opened",
            str(doctor_user_id),
            session_id,
            {"surface": "public_download_portal"},
        )
        await repo.log_audit(
            "data_accessed",
            str(doctor_user_id),
            "session",
            session_id,
            "patient_prescription_opened",
        )
        return HTMLResponse(content=html)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to render public prescription: %s", exc)
        raise HTTPException(status_code=404, detail="Prescription file could not be generated")


@router.get("/public/patient-summary")
async def get_patient_summary(phone: str, request: Request) -> dict:
    """
    Return a patient's recent prescription, lab order, and follow-up status.
    No ABHA required — patient phone is the implicit access key (same number
    we WhatsApp the link to, so possession of the number = authorisation).
    """
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    check_rate_limit(
        request,
        f"patient_summary:{digits[-10:]}",
        max_attempts=20,
        window_seconds=3600,
    )

    last10 = digits[-10:]

    async with db_connect() as db:
        async with db.execute(
            """
            SELECT id, patient_name, doctor_name, status, created_at, clinical_facts, user_id
            FROM sessions
            WHERE patient_phone=?
            ORDER BY created_at DESC LIMIT 1
            """,
            (digits,),
        ) as cur:
            session_row = await cur.fetchone()

        async with db.execute(
            "SELECT id FROM patients WHERE phone_number=?", (last10,)
        ) as cur:
            patient_row = await cur.fetchone()

        async with db.execute(
            """
            SELECT session_id, tests_json, dispatched_at, status
            FROM lab_dispatch_log
            WHERE patient_phone=?
            ORDER BY dispatched_at DESC LIMIT 1
            """,
            (digits,),
        ) as cur:
            lab_row = await cur.fetchone()

        async with db.execute(
            """
            SELECT id, reminder_text, scheduled_for, doctor_name, status
            FROM follow_up_reminders
            WHERE patient_phone=? AND status IN ('sent','pending','confirmed')
            ORDER BY created_at DESC LIMIT 1
            """,
            (digits,),
        ) as cur:
            fu_row = await cur.fetchone()

    prescription = None
    doctor_user_id = None
    if session_row:
        session_id, patient_name, doctor_name, status, created_at, facts_json, doctor_user_id = session_row
        facts = _json_loads(facts_json)
        medications = facts.get("medications", []) if isinstance(facts, dict) else []
        diagnosis = (facts.get("diagnosis") or facts.get("provisional_diagnosis")) if isinstance(facts, dict) else None
        prescription = {
            "session_id": session_id,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "status": status,
            "created_at": created_at,
            "diagnosis": diagnosis,
            "medications": medications,
        }

    lab_order = None
    if lab_row:
        lab_order = {
            "session_id": lab_row[0],
            "labs": _json_loads(lab_row[1]) if lab_row[1] else [],
            "dispatched_at": lab_row[2],
            "status": lab_row[3],
        }

    follow_up = None
    if fu_row:
        follow_up = {
            "reminder_id": fu_row[0],
            "follow_up_text": fu_row[1],
            "follow_up_date": fu_row[2],
            "doctor_name": fu_row[3],
            "status": fu_row[4],
        }

    if not prescription and not lab_order and not follow_up:
        raise HTTPException(status_code=404, detail="No records found for this number")

    return {
        "phone_last4": digits[-4:],
        "prescription": prescription,
        "lab_order": lab_order,
        "follow_up": follow_up,
        "patient_id": patient_row[0] if patient_row else None,
        "doctor_user_id": str(doctor_user_id) if doctor_user_id else None,
    }


@router.get("/public/patient-history")
async def get_patient_history(phone: str, request: Request) -> dict:
    """Cross-visit history for a patient, keyed by phone (last 10 digits,
    same match convention as get_patient_summary above). Unlike that endpoint,
    which returns only the most recent visit, this returns every signed
    consultation so a patient can see their full record over time."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    last10 = digits[-10:]

    check_rate_limit(request, f"patient_history:{last10}", max_attempts=20, window_seconds=3600)

    async with db_connect() as db:
        async with db.execute(
            """
            SELECT id, doctor_name, status, created_at, clinical_facts
            FROM sessions
            WHERE patient_phone=? AND status='complete'
            ORDER BY created_at DESC LIMIT 25
            """,
            (last10,),
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No visit history found for this number")

    visits = []
    for session_id, doctor_name, status, created_at, facts_json in rows:
        facts = _json_loads(facts_json)
        diagnosis = (facts.get("diagnosis") or facts.get("provisional_diagnosis")) if isinstance(facts, dict) else None
        medications = facts.get("medications", []) if isinstance(facts, dict) else []
        visits.append({
            "session_id": session_id,
            "doctor_name": doctor_name,
            "created_at": created_at,
            "diagnosis": diagnosis,
            "medication_count": len(medications) if isinstance(medications, list) else 0,
        })

    return {"phone_last4": last10[-4:], "visits": visits}


class BookViaPatientIdRequest(BaseModel):
    doctor_user_id: str
    slot_datetime: str
    chief_complaint: str = ""


@router.get("/public/patients/{patient_id}/available-slots")
async def get_available_slots_public(patient_id: str, doctor_user_id: str, request: Request) -> dict:
    """Available appointment slots for a doctor, surfaced to a patient who's
    already resolved their identity via the phone-lookup portal above. The
    patient_id itself is not sensitive (no name/phone embedded in it) but the
    endpoint is still rate-limited like the other public booking surfaces."""
    check_rate_limit(request, f"slots_view:{patient_id}", max_attempts=30, window_seconds=3600)

    async with db_connect() as db:
        async with db.execute("SELECT id FROM patients WHERE id=?", (patient_id,)) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="Patient not found")

    from app.services.appointment_booking import get_available_slots
    slots = await get_available_slots(doctor_user_id)
    return {"slots": slots}


@router.post("/public/patients/{patient_id}/book-appointment")
async def book_appointment_via_patient_id(
    patient_id: str,
    body: BookViaPatientIdRequest,
    request: Request,
) -> dict:
    """Patient books directly using their patient_id — name and phone are
    pulled from the canonical patients record, not re-entered, so the same
    person can't accidentally create a second, slightly-misspelled identity."""
    check_rate_limit(request, f"book_via_patient:{patient_id}", max_attempts=5, window_seconds=3600)

    async with db_connect() as db:
        async with db.execute(
            "SELECT phone_number, name FROM patients WHERE id=?", (patient_id,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient_phone, patient_name = row

    from app.services.appointment_booking import book_appointment
    appt_id = await book_appointment(
        clinic_user_id=body.doctor_user_id,
        patient_phone=patient_phone,
        patient_name=patient_name or "Patient",
        slot_datetime=body.slot_datetime,
        chief_complaint=body.chief_complaint,
    )
    return {"success": True, "appointment_id": appt_id}


# ---------------------------------------------------------------------------
# Doctor no-login signing flow
# ---------------------------------------------------------------------------

def _decode_doctor_sign_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="This signing link has expired. Please ask for a new note.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid signing link.")

    if payload.get("scope") != "doctor_session_sign":
        raise HTTPException(status_code=401, detail="Invalid signing link.")
    session_id = payload.get("session_id") or payload.get("sub")
    user_id = payload.get("user_id")
    if not session_id or not user_id:
        raise HTTPException(status_code=401, detail="Invalid signing link.")
    payload["session_id"] = session_id
    payload["user_id"] = user_id
    return payload


@router.get("/public/sign/{token}")
async def get_doctor_sign_page(token: str) -> dict:
    """Return session data for the no-login mobile signing page."""
    payload = _decode_doctor_sign_token(token)
    session_id = payload["session_id"]

    async with db_connect() as db:
        async with db.execute(
            """SELECT patient_name, doctor_name, soap_note, clinical_facts,
                      patient_phone, patient_age, patient_sex, signed_at, status,
                      cds_suggestions
               FROM sessions WHERE id = ?""",
            (session_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    patient_name, doctor_name, soap_raw, facts_raw, patient_phone, patient_age, patient_sex, signed_at, status, cds_raw = row

    soap: dict = {}
    if soap_raw:
        try:
            soap = json.loads(soap_raw) if isinstance(soap_raw, str) else soap_raw
        except Exception:
            soap = {"raw": soap_raw}

    facts: dict = {}
    if facts_raw:
        try:
            facts = json.loads(facts_raw) if isinstance(facts_raw, str) else facts_raw
        except Exception:
            pass

    cds: list = []
    if cds_raw:
        try:
            cds = json.loads(cds_raw) if isinstance(cds_raw, str) else cds_raw
            if not isinstance(cds, list):
                cds = []
        except Exception:
            cds = []

    already_signed = bool(signed_at)

    raw_diagnoses = facts.get("diagnoses") or facts.get("diagnosis") or []
    annotated_dx = annotate_diagnoses(raw_diagnoses)

    return {
        "session_id": session_id,
        "patient_name": patient_name or "Patient",
        "doctor_name": doctor_name or "Doctor",
        "patient_age": patient_age,
        "patient_sex": patient_sex,
        "patient_phone": patient_phone,
        "soap": soap,
        "diagnoses": raw_diagnoses,
        "diagnoses_annotated": annotated_dx,
        "medications": facts.get("medications") or [],
        "investigations": facts.get("investigations") or [],
        "vitals": facts.get("vitals") or [],
        "follow_up": facts.get("follow_up"),
        "cds_alerts": cds,
        "already_signed": already_signed,
        "signed_at": signed_at,
    }


@router.post("/public/sign/{token}")
async def doctor_sign_and_send(token: str) -> dict:
    """
    Doctor taps 'Sign & Send' on the mobile page.
    Marks the session signed and dispatches the prescription to the patient's WhatsApp.
    """
    payload = _decode_doctor_sign_token(token)
    session_id = payload["session_id"]
    user_id = payload["user_id"]

    async with db_connect() as db:
        async with db.execute(
            """SELECT patient_name, doctor_name, soap_note, clinical_facts,
                      patient_phone, patient_age, patient_sex, signed_at
               FROM sessions WHERE id = ? AND user_id = ?""",
            (session_id, str(user_id)),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    patient_name, doctor_name, soap_raw, facts_raw, patient_phone, patient_age, patient_sex, signed_at = row

    if signed_at:
        return {"success": True, "already_signed": True, "message": "Already signed."}

    facts: dict = {}
    if facts_raw:
        try:
            facts = json.loads(facts_raw) if isinstance(facts_raw, str) else facts_raw
        except Exception:
            pass

    soap: dict = {}
    if soap_raw:
        try:
            soap = json.loads(soap_raw) if isinstance(soap_raw, str) else soap_raw
        except Exception:
            pass

    # Mark as signed
    now = datetime.now(timezone.utc).isoformat()
    async with db_connect() as db:
        await db.execute(
            "UPDATE sessions SET signed_at = ? WHERE id = ?",
            (now, session_id),
        )
        await db.commit()

    # Dispatch rich care message + prescription link to patient WhatsApp
    whatsapp_result = None
    if patient_phone:
        try:
            expires = datetime.now(timezone.utc) + timedelta(hours=24)
            share_payload = {
                "sub": session_id,
                "session_id": session_id,
                "doctor_user_id": str(user_id),
                "scope": "patient_prescription_share",
                "exp": expires,
            }
            share_token = jwt.encode(share_payload, settings.secret_key, algorithm=settings.algorithm)
            base = settings.app_base_url.rstrip("/")
            prescription_link = f"{base}/patient-download/{share_token}"

            # Build a rich, readable WhatsApp message for the patient
            msg_lines = [
                f"Namaste {patient_name or 'there'} 🙏",
                f"",
                f"*Dr. {doctor_name or 'your doctor'}* ne aapka note review aur sign kar diya hai.",
                f"",
            ]

            # Assessment / Clinical impression from SOAP
            assessment = (
                soap.get("A") or soap.get("assessment") or soap.get("Assessment") or ""
            )
            if assessment and "not documented" not in assessment.lower():
                msg_lines.append("*Clinical Assessment:*")
                msg_lines.append(assessment.strip())
                msg_lines.append("")

            # Diagnoses
            diagnoses = facts.get("diagnoses") or facts.get("diagnosis") or []
            if diagnoses:
                dx_list = diagnoses if isinstance(diagnoses, list) else [diagnoses]
                msg_lines.append("*Diagnosis:*")
                for dx in dx_list[:4]:
                    msg_lines.append(f"  • {dx}")
                msg_lines.append("")

            # Medications
            medications = facts.get("medications") or []
            if medications:
                msg_lines.append("*Medications:*")
                for med in medications[:6]:
                    name = med if isinstance(med, str) else med.get("name", str(med))
                    dosage = "" if isinstance(med, str) else med.get("dosage") or med.get("dose") or ""
                    frequency = "" if isinstance(med, str) else med.get("frequency") or ""
                    parts = [name]
                    if dosage:
                        parts.append(dosage)
                    if frequency:
                        parts.append(frequency)
                    msg_lines.append(f"  • {' '.join(parts)}")
                msg_lines.append("")

            # Lab investigations
            investigations = facts.get("investigations") or []
            if investigations:
                inv_list = investigations if isinstance(investigations, list) else [investigations]
                inv_strings = []
                for inv in inv_list[:8]:
                    inv_strings.append(inv if isinstance(inv, str) else inv.get("name", str(inv)))
                if inv_strings:
                    msg_lines.append("*Tests ordered:*")
                    for t in inv_strings:
                        msg_lines.append(f"  🔬 {t}")
                    msg_lines.append("")
                    inv_link = f"{base}/api/public/investigation-order/{session_id}"
                    msg_lines.append(f"📋 Investigation order: {inv_link}")
                    msg_lines.append("")

            # Follow-up
            follow_up = facts.get("follow_up")
            if follow_up:
                fu_text = follow_up if isinstance(follow_up, str) else (follow_up[0] if isinstance(follow_up, list) and follow_up else str(follow_up))
                if fu_text and "advised by physician" not in fu_text.lower():
                    msg_lines.append(f"*Follow-up:* {fu_text}")
                    msg_lines.append("")

            # Prescription link
            msg_lines += [
                "📄 *Prescription download:*",
                prescription_link,
                "",
                "_Yeh link 24 ghante valid hai. Pharmacist ko dikhayein._",
            ]

            message = "\n".join(msg_lines)
            whatsapp_result = await WhatsAppService.send_text_message(patient_phone, message)
        except Exception as exc:
            logger.warning("Failed to dispatch prescription to patient after sign: %s", exc)

    return {
        "success": True,
        "already_signed": False,
        "signed_at": now,
        "prescription_dispatched": bool(whatsapp_result and whatsapp_result.get("success")),
        "patient_phone": patient_phone,
    }


@router.get("/public/investigation-order/{session_id}", response_class=HTMLResponse)
async def get_investigation_order_public(session_id: str):
    """
    Public patient-facing investigation order page — no auth required.
    The session_id UUID is the access token. Sent to patients via WhatsApp.
    """
    session = await repo.get_session_public(session_id)
    if not session or not session.user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        html = await render_investigation_order_html(session_id, session.user_id)
    except PermissionError:
        # No confirmed facts yet — show a simple "your tests will appear shortly" page
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Investigation Order</title>"
            "<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;"
            "min-height:100vh;margin:0;background:#fafaf7;color:#1a1a1a;text-align:center;padding:2rem}</style>"
            "</head><body>"
            "<div><h2>Your investigation order is being prepared</h2>"
            "<p style='color:#64748b'>The doctor is finalising your note. This page will be ready shortly.</p>"
            "</div></body></html>"
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    return HTMLResponse(content=html)


class PreVisitFormRequest(BaseModel):
    chief_complaint: str = ""
    current_medications: str = ""
    allergies: str = ""
    additional_notes: str = ""


@router.get("/public/appointments/{appointment_id}")
async def get_appointment_public(appointment_id: str, request: Request) -> dict:
    """Minimal appointment info for the pre-visit form page — no auth, the
    appointment id itself (sent only to the booking patient via WhatsApp) is
    the access key, same pattern as the other public patient-facing pages."""
    check_rate_limit(request, f"pre_visit_view:{appointment_id}", max_attempts=30, window_seconds=3600)

    async with db_connect() as db:
        async with db.execute(
            "SELECT id, patient_name, slot_datetime, status FROM appointments WHERE id=?",
            (appointment_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")

        async with db.execute(
            "SELECT submitted_at FROM pre_visit_forms WHERE appointment_id=? ORDER BY submitted_at DESC LIMIT 1",
            (appointment_id,),
        ) as cur:
            form_row = await cur.fetchone()

    return {
        "appointment_id": row[0],
        "patient_name": row[1],
        "slot_datetime": row[2],
        "status": row[3],
        "already_submitted": bool(form_row),
    }


@router.post("/public/appointments/{appointment_id}/pre-visit-form")
async def submit_pre_visit_form(
    appointment_id: str,
    body: PreVisitFormRequest,
    request: Request,
) -> dict:
    """Patient submits pre-visit info before their booked appointment, so the
    doctor can prepare. No auth — same access-key-by-possession pattern as
    the appointment lookup above."""
    check_rate_limit(request, f"pre_visit_submit:{appointment_id}", max_attempts=5, window_seconds=3600)

    async with db_connect() as db:
        async with db.execute(
            "SELECT id FROM appointments WHERE id=?", (appointment_id,)
        ) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="Appointment not found")

        await db.execute(
            "INSERT INTO pre_visit_forms (id, appointment_id, chief_complaint, current_medications, allergies, additional_notes, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()), appointment_id, body.chief_complaint.strip(),
                body.current_medications.strip(), body.allergies.strip(),
                body.additional_notes.strip(), datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()

    return {"success": True}

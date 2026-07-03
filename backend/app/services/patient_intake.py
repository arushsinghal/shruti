"""
Patient WhatsApp intake — conversational pre-consultation flow.

Patient texts the clinic's shared Lipi number before their visit.
Lipi collects chief complaint, age, and current medications,
then sends the doctor a brief before the patient walks in.

State machine steps:
  awaiting_clinic_code → awaiting_name → awaiting_age
  → awaiting_complaint → awaiting_medications → complete
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.storage.db import db_connect
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

STEPS = [
    "awaiting_clinic_code",
    "awaiting_name",
    "awaiting_age",
    "awaiting_complaint",
    "awaiting_medications",
    "complete",
]


async def get_active_intake(from_phone: str) -> Optional[dict]:
    """Return in-progress intake session for this patient phone, if any."""
    async with db_connect() as db:
        async with db.execute(
            "SELECT id, step, clinic_code, clinic_user_id, patient_name, patient_age, chief_complaint, current_medications FROM patient_intake_sessions WHERE from_phone=? AND step != 'complete' ORDER BY created_at DESC LIMIT 1",
            (from_phone,),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0], "step": row[1], "clinic_code": row[2],
        "clinic_user_id": row[3], "patient_name": row[4],
        "patient_age": row[5], "chief_complaint": row[6],
        "current_medications": row[7],
    }


async def _lookup_clinic_by_code(code: str) -> Optional[dict]:
    """Find the doctor whose clinic code matches."""
    async with db_connect() as db:
        async with db.execute(
            "SELECT id, full_name FROM users WHERE clinic_invite_code=?",
            (code.upper().strip(),),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    return {"user_id": str(row[0]), "name": row[1] or ""}


async def _get_doctor_whatsapp(user_id: str) -> Optional[str]:
    async with db_connect() as db:
        async with db.execute(
            "SELECT whatsapp_phone FROM doctor_profiles WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row and row[0] else None


async def start_intake(from_phone: str) -> str:
    """Create a new intake session and return the first question."""
    intake_id = str(uuid.uuid4())
    async with db_connect() as db:
        await db.execute(
            "INSERT INTO patient_intake_sessions (id, from_phone, step, created_at) VALUES (?, ?, 'awaiting_clinic_code', ?)",
            (intake_id, from_phone, datetime.utcnow().isoformat()),
        )
        await db.commit()
    return (
        "Namaste! 🙏 Aap Lipi Health ke through apne doctor ke liye pre-visit brief bhej sakte hain.\n\n"
        "Pehle apna *clinic code* enter karein.\n"
        "(Doctor se maangein — 6 digit ka code, jaise A1B2C3)"
    )


async def advance_intake(intake: dict, body: str, from_phone: str) -> str:
    """Process patient reply, advance state machine, return next prompt or completion."""
    step = intake["step"]
    intake_id = intake["id"]

    async with db_connect() as db:
        if step == "awaiting_clinic_code":
            clinic = await _lookup_clinic_by_code(body.strip())
            if not clinic:
                return "Yeh clinic code nahi mila. Dobara check karein aur bhejein. 🔄"
            await db.execute(
                "UPDATE patient_intake_sessions SET step='awaiting_name', clinic_code=?, clinic_user_id=? WHERE id=?",
                (body.strip().upper(), clinic["user_id"], intake_id),
            )
            await db.commit()
            return f"✅ Dr. {clinic['name'].split()[0] if clinic['name'] else 'Doctor'} ki clinic mili!\n\nAapka *poora naam* kya hai?"

        elif step == "awaiting_name":
            await db.execute(
                "UPDATE patient_intake_sessions SET step='awaiting_age', patient_name=? WHERE id=?",
                (body.strip(), intake_id),
            )
            await db.commit()
            return f"Shukriya, {body.strip().split()[0]}! Aapki *umar* kya hai? (sirf number, jaise 45)"

        elif step == "awaiting_age":
            await db.execute(
                "UPDATE patient_intake_sessions SET step='awaiting_complaint', patient_age=? WHERE id=?",
                (body.strip(), intake_id),
            )
            await db.commit()
            return "Aaj *kya takleef* hai? Jo bhi problem hai woh likhein.\n(jaise: sir dard, bukhar, pet dard, khaans...)"

        elif step == "awaiting_complaint":
            await db.execute(
                "UPDATE patient_intake_sessions SET step='awaiting_medications', chief_complaint=? WHERE id=?",
                (body.strip(), intake_id),
            )
            await db.commit()
            return "Koi *dawa chal rahi hai abhi?* Haan toh naam likhein, nahi toh 'nahi' likhein."

        elif step == "awaiting_medications":
            meds = body.strip()
            await db.execute(
                "UPDATE patient_intake_sessions SET step='complete', current_medications=?, completed_at=? WHERE id=?",
                (meds, datetime.utcnow().isoformat(), intake_id),
            )
            await db.commit()

            # Fetch complete intake to send to doctor
            async with db.execute(
                "SELECT patient_name, patient_age, chief_complaint, current_medications, clinic_user_id FROM patient_intake_sessions WHERE id=?",
                (intake_id,),
            ) as cur:
                row = await cur.fetchone()

            if row:
                patient_name, age, complaint, medications, clinic_user_id = row
                await _notify_doctor(clinic_user_id, patient_name, age, complaint, medications)

            return (
                "✅ *Brief bhej diya gaya!*\n\n"
                "Doctor ko aapki jaankari mil gayi hai. Seedhe clinic aayein — koi form nahi bharna. 🏥\n\n"
                "_Lipi Health — AI-native OPD service_"
            )

    return "Kuch galat ho gaya. Dobara try karein."


async def _notify_doctor(
    clinic_user_id: str,
    patient_name: str,
    age: str,
    complaint: str,
    medications: str,
) -> None:
    """Send the pre-visit brief to the doctor on WhatsApp."""
    wa_phone = await _get_doctor_whatsapp(clinic_user_id)
    if not wa_phone:
        logger.warning("Patient intake: no WhatsApp phone for user %s", clinic_user_id)
        return

    meds_line = medications if medications.lower() not in ("nahi", "no", "none", "nhi", "") else "None"
    msg = (
        f"🔔 *New patient brief*\n\n"
        f"👤 *{patient_name}*, {age} years\n"
        f"🩺 *Chief complaint:* {complaint}\n"
        f"💊 *Current medications:* {meds_line}\n\n"
        f"_Patient clinic mein aa rahe hain — Lipi se bheja gaya_"
    )
    try:
        await WhatsAppService.send_text_message(wa_phone, msg)
    except Exception as exc:
        logger.warning("Patient intake doctor notify failed: %s", exc)

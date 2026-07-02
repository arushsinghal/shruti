"""
Appointment booking via WhatsApp.

Patient texts "book" or "appointment" → sees available slots → picks one →
doctor gets notified → patient gets confirmation.

Doctor sets availability in DoctorProfile (stored in doctor_availability table).
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.storage.db import db_connect
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_NAMES_HI = ["Somvar", "Mangalvar", "Budhvar", "Guruvar", "Shukravar", "Shanivar", "Ravivar"]


async def get_available_slots(clinic_user_id: str, days_ahead: int = 3) -> list[dict]:
    """Return the next N available appointment slots for a clinic."""
    async with db_connect() as db:
        async with db.execute(
            "SELECT day_of_week, start_time, end_time, slot_duration_minutes FROM doctor_availability WHERE user_id=? AND is_active=1",
            (clinic_user_id,),
        ) as cur:
            availability = await cur.fetchall()

    if not availability:
        return []

    # Build slot list for next `days_ahead` days
    slots = []
    now = datetime.utcnow()
    for offset in range(1, days_ahead + 3):
        candidate = now + timedelta(days=offset)
        dow = candidate.weekday()  # 0=Monday
        for avail in availability:
            if avail[0] != dow:
                continue
            start_h, start_m = map(int, avail[1].split(":"))
            end_h, end_m = map(int, avail[2].split(":"))
            duration = avail[3]
            slot_dt = candidate.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            end_dt = candidate.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            while slot_dt < end_dt and len(slots) < 5:
                slots.append({
                    "datetime": slot_dt.isoformat(),
                    "label": f"{DAY_NAMES[dow]}, {slot_dt.strftime('%d %b')} at {slot_dt.strftime('%I:%M %p')}",
                })
                slot_dt += timedelta(minutes=duration)
        if len(slots) >= 5:
            break

    return slots[:5]


async def book_appointment(
    clinic_user_id: str,
    patient_phone: str,
    patient_name: str,
    slot_datetime: str,
    chief_complaint: str = "",
) -> str:
    """Create appointment record and notify doctor. Returns appointment ID."""
    appt_id = str(uuid.uuid4())
    async with db_connect() as db:
        await db.execute(
            "INSERT INTO appointments (id, clinic_user_id, patient_phone, patient_name, slot_datetime, chief_complaint, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (appt_id, clinic_user_id, patient_phone, patient_name, slot_datetime, chief_complaint, "confirmed", datetime.utcnow().isoformat()),
        )
        await db.commit()

        async with db.execute(
            "SELECT whatsapp_phone FROM doctor_profiles WHERE user_id=?", (clinic_user_id,)
        ) as cur:
            row = await cur.fetchone()
        doctor_wa = row[0] if row and row[0] else None

    slot_label = datetime.fromisoformat(slot_datetime).strftime("%A, %d %b at %I:%M %p")

    if doctor_wa:
        msg = (
            f"📅 *New appointment booked*\n\n"
            f"👤 *{patient_name}*\n"
            f"🕐 {slot_label}\n"
            f"📞 {patient_phone[-4:].rjust(10, '•')}\n"
            + (f"🩺 {chief_complaint}" if chief_complaint else "")
        )
        try:
            await WhatsAppService.send_text_message(doctor_wa, msg)
        except Exception as exc:
            logger.warning("Appointment booking doctor notify failed: %s", exc)

    # Patient-facing confirmation with the pre-visit form link, so the doctor
    # can prepare before the visit. Never let this block the booking itself.
    try:
        from app.utils.config import settings
        base = (settings.app_base_url or "").rstrip("/")
        form_link = f"{base}/pre-visit/{appt_id}" if base else ""
        patient_msg = (
            f"✅ *Appointment confirmed*\n\n"
            f"🕐 {slot_label}\n\n"
            + (f"Please fill a quick pre-visit form so your doctor can prepare: {form_link}" if form_link else "")
        )
        await WhatsAppService.send_text_message(patient_phone, patient_msg)
    except Exception as exc:
        logger.warning("Appointment booking patient confirm failed: %s", exc)

    return appt_id


async def save_doctor_availability(
    user_id: str,
    slots: list[dict],
) -> None:
    """
    Replace doctor's availability schedule.
    slots: [{"day_of_week": 0, "start_time": "09:00", "end_time": "13:00", "slot_duration_minutes": 15}]
    """
    async with db_connect() as db:
        await db.execute("DELETE FROM doctor_availability WHERE user_id=?", (user_id,))
        for s in slots:
            await db.execute(
                "INSERT INTO doctor_availability (id, user_id, day_of_week, start_time, end_time, slot_duration_minutes, is_active) VALUES (?,?,?,?,?,?,1)",
                (str(uuid.uuid4()), user_id, s["day_of_week"], s["start_time"], s["end_time"], s.get("slot_duration_minutes", 15)),
            )
        await db.commit()


async def get_doctor_availability(user_id: str) -> list[dict]:
    async with db_connect() as db:
        async with db.execute(
            "SELECT id, day_of_week, start_time, end_time, slot_duration_minutes, is_active FROM doctor_availability WHERE user_id=? ORDER BY day_of_week, start_time",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [
        {"id": r[0], "day_of_week": r[1], "day_name": DAY_NAMES[r[1]], "start_time": r[2], "end_time": r[3], "slot_duration_minutes": r[4], "is_active": bool(r[5])}
        for r in rows
    ]

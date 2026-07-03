"""
Auto follow-up reminder engine.

When a consultation is processed and follow_up is extracted:
  1. Parse the follow-up interval ("3 din baad", "1 week", etc.)
  2. Compute follow-up date (today + N days) and reminder date (D-2)
  3. Store in follow_up_reminders table
  4. Background loop fires reminders via WhatsApp when reminder_date arrives
  5. Patient replies HAAN or NAHI → handled in routes_whatsapp.py
"""

import asyncio
import logging
import re
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from app.services.whatsapp_service import WhatsAppService
from app.storage.db import db_connect

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Follow-up text → days parser
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[re.Pattern, any]] = [
    (re.compile(r'(\d+)\s*(?:din|day|days)', re.I),   lambda m: int(m.group(1))),
    (re.compile(r'(\d+)\s*(?:hafte|hafta|week|weeks)', re.I), lambda m: int(m.group(1)) * 7),
    (re.compile(r'(\d+)\s*(?:mahine|mahina|month|months)', re.I), lambda m: int(m.group(1)) * 30),
    (re.compile(r'(\d+)\s*(?:saal|year|years)', re.I), lambda m: int(m.group(1)) * 365),
    (re.compile(r'ek\s+(?:hafte|hafta|week)', re.I),  lambda m: 7),
    (re.compile(r'ek\s+(?:mahine|mahina|month)', re.I), lambda m: 30),
    (re.compile(r'do\s+(?:hafte|hafta|week)', re.I),  lambda m: 14),
    (re.compile(r'teen\s+(?:din|day)', re.I),          lambda m: 3),
    (re.compile(r'char\s+(?:din|day)', re.I),          lambda m: 4),
    # "fortnight" edge case
    (re.compile(r'fortnight', re.I),                    lambda m: 14),
]


def _parse_days(text: str) -> Optional[int]:
    for pattern, extractor in _PATTERNS:
        m = pattern.search(text)
        if m:
            try:
                return int(extractor(m))
            except Exception:
                continue
    return None


def _friendly_date(iso_date: str) -> str:
    try:
        d = date.fromisoformat(iso_date)
        return d.strftime("%-d %B %Y")  # e.g. "5 July 2026"
    except Exception:
        return iso_date


def _doctor_display(name: str) -> str:
    if not name:
        return "aapke doctor"
    n = name.strip()
    return n if n.lower().startswith("dr") else f"Dr. {n}"


# ---------------------------------------------------------------------------
# Public API: schedule a reminder
# ---------------------------------------------------------------------------

async def schedule_follow_up(
    session_id: str,
    user_id: str,
    patient_phone: str,
    patient_name: Optional[str],
    doctor_name: str,
    follow_up_text: str,
) -> Optional[str]:
    """
    Parse follow_up_text, compute dates, and persist a pending reminder.
    Returns the reminder_id, or None if the text couldn't be parsed.
    """
    text = follow_up_text if isinstance(follow_up_text, str) else str(follow_up_text)
    days = _parse_days(text)
    if not days or not (1 <= days <= 730):
        logger.info("Could not parse follow-up days from %r", text)
        return None

    now = datetime.utcnow()
    follow_up_dt = now + timedelta(days=days)
    reminder_dt = follow_up_dt - timedelta(days=2)

    # If reminder is already past or today, send in 1 hour
    if reminder_dt.date() <= now.date():
        reminder_dt = now + timedelta(hours=1)

    async with db_connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO follow_up_reminders
              (session_id, user_id, patient_phone, patient_name, doctor_name,
               scheduled_for, due_at, reminder_text, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                session_id, user_id, patient_phone, patient_name,
                doctor_name, follow_up_dt.date().isoformat(),
                reminder_dt.isoformat(), text,
            ),
        )
        await db.commit()
        reminder_id = str(cursor.lastrowid)

    logger.info(
        "Scheduled reminder %s: patient=%s follow_up=%s remind_at=%s",
        reminder_id, patient_phone, follow_up_dt.date(), reminder_dt.date(),
    )
    return reminder_id


# ---------------------------------------------------------------------------
# Patient interaction tracking
# ---------------------------------------------------------------------------

async def register_patient_interaction(
    patient_phone: str,
    interaction_type: str,
    reference_id: str,
    doctor_user_id: str,
    ttl_days: int = 7,
) -> None:
    expires_at = (datetime.utcnow() + timedelta(days=ttl_days)).isoformat()
    async with db_connect() as db:
        # Replace any existing pending interaction for this phone (one at a time)
        await db.execute(
            "UPDATE patient_interactions SET status = 'superseded' WHERE patient_phone = ? AND status = 'pending'",
            (patient_phone,),
        )
        await db.execute(
            """
            INSERT INTO patient_interactions
              (id, patient_phone, interaction_type, reference_id, doctor_user_id, expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
            (str(uuid.uuid4()), patient_phone, interaction_type, reference_id, doctor_user_id, expires_at),
        )
        await db.commit()


async def get_pending_interaction(patient_phone: str) -> Optional[dict]:
    """Return the most recent pending interaction for this phone number."""
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT id, interaction_type, reference_id, doctor_user_id
            FROM patient_interactions
            WHERE patient_phone = ? AND status = 'pending' AND expires_at > ?
            ORDER BY expires_at DESC LIMIT 1
            """,
            (patient_phone, now),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "type": row[1], "reference_id": row[2], "doctor_user_id": row[3]}


async def mark_interaction_responded(interaction_id: str) -> None:
    async with db_connect() as db:
        await db.execute(
            "UPDATE patient_interactions SET status = 'responded' WHERE id = ?",
            (interaction_id,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# HAAN / NAHI handlers
# ---------------------------------------------------------------------------

async def handle_haan(reminder_id: str, doctor_user_id: str) -> str:
    from app.utils.config import settings

    reminder_db_id = int(reminder_id)
    async with db_connect() as db:
        async with db.execute(
            "SELECT scheduled_for, doctor_name, patient_name, session_id, patient_phone FROM follow_up_reminders WHERE id = ?",
            (reminder_db_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return "Maafi karein, appointment details nahi mil rahi. Clinic se seedha contact karein."

        follow_up_date, doctor_name, patient_name, session_id, patient_phone = row

        await db.execute(
            "UPDATE follow_up_reminders SET status = 'confirmed' WHERE id = ?",
            (reminder_db_id,),
        )

        # Create a task for the assistant to lock in the slot
        await db.execute(
            """
            INSERT INTO assistant_tasks (id, session_id, user_id, task_type, title, status, created_at)
            VALUES (?, ?, ?, 'follow_up_confirmed', ?, 'open', ?)
            """,
            (
                str(uuid.uuid4()), session_id, doctor_user_id,
                f"Follow-up confirmed: {patient_name or 'Patient'} → {_friendly_date(follow_up_date)}",
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()

    confirmation = (
        f"Shukriya! ✅\n\n"
        f"Aapka follow-up {_doctor_display(doctor_name)} ke saath "
        f"{_friendly_date(follow_up_date)} ke liye confirm ho gaya hai.\n\n"
        f"Clinic ki taraf se reminder aayega. Koi bhi problem ho toh "
        f"seedha clinic call karein."
    )

    # Settlement loop — send payment link if configured
    if patient_phone and settings.razorpay_page_id and settings.consultation_fee_rupees > 0:
        fee = settings.consultation_fee_rupees
        pay_url = f"https://rzp.io/l/{settings.razorpay_page_id}"
        payment_msg = (
            f"Ek aur baat — aapka consultation fee ₹{fee} abhi bhi baaki hai.\n\n"
            f"Yahan se pay karein (UPI / Card / Net Banking):\n{pay_url}\n\n"
            f"Koi dikkat ho toh clinic call karein."
        )
        try:
            await WhatsAppService.send_text_message(patient_phone, payment_msg)
        except Exception as exc:
            logger.warning("Settlement WhatsApp failed for %s: %s", patient_phone, exc)

    return confirmation


async def handle_nahi(reminder_id: str) -> str:
    async with db_connect() as db:
        await db.execute(
            "UPDATE follow_up_reminders SET status = 'declined' WHERE id = ?",
            (int(reminder_id),),
        )
        await db.commit()

    return (
        "Samajh gaye 🙏\n\n"
        "Aap kab aa sakte hain? Date aur time batayein — "
        "hum clinic se confirm karke aapko bata denge.\n\n"
        "Ya seedha clinic call karein appointment reschedule karne ke liye."
    )


# ---------------------------------------------------------------------------
# Background scheduler loop
# ---------------------------------------------------------------------------

async def _send_due_reminders() -> None:
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT id, patient_phone, patient_name, doctor_name,
                   scheduled_for, user_id
            FROM follow_up_reminders
            WHERE status = 'pending' AND due_at <= ?
            LIMIT 50
            """,
            (now,),
        ) as cur:
            rows = await cur.fetchall()

    for row in rows:
        reminder_id, phone, patient_name, doctor_name, follow_up_date, user_id = row
        name = patient_name or "aap"
        doc = _doctor_display(doctor_name)
        friendly = _friendly_date(follow_up_date)

        message = (
            f"Namaste {name} 🙏\n\n"
            f"{doc} ne aapko {friendly} ko follow-up ke liye bulaya hai.\n\n"
            f"Kya aap aa sakte hain?\n"
            f"Reply karein *HAAN* (confirm) ya *NAHI* (reschedule chahiye)"
        )

        result = await WhatsAppService.send_text_message(phone, message)
        sent_ok = result.get("success", False)

        await register_patient_interaction(
            patient_phone=phone,
            interaction_type="follow_up_confirm",
            reference_id=str(reminder_id),
            doctor_user_id=user_id,
        )

        new_status = "sent" if sent_ok else "send_failed"
        error_text = None if sent_ok else str(result.get("error") or "send failed")
        async with db_connect() as db:
            await db.execute(
                "UPDATE follow_up_reminders SET status = ?, error_text = ? WHERE id = ?",
                (new_status, error_text, reminder_id),
            )
            await db.commit()

        logger.info("Reminder %s → %s (%s)", reminder_id, phone, new_status)


async def follow_up_reminder_loop() -> None:
    """Asyncio background task started on app startup. Polls every 15 minutes."""
    logger.info("Follow-up reminder scheduler started (15-min poll)")
    while True:
        try:
            await _send_due_reminders()
        except Exception as exc:
            logger.error("Reminder loop error: %s", exc, exc_info=True)
        await asyncio.sleep(900)  # 15 minutes

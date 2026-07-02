"""
Lab order → patient WhatsApp dispatch.

When a consultation is processed and investigations are found:
  1. Format test names into a readable WhatsApp message
  2. Generate a Thyrocare/1mg pre-filled booking link
  3. Send to patient phone via WhatsApp
  4. Log the dispatch for revenue tracking
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from app.services.whatsapp_service import WhatsAppService
from app.storage.db import db_connect
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Common Indian test name normalization for cleaner display
_TEST_DISPLAY: dict[str, str] = {
    "cbc": "CBC (Complete Blood Count)",
    "complete blood count": "CBC (Complete Blood Count)",
    "crp": "CRP (C-Reactive Protein)",
    "c reactive protein": "CRP (C-Reactive Protein)",
    "hba1c": "HbA1c (Glycated Haemoglobin)",
    "fasting blood sugar": "Fasting Blood Sugar (FBS)",
    "fbs": "Fasting Blood Sugar (FBS)",
    "ppbs": "Post-Prandial Blood Sugar (PPBS)",
    "lft": "LFT (Liver Function Test)",
    "kft": "KFT (Kidney Function Test)",
    "rft": "RFT (Kidney Function Test)",
    "tsh": "TSH (Thyroid Stimulating Hormone)",
    "t3 t4 tsh": "Thyroid Profile (T3, T4, TSH)",
    "lipid profile": "Lipid Profile",
    "urine routine": "Urine Routine Examination",
    "urine r/m": "Urine Routine Examination",
    "ecg": "ECG (Electrocardiogram)",
    "echo": "Echocardiography",
    "usg abdomen": "USG Abdomen",
    "xray chest": "X-Ray Chest (PA view)",
    "chest xray": "X-Ray Chest (PA view)",
}


def _normalize_test(name: str) -> str:
    key = name.strip().lower()
    return _TEST_DISPLAY.get(key, name.strip().title())


def _thyrocare_link(tests: list[str]) -> str:
    """Generate a Thyrocare search URL pre-filled with the first test name."""
    if not tests:
        return "https://www.thyrocare.com"
    query = quote(tests[0].strip())
    return f"https://www.thyrocare.com/searchtest/{query}"


def _onemg_link(tests: list[str]) -> str:
    """Generate a 1mg lab test search URL."""
    if not tests:
        return "https://www.1mg.com/lab-tests"
    query = quote(" ".join(tests[:2]))
    return f"https://www.1mg.com/lab-tests?query={query}"


def _format_lab_message(
    doctor_name: str,
    patient_name: Optional[str],
    tests: list[str],
    session_id: str,
) -> str:
    doc = doctor_name.strip() if doctor_name else "Aapke doctor"
    if doc and not doc.lower().startswith("dr"):
        doc = f"Dr. {doc}"

    test_lines = "\n".join(f"  🔬 {_normalize_test(t)}" for t in tests[:6])
    if len(tests) > 6:
        test_lines += f"\n  ... aur {len(tests) - 6} aur tests"

    booking_link = _onemg_link(tests)
    thyrocare_link = _thyrocare_link(tests)

    # Build review link if app_base_url is configured
    review_link = ""
    if settings.app_base_url and session_id:
        base = settings.app_base_url.rstrip("/")
        review_link = f"\n📋 Aapka investigation order dekhein: {base}/api/public/investigation-order/{session_id}"

    return (
        f"Namaste{' ' + patient_name if patient_name else ''} 🙏\n\n"
        f"{doc} ne aapke liye yeh tests order kiye hain:\n\n"
        f"{test_lines}\n\n"
        f"🏠 *Home collection ke liye book karein:*\n"
        f"1mg: {booking_link}\n"
        f"Thyrocare: {thyrocare_link}"
        f"{review_link}\n\n"
        f"Koi sawal ho toh clinic se contact karein."
    )


async def dispatch_lab_order_to_patient(
    session_id: str,
    user_id: str,
    patient_phone: str,
    patient_name: Optional[str],
    doctor_name: str,
    investigations: list,
) -> bool:
    """
    Send lab order WhatsApp to patient and log the dispatch.
    Returns True if sent (or mock-sent) successfully.
    """
    # Normalize investigations to strings
    tests = []
    for item in investigations:
        if isinstance(item, str) and item.strip():
            tests.append(item.strip())
        elif isinstance(item, dict):
            name = item.get("name") or item.get("test") or str(item)
            if name:
                tests.append(name.strip())

    if not tests:
        logger.info("No parseable investigations for session %s", session_id)
        return False

    message = _format_lab_message(doctor_name, patient_name, tests, session_id)
    result = await WhatsAppService.send_text_message(patient_phone, message)
    success = result.get("success", False)

    # Log the dispatch regardless of success (for revenue tracking)
    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO lab_dispatch_log
              (id, session_id, user_id, patient_phone, tests_json, dispatched_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()), session_id, user_id, patient_phone,
                json.dumps(tests), datetime.utcnow().isoformat(),
                "sent" if success else "failed",
            ),
        )
        await db.commit()

    if success:
        logger.info("Lab order dispatched to patient %s: %s", patient_phone, tests)
    else:
        logger.warning("Lab order dispatch failed for %s: %s", patient_phone, result)

    return success


# ---------------------------------------------------------------------------
# Revenue tracking query
# ---------------------------------------------------------------------------

async def get_lab_dispatch_stats(user_id: str, since_days: int = 30) -> dict:
    """Return count of lab orders dispatched for this doctor in the last N days."""
    cutoff = (datetime.utcnow().replace(hour=0, minute=0, second=0)
              - __import__('datetime').timedelta(days=since_days)).isoformat()
    async with db_connect() as db:
        async with db.execute(
            "SELECT COUNT(*) FROM lab_dispatch_log WHERE user_id = ? AND dispatched_at >= ? AND status = 'sent'",
            (user_id, cutoff),
        ) as cur:
            row = await cur.fetchone()
    return {"lab_orders_dispatched": row[0] if row else 0, "since_days": since_days}

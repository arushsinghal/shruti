"""
DHIS (Digital Health Incentive Scheme) transaction tracker.

Every time Lipi pushes a health record to ABDM HIE-CM, we log the transaction here.
NHA pays both the clinic (75%) and Lipi DSC (25%) per ABHA-linked record, monthly.

Cat1 (discharge/lab reports): ₹20 total → clinic ₹15, Lipi ₹5
Cat2 (OPD consultations):     ₹10 total → clinic ₹7.50, Lipi ₹2.50

Threshold: first 100 tx/month/facility are unpaid (anti-abuse floor).
Claims submitted monthly via NHA dashboard.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.storage.db import db_connect

logger = logging.getLogger(__name__)

# Payout rates per category (in rupees)
_CLINIC_SHARE = {"Cat1": 15.0, "Cat2": 7.50}
_DSC_SHARE = {"Cat1": 5.0, "Cat2": 2.50}
_UNPAID_THRESHOLD = 100


async def log_transaction(
    session_id: str,
    user_id: str,
    abha_id: str,
    facility_hfr_id: str,
    category: str = "Cat2",
    transaction_id: Optional[str] = None,
) -> str:
    """
    Record a DHIS-eligible transaction after successful HIE push.
    Returns the internal dhis_transaction id.
    """
    clinic_amount = _CLINIC_SHARE.get(category, 7.50)
    dsc_amount = _DSC_SHARE.get(category, 2.50)
    tx_id = str(uuid.uuid4())

    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO dhis_transactions
              (id, session_id, user_id, abha_id, facility_hfr_id, category,
               abdm_transaction_id, clinic_amount, dsc_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_claim', ?)
            """,
            (
                tx_id, session_id, user_id, abha_id, facility_hfr_id,
                category, transaction_id or "", clinic_amount, dsc_amount,
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()

    logger.info(
        "DHIS tx logged: id=%s category=%s clinic=₹%.2f dsc=₹%.2f abha=%s",
        tx_id, category, clinic_amount, dsc_amount, abha_id,
    )
    return tx_id


async def get_monthly_claim_report(user_id: str, month: str) -> dict:
    """
    Return a summary of DHIS-eligible transactions for a given month (YYYY-MM).
    Deducts the 100-tx unpaid threshold from Cat2 count before computing payable.

    Returns:
      {
        month, total_transactions, cat1_count, cat2_count,
        payable_cat1, payable_cat2,
        clinic_gross, dsc_gross,
        clinic_payable, dsc_payable,
        threshold_deducted
      }
    """
    start = f"{month}-01"
    # Next month boundary
    year, mo = int(month[:4]), int(month[5:7])
    if mo == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{mo + 1:02d}-01"

    async with db_connect() as db:
        async with db.execute(
            """
            SELECT category, COUNT(*), SUM(clinic_amount), SUM(dsc_amount)
            FROM dhis_transactions
            WHERE user_id = ? AND created_at >= ? AND created_at < ?
            GROUP BY category
            """,
            (user_id, start, end),
        ) as cur:
            rows = await cur.fetchall()

    cat1_count = 0
    cat2_count = 0
    cat1_clinic = 0.0
    cat1_dsc = 0.0
    cat2_clinic = 0.0
    cat2_dsc = 0.0

    for row in rows:
        cat, count, clinic_sum, dsc_sum = row
        if cat == "Cat1":
            cat1_count = count
            cat1_clinic = float(clinic_sum or 0)
            cat1_dsc = float(dsc_sum or 0)
        elif cat == "Cat2":
            cat2_count = count
            cat2_clinic = float(clinic_sum or 0)
            cat2_dsc = float(dsc_sum or 0)

    total = cat1_count + cat2_count
    threshold_deducted = min(_UNPAID_THRESHOLD, cat2_count)
    payable_cat2 = max(0, cat2_count - threshold_deducted)
    payable_cat1 = cat1_count  # Cat1 threshold separate (simplified: same pool)

    clinic_payable = payable_cat1 * _CLINIC_SHARE["Cat1"] + payable_cat2 * _CLINIC_SHARE["Cat2"]
    dsc_payable = payable_cat1 * _DSC_SHARE["Cat1"] + payable_cat2 * _DSC_SHARE["Cat2"]

    return {
        "month": month,
        "total_transactions": total,
        "cat1_count": cat1_count,
        "cat2_count": cat2_count,
        "payable_cat1": payable_cat1,
        "payable_cat2": payable_cat2,
        "clinic_gross": cat1_clinic + cat2_clinic,
        "dsc_gross": cat1_dsc + cat2_dsc,
        "clinic_payable": clinic_payable,
        "dsc_payable": dsc_payable,
        "threshold_deducted": threshold_deducted,
    }

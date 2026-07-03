"""
Monthly value report — WhatsApp to every doctor on the 1st of each month.
Shows: consults documented, lab orders sent, follow-ups scheduled, hours saved.
This is the retention weapon — doctor sees ROI in numbers every month.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.storage.db import db_connect
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


async def send_monthly_report(user_id: str, whatsapp_phone: str, doctor_name: str) -> None:
    now = datetime.utcnow()
    # Last month
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_last_month = (first_of_this_month - timedelta(days=1)).replace(day=1)
    month_label = first_of_last_month.strftime("%B %Y")

    async with db_connect() as db:
        async with db.execute(
            "SELECT COUNT(*) FROM sessions WHERE user_id=? AND created_at>=? AND created_at<?",
            (user_id, first_of_last_month.isoformat(), first_of_this_month.isoformat()),
        ) as cur:
            row = await cur.fetchone()
        consults = int(row[0]) if row else 0

        async with db.execute(
            "SELECT COUNT(*) FROM lab_dispatch_log WHERE user_id=? AND dispatched_at>=? AND dispatched_at<? AND status='sent'",
            (user_id, first_of_last_month.isoformat(), first_of_this_month.isoformat()),
        ) as cur:
            row = await cur.fetchone()
        lab_orders = int(row[0]) if row else 0

        async with db.execute(
            "SELECT COUNT(*) FROM follow_up_reminders WHERE user_id=? AND created_at>=? AND created_at<?",
            (user_id, first_of_last_month.isoformat(), first_of_this_month.isoformat()),
        ) as cur:
            row = await cur.fetchone()
        follow_ups = int(row[0]) if row else 0

        async with db.execute(
            "SELECT COUNT(*), COALESCE(SUM(dsc_amount + clinic_amount), 0) FROM dhis_transactions WHERE user_id=? AND created_at>=? AND created_at<?",
            (user_id, first_of_last_month.isoformat(), first_of_this_month.isoformat()),
        ) as cur:
            row = await cur.fetchone()
        dhis_count = int(row[0]) if row else 0
        dhis_income = float(row[1]) if row else 0.0

    if consults == 0:
        return  # Nothing to report — don't spam inactive doctors

    hours_saved = round(consults * 0.75, 1)  # ~45 min per consult
    name = doctor_name.split()[0] if doctor_name else "Doctor"

    lines = [
        f"📊 *Lipi — {month_label} summary*",
        "",
        f"Namaste Dr. {name}! Pichle mahine ki report:",
        "",
        f"🩺 *{consults}* consultations documented",
        f"🧪 *{lab_orders}* lab orders sent to patients",
        f"📅 *{follow_ups}* follow-up reminders scheduled",
        f"⏱ *{hours_saved} hours* saved on paperwork",
    ]
    if dhis_count > 0:
        lines.append(f"🏛 *{dhis_count}* ABDM records filed (₹{dhis_income:,.0f} DHIS income pending)")

    lines += [
        "",
        "Lipi chalata raha — aap doctori karte raho. 🙏",
    ]

    message = "\n".join(lines)
    try:
        await WhatsAppService.send_text_message(whatsapp_phone, message)
        logger.info("Monthly report sent: user=%s consults=%d", user_id, consults)
    except Exception as exc:
        logger.warning("Monthly report WhatsApp failed: user=%s err=%s", user_id, exc)


async def monthly_report_loop() -> None:
    """Background loop — fires once on the 1st of each month for every active doctor."""
    logger.info("Monthly report loop started")
    last_run_month: str = ""

    while True:
        try:
            now = datetime.utcnow()
            this_month = now.strftime("%Y-%m")

            if now.day == 1 and this_month != last_run_month:
                logger.info("Running monthly reports for %s", this_month)
                async with db_connect() as db:
                    async with db.execute(
                        """
                        SELECT u.id, u.full_name, dp.whatsapp_phone
                        FROM users u
                        JOIN doctor_profiles dp ON dp.user_id = u.id
                        WHERE dp.whatsapp_phone IS NOT NULL AND dp.whatsapp_phone != ''
                        """
                    ) as cur:
                        doctors = await cur.fetchall()

                for user_id, full_name, whatsapp_phone in doctors:
                    await send_monthly_report(str(user_id), whatsapp_phone, full_name or "")
                    await asyncio.sleep(2)  # rate-limit sends

                last_run_month = this_month

        except Exception as exc:
            logger.error("Monthly report loop error: %s", exc)

        await asyncio.sleep(3600)  # check every hour

"""Billing, trial enforcement, and Razorpay webhook."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect
from app.utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_billing_row(user_id: str) -> dict:
    # asyncpg is strict about types: PostgreSQL id is INTEGER, so cast when possible
    param = int(user_id) if str(user_id).isdigit() else user_id
    try:
        async with db_connect() as db:
            async with db.execute(
                "SELECT plan, trial_sessions_used, paid_until, razorpay_payment_id FROM users WHERE id=?",
                (param,),
            ) as cur:
                row = await cur.fetchone()
    except Exception:
        return {"plan": "trial", "trial_sessions_used": 0, "paid_until": None, "payment_id": None}
    if not row:
        return {"plan": "trial", "trial_sessions_used": 0, "paid_until": None, "payment_id": None}
    return {
        "plan": row[0] or "trial",
        "trial_sessions_used": row[1] or 0,
        "paid_until": row[2],
        "payment_id": row[3],
    }


def _is_paid_active(billing: dict) -> bool:
    if billing["plan"] != "paid":
        return False
    paid_until = billing.get("paid_until")
    if not paid_until:
        return True  # legacy paid rows with no expiry
    try:
        exp = datetime.fromisoformat(paid_until)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp > datetime.now(timezone.utc)
    except Exception:
        return True


async def check_can_create_session(user_id: str) -> None:
    """Raise 402 if user is on expired trial and not paid."""
    billing = await get_billing_row(user_id)
    if _is_paid_active(billing):
        return
    limit = settings.trial_session_limit
    if billing["trial_sessions_used"] >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "trial_expired",
                "sessions_used": billing["trial_sessions_used"],
                "limit": limit,
                "razorpay_page_id": settings.razorpay_page_id,
                "price_rupees": settings.subscription_price_rupees,
            },
        )


async def increment_trial_usage(user_id: str) -> None:
    """Call when a session is created to tick the trial counter."""
    billing = await get_billing_row(user_id)
    if _is_paid_active(billing):
        return
    param = int(user_id) if str(user_id).isdigit() else user_id
    async with db_connect() as db:
        await db.execute(
            "UPDATE users SET trial_sessions_used = COALESCE(trial_sessions_used, 0) + 1 WHERE id=?",
            (param,),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Billing status endpoint
# ---------------------------------------------------------------------------

@router.get("/billing/status")
async def billing_status(current_user: dict = Depends(get_current_user)) -> dict:
    user_id = str(current_user["id"])
    billing = await get_billing_row(user_id)
    limit = settings.trial_session_limit
    paid = _is_paid_active(billing)
    sessions_left = max(0, limit - billing["trial_sessions_used"]) if not paid else None

    return {
        "plan": "paid" if paid else "trial",
        "trial_sessions_used": billing["trial_sessions_used"],
        "trial_limit": limit,
        "sessions_left": sessions_left,
        "paid_until": billing["paid_until"],
        "razorpay_page_id": settings.razorpay_page_id,
        "price_rupees": settings.subscription_price_rupees,
        "can_create_session": paid or billing["trial_sessions_used"] < limit,
    }


# ---------------------------------------------------------------------------
# Razorpay webhook
# ---------------------------------------------------------------------------

@router.post("/billing/webhook/razorpay", status_code=200)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
):
    """Razorpay calls this after a payment page payment is completed."""
    body = await request.body()

    # Verify HMAC-SHA256 signature if secret configured
    secret = settings.razorpay_webhook_secret
    if secret:
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, x_razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("event", "")
    logger.info("Razorpay webhook: %s", event)

    # Payment page payment — entity.email identifies the doctor
    if event in ("payment_link.paid", "payment.captured", "payment_page.paid"):
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not entity:
            entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        email = entity.get("email") or ""
        payment_id = entity.get("id") or ""

        if email:
            # Compute paid_until = 30 days from now
            from datetime import timedelta
            paid_until = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            async with db_connect() as db:
                await db.execute(
                    "UPDATE users SET plan='paid', paid_until=?, razorpay_payment_id=? WHERE email=?",
                    (paid_until, payment_id, email),
                )
                await db.commit()
            logger.info("Marked user %s as paid until %s", email, paid_until)
        else:
            logger.warning("Razorpay webhook: no email in payload")

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Manual payment confirmation (for demo / offline verification)
# ---------------------------------------------------------------------------

class ManualActivateRequest:
    pass


@router.post("/billing/admin/activate/{user_id}")
async def admin_activate(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Admin manually activates a user's paid plan (e.g. bank transfer, demo)."""
    if current_user.get("role") not in ("admin", "doctor"):
        raise HTTPException(status_code=403, detail="Not allowed")
    from datetime import timedelta
    paid_until = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    async with db_connect() as db:
        await db.execute(
            "UPDATE users SET plan='paid', paid_until=? WHERE id=?",
            (paid_until, user_id),
        )
        await db.commit()
    return {"success": True, "paid_until": paid_until}

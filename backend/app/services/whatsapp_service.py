"""WhatsApp notification dispatch service using Twilio.

If credentials are not configured in settings, falls back to logging the payload
directly to the standard logging output (ideal for local YC demo environments).
"""
import logging
from typing import Any

import httpx
from app.utils.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    @staticmethod
    def _format_phone_number(phone_number: str) -> str | None:
        clean_phone = "".join(c for c in phone_number if c.isdigit() or c == "+")
        if not clean_phone:
            return None
        if not clean_phone.startswith("+"):
            if len(clean_phone) == 10:
                clean_phone = f"+91{clean_phone}"
            else:
                clean_phone = f"+{clean_phone}"
        digits = "".join(c for c in clean_phone if c.isdigit())
        if len(digits) < 8 or len(digits) > 15:
            return None
        return clean_phone

    @staticmethod
    def _doctor_display_name(doctor_name: str) -> str:
        display = doctor_name.strip() or "your doctor"
        if display.lower().startswith("dr.") or display.lower() == "your doctor":
            return display
        return f"Dr. {display}"

    @classmethod
    async def send_message(cls, phone_number: str, doctor_name: str, secure_link: str) -> dict[str, Any]:
        """Sends a WhatsApp message via Twilio HTTP endpoint.

        Args:
            phone_number: Destination phone number (E.164 format preferred).
            doctor_name: Doctor name used in the approved template body.
            secure_link: Short-lived patient verification portal URL.

        Returns:
            Structured success/error metadata. No clinical data is included.
        """
        clean_phone = cls._format_phone_number(phone_number)
        if not clean_phone:
            return {
                "success": False,
                "error": "invalid_phone_number",
                "detail": "Patient WhatsApp phone number must be a valid international or 10-digit Indian number",
            }

        message_body = (
            f"Hello, your prescription from {cls._doctor_display_name(doctor_name)} is ready. "
            f"View it here: {secure_link}. This link expires in 24 hours."
        )

        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        from_num = settings.twilio_whatsapp_number

        # Fallback to local mock logger if keys are unconfigured
        if not sid or not token or not from_num:
            logger.info("[MOCK WHATSAPP SHARE] prescription notification dispatched (phone/message redacted from logs)")
            return {
                "success": True,
                "provider": "mock",
                "to": clean_phone,
                "message": message_body,
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        
        # Twilio WhatsApp numbers must be prefixed with "whatsapp:"
        to_whatsapp = f"whatsapp:{clean_phone}"
        from_whatsapp = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"

        data = {
            "From": from_whatsapp,
            "To": to_whatsapp,
            "Body": message_body,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    auth=(sid, token),
                    data=data,
                )
            if response.status_code in (200, 201):
                logger.info("WhatsApp prescription notification dispatched")
                response_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "success": True,
                    "provider": "twilio",
                    "to": clean_phone,
                    "sid": response_body.get("sid"),
                }

            logger.error("Twilio API failed with status %d", response.status_code)
            return {
                "success": False,
                "provider": "twilio",
                "to": clean_phone,
                "error": "twilio_error",
                "status_code": response.status_code,
            }
        except Exception as e:
            logger.error("Failed to connect to Twilio WhatsApp API: %s", e)
            return {
                "success": False,
                "provider": "twilio",
                "to": clean_phone,
                "error": "twilio_connection_error",
                "detail": str(e),
            }

    @classmethod
    async def send_text_message(cls, phone_number: str, message: str) -> dict[str, Any]:
        """Send a free-form text message. Used for inbound webhook replies (SOAP summaries, etc.).

        Falls back to log output when Twilio credentials are not configured.
        """
        clean_phone = cls._format_phone_number(phone_number)
        if not clean_phone:
            logger.warning("send_text_message: invalid phone %s", phone_number)
            return {"success": False, "error": "invalid_phone_number"}

        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        from_num = settings.twilio_whatsapp_number

        if not sid or not token or not from_num:
            logger.info("[MOCK WHATSAPP TEXT] to=%s | %s", clean_phone, message[:120])
            return {"success": True, "provider": "mock", "to": clean_phone}

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = {
            "From": from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}",
            "To": f"whatsapp:{clean_phone}",
            "Body": message,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, auth=(sid, token), data=data)
            if response.status_code in (200, 201):
                body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {"success": True, "provider": "twilio", "to": clean_phone, "sid": body.get("sid")}
            logger.error("Twilio send_text_message failed: %d", response.status_code)
            return {"success": False, "provider": "twilio", "error": "twilio_error", "status_code": response.status_code}
        except Exception as e:
            logger.error("send_text_message connection error: %s", e)
            return {"success": False, "provider": "twilio", "error": "connection_error", "detail": str(e)}

    @classmethod
    async def send_follow_up_reminder(
        cls,
        phone_number: str,
        doctor_name: str,
        follow_up_text: str,
    ) -> dict[str, Any]:
        clean_phone = cls._format_phone_number(phone_number)
        if not clean_phone:
            return {
                "success": False,
                "error": "invalid_phone_number",
                "detail": "Patient WhatsApp phone number must be a valid international or 10-digit Indian number",
            }

        safe_follow_up = " ".join(follow_up_text.split()).strip()
        message_body = (
            f"Hello, this is a follow-up reminder from {cls._doctor_display_name(doctor_name)}: "
            f"{safe_follow_up}. Please contact your clinic if symptoms worsen."
        )

        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        from_num = settings.twilio_whatsapp_number

        if not sid or not token or not from_num:
            logger.info("[MOCK WHATSAPP FOLLOW-UP] reminder dispatched (phone/message redacted from logs)")
            return {
                "success": True,
                "provider": "mock",
                "to": clean_phone,
                "message": message_body,
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = {
            "From": from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}",
            "To": f"whatsapp:{clean_phone}",
            "Body": message_body,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, auth=(sid, token), data=data)
            if response.status_code in (200, 201):
                response_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "success": True,
                    "provider": "twilio",
                    "to": clean_phone,
                    "sid": response_body.get("sid"),
                }
            return {
                "success": False,
                "provider": "twilio",
                "to": clean_phone,
                "error": "twilio_error",
                "detail": response.text,
                "status_code": response.status_code,
            }
        except Exception as e:
            logger.error("Failed to send follow-up reminder via Twilio: %s", e)
            return {
                "success": False,
                "provider": "twilio",
                "to": clean_phone,
                "error": "twilio_connection_error",
                "detail": str(e),
            }

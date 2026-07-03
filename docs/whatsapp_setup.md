# WhatsApp Setup

1. Create a Twilio account at https://www.twilio.com.
2. Activate the WhatsApp Sandbox for demo or pilot testing.
3. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_WHATSAPP_NUMBER` in `.env`.
4. For production after YC/pilot validation, apply for WhatsApp Business API approval through Twilio.
5. Use sender numbers in `whatsapp:+1415XXXXXXX` format. Lipi adds the `whatsapp:` prefix when it is missing.

In demo mode with no Twilio keys, the system logs `MOCK WHATSAPP` and does not send a message.

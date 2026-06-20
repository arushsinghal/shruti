# Lipi — Pilot Privacy Note

**For doctors and clinical staff participating in the Lipi pilot.**

## What is Lipi?

Lipi is an AI-assisted clinical documentation tool. It helps doctors create structured medical notes (SOAP notes) from spoken consultations in Hindi, Hinglish, or English.

**Lipi is an assistive tool — not medical advice.** The doctor is the final authority on every clinical decision, and must review all AI-generated output before any clinical use.

## Patient Consent

- Patient **verbal consent is required** before any recording begins.
- The doctor must confirm consent in the app before the recording/upload function becomes available.
- Suggested consent script: *"Main aapki baat record karunga taaki medical notes sahi ban sakein. Aapki jaankari surakshit hai aur sirf aapke ilaaj ke liye use hogi."*

## Audio Handling

- Audio is sent to Sarvam AI (servers in India) for speech-to-text conversion only.
- **Audio is not stored permanently.** It is deleted from our systems immediately after the clinical note is generated.
- Sarvam does not retain audio beyond the API call.

## PHI (Protected Health Information) Scrubbing

- Before the transcript text is stored, a local privacy scrubber removes sensitive identifiers where detected — including names, phone numbers, email addresses, and absolute dates.
- Clinical content (symptoms, medications, vitals, relative durations like "3 din se bukhar") is preserved because it is medically necessary.
- PHI scrubbing is best-effort and not guaranteed to catch every identifier. Doctor review is required.

## Doctor Review Required

- All AI-generated notes are drafts.
- The doctor must review, edit, and confirm every note before clinical use.
- Lipi never auto-prescribes, never claims diagnostic certainty, and never makes autonomous clinical decisions.

## Data Storage

- Scrubbed transcripts and generated notes are stored securely and are accessible only to the treating doctor's account.
- Session data can be deleted on request.

## Questions?

Contact: arushsinghal98@gmail.com

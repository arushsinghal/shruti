"""Local PHI De-identification Layer (Privacy Scrubber).

Uses spaCy NER and regex fallbacks to detect and redact Protected Health
Information (PHI) from transcripts before review, export, or optional tooling.

Redacts:
- Names (PERSON)
- Dates/Ages (DATE)
- Locations (GPE, LOC)
- Organizations (ORG)
- Phone Numbers (Regex)
- Emails (Regex)
"""

import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
    HAS_NER = True
except OSError:
    nlp = spacy.blank("en")
    HAS_NER = False

_PHONE_REGEX = re.compile(r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b')
_EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
_TITLE_NAME_REGEX = re.compile(r'\b(?:Patient|Dr\.?|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b')


class PHIScrubberService:
    """Scrub PHI from text locally on the edge."""

    def scrub(self, text: str) -> str:
        if not text:
            return ""

        # 1. Regex Replacements (Phones, Emails)
        text = _PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = _EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = _TITLE_NAME_REGEX.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_NAME]"), text)

        if not HAS_NER:
            return text

        # 2. spaCy NER Replacements
        doc = nlp(text)
        
        # Build a list of replacements from the end to the start so offsets don't change
        replacements = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                replacements.append((ent.start_char, ent.end_char, "[REDACTED_NAME]"))
            elif ent.label_ in ("DATE", "TIME"):
                # We often want to keep clinical duration (e.g., "for 3 days"), 
                # but scrub birthdates. For strict PHI, we scrub all exact dates.
                # To be safe but clinical, we scrub exact dates but might leave durations.
                # For this prototype, we'll aggressively scrub DATE.
                replacements.append((ent.start_char, ent.end_char, "[REDACTED_DATE]"))
            elif ent.label_ in ("GPE", "LOC"):
                replacements.append((ent.start_char, ent.end_char, "[REDACTED_LOCATION]"))
            elif ent.label_ == "ORG":
                replacements.append((ent.start_char, ent.end_char, "[REDACTED_ORG]"))

        # Apply replacements in reverse order
        replacements.sort(key=lambda x: x[0], reverse=True)
        scrubbed = text
        for start, end, label in replacements:
            scrubbed = scrubbed[:start] + label + scrubbed[end:]

        return scrubbed

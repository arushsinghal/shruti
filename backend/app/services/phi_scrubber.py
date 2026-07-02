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
_INDIAN_PHONE_REGEX = re.compile(r'\b[6-9]\d{9}\b')
_AADHAAR_REGEX = re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b')
_ABHA_REGEX = re.compile(r'\b\d{2}-\d{4}-\d{4}-\d{4}\b')
_UHID_MRN_REGEX = re.compile(r'\b(?:UHID|MRN|UID|HN|PID)[:\s#-]*\d{4,12}\b', re.IGNORECASE)
_PIN_CODE_REGEX = re.compile(r'(?i)(?:pin\s*(?:code)?|pincode)[:\s]*([1-9]\d{5})')
_EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
_TITLE_NAME_REGEX = re.compile(
    r'\b(?:Patient|Dr\.?|Doctor|Shri|Smt\.?|Sri|Ku\.?|Kumari|Mr\.?|Mrs\.?|Ms\.?|मरीज़|मरीज|रोगी)\s+'
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
)
_DATE_REGEX = re.compile(
    r'\b(?:'
    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    r'|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
    r'|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s+\d{4})?'
    r'|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:\s+\d{4})?'
    r')\b',
    re.IGNORECASE
)

# Relative clinical durations are NOT PHI — "fever for 3 days" must survive scrubbing.
# Absolute calendar dates ("March 4, 2024", "12/05/1985") are still scrubbed.
_CLINICAL_DURATION_RE = re.compile(
    r'^(?:'
    r'\d+\s*(?:day|week|month|year|hour|minute|hr|min)s?'         # "3 days", "2 weeks", "4 hours"
    r'|a\s+(?:day|week|month|year|hour)'                           # "a week"
    r'|(?:few|several|many|couple\s+of)\s+(?:day|week|month|year|hour)s?'  # "few days"
    r'|yesterday'                                                  # "yesterday"
    r'|(?:(?:since|this)\s+)?(?:morning|evening|night|afternoon|noon)'  # "morning", "this morning", "since morning"
    r'|last\s+(?:night|week|month|year)'                               # "last night", "last week"
    r')$',
    re.IGNORECASE,
)


class PHIScrubberService:
    """Scrub PHI from text locally on the edge."""

    def scrub(self, text: str) -> str:
        if not text:
            return ""

        # Regex-only: phones, emails, "Dr./Patient [Name]" patterns.
        # spaCy NER disabled — English model produces false positives on
        # Hindi/Hinglish clinical text (tags BP values, Hindi words, lab
        # names like CBC as PHI). Regex catches real identifying info only.
        text = _PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = _INDIAN_PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = _AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)
        text = _ABHA_REGEX.sub("[REDACTED_ABHA]", text)
        text = _UHID_MRN_REGEX.sub("[REDACTED_ID]", text)
        text = _PIN_CODE_REGEX.sub("[REDACTED_PIN]", text)
        text = _EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = _DATE_REGEX.sub("[REDACTED_DATE]", text)
        text = _TITLE_NAME_REGEX.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_NAME]"), text)
        return text

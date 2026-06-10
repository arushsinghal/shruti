"""Deterministic clinical fact extraction from multilingual (English + Hindi/Hinglish) transcripts.

Uses spaCy for sentence segmentation and regex rules to extract:
- Symptoms (English + transliterated Hindi keywords)
- Vitals (BP, Temperature)
- Allergies
- Investigations
- Medications (with dosage + frequency)

Each extracted fact is linked to its source sentence for audit trail.
"""

import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")


# ------------------------------------------------------------------
# Multilingual keyword mappings (canonical English ← Hindi/Hinglish)
# ------------------------------------------------------------------

_SYMPTOM_MAP: dict[str, str] = {
    # English
    "fever": "fever",
    "cough": "cough",
    "headache": "headache",
    "pain": "pain",
    "chest pain": "chest pain",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "dizziness": "dizziness",
    "weakness": "weakness",
    "fatigue": "fatigue",
    "breathlessness": "breathlessness",
    "shortness of breath": "breathlessness",
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "cold": "cold",
    "sore throat": "sore throat",
    "body ache": "body ache",
    "cavity": "cavity",
    "cavities": "cavity",
    "toothache": "toothache",
    "tooth ache": "toothache",
    "tooth pain": "toothache",
    "teeth pain": "toothache",
    # Hindi / Hinglish transliterations
    "bukhar": "fever",
    "bukhaar": "fever",
    "buhkhar": "fever",
    "khasi": "cough",
    "khansi": "cough",
    "dard": "pain",
    "sir dard": "headache",
    "sar dard": "headache",
    "pet dard": "abdominal pain",
    "seena dard": "chest pain",
    "chakkar": "dizziness",
    "ulti": "vomiting",
    "jee machlana": "nausea",
    "kamzori": "weakness",
    "thakan": "fatigue",
    "saans": "breathlessness",
    "dast": "diarrhea",
    "sardi": "cold",
    "gala kharab": "sore throat",
    "badan dard": "body ache",
    "daant dard": "toothache",
    "dant dard": "toothache",
}

_INVESTIGATION_MAP: dict[str, str] = {
    "x-ray": "X-Ray",
    "x ray": "X-Ray",
    "xray": "X-Ray",
    "blood test": "Blood Test",
    "blood work": "Blood Test",
    "khoon ki jaanch": "Blood Test",
    "cbc": "CBC",
    "crp": "CRP",
    "mri": "MRI",
    "ultrasound": "Ultrasound",
    "ct scan": "CT Scan",
    "ecg": "ECG",
    "ekg": "ECG",
    "echo": "Echocardiography",
    "urine test": "Urine Test",
    "thyroid test": "Thyroid Panel",
    "root canal": "Root Canal Treatment",
    "root canal treatment": "Root Canal Treatment",
    "rct": "Root Canal Treatment",
    "filling": "Cavity Filling",
    "cavity filling": "Cavity Filling",
    "examination": "Clinical Examination",
}

_ALLERGY_PATTERNS = [
    # English
    r'(?:allergic\s+to|allergy\s+to|allergy)\s+([a-zA-Z]+)',
    # Hindi / Hinglish
    r'(?:se\s+allergy|allergy\s+hai)\s+([a-zA-Z]+)',
]

_KNOWN_MEDICATIONS = {
    "painkiller", "painkillers", "pain killer", "pain killers",
    "antibiotic", "antibiotics",
    "paracetamol", "dolo", "crocin", "calpol",
    "cetirizine", "aspirin", "ibuprofen", "amoxicillin", "amox",
    "insulin", "metformin", "pcm", "antacid", "antacids",
}

_UNCERTAINTY_WORDS = re.compile(
    r'\b(maybe|possible|possibly|probably|might|suspected?|shayad|ho\s+sakta)\b',
    re.IGNORECASE,
)

# Negation detection — words that flip a following clinical term to absent/denied
_NEGATION_RE = re.compile(
    r'\b(no|not|denies?|denied|without|never|nor|nahi|nahin|absent)\b',
    re.IGNORECASE,
)
# Clause-boundary words that cancel a preceding negation
# (e.g. "no fever BUT has headache" — "but" cancels "no")
# A comma also resets negation scope.
_CLAUSE_RESET_RE = re.compile(
    r'\b(but|however|and|also|though|although|yet|still|except)\b|,',
    re.IGNORECASE,
)
# Doctor self-correction: "no make it 650 mg", "actually 500 mg", "wait 250 mg"
_CORRECTION_RE = re.compile(
    r'(?:no\s+make\s+it|actually|wait)[,\s]+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))',
    re.IGNORECASE,
)


def _is_negated(text: str, match_start: int, window: int = 40) -> bool:
    """Return True if the keyword at match_start is immediately preceded by a negation word
    with no clause-resetting boundary in between."""
    preceding = text[max(0, match_start - window): match_start]
    neg_match = None
    for m in _NEGATION_RE.finditer(preceding):
        neg_match = m  # keep the rightmost (nearest) negation
    if neg_match is None:
        return False
    # If a clause boundary appears between the negation and the keyword, negation is cancelled
    reset = _CLAUSE_RESET_RE.search(preceding, neg_match.end())
    return reset is None


class ClinicalExtractorService:
    """Extract structured clinical facts from a transcript string."""

    def extract(self, transcript: str) -> dict:
        result: dict = {
            "symptoms": [],
            "medications": [],
            "vitals": [],
            "allergies": [],
            "investigations": [],
            "contexts": {},
        }

        if not transcript or not transcript.strip():
            return result

        doc = nlp(transcript)

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            # Skip uncertain sentences
            if _UNCERTAINTY_WORDS.search(sent_text):
                continue

            self._extract_symptoms(sent_text, result)
            self._extract_vitals(sent_text, result)
            self._extract_allergies(sent_text, result)
            self._extract_investigations(sent_text, result)
            self._extract_medications(sent_text, result)

        return result

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_symptoms(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        for keyword, canonical in _SYMPTOM_MAP.items():
            m = re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower)
            if m and not _is_negated(lower, m.start()):
                if canonical not in result["symptoms"]:
                    result["symptoms"].append(canonical)
                    result["contexts"][canonical] = sent_text

    @staticmethod
    def _extract_vitals(sent_text: str, result: dict) -> None:
        # Blood Pressure — e.g. "150/90", "BP 120/80"
        bp_match = re.search(r'\b(\d{2,3}\s*/\s*\d{2,3})\b', sent_text)
        if bp_match:
            bp_value = bp_match.group(1).replace(" ", "")
            vital = f"BP {bp_value}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Temperature — e.g. "38.5 C", "101F", "temperature 99.2 F"
        temp_match = re.search(
            r'\b(\d{2,3}(?:\.\d{1,2})?)\s*(?:°\s*)?(F|C|fahrenheit|celsius)\b',
            sent_text, re.IGNORECASE,
        )
        if temp_match:
            unit = temp_match.group(2)[0].upper()  # normalize to F or C
            vital = f"Temp {temp_match.group(1)} {unit}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

    @staticmethod
    def _extract_allergies(sent_text: str, result: dict) -> None:
        for pattern in _ALLERGY_PATTERNS:
            match = re.search(pattern, sent_text, re.IGNORECASE)
            if match:
                allergen = match.group(1).lower().strip()
                if allergen and allergen not in result["allergies"]:
                    result["allergies"].append(allergen)
                    result["contexts"][allergen] = sent_text

    @staticmethod
    def _extract_investigations(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        for keyword, canonical in _INVESTIGATION_MAP.items():
            if re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower):
                if canonical not in result["investigations"]:
                    result["investigations"].append(canonical)
                    result["contexts"][canonical] = sent_text

    @staticmethod
    def _extract_medications(sent_text: str, result: dict) -> None:
        freq_pattern = re.compile(
            r'\b(BD|OD|TDS|QID|SOS|PRN|twice\s+daily|once\s+(?:a\s+)?day|'
            r'thrice\s+daily|three\s+times\s+(?:a\s+)?day|'
            r'din\s+mein\s+do\s+baar|din\s+mein\s+teen\s+baar)\b',
            re.IGNORECASE,
        )
        med_matches = re.finditer(
            r'\b([A-Za-z]{3,})\s+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g)\b)',
            sent_text, re.IGNORECASE,
        )

        for match in med_matches:
            name = match.group(1).lower()
            dosage = match.group(2).strip()

            # Skip false-positive words that look like med names
            skip_words = {
                "the", "and", "for", "with", "this", "that", "from",
                "has", "was", "are", "his", "her", "she", "him",
                "not", "also", "but", "start", "give", "take",
                "patient", "doctor", "daily", "twice", "once",
            }
            if name in skip_words:
                continue

            freq = ""
            freq_match = freq_pattern.search(sent_text, match.end())
            if freq_match:
                freq = freq_match.group(1).strip()

            # Don't duplicate the same medication
            existing = [m for m in result["medications"] if m["name"] == name]
            if existing:
                # Update dosage/frequency if they were empty
                if not existing[0]["dosage"]:
                    existing[0]["dosage"] = dosage
                if not existing[0]["frequency"] and freq:
                    existing[0]["frequency"] = freq
            else:
                result["medications"].append({
                    "name": name,
                    "dosage": dosage,
                    "frequency": freq,
                })
                result["contexts"][name] = sent_text

        # Extract known medications without explicit dosage
        lower_sent = sent_text.lower()
        for med_name in _KNOWN_MEDICATIONS:
            pattern = rf'\b{re.escape(med_name)}\b'
            m = re.search(pattern, lower_sent)
            if m:
                # Check if it was already matched
                already_matched = False
                for existing in result["medications"]:
                    if existing["name"] == med_name or med_name in existing["name"] or existing["name"] in med_name:
                        already_matched = True
                        break

                if not already_matched:
                    # Find frequency if present
                    freq = ""
                    freq_match = freq_pattern.search(lower_sent, m.end())
                    if freq_match:
                        freq = freq_match.group(1).strip()

                    result["medications"].append({
                        "name": med_name,
                        "dosage": "",
                        "frequency": freq,
                    })
                    result["contexts"][med_name] = sent_text

        # Doctor self-corrections ("no make it X mg", "actually X mg", "wait X mg")
        # override the most recently extracted medication's dosage/frequency.
        correction = _CORRECTION_RE.search(sent_text)
        if correction and result["medications"]:
            new_dosage = correction.group(1).strip()
            freq_match = freq_pattern.search(sent_text, correction.end())
            last_med = result["medications"][-1]
            last_med["dosage"] = new_dosage
            if freq_match:
                last_med["frequency"] = freq_match.group(1).strip()

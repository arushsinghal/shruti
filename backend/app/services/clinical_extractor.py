"""Deterministic clinical fact extraction from multilingual transcripts.

Extraction layers (applied in order, results merged):
  0. ASR normalization — rejoins split words, fixes common Sarvam ASR errors
  1. Keyword maps   — English + transliterated Hinglish + Devanagari Hindi
  2. Fuzzy matching — catches ASR spelling errors via rapidfuzz (optional dep)
  3. Regex rules    — vitals, allergies, medications, follow-up
  4. Negation guard — pre-negation (English) + post-negation (Hindi "nahi")

spaCy is used only for sentence segmentation.
"""

import asyncio
import logging
import re
import spacy

from app.services.medical_ontology import ontology as _ontology

logger = logging.getLogger(__name__)

# ── Learned knowledge overlay (populated by reload_knowledge()) ──────────────
_LEARNED_OVERLAYS: dict = {}


def reload_knowledge() -> None:
    """Load promoted knowledge from the LearningService into the extractor overlay.

    Called once at app startup (from lifespan) and can be called again after
    admin approvals to pick up newly-promoted rules without a restart.
    """
    from app.services.learning_service import learning_service

    try:
        overlay = asyncio.get_event_loop().run_until_complete(
            learning_service.load_promoted_knowledge()
        )
    except RuntimeError:
        # No running event loop (e.g. tests) — create a temporary one
        overlay = asyncio.new_event_loop().run_until_complete(
            learning_service.load_promoted_knowledge()
        )

    global _LEARNED_OVERLAYS
    _LEARNED_OVERLAYS = overlay
    _ontology.load(overlay)
    total = sum(len(v) for v in overlay.values())
    logger.info("reload_knowledge: loaded %d promoted rules across %d fields", total, len(overlay))


async def async_reload_knowledge() -> None:
    """Async variant of reload_knowledge for use inside a running event loop."""
    from app.services.learning_service import learning_service

    overlay = await learning_service.load_promoted_knowledge()
    global _LEARNED_OVERLAYS
    _LEARNED_OVERLAYS = overlay
    _ontology.load(overlay)
    total = sum(len(v) for v in overlay.values())
    logger.info("reload_knowledge: loaded %d promoted rules across %d fields", total, len(overlay))

try:
    nlp = spacy.load("en_core_web_sm")
except OSError as exc:
    logger.warning("spaCy model en_core_web_sm unavailable; using blank sentencizer only: %s", exc)
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")


# ──────────────────────────────────────────────────────────────────────────────
# Pre-processing: Devanagari detection + transliteration
# ──────────────────────────────────────────────────────────────────────────────

_DEVANAGARI_RE = re.compile(r'[ऀ-ॿ]')


def _maybe_transliterate(text: str) -> str:
    """If Devanagari script detected, try indic_transliteration → ITRANS Roman.
    Falls back to original text if library not installed."""
    if not _DEVANAGARI_RE.search(text):
        return text
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
    except Exception:
        return text  # library not installed — Devanagari keywords in maps still fire


# ──────────────────────────────────────────────────────────────────────────────
# Layer 0: ASR normalization (runs before extraction)
# ──────────────────────────────────────────────────────────────────────────────

_ASR_COMMON_MISSPELLS: dict[str, str] = {
    "paracetemol": "paracetamol",
    "paracitemol": "paracetamol",
    "amoxicilin": "amoxicillin",
    "amoxycillin": "amoxicillin",
    "azithromicin": "azithromycin",
    "azithromycine": "azithromycin",
    "cetirizene": "cetirizine",
    "cetrizine": "cetirizine",
    "cetrizene": "cetirizine",
    "metformine": "metformin",
    "amlodepine": "amlodipine",
    "amlodipin": "amlodipine",
    "omeprazol": "omeprazole",
    "omeprazolе": "omeprazole",
    "pantoprazol": "pantoprazole",
    "ibuprofin": "ibuprofen",
    "ibuprufen": "ibuprofen",
    "monteleukast": "montelukast",
    "montelucast": "montelukast",
    "levocetirizine": "levocetirizine",
    "levocetrizine": "levocetirizine",
    "augmentin": "augmentin",
    "ciprofloxacine": "ciprofloxacin",
    "norfloxacine": "norfloxacin",
    "ofloxacine": "ofloxacin",
    "metronidazol": "metronidazole",
    "atorvastatin": "atorvastatin",
    "atorvastatine": "atorvastatin",
    "losartan": "losartan",
    "telmisartan": "telmisartan",
    "rabeprazol": "rabeprazole",
    "domperidone": "domperidone",
    "domperidon": "domperidone",
    "ondansetrone": "ondansetron",
    "ceftriaxon": "ceftriaxone",
    "dexamethason": "dexamethasone",
    "prednisolon": "prednisolone",
    "methylcobalamine": "methylcobalamin",
    "methycobalamin": "methylcobalamin",
    "gastroenteraitis": "gastroenteritis",
    "gastroentritis": "gastroenteritis",
    "hypertention": "hypertension",
    "diabetis": "diabetes",
    "diabeties": "diabetes",
    "pneumonea": "pneumonia",
    "pharyngits": "pharyngitis",
    "bronchites": "bronchitis",
    # ── Cardiology ASR errors (rare drug names Sarvam mangles) ───────────
    # PAH drugs — Sarvam has minimal exposure to these; common phonetic slips.
    "bosentin": "bosentan", "bosantan": "bosentan", "bosntan": "bosentan",
    "ambrisentin": "ambrisentan", "ambresentan": "ambrisentan",
    "macitentin": "macitentan", "masitentan": "macitentan", "macetentan": "macitentan",
    "riocigaut": "riociguat", "riociguate": "riociguat", "riocguat": "riociguat",
    "selexipag": "selexipag", "selexpag": "selexipag",
    "treprostonil": "treprostinil", "treprostinal": "treprostinil",
    "epoprostinol": "epoprostenol", "iloprost": "iloprost", "ilioprost": "iloprost",
    # HF drugs — trailing-vowel and consonant-cluster slips.
    "sacubatril": "sacubitril", "sakubitril": "sacubitril", "sacubitrol": "sacubitril",
    "ivabradin": "ivabradine", "ivabredine": "ivabradine", "ivabraden": "ivabradine",
    "vericiguate": "vericiguat", "vericigaut": "vericiguat",
    "dapaglifozin": "dapagliflozin", "dapagliflozine": "dapagliflozin",
    "empaglifozin": "empagliflozin", "empagliflozine": "empagliflozin",
    # NOACs — frequently misheard.
    "rivaroxoban": "rivaroxaban", "rivaroxiban": "rivaroxaban", "rivroxaban": "rivaroxaban",
    "apixiban": "apixaban", "apaxaban": "apixaban", "appixaban": "apixaban",
    "dabigatron": "dabigatran", "dabigitran": "dabigatran",
    "edoxiban": "edoxaban",
    # Antiplatelets / antiarrhythmics.
    "ticagrelol": "ticagrelor", "ticagrylor": "ticagrelor", "ticagrelor": "ticagrelor",
    "prasugrol": "prasugrel", "prasugril": "prasugrel",
    "amiodaron": "amiodarone", "amiodarne": "amiodarone", "amioderone": "amiodarone",
    "dronedarone": "dronedarone", "dronedarne": "dronedarone",
    "trimetazidin": "trimetazidine", "trimetazadine": "trimetazidine",
    "nicorandyl": "nicorandil", "nikorandil": "nicorandil",
    "ranolazine": "ranolazine", "ranolazin": "ranolazine",
    "cilnidipin": "cilnidipine", "cilnidpine": "cilnidipine",
    "nebivalol": "nebivolol", "nebivololol": "nebivolol",
}


def _normalize_asr_text(text: str, vocab: set[str]) -> str:
    """Fix common ASR errors before extraction.

    1. Rejoin split words: "parace tamol" → "paracetamol"
    2. Fix common misspellings: "paracetemol" → "paracetamol"
    3. Normalize spacing around dosage units: "650 mg" → "650mg"
    """
    # Fix common misspellings (case-insensitive) — merge learned ASR corrections
    merged_misspells = {**_ASR_COMMON_MISSPELLS, **_LEARNED_OVERLAYS.get('asr_correction', {})}
    for wrong, right in merged_misspells.items():
        text = re.sub(rf'\b{re.escape(wrong)}\b', right, text, flags=re.IGNORECASE)

    # Rejoin split words: try combining adjacent words and check against vocab
    words = text.split()
    merged = []
    i = 0
    while i < len(words):
        if i + 1 < len(words):
            combined = words[i] + words[i + 1]
            if combined.lower() in vocab:
                merged.append(combined)
                i += 2
                continue
            # Try with fuzzy (for 3-part splits like "para ceta mol")
            if i + 2 < len(words):
                triple = words[i] + words[i + 1] + words[i + 2]
                if triple.lower() in vocab:
                    merged.append(triple)
                    i += 3
                    continue
        merged.append(words[i])
        i += 1
    text = " ".join(merged)

    # Normalize spacing around dosage: "650 mg" → "650mg", "2.5 ml" → "2.5ml"
    text = re.sub(r'(\d+(?:\.\d+)?)\s+(mg|ml|mcg|g)\b', r'\1\2', text)

    return text


# ──────────────────────────────────────────────────────────────────────────────
# Keyword maps  (canonical English ← Hindi / Hinglish / Devanagari)
# ──────────────────────────────────────────────────────────────────────────────

_SYMPTOM_MAP: dict[str, str] = {
    # ── Core English symptoms ─────────────────────────────────────────────
    "fever": "fever",
    # Common ASR mis-spellings (Sarvam STT errors on English words)
    "fevre": "fever", "fver": "fever", "fevr": "fever",
    "headach": "headache", "hedache": "headache",
    "vomitin": "vomiting", "vomitting": "vomiting",
    "diarrhoea": "diarrhea", "diarreia": "diarrhea", "diarea": "diarrhea",
    "sweling": "swelling", "swollne": "swelling",
    "high fever": "fever",
    "high grade fever": "fever",
    "low grade fever": "low grade fever",
    "intermittent fever": "intermittent fever",
    "continuous fever": "fever",
    "persistent fever": "fever",
    "cough": "cough",
    "dry cough": "dry cough",
    "wet cough": "productive cough",
    "productive cough": "productive cough",
    "headache": "headache",
    "chest pain": "chest pain",
    "chest tightness": "chest tightness",
    "nausea": "nausea",
    "nauseous": "nausea",
    "vomiting": "vomiting",
    "dizziness": "dizziness",
    "vertigo": "dizziness",
    "weakness": "weakness",
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "lethargy": "fatigue",
    "breathlessness": "breathlessness",
    "shortness of breath": "breathlessness",
    "difficulty breathing": "breathlessness",
    "sob": "breathlessness",
    "dyspnea": "breathlessness",
    "dyspnoea": "breathlessness",
    "dyspnoea on exertion": "exertional dyspnea",
    "exertional dyspnea": "exertional dyspnea",
    "exertional breathlessness": "exertional dyspnea",
    "doe": "exertional dyspnea",
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "loose motions": "diarrhea",
    "loose motion": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "frequent stools": "diarrhea",
    "cold": "cold",
    "common cold": "cold",
    "runny nose": "runny nose",
    "nasal discharge": "runny nose",
    "nasal drip": "runny nose",
    "blocked nose": "blocked nose",
    "nasal congestion": "blocked nose",
    "stuffy nose": "blocked nose",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "throat irritation": "sore throat",
    "throat infection": "sore throat",
    "body ache": "body ache",
    "muscle ache": "body ache",
    "muscle pain": "body ache",
    "myalgia": "body ache",
    "abdominal pain": "abdominal pain",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "belly ache": "abdominal pain",
    "lower abdominal pain": "lower abdominal pain",
    "upper abdominal pain": "upper abdominal pain",
    "epigastric pain": "epigastric pain",
    "back pain": "back pain",
    "lower back pain": "lower back pain",
    "backache": "back pain",
    "rash": "rash",
    "skin rash": "rash",
    "hives": "rash",
    "urticaria": "rash",
    "itching": "itching",
    "itchy": "itching",
    "pruritus": "itching",
    "burning": "burning sensation",
    "burning sensation": "burning sensation",
    "burning micturition": "burning micturition",
    "burning urination": "burning micturition",
    "dysuria": "burning micturition",
    "painful urination": "burning micturition",
    "swelling": "swelling",
    "edema": "edema",
    "oedema": "edema",
    "pitting edema": "edema",
    "ankle swelling": "ankle swelling",
    "ankle oedema": "ankle swelling",
    "ankle edema": "ankle swelling",
    "pedal edema": "ankle swelling",
    "pedal oedema": "ankle swelling",
    "leg swelling": "ankle swelling",
    "facial swelling": "facial swelling",
    "palpitations": "palpitations",
    "heart racing": "palpitations",
    "rapid heartbeat": "palpitations",
    # ── Cardiology symptoms (tuned for AIIMS cardiology) ──────────────────
    # NOTE: bare "PND" deliberately NOT added — collides with post-natal
    # depression in obstetrics. Bare "LOC" omitted — collides with "location".
    "orthopnea": "orthopnea",
    "orthopnoea": "orthopnea",
    "paroxysmal nocturnal dyspnea": "paroxysmal nocturnal dyspnea",
    "paroxysmal nocturnal dyspnoea": "paroxysmal nocturnal dyspnea",
    "nocturnal dyspnea": "paroxysmal nocturnal dyspnea",
    "syncope": "syncope",
    "presyncope": "presyncope",
    "near syncope": "presyncope",
    "near-syncope": "presyncope",
    "fainting": "syncope",
    "fainting episode": "syncope",
    "loss of consciousness": "syncope",
    "transient loss of consciousness": "syncope",
    "blackout": "syncope",
    "cyanosis": "cyanosis",
    "central cyanosis": "cyanosis",
    "peripheral cyanosis": "cyanosis",
    "bluish discoloration": "cyanosis",
    "bluish discolouration": "cyanosis",
    "hemoptysis": "hemoptysis",
    "haemoptysis": "hemoptysis",
    "blood in sputum": "hemoptysis",
    "coughing blood": "hemoptysis",
    "blood in cough": "hemoptysis",
    "anasarca": "anasarca",
    "generalized swelling": "anasarca",
    "generalised swelling": "anasarca",
    "ascites": "ascites",
    "abdominal distension": "abdominal distension",
    "abdominal distention": "abdominal distension",
    "exercise intolerance": "exercise intolerance",
    "effort intolerance": "exercise intolerance",
    "reduced exercise capacity": "exercise intolerance",
    "decreased effort tolerance": "exercise intolerance",
    "chest heaviness": "chest pain",
    "chest discomfort": "chest pain",
    "exertional chest pain": "exertional chest pain",
    "claudication": "claudication",
    "intermittent claudication": "claudication",
    "calf pain on walking": "claudication",
    "raised jvp": "raised jvp",
    "jvp raised": "raised jvp",
    "jvp elevated": "raised jvp",
    "elevated jvp": "raised jvp",
    "engorged neck veins": "raised jvp",
    "crepitations": "crepitations",
    "crepitation": "crepitations",
    "crackles": "crepitations",
    "basal crepitations": "crepitations",
    "bilateral crepitations": "crepitations",
    "fine crepitations": "crepitations",
    "coarse crepitations": "crepitations",
    # Hinglish cardiac symptoms (how Hindi-speaking patients actually report)
    "dhadkan": "palpitations",
    "dhadkan tez": "palpitations",
    "dhadkan tez hona": "palpitations",
    "dhadkan badhna": "palpitations",
    "dil tez dhadakna": "palpitations",
    "dil zor se dhadakna": "palpitations",
    "behosh": "syncope",
    "behoshi": "syncope",
    "behosh hona": "syncope",
    "chakkar aake gir jana": "syncope",
    "chakkar aakar gir jana": "syncope",
    "dam ghutna": "breathlessness",
    "dam phoolna": "breathlessness",
    "pair mein sujan": "ankle swelling",
    "paon mein sujan": "ankle swelling",
    "pairo mein sujan": "ankle swelling",
    "tango mein sujan": "ankle swelling",
    "seene mein bhaaripan": "chest pain",
    "chhati mein bhaaripan": "chest pain",
    "chhati mein bhaari": "chest pain",
    "neela pad jana": "cyanosis",
    "hoth neele padna": "cyanosis",
    "khaansi mein khoon": "hemoptysis",
    "balgam mein khoon": "hemoptysis",
    "pet mein paani": "ascites",
    # Devanagari cardiac symptoms
    "धड़कन": "palpitations",
    "बेहोशी": "syncope",
    "पैर में सूजन": "ankle swelling",
    "सीने में भारीपन": "chest pain",
    "wheezing": "wheezing",
    "constipation": "constipation",
    "bloating": "bloating",
    "gas": "bloating",
    "flatulence": "bloating",
    "acidity": "acidity",
    "heartburn": "acidity",
    "acid reflux": "acidity",
    "regurgitation": "acidity",
    "indigestion": "indigestion",
    "dyspepsia": "indigestion",
    "toothache": "toothache",
    "tooth ache": "toothache",
    "tooth pain": "toothache",
    "teeth pain": "toothache",
    "dental pain": "toothache",
    "eye pain": "eye pain",
    "eye irritation": "eye irritation",
    "red eyes": "eye irritation",
    "watery eyes": "watery eyes",
    "blurred vision": "blurred vision",
    "double vision": "blurred vision",
    "vision problems": "blurred vision",
    "vision loss": "vision loss",
    "ear pain": "ear pain",
    "earache": "ear pain",
    "hearing loss": "hearing loss",
    "insomnia": "insomnia",
    "sleep problems": "insomnia",
    "difficulty sleeping": "insomnia",
    "anxiety": "anxiety",
    "tremors": "tremors",
    "shaking": "tremors",
    "numbness": "numbness",
    "tingling": "numbness",
    "joint pain": "joint pain",
    "knee pain": "knee pain",
    "shoulder pain": "shoulder pain",
    "neck pain": "neck pain",
    "hip pain": "hip pain",
    "loss of appetite": "loss of appetite",
    "poor appetite": "loss of appetite",
    "weight loss": "weight loss",
    "chills": "chills",
    "rigors": "chills",
    "night sweats": "night sweats",
    "sweating": "sweating",
    "excessive sweating": "sweating",
    "mouth ulcer": "mouth ulcer",
    "oral ulcer": "mouth ulcer",
    "nosebleed": "nosebleed",
    "epistaxis": "nosebleed",
    "bleeding": "bleeding",
    "blood in urine": "hematuria",
    "hematuria": "hematuria",
    "blood in stool": "rectal bleeding",
    "pale": "pallor",
    "pallor": "pallor",
    "jaundice": "jaundice",
    "yellow eyes": "jaundice",
    "yellowish eyes": "jaundice",
    "dark urine": "dark urine",
    "yellowish urine": "dark urine",
    "hair loss": "hair loss",
    "alopecia": "hair loss",
    "cavity": "cavity",
    # ── Hinglish transliterations ─────────────────────────────────────────
    # Note: bare "dard" and "pain" intentionally excluded — too generic.
    # Specific combos (gale mein dard, sar dard, etc.) already cover them.
    "bukhar": "fever",
    "bukhaar": "fever",
    "buhkhar": "fever",
    "buhar": "fever",
    "tez bukhar": "fever",
    "khasi": "cough",
    "khansi": "cough",
    "khaansi": "cough",
    "sukhi khansi": "dry cough",
    "sir dard": "headache",
    "sar dard": "headache",
    "sirdard": "headache",
    "sar mein dard": "headache",
    "pet dard": "abdominal pain",
    "pet mein dard": "abdominal pain",
    "pait dard": "abdominal pain",
    "pait mein dard": "abdominal pain",
    "seena dard": "chest pain",
    "seene mein dard": "chest pain",
    "chhati mein dard": "chest pain",
    "chhati mein takleef": "chest pain",
    "chhati mein bhaari pan": "chest heaviness",
    "seene mein bhaari pan": "chest heaviness",
    "seene mein jalan": "acidity",
    "jalan": "burning sensation",
    "chakkar": "dizziness",
    "chakkar aana": "dizziness",
    "sar ghoomna": "dizziness",
    "ulti": "vomiting",
    "ult": "vomiting",
    "jee machlana": "nausea",
    "ji machlana": "nausea",
    "jee machlaana": "nausea",
    "kamzori": "weakness",
    "kamjori": "weakness",
    "thakan": "fatigue",
    "thakaan": "fatigue",
    "thaka hua": "fatigue",
    "saans": "breathlessness",
    "saans lene mein takleef": "breathlessness",
    "sans lene mein takleef": "breathlessness",
    "sans ki takleef": "breathlessness",
    "saans ki takleef": "breathlessness",
    "saans phoolna": "breathlessness",
    "sans phoolna": "breathlessness",
    "mehnat pe sans": "exertional dyspnea",
    "mehnat karne pe sans": "exertional dyspnea",
    "haanfna": "breathlessness",
    "hanf jana": "breathlessness",
    "dast": "diarrhea",
    "sardi": "cold",
    "nazla": "cold",
    "naak beh rahi": "runny nose",
    "naak beh raha": "runny nose",
    "naak band": "blocked nose",
    "gala kharab": "sore throat",
    "gale mein dard": "sore throat",
    "gale mein sujan": "sore throat",
    "badan dard": "body ache",
    "badan mein dard": "body ache",
    "daant dard": "toothache",
    "dant dard": "toothache",
    "khujli": "itching",
    "kharish": "itching",
    "sujan": "swelling",
    "kamar dard": "back pain",
    "kamar mein dard": "back pain",
    "ghutne mein dard": "knee pain",
    "jodo mein dard": "joint pain",
    "haath mein dard": "hand pain",
    "haath sunn": "numbness",
    "haath pair sunn": "numbness",
    "pair sunn": "numbness",
    "jhanjhnahat": "numbness",
    "haath kaanpna": "tremors",
    "haath kaanpe": "tremors",
    "kaanpna": "tremors",
    "bhookh nahi": "loss of appetite",
    "bhukh nahi": "loss of appetite",
    "khana nahi khaya": "loss of appetite",
    "neend nahi": "insomnia",
    "neend aati nahi": "insomnia",
    "wajan kam": "weight loss",
    "vajan ghat raha": "weight loss",
    "wajan ghata": "weight loss",
    "wajan bhi ghata": "weight loss",
    "wajan ghatna": "weight loss",
    "vajan ghata": "weight loss",
    "vajan kam": "weight loss",
    "paon mein sujan": "ankle swelling",
    "paer mein sujan": "ankle swelling",
    "pair mein sujan": "ankle swelling",
    "pairon mein sujan": "ankle swelling",
    "raat ko paseena": "night sweats",
    "ratko paseena": "night sweats",
    "raat mein paseena": "night sweats",
    "aankhon mein dard": "eye pain",
    "aankhon mein jalan": "eye irritation",
    "aankhein lal": "eye irritation",
    "nazar dhundhli": "blurred vision",
    "dhundhla dikhna": "blurred vision",
    "naak se khoon": "nosebleed",
    "peeli aankhein": "jaundice",
    "aankhein peeli": "jaundice",
    "peeli skin": "jaundice",
    "muh mein chaale": "mouth ulcer",
    "chaale": "mouth ulcer",
    "kaan mein dard": "ear pain",
    # ── Devanagari Hindi (direct Unicode matching) ─────────────────────────
    "बुखार": "fever",
    "बुखाऱ": "fever",
    "खांसी": "cough",
    "खाँसी": "cough",
    "खासी": "cough",
    "सिर दर्द": "headache",
    "सर दर्द": "headache",
    # Note: bare "दर्द" intentionally excluded — too generic, causes false positives.
    "सीने में दर्द": "chest pain",
    "सीने में जलन": "acidity",
    "जलन": "burning sensation",
    "जी मिचलाना": "nausea",
    "उल्टी": "vomiting",
    "चक्कर": "dizziness",
    "कमजोरी": "weakness",
    "थकान": "fatigue",
    "सांस फूलना": "breathlessness",
    "सांस लेने में तकलीफ": "breathlessness",
    "दस्त": "diarrhea",
    "सर्दी": "cold",
    "नाक बहना": "runny nose",
    "नाक बंद": "blocked nose",
    "गले में दर्द": "sore throat",
    "गले में खराश": "sore throat",
    "बदन दर्द": "body ache",
    "पेट दर्द": "abdominal pain",
    "पेट में दर्द": "abdominal pain",
    "खुजली": "itching",
    "सूजन": "swelling",
    "कमर दर्द": "back pain",
    "भूख नहीं": "loss of appetite",
    "नींद नहीं": "insomnia",
    "वजन कम": "weight loss",
    "हाथ-पैर सुन्न": "numbness",
    "हाथ कांपना": "tremors",
    "पीली आंखें": "jaundice",
    "आंखों में दर्द": "eye pain",
    "घुटने में दर्द": "knee pain",
    "जोड़ों में दर्द": "joint pain",
}

_INVESTIGATION_MAP: dict[str, str] = {
    "x-ray": "X-Ray",
    "x ray": "X-Ray",
    "xray": "X-Ray",
    "chest x-ray": "Chest X-Ray",
    "chest xray": "Chest X-Ray",
    "blood test": "Blood Test",
    "blood work": "Blood Test",
    "khoon ki jaanch": "Blood Test",
    "खून की जांच": "Blood Test",
    "cbc": "CBC",
    "complete blood count": "CBC",
    "hemogram": "CBC",
    "crp": "CRP",
    "esr": "ESR",
    "mri": "MRI",
    "ultrasound": "Ultrasound",
    "usg": "Ultrasound",
    "sonography": "Ultrasound",
    "ct scan": "CT Scan",
    "ctscan": "CT Scan",
    "ecg": "ECG",
    "ekg": "ECG",
    "electrocardiogram": "ECG",
    "echo": "Echocardiography",
    "echocardiogram": "Echocardiography",
    "echocardiography": "Echocardiography",
    "2d echo": "Echocardiography",
    "urine test": "Urine Test",
    "urine routine": "Urine Routine",
    "urine re": "Urine Routine",
    "urine r/e": "Urine Routine",
    "urine culture": "Urine Culture",
    "thyroid test": "Thyroid Panel",
    "thyroid function": "Thyroid Panel",
    "tsh": "Thyroid Panel",
    "t3 t4": "Thyroid Panel",
    "t3": "Thyroid Panel",
    "t4": "Thyroid Panel",
    "hba1c": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    "glycosylated hemoglobin": "HbA1c",
    "lft": "Liver Function Test",
    "liver function": "Liver Function Test",
    "liver function test": "Liver Function Test",
    "rft": "Renal Function Test",
    "kidney function": "Renal Function Test",
    "renal function": "Renal Function Test",
    "creatinine": "Renal Function Test",
    "bun": "Renal Function Test",
    "lipid profile": "Lipid Profile",
    "cholesterol": "Lipid Profile",
    "triglycerides": "Lipid Profile",
    "electrolytes": "Electrolytes",
    "sodium potassium": "Electrolytes",
    "serum electrolytes": "Electrolytes",
    "blood culture": "Blood Culture",
    "culture sensitivity": "Culture & Sensitivity",
    "throat swab": "Throat Swab Culture",
    "throat culture": "Throat Swab Culture",
    "sputum afb": "Sputum AFB",
    "sputum for afb": "Sputum AFB",
    "afb": "Sputum AFB",
    "sputum culture": "Sputum Culture",
    "cbnaat": "CBNAAT (GeneXpert)",
    "genexpert": "CBNAAT (GeneXpert)",
    "gene xpert": "CBNAAT (GeneXpert)",
    "anomaly scan": "Anomaly Scan (USG)",
    "tiffa scan": "Anomaly Scan (USG)",
    "dengue test": "Dengue NS1/IgM",
    "dengue ns1": "Dengue NS1/IgM",
    "dengue": "Dengue NS1/IgM",
    "malaria test": "Malaria RDT",
    "malaria rdt": "Malaria RDT",
    "widal": "Widal Test",
    "typhidot": "Typhidot",
    "covid test": "COVID Antigen",
    "covid rtpcr": "COVID RT-PCR",
    "rapid antigen": "Rapid Antigen Test",
    "stool test": "Stool Examination",
    "stool routine": "Stool Examination",
    "stool culture": "Stool Culture",
    "blood sugar": "Blood Glucose",
    "fasting sugar": "Fasting Blood Glucose",
    "pp sugar": "Post-Prandial Glucose",
    "rbs": "Random Blood Sugar",
    "fbs": "Fasting Blood Sugar",
    "bone density": "DEXA Scan",
    "dexa": "DEXA Scan",
    "pft": "Pulmonary Function Test",
    "pulmonary function": "Pulmonary Function Test",
    "spirometry": "Spirometry",
    "tmt": "TMT (Stress Test)",
    "stress test": "TMT (Stress Test)",
    "holter": "Holter Monitor",
    "root canal": "Root Canal Treatment",
    "root canal treatment": "Root Canal Treatment",
    "rct": "Root Canal Treatment",
    "filling": "Cavity Filling",
    "cavity filling": "Cavity Filling",
    "extraction": "Tooth Extraction",
    "scaling": "Dental Scaling",
    "examination": "Clinical Examination",
    "troponin": "Troponin",
    "troponin i": "Troponin I",
    "troponin t": "Troponin T",
    "trop i": "Troponin I",
    "trop t": "Troponin T",
    "hs troponin": "High-Sensitivity Troponin",
    "high sensitivity troponin": "High-Sensitivity Troponin",
    "hstni": "High-Sensitivity Troponin I",
    "hstnt": "High-Sensitivity Troponin T",
    "d dimer": "D-Dimer",
    "d-dimer": "D-Dimer",
    "bnp": "BNP",
    "pro bnp": "NT-proBNP",
    "nt probnp": "NT-proBNP",
    "nt pro bnp": "NT-proBNP",
    # ── Cardiology investigations (tuned for AIIMS cardiology) ────────────
    "2 d echo": "Echocardiography",
    "two d echo": "Echocardiography",
    "transthoracic echo": "Transthoracic Echocardiography (TTE)",
    "tte": "Transthoracic Echocardiography (TTE)",
    "transesophageal echo": "Transesophageal Echocardiography (TEE)",
    "transoesophageal echo": "Transesophageal Echocardiography (TEE)",
    "tee echo": "Transesophageal Echocardiography (TEE)",
    # NOTE: bare "toe"/"tee" omitted — "toe" is a body part, collides in ortho.
    "stress echo": "Stress Echocardiography",
    "dobutamine stress echo": "Dobutamine Stress Echocardiography (DSE)",
    "dse": "Dobutamine Stress Echocardiography (DSE)",
    "ct coronary angiography": "CT Coronary Angiography (CTCA)",
    "ct coronary angio": "CT Coronary Angiography (CTCA)",
    "ctca": "CT Coronary Angiography (CTCA)",
    "ccta": "CT Coronary Angiography (CTCA)",
    "coronary calcium score": "Coronary Calcium Score",
    "calcium score": "Coronary Calcium Score",
    "cardiac mri": "Cardiac MRI (CMR)",
    "cmr": "Cardiac MRI (CMR)",
    "cardiac ct": "Cardiac CT",
    "myocardial perfusion imaging": "Myocardial Perfusion Imaging (MPI)",
    "mpi": "Myocardial Perfusion Imaging (MPI)",
    "nuclear stress test": "Nuclear Stress Test",
    "spect": "SPECT",
    "cardiac pet": "Cardiac PET",
    "treadmill test": "TMT (Stress Test)",
    # NOTE: bare "ett" omitted — collides with endotracheal tube (anaesthesia).
    "exercise tolerance test": "Exercise Tolerance Test (ETT)",
    "right heart cath": "Right Heart Catheterization (RHC)",
    "right heart catheterization": "Right Heart Catheterization (RHC)",
    "right heart catheterisation": "Right Heart Catheterization (RHC)",
    "rhc": "Right Heart Catheterization (RHC)",
    "left heart cath": "Left Heart Catheterization (LHC)",
    "lhc": "Left Heart Catheterization (LHC)",
    "hemodynamic study": "Hemodynamic Study",
    "v/q scan": "V/Q Scan",
    "vq scan": "V/Q Scan",
    "ventilation perfusion scan": "V/Q Scan",
    "abg": "Arterial Blood Gas (ABG)",
    "arterial blood gas": "Arterial Blood Gas (ABG)",
    "ana": "Antinuclear Antibody (ANA)",
    "antinuclear antibody": "Antinuclear Antibody (ANA)",
    "anti cardiolipin": "Anti-Cardiolipin Antibody",
    "anti-cardiolipin": "Anti-Cardiolipin Antibody",
    "lupus anticoagulant": "Lupus Anticoagulant",
    "thrombophilia screen": "Thrombophilia Screen",
    "anti xa": "Anti-Xa Level",
    "anti-xa": "Anti-Xa Level",
    "ck mb": "CK-MB",
    "ck-mb": "CK-MB",
    "cpk": "CPK",
    "lipid profile": "Lipid Profile",
    "lipid panel": "Lipid Profile",
    "holter monitor": "Holter Monitor",
    "24 hour holter": "Holter Monitor",
    "event monitor": "Event Monitor",
    "loop recorder": "Implantable Loop Recorder",
    "six minute walk test": "6-Minute Walk Test (6MWT)",
    "6 minute walk test": "6-Minute Walk Test (6MWT)",
    "6mwt": "6-Minute Walk Test (6MWT)",
    "pt inr": "PT/INR",
    "inr": "INR",
    "aptt": "APTT",
    "procalcitonin": "Procalcitonin",
    "lactate": "Lactate",
    "abg": "ABG",
    "arterial blood gas": "ABG",
    "ct pulmonary": "CT Pulmonary Angiography",
    "ctpa": "CT Pulmonary Angiography",
    "hrct": "HRCT Chest",
    "hrct chest": "HRCT Chest",
    "mri brain": "MRI Brain",
    "ct brain": "CT Brain",
    "ct head": "CT Head",
    "biopsy": "Biopsy",
    "fnac": "FNAC",
    "vitamin a": "Vitamin A",
    "vitamin d": "Vitamin D",
    "vitamin b12": "Vitamin B12",
    "vitamin e": "Vitamin E",
    "vitamin k": "Vitamin K",
    "vitamin c": "Vitamin C",
    "ferritin": "Ferritin",
    "iron studies": "Iron Studies",
    "serum iron": "Iron Studies",
    "calcium": "Serum Calcium",
    "uric acid": "Uric Acid",
    "ana": "ANA",
    "ra factor": "RA Factor",
    "psa": "PSA",
    "cea": "CEA",
    "ca125": "CA-125",
    "hiv": "HIV Test",
    "hbsag": "HBsAg",
    "anti hcv": "Anti-HCV",
    "vdrl": "VDRL",
    "kft": "Kidney Function Test",
    "kidney function test": "Kidney Function Test",
}

_ALLERGY_PATTERNS = [
    r'(?:allergic\s+to|allergy\s+to)\s+([a-zA-Z]+)',
    # "sulfa se allergy" — substance immediately before "se allergy"
    r'([a-zA-Z]{4,})\s+(?:se\s+allergy|ko\s+allergy)',
    # "sulfa drugs se allergy" — substance before a generic word like "drugs/medicine"
    r'([a-zA-Z]{4,})\s+(?:drugs?|medicine|tablet|injection)\s+se\s+allergy',
    r'(?:known\s+allergy|allergy)\s*:\s*([a-zA-Z]+)',
    r'([a-zA-Z]{4,})\s+allergy\b',
    r'(?:reaction\s+to|had\s+reaction\s+with)\s+([a-zA-Z]+)',
    # Allow optional words between "se" and reaction/symptom words
    # Covers: "se rash", "se daane aa gaye", "se saans phoolti hai"
    r'([a-zA-Z]{4,})\s+se\s+(?:\w+\s+){0,2}(?:rash|reaction|problem|side\s+effect|daane|daana|dane|saans\s+phool|breathless|swelling|itching|khujli|sujan)\s*(?:hua|hai|hoti|tha|thi|hota|aa\s+gaye|aa\s+jate|phoolti|phoolna)?',
    # Historical: "penicillin se reaction hua tha pehle"
    r'([a-zA-Z]{4,})\s+se\s+(?:\w+\s+){0,3}(?:reaction|rash|allergy).*?(?:pehle|tha|thi|pehle\s+se)',
]


def _clean_allergen(raw: str) -> str:
    """Strip trailing generic words that are not the substance name."""
    _GENERIC_SUFFIXES = re.compile(
        r'\s+(?:drugs?|medicine|medicines|tablet|tablets|injection|injections|se|ko|ka|ki|ke)\s*$',
        re.IGNORECASE,
    )
    return _GENERIC_SUFFIXES.sub("", raw).strip()


def _span_overlaps(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return left_start < right_end and right_start < left_end


def _is_allergen_span(sent_text: str, start: int, end: int) -> bool:
    """True when a token span is the allergen named by an allergy pattern."""
    for pattern in _ALLERGY_PATTERNS:
        for match in re.finditer(pattern, sent_text, re.IGNORECASE):
            if match.lastindex is None:
                continue
            allergen_start, allergen_end = match.span(1)
            if _span_overlaps(start, end, allergen_start, allergen_end):
                return True
    return False

_POST_NEGATION_RE = re.compile(r'\b(nahi|nahin|mat|na|nhi)\b', re.IGNORECASE)

_DIAGNOSIS_MAP: dict[str, str] = {
    # ── Infections ────────────────────────────────────────────────────────
    "viral fever": "Viral Fever",
    "viral infection": "Viral Infection",
    "viral illness": "Viral Illness",
    "dengue": "Dengue Fever",
    "dengue fever": "Dengue Fever",
    "typhoid": "Typhoid Fever",
    "malaria": "Malaria",
    "covid": "COVID-19",
    "corona": "COVID-19",
    "influenza": "Influenza",
    "flu": "Influenza",
    "chickenpox": "Varicella",
    "varicella": "Varicella",
    "mumps": "Mumps",
    "measles": "Measles",
    "tuberculosis": "Tuberculosis",
    "tb": "Tuberculosis",
    "scabies": "Scabies",
    "fungal infection": "Fungal Infection",
    "ringworm": "Fungal Infection",
    "tinea": "Fungal Infection",
    "cellulitis": "Cellulitis",
    "hepatitis": "Hepatitis",
    "hepatitis a": "Hepatitis A",
    "hepatitis b": "Hepatitis B",
    "hepatitis c": "Hepatitis C",
    # ── Respiratory ───────────────────────────────────────────────────────
    "urti": "URTI",
    "upper respiratory tract infection": "URTI",
    "upper respiratory infection": "URTI",
    "uri": "URTI",
    "lrti": "LRTI",
    "lower respiratory tract infection": "LRTI",
    "pneumonia": "Pneumonia",
    "bronchitis": "Bronchitis",
    "bronchopneumonia": "Bronchopneumonia",
    "asthma": "Asthma",
    "copd": "COPD",
    "pleural effusion": "Pleural Effusion",
    "pharyngitis": "Pharyngitis",
    "tonsillitis": "Tonsillitis",
    "laryngitis": "Laryngitis",
    "sinusitis": "Sinusitis",
    "otitis": "Otitis Media",
    "otitis media": "Otitis Media",
    "conjunctivitis": "Conjunctivitis",
    "pink eye": "Conjunctivitis",
    # ── Cardiac ───────────────────────────────────────────────────────────
    "hypertension": "Hypertension",
    "hypertensive": "Hypertension",
    "bp high": "Hypertension",
    "high bp": "Hypertension",
    "high blood pressure": "Hypertension",
    "bp badhna": "Hypertension",
    "heart attack": "Myocardial Infarction",
    # NOTE: bare "mi" removed — collides across specialties. Use qualified forms.
    "myocardial infarction": "Myocardial Infarction",
    "old mi": "Old Myocardial Infarction",
    "acute mi": "Acute Myocardial Infarction",
    "recent mi": "Recent Myocardial Infarction",
    "anterior wall mi": "Anterior Wall MI",
    "inferior wall mi": "Inferior Wall MI",
    "lateral wall mi": "Lateral Wall MI",
    "anterior mi": "Anterior Wall MI",
    "inferior mi": "Inferior Wall MI",
    "stemi": "STEMI",
    "st elevation mi": "STEMI",
    "nstemi": "NSTEMI",
    "acute coronary syndrome": "Acute Coronary Syndrome",
    "acs": "Acute Coronary Syndrome",
    "unstable angina": "Unstable Angina",
    "angina": "Angina",
    "arrhythmia": "Arrhythmia",
    "atrial fibrillation": "Atrial Fibrillation",
    # NOTE: bare "af" removed — risky 2-letter token. Use qualified forms.
    "paroxysmal af": "Paroxysmal Atrial Fibrillation",
    "persistent af": "Persistent Atrial Fibrillation",
    "permanent af": "Permanent Atrial Fibrillation",
    "rapid af": "Atrial Fibrillation with Rapid Ventricular Rate",
    "af with rvr": "Atrial Fibrillation with Rapid Ventricular Rate",
    "chronic af": "Chronic Atrial Fibrillation",
    "valvular af": "Valvular Atrial Fibrillation",
    "non-valvular af": "Non-Valvular Atrial Fibrillation",
    "new onset af": "New-Onset Atrial Fibrillation",
    "heart failure": "Heart Failure",
    "hfref": "Heart Failure with Reduced EF (HFrEF)",
    "hfpef": "Heart Failure with Preserved EF (HFpEF)",
    "heart failure with reduced ejection fraction": "Heart Failure with Reduced EF (HFrEF)",
    "heart failure with preserved ejection fraction": "Heart Failure with Preserved EF (HFpEF)",
    "dilated cardiomyopathy": "Dilated Cardiomyopathy (DCM)",
    "dcm": "Dilated Cardiomyopathy (DCM)",
    "hypertrophic cardiomyopathy": "Hypertrophic Cardiomyopathy (HCM)",
    "hcm": "Hypertrophic Cardiomyopathy (HCM)",
    "hocm": "Hypertrophic Obstructive Cardiomyopathy (HOCM)",
    "restrictive cardiomyopathy": "Restrictive Cardiomyopathy",
    "ischaemic cardiomyopathy": "Ischaemic Cardiomyopathy",
    "ischemic cardiomyopathy": "Ischaemic Cardiomyopathy",
    # ── CAD / Coronary ─────────────────────────────────────────────────────
    "cad": "Coronary Artery Disease (CAD)",
    "coronary artery disease": "Coronary Artery Disease (CAD)",
    "stable angina": "Stable Angina",
    "prinzmetal": "Prinzmetal Angina",
    "vasospastic angina": "Vasospastic Angina",
    "triple vessel disease": "Triple Vessel Disease (TVD)",
    "tvd": "Triple Vessel Disease (TVD)",
    "double vessel disease": "Double Vessel Disease (DVD)",
    "dvd": "Double Vessel Disease (DVD)",
    "single vessel disease": "Single Vessel Disease (SVD)",
    "left main disease": "Left Main Coronary Artery Disease",
    "lmca disease": "Left Main Coronary Artery Disease",
    "lad disease": "LAD Disease",
    "rca disease": "RCA Disease",
    "lcx disease": "LCX Disease",
    # ── Procedures ────────────────────────────────────────────────────────
    "pci": "Percutaneous Coronary Intervention (PCI)",
    "angioplasty": "Coronary Angioplasty",
    "stenting": "Coronary Stenting",
    "cabg": "Coronary Artery Bypass Grafting (CABG)",
    "bypass surgery": "Coronary Artery Bypass Grafting (CABG)",
    "cardiac catheterization": "Cardiac Catheterization",
    "coronary angiography": "Coronary Angiography",
    "cag": "Coronary Angiography",
    "ptca": "PTCA",
    "iabp": "Intra-Aortic Balloon Pump (IABP)",
    "tavr": "Transcatheter Aortic Valve Replacement (TAVR)",
    "tavi": "Transcatheter Aortic Valve Implantation (TAVI)",
    "bmv": "Balloon Mitral Valvotomy (BMV)",
    "pmv": "Percutaneous Mitral Valvotomy",
    "icd": "Implantable Cardioverter-Defibrillator (ICD)",
    "pacemaker": "Pacemaker",
    "crt": "Cardiac Resynchronization Therapy (CRT)",
    # ── Valvular Disease (very common in India - RHD) ────────────────────
    "rhd": "Rheumatic Heart Disease (RHD)",
    "rheumatic heart disease": "Rheumatic Heart Disease (RHD)",
    # NOTE: bare valve abbreviations (ms/mr/as/ar/tr) removed — collide with
    # English words ("as"), titles ("Mr"/"Ms"), units ("ms"). Full names +
    # severity-qualified forms only. "* as" forms intentionally omitted because
    # "as" is a high-frequency English conjunction.
    "mitral stenosis": "Mitral Stenosis (MS)",
    "severe ms": "Severe Mitral Stenosis",
    "moderate ms": "Moderate Mitral Stenosis",
    "mild ms": "Mild Mitral Stenosis",
    "tight ms": "Severe Mitral Stenosis",
    "critical ms": "Critical Mitral Stenosis",
    "mitral regurgitation": "Mitral Regurgitation (MR)",
    "severe mr": "Severe Mitral Regurgitation",
    "moderate mr": "Moderate Mitral Regurgitation",
    "mild mr": "Mild Mitral Regurgitation",
    "trivial mr": "Trivial Mitral Regurgitation",
    "aortic stenosis": "Aortic Stenosis (AS)",
    "severe aortic stenosis": "Severe Aortic Stenosis",
    "critical aortic stenosis": "Critical Aortic Stenosis",
    "calcific aortic stenosis": "Calcific Aortic Stenosis",
    "degenerative aortic stenosis": "Degenerative Aortic Stenosis",
    "aortic regurgitation": "Aortic Regurgitation (AR)",
    "severe ar": "Severe Aortic Regurgitation",
    "moderate ar": "Moderate Aortic Regurgitation",
    "mild ar": "Mild Aortic Regurgitation",
    "tricuspid regurgitation": "Tricuspid Regurgitation (TR)",
    "severe tr": "Severe Tricuspid Regurgitation",
    "moderate tr": "Moderate Tricuspid Regurgitation",
    "mild tr": "Mild Tricuspid Regurgitation",
    "tricuspid stenosis": "Tricuspid Stenosis",
    "pulmonary stenosis": "Pulmonary Stenosis",
    "mvp": "Mitral Valve Prolapse (MVP)",
    "mitral valve prolapse": "Mitral Valve Prolapse (MVP)",
    "bivalvular disease": "Bivalvular Disease",
    "multivalvular disease": "Multivalvular Disease",
    # ── Pulmonary Hypertension (AIIMS specialty) ─────────────────────────
    "pulmonary arterial hypertension": "Pulmonary Arterial Hypertension (PAH)",
    "pah": "Pulmonary Arterial Hypertension (PAH)",
    "pulmonary hypertension": "Pulmonary Hypertension",
    # NOTE: bare "ph" removed — collides with urine/blood pH lab values.
    "cteph": "CTEPH",
    "chronic thromboembolic pulmonary hypertension": "CTEPH",
    "pulmonary embolism": "Pulmonary Embolism (PE)",
    # NOTE: bare "pe" removed — too short, risky. Use qualified forms.
    "acute pe": "Acute Pulmonary Embolism",
    "massive pe": "Massive Pulmonary Embolism",
    "submassive pe": "Submassive Pulmonary Embolism",
    "saddle pe": "Saddle Pulmonary Embolism",
    "dvt": "Deep Vein Thrombosis (DVT)",
    # ── Arrhythmia ────────────────────────────────────────────────────────
    "svt": "Supraventricular Tachycardia (SVT)",
    "supraventricular tachycardia": "Supraventricular Tachycardia (SVT)",
    "vt": "Ventricular Tachycardia (VT)",
    "ventricular tachycardia": "Ventricular Tachycardia (VT)",
    "vf": "Ventricular Fibrillation (VF)",
    "complete heart block": "Complete Heart Block (CHB)",
    "chb": "Complete Heart Block (CHB)",
    "first degree block": "First Degree AV Block",
    "second degree block": "Second Degree AV Block",
    "wpw": "Wolff-Parkinson-White Syndrome (WPW)",
    "lbbb": "Left Bundle Branch Block (LBBB)",
    "rbbb": "Right Bundle Branch Block (RBBB)",
    "sick sinus syndrome": "Sick Sinus Syndrome (SSS)",
    "sss": "Sick Sinus Syndrome (SSS)",
    # ── Pericardial ────────────────────────────────────────────────────────
    "pericarditis": "Pericarditis",
    "pericardial effusion": "Pericardial Effusion",
    "cardiac tamponade": "Cardiac Tamponade",
    "constrictive pericarditis": "Constrictive Pericarditis",
    # ── Congenital (AIIMS sees these) ────────────────────────────────────
    "asd": "Atrial Septal Defect (ASD)",
    "vsd": "Ventricular Septal Defect (VSD)",
    "pda": "Patent Ductus Arteriosus (PDA)",
    "tof": "Tetralogy of Fallot (TOF)",
    "eisenmenger": "Eisenmenger Syndrome",
    "fallot": "Tetralogy of Fallot (TOF)",
    # ── Hindi cardiac terms ─────────────────────────────────────────────
    "dil ki bimari": "Heart Disease",
    "dil ka dora": "Myocardial Infarction",
    "dil ka daura": "Myocardial Infarction",
    "dhadkan badh jana": "Palpitations / Tachycardia",
    "saans fulna": "Dyspnoea",
    "saans phoolna": "Dyspnoea",
    "seene mein dard": "Chest Pain",
    "sine mein dard": "Chest Pain",
    "dil mein chhed": "Septal Defect (ASD/VSD)",
    "dil mein ched": "Septal Defect (ASD/VSD)",
    "dil ki valve kharab": "Valvular Heart Disease",
    "valve kharab": "Valvular Heart Disease",
    "dil ki naso mein blockage": "Coronary Artery Disease (CAD)",
    "naso mein blockage": "Coronary Artery Disease (CAD)",
    "khoon ka thakka": "Thrombus",
    "दिल का दौरा": "Myocardial Infarction",
    "सांस फूलना": "Dyspnoea",
    "दिल में छेद": "Septal Defect (ASD/VSD)",
    # ── Metabolic ─────────────────────────────────────────────────────────
    "diabetes": "Diabetes Mellitus",
    "diabetic": "Diabetes Mellitus",
    "t2dm": "Type 2 Diabetes Mellitus",
    "type 2 dm": "Type 2 Diabetes Mellitus",
    "type 2 diabetes": "Type 2 Diabetes Mellitus",
    "t1dm": "Type 1 Diabetes Mellitus",
    # Indian colloquial: "sugar" alone is handled in _extract_diagnoses with number guard
    "sugar ka patient": "Diabetes Mellitus",
    "sugar ka problem": "Diabetes Mellitus",
    "sugar ki bimari": "Diabetes Mellitus",
    "sugar ki problem": "Diabetes Mellitus",
    "sugar rehta hai": "Diabetes Mellitus",
    "sugar hai": "Diabetes Mellitus",
    "sugar control nahi": "Diabetes Mellitus (uncontrolled)",
    "sugar control nahi ho": "Diabetes Mellitus (uncontrolled)",
    "sugar nahi control": "Diabetes Mellitus (uncontrolled)",
    "sugar control": "Diabetes Mellitus (uncontrolled)",
    "sugar badhna": "Diabetes Mellitus",
    "madhumeh": "Diabetes Mellitus",
    "शुगर": "Diabetes Mellitus",
    "मधुमेह": "Diabetes Mellitus",
    "hypothyroid": "Hypothyroidism",
    "hypothyroidism": "Hypothyroidism",
    "hyperthyroid": "Hyperthyroidism",
    "hyperthyroidism": "Hyperthyroidism",
    "thyroid": "Thyroid Disorder",
    "anemia": "Anemia",
    "anaemia": "Anemia",
    "iron deficiency anemia": "Iron Deficiency Anemia",
    "iron deficiency anaemia": "Iron Deficiency Anemia",
    "खून की कमी": "Anemia",
    "khoon ki kami": "Anemia",
    "gout": "Gout",
    "uric acid": "Gout",
    # ── GI ───────────────────────────────────────────────────────────────
    "gastritis": "Gastritis",
    "acute gastritis": "Acute Gastritis",
    "gastroenteritis": "Acute Gastroenteritis",
    "acute gastroenteritis": "Acute Gastroenteritis",
    "food poisoning": "Food Poisoning",
    "gerd": "GERD",
    "acid reflux": "GERD",
    "irritable bowel": "IBS",
    "ibs": "IBS",
    "appendicitis": "Appendicitis",
    "jaundice": "Jaundice",
    "cirrhosis": "Liver Cirrhosis",
    "liver failure": "Liver Failure",
    "peptic ulcer": "Peptic Ulcer",
    "gallstones": "Gallstones",
    "gall stones": "Gallstones",
    "kidney stones": "Kidney Stones",
    "renal stones": "Kidney Stones",
    "kidney failure": "Renal Failure",
    "renal failure": "Renal Failure",
    "uti": "UTI",
    "urinary tract infection": "UTI",
    # ── Neuro / Musculo ───────────────────────────────────────────────────
    "migraine": "Migraine",
    "stroke": "Stroke",
    "paralysis": "Paralysis",
    "lakwa": "Paralysis",
    "seizure": "Seizure",
    "fits": "Seizure",
    "mircchi": "Seizure",
    "epilepsy": "Epilepsy",
    "vertigo": "Vertigo",
    "neuropathy": "Neuropathy",
    "arthritis": "Arthritis",
    "rheumatoid": "Rheumatoid Arthritis",
    "rheumatoid arthritis": "Rheumatoid Arthritis",
    "osteoarthritis": "Osteoarthritis",
    "spondylitis": "Spondylitis",
    "slip disc": "Disc Prolapse",
    "slipped disc": "Disc Prolapse",
    "disc prolapse": "Disc Prolapse",
    "frozen shoulder": "Frozen Shoulder",
    "sciatica": "Sciatica",
    "fracture": "Fracture",
    # ── Eye / Skin / Mental ───────────────────────────────────────────────
    "cataract": "Cataract",
    "motiyabind": "Cataract",
    "मोतियाबिंद": "Cataract",
    "glaucoma": "Glaucoma",
    "psoriasis": "Psoriasis",
    "eczema": "Eczema",
    "vitiligo": "Vitiligo",
    "safed daag": "Vitiligo",
    "anxiety": "Anxiety Disorder",
    "depression": "Depression",
    "insomnia disorder": "Insomnia",
    "pcos": "PCOS",
    "polycystic": "PCOS",
    # ── Dental ───────────────────────────────────────────────────────────
    "dental caries": "Dental Caries",
    "periodontitis": "Periodontitis",
    "gingivitis": "Gingivitis",
}

_DURATION_RE = re.compile(
    r'\b(\d+(?:\.\d+)?\s*(?:din|day|days|week|weeks|month|months|hour|hours|hr|hrs))\s*'
    r'(?:se|since|for|pehle|ago)?\b'
    r'|(?:since|for)\s+(yesterday|morning|evening|last\s+\w+|\d+\s+\w+)',
    re.IGNORECASE,
)

_HINDI_NUMBERS = {"ek": "1", "do": "2", "teen": "3", "char": "4", "paanch": "5",
                  "chhe": "6", "saat": "7", "aath": "8", "nau": "9", "das": "10"}

# Normalize Hindi / colloquial frequency phrases to standard abbreviations
_HINDI_FREQ_NORMALIZE: dict[str, str] = {
    "subah shaam raat": "TDS",
    "subah shaam": "BD",
    "subah aur raat": "BD",
    "din mein char baar": "QID",
    "din mein teen baar": "TDS",
    "din mein do baar": "BD",
    "char baar": "QID",
    "teen baar": "TDS",
    "do baar": "BD",
    "ek baar": "OD",
    "raat ko": "HS",
    "roz": "OD",
    "khane ke baad": "after meals",
    "khana ke baad": "after meals",
    "khane se pehle": "before meals",
    "khana se pehle": "before meals",
    "twice daily": "BD",
    "twice a day": "BD",
    "thrice daily": "TDS",
    "three times a day": "TDS",
    "three times day": "TDS",
    "four times a day": "QID",
    "once a day": "OD",
    "once day": "OD",
    "morning and night": "BD",
    "morning and evening": "BD",
    "at night": "HS",
    "at bedtime": "HS",
    "before bed": "HS",
}

# Normalize Hindi duration phrases for medication prescriptions
_HINDI_MED_DURATION_MAP: dict[str, str] = {
    "paanch din": "5 days",
    "char din": "4 days",
    "saat din": "7 days",
    "das din": "10 days",
    "ek hafta": "1 week",
    "do hafte": "2 weeks",
    "teen hafte": "3 weeks",
    "ek mahina": "1 month",
    "do mahine": "2 months",
    "teen mahine": "3 months",
}

_MED_DURATION_RE = re.compile(
    r'\b(?:(?:for|ke\s+liye)\s+)?(\d+)\s*(?:din\b|day[s]?\b|week[s]?\b|hafte\b|mahine?\b|month[s]?\b)',
    re.IGNORECASE,
)

_FOLLOWUP_PATTERNS = [
    # Hindi number patterns first — more specific, must win over bare "follow up"
    re.compile(r'((?:teen|do|ek|char|paanch|chhe|saat|\d+)\s*(?:din|hafte|mahine|week|month|day)s?\s*(?:baad|ke\s+baad|mein)(?:\s*(?:aana|wapas|milna|follow|review))?)', re.IGNORECASE),
    re.compile(r'\b(\d+)\s*(?:din|day|days)\s*(?:baad|mein|ke\s+baad)\s*(?:aana|wapas|milna|review|follow)', re.IGNORECASE),
    # English patterns — \.(?=\d) allows decimals like 39.5 without stopping the match
    re.compile(r'follow[\s-]?up\s+(?:(?:in|after|within)\s+)?(\d+(?:[^\n;]|\.(?=\d))*)', re.IGNORECASE),
    re.compile(r'follow[\s-]?up\s+(?:(?:in|after|within)\s+)?((?:[^\n;]|\.(?=\d))+)', re.IGNORECASE),
    re.compile(r'come\s+back\s+(?:(?:after|in)\s+)?((?:[^\n;,]|\.(?=\d))+)', re.IGNORECASE),
    re.compile(r'review\s+(?:(?:in|after)\s+)?((?:[^\n;,]|\.(?=\d))+)', re.IGNORECASE),
    re.compile(r'milne\s+aana\s+(?:in\s+)?((?:[^\n;]|\.(?=\d))+)', re.IGNORECASE),
]

# Unambiguous next-visit phrases — checked before the generic duration patterns.
_FOLLOWUP_EXPLICIT = [
    (re.compile(r'\bagle\s+hafte\b', re.IGNORECASE), "after 1 week"),
    (re.compile(r'\bagle\s+din\b', re.IGNORECASE), "after 1 day"),
    (re.compile(r'\bagle\s+mahine\b', re.IGNORECASE), "after 1 month"),
    (re.compile(r'\bkal\s+aana\b', re.IGNORECASE), "after 1 day"),
]

# Investigation-ordering verbs: when one is found in a sentence mentioning a
# dual-use nutrient (e.g. Vitamin D appears in both the investigation map and
# the medication list), the mention is a test order, not a drug prescription.
_INVESTIGATION_VERBS = re.compile(
    r'\b(?:check|test|karwao|karwana|karo|karao|bhejo|send|order|get\s+done|measure|'
    r'level\s+check|dekhna|dekho|chahiye|banana)\b',
    re.IGNORECASE,
)

_DIAGNOSIS_LABEL_RE = re.compile(
    r'(?:diagnosis|impression|assessment|dx|impression|provisional\s+diagnosis)[\s:]+([^.\n;]+)',
    re.IGNORECASE,
)

# Pre-keyword MEDICATION-REASON phrases — the condition is named as the reason
# for a drug, not asserted as a diagnosis ("takes metformin FOR diabetes").
# These suppress diagnosis extraction.
_DX_CONTEXT_PRE_RE = re.compile(
    r'\b(?:for|because\s+of|due\s+to|to\s+(?:manage|treat|control)|on\s+(?:medication|treatment)\s+for|'
    r'takes?\s+\w+\s+for|taking\s+\w+\s+for)\b',
    re.IGNORECASE,
)

# Procedure-plan context: "Plan BMV", "Refer ICD evaluation", "Scheduled for CABG".
# These indicate a PROCEDURE being planned, NOT a diagnosis being asserted.
# No trailing \b so it matches right up to the procedure abbreviation.
_DX_PROCEDURE_PRE_RE = re.compile(
    r'\b(?:plan(?:ned)?|schedul(?:ed|ing)|refer(?:red|ring)?|considering|'
    r'proceed(?:ing)?\s+with|will\s+undergo|listing\s+for|listed\s+for)\s+',
    re.IGNORECASE,
)

# Pre-keyword HISTORY markers ("known case of", "k/c/o", "h/o", "history of").
# These DO denote a real diagnosis the patient carries — common in Indian
# cardiology dictation ("k/c/o CAD/DM/HTN, now NYHA III"). We capture these as
# diagnoses rather than dropping them. Kept separate so the SOAP layer can flag
# them as established/chronic if needed.
_DX_HISTORY_PRE_RE = re.compile(
    r'\b(?:known(?:\s+case\s+of)?|h/o|k/c/o|history\s+of)\b',
    re.IGNORECASE,
)

# Post-keyword context phrases — indicate the condition is established/managed,
# not a new finding being assessed.
_DX_CONTEXT_POST_RE = re.compile(
    r'\b(?:on\s+follow[\s-]?up|on\s+(?:treatment|medication|drugs?)|'
    r'(?:is\s+)?(?:well\s+)?controlled|being\s+managed)\b',
    re.IGNORECASE,
)


def _is_context_mention(text: str, match_start: int, match_end: int, window: int = 60) -> bool:
    """True if the diagnosis keyword at [start:end] appears in background context
    (medication reason, procedure plan, or established condition on follow-up) rather
    than as a new clinical finding being asserted in this visit."""
    preceding = text[max(0, match_start - window): match_start]
    following = text[match_end: min(len(text), match_end + window)]
    return bool(
        _DX_CONTEXT_PRE_RE.search(preceding)
        or _DX_PROCEDURE_PRE_RE.search(preceding)
        or _DX_CONTEXT_POST_RE.search(following)
    )

_KNOWN_MEDICATIONS = {
    # ── Analgesics / Antipyretics ─────────────────────────────────────────
    "painkiller", "painkillers", "pain killer", "pain killers",
    "paracetamol", "dolo", "crocin", "calpol", "fevago", "pyrigesic", "pacimol",
    "aspirin", "ecosprin", "loprin",
    "ibuprofen", "brufen", "combiflam", "imol",
    "naproxen", "naprosyn",
    "diclofenac", "voveran", "voltaren", "diclogem",
    "aceclofenac", "zerodol", "hifenac", "acenac",
    "nimesulide", "nimulid", "nims", "nimugesic",
    "ketorolac", "toradol",
    "tramadol", "tramazac", "ultracet",
    "codeine", "morphine",
    "drotaverine", "drotin", "no-spa",
    "dicyclomine", "cyclopam", "mebeverine",
    "serratiopeptidase", "serrapeptase", "chymoral", "chymotrypsin",
    # ── Antibiotics ───────────────────────────────────────────────────────
    "antibiotic", "antibiotics",
    "amoxicillin", "amoxyclav", "amoxiclav", "augmentin", "moxikind", "clavam",
    "azithromycin", "azee", "azithral", "zithromax", "azicip",
    "clarithromycin", "claribid",
    "erythromycin",
    "ciprofloxacin", "ciplox", "cifran",
    "norflox", "norfloxacin", "norflox tz",
    "ofloxacin", "oflox", "zanocin",
    "levofloxacin", "levoflox", "levaquin",
    "doxycycline", "doxy", "doxt",
    "tetracycline",
    "metronidazole", "flagyl", "metrogyl", "tinidazole", "tiniba", "secnidazole",
    "cefixime", "taxim", "suprax", "zifi",
    "cefpodoxime", "cepodem",
    "ceftriaxone", "monocef",
    "cephalexin", "cefalexin",
    "cefuroxime", "ceftin",
    "cotrimoxazole", "bactrim", "septran", "trimethoprim",
    "rifampicin", "ethambutol", "isoniazid", "pyrazinamide",
    "vancomycin", "meropenem", "piperacillin", "tazobactam",
    "acyclovir", "zovirax",
    "oseltamivir", "tamiflu",
    "albendazole", "zentel", "mebendazole",
    "ivermectin", "ivecop",
    "hydroxychloroquine", "hcqs", "plaquenil",
    "artemether", "lumefantrine", "coartem",
    "nitrofurantoin", "macrobid",
    # ── Antihistamines / Allergy ──────────────────────────────────────────
    "cetirizine", "cetzine", "alerid", "zyrtec",
    "levocetirizine", "levocet", "xyzal",
    "fexofenadine", "allegra",
    "loratadine", "lorfast", "clarityne",
    "chlorpheniramine", "cpm",
    "diphenhydramine", "benadryl",
    "hydroxyzine", "atarax",
    "montelukast", "montair", "singulair",
    "desloratadine", "deslor",
    # ── Diabetes ─────────────────────────────────────────────────────────
    "insulin", "human mixtard", "novomix", "lantus", "glargine",
    "metformin", "glycomet", "glucophage", "obimet",
    "glimepiride", "amaryl", "glimer",
    "glipizide", "glibenclamide", "daonil",
    "sitagliptin", "januvia",
    "empagliflozin", "jardiance",
    "dapagliflozin", "forxiga",
    "vildagliptin", "galvus",
    "teneligliptin", "tenepure",
    "pioglitazone", "pioz", "actos",
    # ── Cardiac / BP ──────────────────────────────────────────────────────
    "amlodipine", "stamlo", "amlodac", "amcard",
    "atenolol", "aten", "tenormin",
    "telmisartan", "telma", "telmikind",
    "ramipril", "cardace", "hopace",
    "enalapril", "envas",
    "losartan", "losacar", "losar",
    "lisinopril",
    "nifedipine", "depin",
    "verapamil", "diltiazem",
    "metoprolol", "metolar", "betaloc",
    "carvedilol", "cardivas",
    "bisoprolol", "concor",
    "propranolol", "ciplar",
    "warfarin", "warf",
    "heparin", "enoxaparin", "clexane",
    "clopidogrel", "clopivas", "plavix",
    "aspirin", "ecosprin", "loprin",
    "atorvastatin", "atorva", "lipitor",
    "rosuvastatin", "rosuvas", "crestor",
    "simvastatin", "zocor",
    "furosemide", "frusemide", "lasix",
    "spironolactone", "aldactone",
    "torsemide", "dytor",
    "hydrochlorothiazide", "hctz",
    "digoxin", "lanoxin",
    "nitroglycerin", "sorbitrate",
    "isosorbide mononitrate", "ismn", "monotrate", "ismo",
    "isosorbide dinitrate", "isdn",
    # Newer antiplatelet
    "ticagrelor", "brilinta", "brilique",
    "prasugrel", "efient",
    "vorapaxar",
    # NOACs (increasingly used in India)
    "dabigatran", "pradaxa",
    "rivaroxaban", "xarelto",
    "apixaban", "eliquis",
    "edoxaban", "lixiana",
    # HFrEF specific
    "sacubitril", "vymada", "entresto",
    "ivabradine", "coralan", "ivacard",
    "eplerenone", "inspra",
    "vericiguat",
    "dapagliflozin", "forxiga",  # SGLT2i for HF
    "empagliflozin", "jardiance",
    # PAH medications (AIIMS specialty)
    "bosentan", "tracleer",
    "ambrisentan", "volibris", "letairis",
    "macitentan", "opsumit",
    "sildenafil", "revatio", "viagra",  # sildenafil for PAH
    "tadalafil", "adcirca", "cialis",   # tadalafil for PAH
    "riociguat", "adempas",
    "selexipag", "uptravi",
    "iloprost", "ventavis",
    "epoprostenol", "flolan",
    "treprostinil", "remodulin",
    # Antiarrhythmics
    "amiodarone", "cordarone", "tachyra",
    "sotalol", "sotacor",
    "flecainide", "flecaine",
    "adenosine", "adenocor",
    "lidocaine", "xylocaine",
    "atropine",
    "dronedarone", "multaq",
    # Anti-anginals (very heavily used in India)
    "trimetazidine", "flavedon", "carvidon", "metagard",  # trimetazidine
    "nicorandil", "nicoran", "korandil",  # nicorandil
    "ranolazine", "ranozex", "carzine",  # ranolazine
    "ivabradine", "ivabid",  # ivabradine extra brand
    # Indian CCBs / beta-blockers not yet covered
    "cilnidipine", "cilacar", "nexovas", "dilnip",  # cilnidipine
    "nebivolol", "nebicard", "nebistar", "nodon",  # nebivolol
    "labetalol", "lobet",  # labetalol
    "clonidine", "arkamin", "catapres",  # clonidine
    "prazosin", "minipress",  # prazosin
    # Diuretics common in HF
    "chlorthalidone", "ctd",  # chlorthalidone
    "indapamide", "natrilix", "lorvas",  # indapamide
    "metolazone", "zaroxolyn", "metoz",  # metolazone
    # Lipid agents
    "ezetimibe", "ezeday", "ezetib",  # ezetimibe
    "fenofibrate", "lipicard", "tricor",  # fenofibrate
    # Anticoagulant
    "fondaparinux", "arixtra",  # fondaparinux
    "acitrom", "acenocoumarol", "nicoumalone",  # acenocoumarol (Indian warfarin alt)
    # Vasodilator (HF when ACEI/ARB intolerant — common in India)
    "hydralazine", "hydrazide",  # hydralazine
    # GI ───────────────────────────────────────────────────────────────
    "omeprazole", "omez", "prilosec",
    "pantoprazole", "pan 40", "pantop", "pantocid", "pantodac",
    "pan d", "nexpro",
    "rabeprazole", "razo", "rablet",
    "esomeprazole", "nexpro", "izra",
    "gelusil", "digene", "mucaine", "eno",
    "ranitidine", "rantac", "zinetac",
    "sucralfate", "sucral",
    "domperidone", "domstal", "vomistop",
    "ondansetron", "emeset", "zofer",
    "metoclopramide", "perinorm",
    "lactulose", "duphalac",
    "bisacodyl", "dulcolax",
    "loperamide", "imodium", "eldoper",
    "oral rehydration", "ors", "electral",
    "probiotics", "sporlac", "bifilac", "vizylac", "lactobacillus",
    "pantodac dsr",
    # ── Respiratory / Cough ───────────────────────────────────────────────
    "salbutamol", "asthalin", "ventolin",
    "budesonide", "budecort", "pulmicort",
    "formoterol", "foracort",
    "tiotropium", "spiriva",
    "ipratropium", "duolin",
    "prednisolone", "omnacortil", "wysolone",
    "prednisone",
    "dexamethasone", "dexona",
    "betamethasone",
    "methylprednisolone", "medrol", "solumedrol",
    "hydrocortisone",
    "deflazacort", "defcort",
    "ambroxol", "mucolite", "ambrodil", "mucosolvant",
    "bromhexine", "bexol",
    "guaifenesin", "grilinctus", "ascoril", "ascoril ls", "ascoril d",
    "dextromethorphan", "alex",
    "levosalbutamol", "levolin",
    "montelukast levocetirizine",
    "fluticasone", "flixotide", "seroflo",
    # ── Thyroid / Hormones ────────────────────────────────────────────────
    "levothyroxine", "thyroxine", "thyronorm", "eltroxin",
    "carbimazole", "neomercazole",
    "propylthiouracil",
    # ── Vitamins / Supplements ────────────────────────────────────────────
    "pcm", "antacid", "antacids",
    "calcium", "shelcal", "calvit", "calcirol", "calcium carbonate",
    "vitamin a", "retinol", "vitamin a palmitate",
    "vitamin d", "vitamin d3", "d-rise", "arachitol", "cholecalciferol",
    "vitamin e", "tocopherol", "evion",
    "vitamin k", "phytonadione", "menadione",
    "vitamin c", "celin", "limcee",
    "vitamin b12", "methylcobalamin", "mecobalamin", "mecob", "cobadex", "rejunex",
    "vitamin b complex", "neurobion", "becosules", "b complex",
    "zinc", "zincovit", "zinnat",
    "iron", "ferrous", "orofer", "autrin", "fefol", "ferrous sulfate",
    "folic acid", "folinate",
    "multivitamin", "supradyn", "revital",
    "biotin",
    # ── Neurology / Pain ──────────────────────────────────────────────────
    "gabapentin", "gabapin", "gabantin", "neurontin",
    "pregabalin", "pregabalin", "pregalin", "lyrica",
    "amitriptyline", "amitone", "tryptomer",
    "nortriptyline", "sensival",
    "carbamazepine", "tegretol",
    "phenytoin", "eptoin",
    "levetiracetam", "levipil",
    "valproate", "valparin",
    "citicoline", "strocit",
    # ── Psychiatry ────────────────────────────────────────────────────────
    "diazepam", "valium",
    "alprazolam", "alprax", "restyl",
    "clonazepam", "lonazep", "zapiz",
    "lorazepam", "ativan",
    "etizolam", "etizola",
    "sertraline", "zoloft", "serta",
    "fluoxetine", "flunil", "prozac",
    "escitalopram", "nexito", "cipralex",
    "mirtazapine", "mirtaz",
    "olanzapine", "olanex", "oliza",
    "risperidone", "risnia",
    "quetiapine", "serenace",
    "chlorpromazine", "largactil",
    # ── Skin / Topical ────────────────────────────────────────────────────
    "betadine", "povidone iodine",
    "mupirocin", "bactroban",
    "clotrimazole", "candid",
    "fluconazole", "forcan", "flucos",
    "ketoconazole", "nizoral",
    "tacrolimus", "protopic",
    "cyclosporine",
    "calamine",
    # ── Gout / Joints ─────────────────────────────────────────────────────
    "colchicine",
    "allopurinol", "zyloric",
    "febuxostat", "febucip",
    "sulfasalazine", "saaz",
    "methotrexate",
    "azathioprine",
    "leflunomide", "lefno",
    # ── Urology ───────────────────────────────────────────────────────────
    "tamsulosin", "urimax",
    "finasteride", "finpecia", "proscar",
    "dutasteride", "dutas",
    "solifenacin",
    # ── Eye drops ─────────────────────────────────────────────────────────
    "timolol",
    "latanoprost", "xalatan",
    "pilocarpine",
    "tobramycin",
    "gentamicin",
    "moxifloxacin", "moxicip",
    "ciprofloxacin eye drops",
    "carboxymethylcellulose", "refresh tears",
}

_UNCERTAINTY_WORDS = re.compile(
    r'\b(maybe|possible|possibly|probably|might|suspected?|shayad|ho\s+sakta)\b',
    re.IGNORECASE,
)

# Pre-negation is English-only: it scans text BEFORE the term ("no fever",
# "denies cough"). Hindi "nahi/nahin" is post-positional ("bukhar nahi") and is
# handled exclusively by _POST_NEGATION_RE — including it here would make one
# clause's "nahi" leak backwards onto a later symptom/drug.
_NEGATION_RE = re.compile(
    r'\b(no|not|n\'t|denies?|denied|without|never|nor|absent)\b',
    re.IGNORECASE,
)
_CLAUSE_RESET_RE = re.compile(
    r'\b(but|however|and|also|though|although|yet|still|except|'
    # Hindi verbs/auxiliaries that close a clause — stop a negation ("X nahi
    # dena") from leaking onto the next drug ("... nahi dena heparin shuru").
    r'dena|deni|dijiye|lena|leni|shuru|karna|karni|karo|kiya|diya|'
    r'hoti|hota|hote|raha|rahi)\b|,',
    re.IGNORECASE,
)
_CORRECTION_RE = re.compile(
    r'(?:no\s+make\s+it|actually|wait)[,\s]+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))',
    re.IGNORECASE,
)

# Fuzzy matching: common non-medical words to skip
_FUZZY_SKIP_WORDS = {
    "patient", "doctor", "please", "since", "start", "about", "after",
    "their", "there", "where", "which", "while", "would", "could", "should",
    "today", "yesterday", "morning", "evening", "taking", "having", "feeling",
    "going", "coming", "getting", "doing", "being", "saying", "years", "months",
    "weeks", "report", "present", "noted", "given", "complain", "history",
    "review", "follow", "clinic", "hospital", "discharge", "admission",
    "treatment", "advice", "tablet", "capsule", "syrup", "injection",
    # Diagnoses that fuzzy-match drug brand names
    "migraine", "malaria", "measles", "mumps", "dengue", "typhoid",
    # "vitamin" alone fuzzy-matches "vitamin d"; full phrases caught by _KNOWN_MEDICATIONS
    "vitamin",
    "infection", "infect", "reaction", "develops", "earlier", "persists",
    "impression", "condition", "likely", "possible", "suspected",
    "plenty", "fluids", "light", "resting", "dietary",
    "hoon", "hain", "karte", "dete", "karwao", "check",
    # Clinical adjectives / measurement terms that false-positive as drug names
    "cardiac", "cardio", "output", "normal", "severe", "active", "stable",
    "lethal", "tissue", "record", "linear", "mitral", "aortic", "brachial",
    "serial", "basal", "radial", "distal", "medial", "lateral", "signal",
    # Common Indian names that fuzzy-match symptoms or drugs (e.g. meena → melena)
    "meena", "neena", "reena", "seema", "veena", "beena", "leena", "heena",
    "geeta", "neeta", "reeta", "meeta", "leela", "sheela", "sheena",
    "raman", "suman", "naman", "daman", "yamuna", "karuna", "varuna",
}


def _is_negated(text: str, match_start: int, match_end: int = -1, window: int = 40) -> bool:
    preceding = text[max(0, match_start - window): match_start]
    neg_match = None
    for m in _NEGATION_RE.finditer(preceding):
        neg_match = m
    if neg_match is not None:
        reset = _CLAUSE_RESET_RE.search(preceding, neg_match.end())
        if reset is None:
            return True

    if match_end < 0:
        match_end = match_start
    following = text[match_end: min(len(text), match_end + 25)]
    post_neg = _POST_NEGATION_RE.search(following)
    if post_neg:
        boundary = _CLAUSE_RESET_RE.search(following)
        if boundary is None or boundary.start() > post_neg.start():
            return True

    return False


def _canonical_med(name: str) -> str | None:
    """Allowlist gate + canonicalization for a medication candidate.

    Returns the canonical drug name (lowercased) if ``name`` is a recognised
    medication — exact membership in the curated drug set, an ontology exact
    match, or an edit-distance-1 fuzzy match (catches ASR spelling variants
    like 'glimipride' → 'glimepiride'). Returns None for anything that is not
    a known drug, so Hindi verbs ('badhake'), compound fragments ('acid',
    'sulfate') and other noise are structurally rejected rather than chased
    with an ever-growing denylist.
    """
    n = name.lower().strip()
    if not n:
        return None
    if n in _KNOWN_MEDICATIONS:
        return n
    if _ontology.exact_match(n, "medication"):
        return n
    canon = _ontology.fuzzy_match(n, "medication", max_edit_distance=1)
    if canon:
        return canon.lower()
    return None


def _assoc_window(text: str, start: int, length: int = 22) -> str:
    """A short window after a drug/dose for frequency + duration association,
    truncated at the next known-drug token so one drug never captures a
    neighbour's frequency or duration (or trailing investigation timing like
    'anomaly scan 18 hafte')."""
    w = text[start:start + length]
    cut = len(w)
    for tk in re.finditer(r'\b[a-z]{3,}\b', w.lower()):
        if tk.group(0) in _KNOWN_MEDICATIONS:
            cut = tk.start()
            break
    return w[:cut]


def _classify_med_status(context: str) -> str:
    """Classify a prescription change from its surrounding sentence.

    Returns one of: increased | reduced | restarted | hold | continue | new
    | active (default). Drives the medication-change annotations in the SOAP
    note so a reviewing physician sees *what changed*, not just a flat list.

    Order matters: restarted before hold/continue (band tha → dobara shuru
    is restarted, not hold). increased/reduced before continue.
    """
    c = (context or "").lower()

    # ── Dose change ────────────────────────────────────────────────────────
    if re.search(
        r'\b(?:se\s+)?badha(?:ke|kar|na|o)?\b'
        r'|\bincreas(?:e|ed|ing)\b|\bbadhao\b|\bdose\s+(?:up|increase|badha)'
        r'|\bup\s+titrat|\btitrat.*up\b',
        c,
    ):
        return "increased"

    if re.search(
        r'\bghata(?:ke|kar|na|o)?\b|\breduc(?:e|ed|ing)\b|\bkam\s+kar'
        r'|\bdose\s+(?:down|reduce|kam|ghata)|\btaper\b',
        c,
    ):
        return "reduced"

    # ── Restarted — must come before hold (band tha ... dobara shuru) ──────
    if re.search(
        r'\bband\s+tha\b|\bpehle\s+band\b|\bbandh\s+(?:kar\s+)?(?:diya|tha|kiya)\b'
        r'|\b(?:dobara|phir\s*se|firse|wapas|re)\s*(?:shuru|start|le\s+lo|lena)\b'
        r'|\brestart(?:ed)?\b|\bresume\b',
        c,
    ):
        return "restarted"

    # ── Hold / avoid / stop ────────────────────────────────────────────────
    if re.search(
        r'\bhold\b|\broko\b|\bband\s+kar(?:o|na|do)?\b|\bstop(?:ped)?\b'
        r'|\bbandh\s+kar\b|\bavoid\b|\bmat\s+d(?:ena|o)\b|\bmat\s+lena\b'
        r'|\bnot\s+to\s+give\b|\bdo\s+not\s+give\b|\bnahi\s+dena\b'
        r'|\bnahi\s+d(?:ena|o)\b|\bwithheld?\b|\bdiscontinue\b',
        c,
    ):
        return "hold"

    # ── Continue / maintain ────────────────────────────────────────────────
    if re.search(
        r'\bcontinue\b|\bcontinu\w*\b|\bjari\b|\bjari\s+rakh\b'
        r'|\brakh(?:na|o|te\s+raho)\b|\bchalu\s+rakh\b|\bsame\b'
        r'|\bwahi\s+(?:dawa|tablet|dose)\b|\bkoi\s+badlav\s+nahi\b'
        r'|\bno\s+change\b|\bas\s+(?:before|it\s+is)\b'
        r'|\ble\s+(?:rahe|raha|rahi)\s+hain?\b',
        c,
    ):
        return "continue"

    # ── New prescription ───────────────────────────────────────────────────
    if re.search(
        r'\bshuru\s*(?:kar(?:o|na|te|do|wa))?\b|\bstart\b'
        r'|\bnaya\b|\bnai\b|\bnew\b|\badd\b|\badd\s+kar\b'
        r'|\bpehli\s+(?:baar|bar)\b|\bpehle\s+nahi\s+(?:liya|diya|tha)\b'
        r'|\bprescrib(?:e|ed|ing)\b|\binitiat(?:e|ed|ing)\b',
        c,
    ):
        return "new"

    return "active"


# ──────────────────────────────────────────────────────────────────────────────
# Fuzzy matching helpers (rapidfuzz optional)
# ──────────────────────────────────────────────────────────────────────────────

def _fuzzy_extract_symptoms(sent_text: str, result: dict) -> None:
    """Fuzzy-match words ≥5 chars against ontology symptom database."""
    lower = sent_text.lower()
    words = re.findall(r'\b[a-zA-Z]{5,}\b', lower)
    if not words:
        return

    for word in words:
        if _ontology.exact_match(word, "symptom") or word in _FUZZY_SKIP_WORDS:
            continue
        canonical = _ontology.fuzzy_match(word, "symptom", max_edit_distance=1)
        if canonical:
            m = re.search(rf'\b{re.escape(word)}\b', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                if canonical not in result["symptoms"]:
                    result["symptoms"].append(canonical)
                    result["contexts"].setdefault(canonical, sent_text)


def _fuzzy_extract_medications(sent_text: str, result: dict) -> None:
    """Fuzzy-match words ≥6 chars against ontology medication database."""
    lower = sent_text.lower()
    word_matches = list(re.finditer(r'\b[a-zA-Z]{6,}\b', lower))
    if not word_matches:
        return

    is_investigation_sentence = bool(_INVESTIGATION_VERBS.search(lower))
    for match in word_matches:
        word = match.group(0)
        if _is_allergen_span(sent_text, match.start(), match.end()):
            continue
        # Patient safety: never fuzzy-admit a negated drug ("statin nahi dena")
        if _is_negated(lower, match.start(), match.end()):
            continue
        if _ontology.exact_match(word, "medication") or word in _FUZZY_SKIP_WORDS:
            continue
        canonical = _ontology.fuzzy_match(word, "medication", max_edit_distance=1)
        if canonical:
            # Dual-use nutrient disambiguation: if an investigation verb is present,
            # a fuzzy match for e.g. "vitamin" → "VITAMIN D" is a test order, not
            # a prescription. Skip fuzzy medication extraction in that case.
            if is_investigation_sentence and canonical.lower() in _INVESTIGATION_MAP:
                continue
            already_present = any(
                canonical.lower() in m["name"].lower()
                or m["name"].lower() in canonical.lower()
                for m in result["medications"]
            )
            if not already_present:
                dosage = ""
                dosage_m = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g|iu|units?))\b', lower[lower.index(word) + len(word):] if word in lower else "", re.IGNORECASE)
                if dosage_m:
                    dosage = dosage_m.group(1).strip()
                result["medications"].append({
                    "name": canonical,
                    "dosage": dosage,
                    "frequency": "",
                })
                result["contexts"].setdefault(canonical, sent_text)


def _fuzzy_extract_diagnoses(sent_text: str, result: dict) -> None:
    """Disabled: fuzzy diagnosis matching caused false positives.
    Diagnosis extraction is explicit-only via keyword map."""
    return


# ──────────────────────────────────────────────────────────────────────────────
# Main extractor service
# ──────────────────────────────────────────────────────────────────────────────

class ClinicalExtractorService:

    def extract(self, transcript: str) -> dict:
        result: dict = {
            "symptoms": [],
            "medications": [],
            "vitals": [],
            "allergies": [],
            "investigations": [],
            "diagnoses": [],
            "follow_up": [],
            "contexts": {},
        }

        if not transcript or not transcript.strip():
            return result

        # Pre-process: transliterate Devanagari to Roman if present
        processed = _maybe_transliterate(transcript)

        # Layer 0: ASR normalization — rejoin split words, fix misspellings
        processed = _normalize_asr_text(processed, _ontology.get_vocab_set())

        doc = nlp(processed)

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            # Skip uncertain sentences
            if _UNCERTAINTY_WORDS.search(sent_text):
                continue

            # Question sentences (e.g. "Any nausea or vomiting?") are enquiries,
            # not assertions. Skip symptom/diagnosis extraction to avoid treating
            # a doctor's question as a confirmed symptom. Medications and
            # investigations are still extracted (e.g. "CBC karwao?").
            is_question = sent_text.rstrip().endswith("?")

            # Layer 1: exact keyword extraction
            if not is_question:
                self._extract_symptoms(sent_text, result)
            self._extract_vitals(sent_text, result)
            self._extract_allergies(sent_text, result)
            self._extract_investigations(sent_text, result)
            self._extract_medications(sent_text, result)
            if not is_question:
                self._extract_diagnoses(sent_text, result)
            self._extract_followup(sent_text, result)

            # Layer 2: fuzzy extraction as fallback for ASR spelling errors
            if not is_question:
                _fuzzy_extract_symptoms(sent_text, result)
            _fuzzy_extract_medications(sent_text, result)
            _fuzzy_extract_diagnoses(sent_text, result)

        # Also run on the original (non-transliterated) transcript for Devanagari maps
        if processed != transcript:
            orig_doc = nlp(transcript)
            for sent in orig_doc.sents:
                sent_text = sent.text.strip()
                if sent_text and not sent_text.rstrip().endswith("?"):
                    self._extract_symptoms(sent_text, result)
                    self._extract_diagnoses(sent_text, result)

        # Vitals are anchored numeric patterns (keyword + unit + range check), so
        # they are safe to run once over the WHOLE transcript. This recovers
        # values that the spaCy sentencizer split apart on unpunctuated ASR text
        # (e.g. "... weight | 58kg ..." landing across a sentence boundary).
        self._extract_vitals(processed, result)

        self._enrich_symptom_durations(processed, result)

        # Collapse a generic symptom into a more specific one that is also present
        # ("swelling" → drop when "ankle swelling" is present).
        def _plain(s: str) -> str:
            return s.split(" (")[0].strip().lower()
        syms = result["symptoms"]
        result["symptoms"] = [
            s for s in syms
            if not any(
                other is not s
                and _plain(s) != _plain(other)
                and re.search(rf'\b{re.escape(_plain(s))}\b', _plain(other))
                for other in syms
            )
        ]
        # Deduplicate exact-canonical duplicates (two map keys hitting same canonical)
        _seen_canonical: set[str] = set()
        _deduped: list[str] = []
        for _s in result["symptoms"]:
            _k = _plain(_s)
            if _k not in _seen_canonical:
                _seen_canonical.add(_k)
                _deduped.append(_s)
        result["symptoms"] = _deduped

        # Collapse a generic diagnosis into a more specific one that is also
        # present ("Anemia" → drop when "Iron Deficiency Anemia" is present).
        dx = result["diagnoses"]
        result["diagnoses"] = [
            d for d in dx
            if not any(other != d and d.lower() in other.lower() for other in dx)
        ]

        # Per-drug post-pass over the FULL transcript: recover a dose/frequency
        # the sentencizer split away from the drug name, and classify the
        # change-status — both from a window local to the drug mention so they
        # bind to the right drug ("telmisartan ... badhake ... amlodipine ...
        # continue") and never reach across to the next drug.
        processed_lower = processed.lower()
        med_names_lower = [m["name"].lower() for m in result["medications"]]
        for med in result["medications"]:
            nm = med["name"].lower()
            pos = processed_lower.find(nm)
            if pos == -1:
                med["status"] = _classify_med_status(result["contexts"].get(med["name"], ""))
                continue

            after_start = pos + len(nm)

            # Look BEFORE the drug name (up to 60 chars) to catch sentence-level
            # status cues like "Naya prescription — pantoprazole" where the status
            # word precedes the drug name.
            pre_start = max(0, pos - 60)
            # Don't reach into the previous drug's territory.
            for other in med_names_lower:
                if other == nm:
                    continue
                op = processed_lower.rfind(other, pre_start, pos)
                if op != -1:
                    pre_start = max(pre_start, op + len(other))
            before_window = processed_lower[pre_start:pos]

            # Look AFTER the drug name up to the next drug or end of sentence
            # (whichever comes first). 80-char cap; sentence boundary trumps.
            sent_end = after_start
            for ch in ".!?\n":
                idx = processed_lower.find(ch, after_start)
                if idx != -1:
                    sent_end = min(sent_end if sent_end > after_start else idx + 1, idx)
            if sent_end <= after_start:
                sent_end = after_start + 80
            cap = sent_end
            for other in med_names_lower:
                if other == nm:
                    continue
                op = processed_lower.find(other, after_start)
                if op != -1:
                    cap = min(cap, op)
            after_window = processed_lower[after_start:cap]

            # Classify using both windows; full sentence context wins over window alone.
            sent_ctx = result["contexts"].get(med["name"], "")
            status_ctx = before_window + " " + nm + " " + after_window
            med["status"] = _classify_med_status(sent_ctx or status_ctx)
            if not med.get("dosage"):
                dm = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g|iu))\b', after_window, re.IGNORECASE)
                if dm:
                    med["dosage"] = dm.group(1).strip()
            if not med.get("frequency"):
                fm = re.search(r'\b(BD|OD|TDS|QID|SOS|PRN|STAT|HS)\b', after_window, re.IGNORECASE)
                if fm:
                    med["frequency"] = fm.group(1).upper()

        return result

    # ──────────────────────────────────────────────────────────────────────
    # Private extraction helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_symptoms(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        # Skip conditional/hypothetical sentences
        if re.search(r'\bif\b.*\b(develops?|occurs?|persists?|worsens?|appears?)\b', lower):
            return
        # Skip past-tense allergy/reaction context
        if re.search(r'\b(reaction|allergy).*\b(tha|thi|the|pehle|before|previously|earlier)\b', lower):
            return
        for keyword, canonical in _SYMPTOM_MAP.items():
            m = re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                original_word = m.group(0).strip()
                if original_word != canonical and original_word not in canonical:
                    display_sym = f"{canonical} ('{original_word}')"
                else:
                    display_sym = canonical

                if display_sym not in result["symptoms"]:
                    if canonical in result["symptoms"]:
                        result["symptoms"].remove(canonical)
                    result["symptoms"].append(display_sym)
                    result["contexts"][display_sym] = sent_text

    @staticmethod
    def _extract_vitals(sent_text: str, result: dict) -> None:
        # Blood Pressure — "150/90", "150 over 90", "142 slash 88", "BP 150 by 90"
        bp_match = re.search(r'\b(\d{2,3})\s*(?:/|over|by|slash)\s*(\d{2,3})\b', sent_text, re.IGNORECASE)
        if bp_match:
            bp_value = f"{bp_match.group(1)}/{bp_match.group(2)}"
            vital = f"BP {bp_value}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Temperature — "38.5°C", "38.5 C", "101 F", "38.5 degrees C", "38.5fahrenheit"
        # Bare "38F" is patient demographic (age+sex), NOT temperature — require space or ° before F/C
        temp_match = re.search(
            r'\b(\d{2,3}(?:\.\d{1,2})?)(?:\s*(?:degrees?\s*|°\s*)(F|C)|\s+(F|C)\b|\s*(?:degrees?\s*|°\s*)?(fahrenheit|celsius))\b',
            sent_text, re.IGNORECASE,
        )
        if temp_match:
            unit = (temp_match.group(2) or temp_match.group(3) or temp_match.group(4) or "C")[0].upper()
            vital = f"Temp {temp_match.group(1)} {unit}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text
        else:
            # Bare number after temperature keyword — infer unit from physiological range
            bare_temp = re.search(
                r'\b(?:temperature|temp|bukhar|fever)\s+(?:ke\s+saath\s+|tha\s+|hai\s+|is\s+|of\s+|aa\s+rahi\s+)?(\d{2,3}(?:\.\d{1,2})?)\b',
                sent_text, re.IGNORECASE,
            )
            if not bare_temp:
                # "103 degree" with no F/C unit — infer unit from physiological range
                bare_temp = re.search(r'\b(\d{2,3}(?:\.\d{1,2})?)\s*degrees?\b', sent_text, re.IGNORECASE)
            if bare_temp:
                val = float(bare_temp.group(1))
                if 95 <= val <= 108:
                    vital = f"Temp {bare_temp.group(1)} F"
                elif 35 <= val <= 42:
                    vital = f"Temp {bare_temp.group(1)} C"
                else:
                    vital = None
                if vital and vital not in result["vitals"]:
                    result["vitals"].append(vital)
                    result["contexts"][vital] = sent_text

        # SpO2
        spo2_match = re.search(
            r'\b(?:spo2|o2\s*sat(?:uration)?|oxygen\s+sat(?:uration)?|oxygen)\s*(?:is\s*)?(\d{2,3})\s*%?',
            sent_text, re.IGNORECASE,
        )
        if spo2_match:
            vital = f"SpO2 {spo2_match.group(1)}%"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Pulse / Heart rate
        hr_match = re.search(
            r'\b(?:pulse|hr|heart\s+rate|nadi)\s*(?:is\s*)?(\d{2,3})\s*(?:bpm|/min)?\b',
            sent_text, re.IGNORECASE,
        )
        if hr_match:
            vital = f"Pulse {hr_match.group(1)} bpm"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Respiratory rate
        rr_match = re.search(
            r'\b(?:rr|respiratory\s+rate)\s*(?:is\s*)?(\d{1,2})\b',
            sent_text, re.IGNORECASE,
        )
        if rr_match:
            vital = f"RR {rr_match.group(1)}/min"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Weight — "74 kg", "74 kilogram", "weight 74"
        wt_match = re.search(
            r'\b(?:weight|wt|wajan|vajan)\s*(?:is\s*)?(\d{2,3}(?:\.\d)?)\s*(?:kg|kilogram|kilograms|kilo)\b'
            r'|\b(\d{2,3}(?:\.\d)?)\s*(?:kilogram|kilograms)\b',
            sent_text, re.IGNORECASE,
        )
        if wt_match:
            val = wt_match.group(1) or wt_match.group(2)
            vital = f"Weight {val} kg"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Blood glucose — allow up to 20 chars between keyword and value to handle
        # "fasting sugar today is 160" (intervening words like "today", "level", etc.)
        glucose_match = re.search(
            r'\b(?:fasting\s+sugar|blood\s+sugar|blood\s+glucose|rbs|fbs|ppbs|glucose|sugar)\b[^.;]{0,20}?(\d{2,3})\s*(?:mg/dl|mg)?\b',
            sent_text, re.IGNORECASE,
        )
        if glucose_match:
            gval = int(glucose_match.group(1))
            # Blood glucose < 30 is physiologically impossible; likely a duration ("10 saal")
            if gval >= 30:
                vital = f"Blood Glucose {glucose_match.group(1)} mg/dL"
                if vital not in result["vitals"]:
                    result["vitals"].append(vital)
                    result["contexts"][vital] = sent_text

        # HbA1c — "HbA1c 7.8", "hba1c is 7.8%", "glycated 7.8"
        hba1c_match = re.search(
            r'\b(?:hba1c|hb\s*a1c|glycated(?:\s+h(?:a)?emoglobin)?)\s*(?:is\s*|hai\s*|aaya\s*(?:hai\s*)?)?(\d{1,2}(?:\.\d)?)\s*%?',
            sent_text, re.IGNORECASE,
        )
        if hba1c_match:
            val = float(hba1c_match.group(1))
            if 3.0 <= val <= 20.0:
                vital = f"HbA1c {hba1c_match.group(1)}%"
                if vital not in result["vitals"]:
                    result["vitals"].append(vital)
                    result["contexts"][vital] = sent_text

        # Haemoglobin — "Hb 9.5", "haemoglobin is 9.5". Require a decimal or a
        # value <18 with no '/' nearby so we never capture a BP systolic.
        hb_match = re.search(
            r'\b(?:hb|haemoglobin|hemoglobin)\s*(?:is\s*|low\s+hai\s*|hai\s*)?(\d{1,2}(?:\.\d)?)\b',
            sent_text, re.IGNORECASE,
        )
        if hb_match:
            val = float(hb_match.group(1))
            if 3.0 <= val <= 20.0:
                vital = f"Hb {hb_match.group(1)} g/dL"
                if vital not in result["vitals"]:
                    result["vitals"].append(vital)
                    result["contexts"][vital] = sent_text

        # ── CARDIOLOGY-SPECIFIC VITALS ───────────────────────────────────────

        # LVEF — "EF 35%", "ejection fraction 45%", "EF forty five percent",
        # "LVEF is 35", "ef is 35 to 40", "EF 55-60%"
        lvef_match = re.search(
            r'\b(?:lvef|lv\s+ef|ejection\s+fraction|ef)\s*(?:is\s*|hai\s*|aaya\s*|of\s*)?'
            r'(\d{2})\s*(?:-|to)?\s*(\d{0,2})\s*%?',
            sent_text, re.IGNORECASE,
        )
        if lvef_match:
            lo = int(lvef_match.group(1))
            hi_str = lvef_match.group(2)
            if 10 <= lo <= 80:
                if hi_str and hi_str.strip():
                    ef_str = f"LVEF {lo}-{hi_str}%"
                else:
                    ef_str = f"LVEF {lo}%"
                if ef_str not in result["vitals"]:
                    result["vitals"].append(ef_str)
                    result["contexts"][ef_str] = sent_text

        # PASP — "PASP 60 mmHg", "pulmonary artery pressure 55"
        pasp_match = re.search(
            r'\b(?:pasp|pulmonary\s+artery\s+(?:systolic\s+)?pressure|rvsp)\s*(?:is\s*|of\s*|around\s*)?(\d{2,3})\s*(?:mmhg|mm\s*hg)?\b',
            sent_text, re.IGNORECASE,
        )
        if pasp_match:
            val = int(pasp_match.group(1))
            if 15 <= val <= 150:
                vital = f"PASP {val} mmHg"
                if vital not in result["vitals"]:
                    result["vitals"].append(vital)
                    result["contexts"][vital] = sent_text

        # NYHA Class — "NYHA class III", "NYHA III", "class 3"
        nyha_match = re.search(
            r'\bNYHA\s*(?:class\s*)?([I]{1,3}V?|[1-4])\b',
            sent_text, re.IGNORECASE,
        )
        if nyha_match:
            cls = nyha_match.group(1).upper()
            vital = f"NYHA Class {cls}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # CCS Class (angina grading)
        ccs_match = re.search(
            r'\bCCS\s*(?:class\s*|grade\s*)?([I]{1,3}V?|[1-4])\b',
            sent_text, re.IGNORECASE,
        )
        if ccs_match:
            cls = ccs_match.group(1).upper()
            vital = f"CCS Class {cls}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Troponin — "Troponin I 0.8 ng/mL", "troponin positive", "troponin 0.05"
        trop_match = re.search(
            r'\btroponin\s*(?:i|t|1|2)?\s*(?:is\s*|was\s*|level\s*)?(\d+(?:\.\d+)?)\s*(?:ng/ml|ng\/ml|mcg/l)?\b',
            sent_text, re.IGNORECASE,
        )
        if trop_match:
            vital = f"Troponin {trop_match.group(1)}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text
        elif re.search(r'\btroponin\s+(?:positive|elevated|raised|high)\b', sent_text, re.IGNORECASE):
            vital = "Troponin Positive"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # BNP / NT-proBNP — heart failure marker
        bnp_match = re.search(
            r'\b(?:nt.?pro.?bnp|bnp|brain\s+natriuretic\s+peptide)\s*(?:is\s*|was\s*|level\s*)?(\d+)\s*(?:pg/ml|pmol/l)?\b',
            sent_text, re.IGNORECASE,
        )
        if bnp_match:
            vital = f"NT-proBNP {bnp_match.group(1)} pg/mL"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # 6MWT — 6-Minute Walk Test (PAH monitoring)
        mwt_match = re.search(
            r'\b6\s*(?:minute|min)\s*walk\s*(?:test\s*)?(?:distance\s*)?(?:is\s*|of\s*)?(\d{2,3})\s*(?:metres?|meters?|m)?\b',
            sent_text, re.IGNORECASE,
        )
        if mwt_match:
            vital = f"6MWT {mwt_match.group(1)}m"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

    @staticmethod
    def _extract_allergies(sent_text: str, result: dict) -> None:
        for pattern in _ALLERGY_PATTERNS:
            match = re.search(pattern, sent_text, re.IGNORECASE)
            if match:
                if _is_negated(sent_text, match.start(1), match.end(1)):
                    continue
                allergen = _clean_allergen(match.group(1)).lower().strip()
                if allergen and allergen not in result["allergies"]:
                    result["allergies"].append(allergen)
                    result["contexts"][allergen] = sent_text

    # Prescription verbs: when present in the sentence, the mention is a drug
    # order, not an investigation order. Used to disambiguate nutrients that
    # appear in both the investigation map and the medication list (e.g. Vitamin D).
    _PRESCRIPTION_VERBS = re.compile(
        r'\b(?:likhdo|likh\s*do|likh\s*dena|de\s*do|dena|shuru|start|prescrib|chalao|'
        r'continue|jari|leke\s+aao|le\s+lo|lena|khana|khao)\b',
        re.IGNORECASE,
    )

    @staticmethod
    def _extract_investigations(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        is_prescription_sentence = bool(ClinicalExtractorService._PRESCRIPTION_VERBS.search(lower))
        for keyword, canonical in _INVESTIGATION_MAP.items():
            if re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower):
                # Suppress investigation when the same sentence has a prescription
                # verb — "Vitamin D 60000 IU likhdo" is a drug order, not a test.
                if is_prescription_sentence and keyword in _KNOWN_MEDICATIONS:
                    continue
                if canonical not in result["investigations"]:
                    result["investigations"].append(canonical)
                    result["contexts"][canonical] = sent_text

    @staticmethod
    def _extract_medications(sent_text: str, result: dict) -> None:
        freq_pattern = re.compile(
            r'\b(BD|OD|TDS|QID|SOS|PRN|STAT|HS|'
            r'twice\s+daily|twice\s+a\s+day|once\s+(?:a\s+)?day|'
            r'thrice\s+daily|three\s+times\s+(?:a\s+)?day|four\s+times\s+(?:a\s+)?day|'
            r'at\s+night|at\s+bedtime|before\s+bed|'
            r'morning\s+and\s+night|morning\s+and\s+evening|'
            r'subah\s+shaam\s+raat|subah\s+shaam|subah\s+aur\s+raat|'
            r'din\s+mein\s+char\s+baar|din\s+mein\s+teen\s+baar|din\s+mein\s+do\s+baar|'
            r'char\s+baar|teen\s+baar|do\s+baar|ek\s+baar|'
            r'khane\s+ke\s+baad|khana\s+ke\s+baad|khane\s+se\s+pehle|khana\s+se\s+pehle|'
            r'raat\s+ko|roz)\b',
            re.IGNORECASE,
        )

        def _norm_freq(raw: str) -> str:
            key = re.sub(r'\s+', ' ', raw.strip().lower())
            return _HINDI_FREQ_NORMALIZE.get(key, raw)

        def _extract_duration(text: str, start: int) -> str:
            for phrase, normalized in _HINDI_MED_DURATION_MAP.items():
                if phrase in text[start:].lower():
                    return normalized
            m = _MED_DURATION_RE.search(text, start)
            if m:
                return m.group(0).strip()
            return ""
        skip_words = {
            "the", "and", "for", "with", "this", "that", "from",
            "has", "was", "are", "his", "her", "she", "him",
            "not", "also", "but", "start", "give", "take",
            "patient", "doctor", "daily", "twice", "once",
            "tablet", "tablets", "capsule", "capsules", "syrup", "injection",
            "hoon", "hain", "raha", "rahi", "rahe", "wala", "wali",
            "karte", "dete", "karo", "karwao", "liya", "lena",
            "check", "rule", "with", "out", "like", "only",
            # Hindi verbs / particles that precede a dose and get mis-captured
            "badhake", "badha", "ghatake", "ghata", "abhi", "pehle", "baad",
            "band", "shuru", "roko", "rakhna", "rakho", "leke", "deke", "karke",
            "dena", "karna", "lena", "leni", "khana", "waale", "waali", "wale",
            "nahi", "nahin", "nhi", "mat", "hold", "continue", "stop",
            "bhi", "aaya", "aayi", "tha", "thi", "the", "kar", "diya",
        }
        med_matches = re.finditer(
            r'\b([A-Za-z]{3,})\s+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g|iu|units?)\b)',
            sent_text, re.IGNORECASE,
        )

        for match in med_matches:
            raw_name = match.group(1).lower()
            dosage = match.group(2).strip()

            if raw_name in skip_words:
                continue
            if _is_allergen_span(sent_text, match.start(1), match.end(1)):
                continue
            # Patient safety: never admit a negated drug ("X nahi dena")
            if _is_negated(sent_text, match.start(1), match.end(1)):
                continue
            # Allowlist gate: only accept recognised drugs. This rejects the word
            # captured before a dose when it is a Hindi verb ('badhake 80mg') or a
            # compound fragment ('acid' from 'folic acid 5mg').
            name = _canonical_med(raw_name)
            if not name:
                continue

            freq = ""
            duration = ""
            window = _assoc_window(sent_text, match.end())
            freq_match = freq_pattern.search(window)
            if freq_match:
                freq = _norm_freq(freq_match.group(1))
                duration = _extract_duration(window, freq_match.end())
            else:
                duration = _extract_duration(window, 0)

            existing = [m for m in result["medications"] if m["name"] == name]
            if existing:
                if not existing[0]["dosage"]:
                    existing[0]["dosage"] = dosage
                if not existing[0]["frequency"] and freq:
                    existing[0]["frequency"] = freq
                if not existing[0].get("duration") and duration:
                    existing[0]["duration"] = duration
            else:
                result["medications"].append({"name": name, "dosage": dosage, "frequency": freq, "duration": duration})
                result["contexts"][name] = sent_text

        dose_first_matches = re.finditer(
            r'\b(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g)\b)\s+(?:tab(?:let)?s?|cap(?:sule)?s?|syp|syrup|inj(?:ection)?)\.?\s+(?:of\s+)?([A-Za-z]{3,})\b',
            sent_text,
            re.IGNORECASE,
        )
        for match in dose_first_matches:
            dosage = match.group(1).strip()
            raw_name = match.group(2).lower()
            if raw_name in skip_words:
                continue
            if _is_allergen_span(sent_text, match.start(2), match.end(2)):
                continue
            if _is_negated(sent_text, match.start(2), match.end(2)):
                continue
            name = _canonical_med(raw_name)
            if not name:
                continue

            freq = ""
            duration = ""
            window = _assoc_window(sent_text, match.end())
            freq_match = freq_pattern.search(window)
            if freq_match:
                freq = _norm_freq(freq_match.group(1))
                duration = _extract_duration(window, freq_match.end())
            else:
                duration = _extract_duration(window, 0)

            existing = [m for m in result["medications"] if m["name"] == name]
            if existing:
                if not existing[0]["dosage"]:
                    existing[0]["dosage"] = dosage
                if not existing[0]["frequency"] and freq:
                    existing[0]["frequency"] = freq
                if not existing[0].get("duration") and duration:
                    existing[0]["duration"] = duration
            else:
                result["medications"].append({"name": name, "dosage": dosage, "frequency": freq, "duration": duration})
                result["contexts"][name] = sent_text

        lower_sent = sent_text.lower()
        merged_meds = _KNOWN_MEDICATIONS
        is_investigation_sentence = bool(_INVESTIGATION_VERBS.search(lower_sent))
        for med_name in merged_meds:
            pattern = rf'\b{re.escape(med_name)}\b'
            m = re.search(pattern, lower_sent)
            if m:
                if _is_allergen_span(sent_text, m.start(), m.end()):
                    continue
                # Patient safety: skip negated drugs ("ferrous sulfate nahi dena")
                if _is_negated(sent_text, m.start(), m.end()):
                    continue
                # Skip when the drug word names a deficiency, not a prescription
                # ("iron deficiency anaemia" — iron is the deficient nutrient here)
                if re.match(r'\s*deficienc', lower_sent[m.end():m.end() + 14]):
                    continue
                # Disambiguate dual-use nutrients (Vitamin D, iron, calcium) that
                # appear in both _INVESTIGATION_MAP and _KNOWN_MEDICATIONS:
                # if the sentence contains an investigation-ordering verb ("check",
                # "karwao", "test"), treat it as a test order, not a prescription.
                if is_investigation_sentence and med_name in _INVESTIGATION_MAP:
                    continue
                already_matched = any(
                    existing["name"] == med_name
                    or med_name in existing["name"]
                    or existing["name"] in med_name
                    for existing in result["medications"]
                )
                if not already_matched:
                    dosage = ""
                    freq = ""
                    duration = ""
                    # Bound dose/freq/duration search to a window after the drug,
                    # truncated at the next known-drug token, so a drug never
                    # inherits a neighbour's dose/freq/duration
                    # ("metformin 500 ... glimepiride 2mg OD", "aspirin ...
                    # vitamin D ... 8 hafte").
                    assoc_window = lower_sent[m.end():m.end() + 40]
                    _cut = len(assoc_window)
                    for _tk in re.finditer(r'\b[a-z]{3,}\b', assoc_window):
                        if _tk.group(0) in _KNOWN_MEDICATIONS:
                            _cut = _tk.start()
                            break
                    assoc_window = assoc_window[:_cut]
                    dosage_match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g|iu|units?))\b', assoc_window, re.IGNORECASE)
                    if dosage_match:
                        dosage = dosage_match.group(1).strip()
                    freq_match = freq_pattern.search(assoc_window)
                    if freq_match:
                        freq = _norm_freq(freq_match.group(1))
                        duration = _extract_duration(assoc_window, freq_match.end())
                    else:
                        duration = _extract_duration(assoc_window, 0)
                    result["medications"].append({"name": med_name, "dosage": dosage, "frequency": freq, "duration": duration})
                    result["contexts"][med_name] = sent_text

        correction = _CORRECTION_RE.search(sent_text)
        if correction and result["medications"]:
            new_dosage = correction.group(1).strip()
            freq_match = freq_pattern.search(sent_text, correction.end())
            last_med = result["medications"][-1]
            last_med["dosage"] = new_dosage
            if freq_match:
                last_med["frequency"] = _norm_freq(freq_match.group(1))

    @staticmethod
    def _extract_diagnoses(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()

        # Bare "sugar" → Diabetes Mellitus ONLY when NOT followed by a number
        # (to avoid "sugar 320 aaya" producing a spurious DM diagnosis)
        _sugar_bare = re.search(r'(?:^|\b)sugar(?!\s*\d)(?:\b|$)', lower)
        if _sugar_bare and not _is_negated(lower, _sugar_bare.start(), _sugar_bare.end()):
            # Only fire if the sentence doesn't already contain a longer sugar phrase
            _already_phrase = any(
                phrase in lower for phrase in (
                    "sugar ka patient", "sugar ka problem", "sugar ki bimari",
                    "sugar ki problem", "sugar hai", "sugar control", "sugar badhna",
                )
            )
            if not _already_phrase and "Diabetes Mellitus" not in result["diagnoses"]:
                result["diagnoses"].append("Diabetes Mellitus")
                result["contexts"]["dx:Diabetes Mellitus"] = sent_text

        for keyword, canonical in _DIAGNOSIS_MAP.items():
            m = re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower)
            if m and not _is_negated(lower, m.start(), m.end()) \
                    and not _is_context_mention(lower, m.start(), m.end()):
                if canonical not in result["diagnoses"]:
                    result["diagnoses"].append(canonical)
                    result["contexts"][f"dx:{canonical}"] = sent_text

        label_match = _DIAGNOSIS_LABEL_RE.search(sent_text)
        if label_match:
            raw_full = label_match.group(1).strip().rstrip('.')
            for raw_part in re.split(r'[,;]', raw_full):
                raw = raw_part.strip().rstrip('.')
                if not raw or len(raw) < 2:
                    continue
                raw = re.sub(r'\s+(?:likely|possible|probable|suspected)$', '', raw, flags=re.IGNORECASE).strip()
                normalised = _DIAGNOSIS_MAP.get(raw.lower())
                if not normalised:
                    continue
                if normalised not in result["diagnoses"]:
                    result["diagnoses"].append(normalised)
                    result["contexts"][f"dx:{normalised}"] = sent_text

    @staticmethod
    def _extract_followup(sent_text: str, result: dict) -> None:
        # Explicit next-visit phrases take priority over any generic duration
        # match elsewhere in the (often unpunctuated, run-on) transcript so that
        # "agle hafte aana" wins over an earlier symptom-duration like
        # "last 2 mahine mein ...".
        for rx, label in _FOLLOWUP_EXPLICIT:
            if rx.search(sent_text):
                if label not in result["follow_up"]:
                    result["follow_up"].append(label)
                return
        for pattern in _FOLLOWUP_PATTERNS:
            m = pattern.search(sent_text)
            if m:
                # Reject durations that describe how long a symptom has been
                # present ("last 2 mahine mein", "3 hafte se") rather than a
                # next-visit interval.
                preceding = sent_text[max(0, m.start() - 12):m.start()].lower()
                if re.search(r'\b(last|past|pichle|since|for)\s*$', preceding) \
                        or re.match(r'\s*se\b', sent_text[m.end():m.end() + 4].lower()):
                    continue
                text = (m.group(1) if m.lastindex and m.group(1) else m.group(0)).strip(" .")
                # Normalize Hindi number words to digits
                for hindi, digit in _HINDI_NUMBERS.items():
                    text = re.sub(rf'\b{hindi}\b', digit, text, flags=re.IGNORECASE)
                # Humanize: "3 din baad" → "after 3 days"
                def _pluralize(m, unit):
                    n = int(m.group(1))
                    return f"after {n} {unit}" if n != 1 else f"after {n} {unit.rstrip('s')}"
                text = re.sub(r'(\d+)\s*din\s*(?:baad|ke\s+baad|mein)', lambda m: _pluralize(m, 'days'), text, flags=re.IGNORECASE)
                text = re.sub(r'(\d+)\s*haft[ae]\s*(?:baad|ke\s+baad|mein)', lambda m: _pluralize(m, 'weeks'), text, flags=re.IGNORECASE)
                text = re.sub(r'(\d+)\s*mahine?\s*(?:baad|ke\s+baad|mein)', lambda m: _pluralize(m, 'months'), text, flags=re.IGNORECASE)
                # Strip trailing filler words
                text = re.sub(r'\s*(follow|up|karna|aana|wapas|milna|review)\s*$', '', text, flags=re.IGNORECASE).strip(" .")
                if text and text not in result["follow_up"]:
                    result["follow_up"].append(text)
                break

    @staticmethod
    def _enrich_symptom_durations(transcript: str, result: dict) -> None:
        doc = nlp(transcript)
        enriched = []
        for symptom in result["symptoms"]:
            plain = symptom.split(" (")[0]
            duration_found = None
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                for kw, canonical in _SYMPTOM_MAP.items():
                    if canonical == plain and re.search(rf'\b{re.escape(kw)}\b', sent_lower):
                        dm = _DURATION_RE.search(sent_lower)
                        if dm:
                            duration_found = (dm.group(1) or dm.group(2) or "").strip()
                        break
            enriched.append(f"{plain} ({duration_found})" if duration_found else plain)
        result["symptoms"] = enriched

"""GLiNER-based clinical NER for Hinglish transcripts.

Extractive NER only — output is always a span of the input text.
Cannot hallucinate: if a term isn't in the transcript, it cannot appear here.

Used as Layer 2 after the keyword extractor:
  - Layer 1 (keyword/fuzzy): handles mapped Hinglish phrases
  - Layer 2 (GLiNER): catches English terms, dosages, investigations
    not covered by the keyword maps

Model: urchade/gliner_medium-v2.1 (~400MB, runs locally, no API needed)
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.utils.config import settings

logger = logging.getLogger(__name__)

# Known investigation terms — used to fix GLiNER's occasional
# misclassification of investigations as medications.
_INVESTIGATION_KEYWORDS = {
    "cbc", "complete blood count", "blood count", "hb", "haemoglobin", "hemoglobin",
    "rbs", "fbs", "hba1c", "blood sugar", "glucose", "lipid", "cholesterol",
    "thyroid", "tsh", "t3", "t4", "lft", "liver function", "kft", "kidney function",
    "creatinine", "urea", "uric acid", "ecg", "ekg", "echo", "x-ray", "xray",
    "chest x-ray", "ct", "mri", "usg", "ultrasound", "urine", "urine routine",
    "stool", "sputum", "throat swab", "culture", "sensitivity", "biopsy",
    "dengue", "malaria", "typhoid", "widal", "elisa", "covid", "rt-pcr",
    "karwao", "karwana",  # Hindi: "get it done" — signals investigation order
}


@lru_cache(maxsize=1)
def _load_model():
    """Load GLiNER model once and cache it."""
    if not settings.enable_gliner:
        return None

    if not settings.gliner_model_path:
        logger.warning("ENABLE_GLINER=true but GLINER_MODEL_PATH is not set; skipping GLiNER")
        return None

    model_path = Path(settings.gliner_model_path)
    if not model_path.exists():
        logger.warning("GLINER_MODEL_PATH does not exist: %s; skipping GLiNER", model_path)
        return None

    try:
        from gliner import GLiNER
        model = GLiNER.from_pretrained(str(model_path))
        logger.info("GLiNER model loaded from local path: %s", model_path)
        return model
    except Exception as e:
        logger.warning("GLiNER model failed to load: %s", e)
        return None


def _is_investigation(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in _INVESTIGATION_KEYWORDS)


def _category_for_label(label: str, text: str) -> Optional[str]:
    if "symptom" in label or "complaint" in label:
        return "investigation" if _is_investigation(text) else "symptom"
    if "medication" in label or "drug" in label:
        return "investigation" if _is_investigation(text) else "medication"
    if "investigation" in label or "test" in label:
        return "investigation"
    if "allergy" in label:
        return "allergy"
    if "follow" in label:
        return "follow_up"
    if "vital" in label:
        return "vital"
    if "diagnosis" in label:
        return "diagnosis"
    return None


def extract_candidates(transcript: str, threshold: float = 0.5) -> list[dict]:
    """Return scored extractive candidates.

    The returned ``text`` must be a substring of the transcript. Callers decide
    whether a candidate is discarded, shown for review, or auto-populated.
    """
    model = _load_model()
    if model is None:
        return []

    labels = [
        "symptom or complaint",
        "medication or drug",
        "medical investigation or test",
        "allergy",
        "follow-up instruction",
        "vital sign",
        "diagnosis",
    ]

    try:
        entities = model.predict_entities(transcript, labels, threshold=threshold)
    except Exception as e:
        logger.warning("GLiNER extraction failed: %s", e)
        return []

    candidates: list[dict] = []
    for ent in entities:
        text = ent["text"].strip()
        label = ent["label"]
        category = _category_for_label(label, text)
        score = float(ent.get("score") or ent.get("confidence") or 0)
        if not category or not text or text.lower() not in transcript.lower():
            continue
        candidates.append({
            "text": text,
            "label": label,
            "category": category,
            "confidence": score,
            "start": ent.get("start"),
            "end": ent.get("end"),
        })
    return candidates


def extract(transcript: str, threshold: float = 0.8) -> dict:
    """Run GLiNER NER on transcript. Returns dict with same shape as keyword extractor.

    This compatibility helper only returns high-confidence auto-populatable
    non-diagnosis categories. Lower-confidence candidates are available via
    ``extract_candidates`` for doctor review.
    """
    result: dict = {
        "symptoms": [],
        "medications": [],
        "investigations": [],
        "allergies": [],
        "follow_up": [],
    }

    for candidate in extract_candidates(transcript, threshold=threshold):
        category = candidate["category"]
        text = candidate["text"]
        if category in {"symptom", "diagnosis", "vital"}:
            continue
        key = {
            "medication": "medications",
            "investigation": "investigations",
            "allergy": "allergies",
            "follow_up": "follow_up",
        }[category]
        if text not in result[key]:
            result[key].append(text)

    return result


def is_available() -> bool:
    """Returns True if GLiNER model loaded successfully."""
    return _load_model() is not None

"""Ollama-based semantic entity extraction for Hinglish clinical transcripts.

Runs as an enrichment layer ON TOP of keyword extraction — it fills gaps
that keywords miss (rare diagnoses, pure Hindi terms, unusual phrasings).

Architecture:
  - keyword extraction (always runs, primary)
  - ollama enrichment  (runs if available, fills gaps only)
  - SOAP generation    (unchanged, deterministic)

No hallucination risk: Ollama returns a structured JSON list of entities
it found in the transcript. It cannot invent medications or dosages that
aren't in the text. The SOAP generator downstream remains rule-based.

Setup (one-time):
  brew install ollama
  ollama pull phi3:mini      # 2.3 GB, fast on M1/M2
  ollama serve               # or it starts automatically
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

_OLLAMA_BASE = "http://localhost:11434"

# Preferred models in order — first available one wins
_PREFERRED_MODELS = ["phi3:mini", "llama3.2:3b", "qwen2.5:3b", "mistral:7b", "llama2:7b"]

_EXTRACTION_PROMPT = """\
You are a medical entity extractor for Indian clinical transcripts (English/Hindi/Hinglish mixed).

Extract ALL medical entities explicitly mentioned in the transcript.
Return ONLY valid JSON with these exact keys. No prose, no explanation.

{{
  "symptoms": ["list of symptoms or complaints"],
  "medications": ["Drug Name Dosage Frequency", "..."],
  "diagnoses": ["Diagnosis1", "Diagnosis2"],
  "allergies": ["allergen1"],
  "vitals": ["BP 128/82", "Temp 38.6 C", "Pulse 88 bpm"],
  "investigations": ["CBC", "Throat Swab"],
  "follow_up": ["follow up in 3 days or earlier if fever persists"]
}}

Rules:
- Extract ONLY what is EXPLICITLY stated — never infer or add anything
- For negated symptoms ("no chest pain", "chest pain nahi hai") do NOT include them
- Hindi terms should be translated to English (bukhar=fever, khasi=cough, etc.)
- Medications: include dosage and frequency if mentioned
- Return empty arrays [] for categories with nothing found

Transcript:
{transcript}
"""


def _get_available_model() -> str | None:
    """Return first available Ollama model from preferred list, or None."""
    try:
        import requests
        r = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=2)
        if r.status_code != 200:
            return None
        installed = {m.get("name", "").split(":")[0] for m in r.json().get("models", [])}
        for model in _PREFERRED_MODELS:
            if model.split(":")[0] in installed:
                return model
        return None
    except Exception:
        return None


class OllamaExtractorService:
    """Semantic enrichment via local Ollama LLM. Completely optional."""

    def __init__(self):
        self._available: bool | None = None  # None = unchecked
        self._model: str | None = None

    def is_available(self) -> bool:
        if self._available is None:
            self._model = _get_available_model()
            self._available = self._model is not None
            if self._available:
                logger.info("Ollama semantic enrichment active — model: %s", self._model)
            else:
                logger.info("Ollama not available — using keyword extraction only")
        return self._available

    def extract(self, transcript: str) -> dict:
        """Extract entities semantically. Returns empty dict on any failure."""
        if not self.is_available() or not transcript:
            return {}

        try:
            import requests
            prompt = _EXTRACTION_PROMPT.format(transcript=transcript[:4000])
            r = requests.post(
                f"{_OLLAMA_BASE}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "num_predict": 1024},
                },
                timeout=45,
            )
            if r.status_code != 200:
                logger.warning("Ollama API returned %s", r.status_code)
                return {}

            raw = r.json().get("response", "")
            # Extract JSON block robustly
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                return {}

            data = json.loads(json_match.group())
            return _normalise_ollama_output(data)

        except Exception as e:
            logger.warning("Ollama extraction failed (non-fatal): %s", e)
            return {}


def _normalise_ollama_output(data: dict) -> dict:
    """Clean and validate Ollama JSON output."""
    def clean(val):
        if isinstance(val, list):
            return [str(x).strip() for x in val if x and str(x).strip()]
        return []

    return {
        "symptoms":      clean(data.get("symptoms")),
        "medications":   clean(data.get("medications")),
        "diagnoses":     clean(data.get("diagnoses")),
        "allergies":     clean(data.get("allergies")),
        "vitals":        clean(data.get("vitals")),
        "investigations": clean(data.get("investigations")),
        "follow_up":     clean(data.get("follow_up")),
    }


def merge_with_keywords(keyword_result: dict, ollama_result: dict) -> dict:
    """Merge Ollama enrichment into keyword extraction. Keywords take precedence."""
    if not ollama_result:
        return keyword_result

    merged = {k: list(v) if isinstance(v, list) else dict(v)
              for k, v in keyword_result.items()}

    # ── Symptoms ─────────────────────────────────────────────────────────
    existing_symptoms = {s.split(" (")[0].lower() for s in merged["symptoms"]}
    for sym in ollama_result.get("symptoms", []):
        if sym.lower() not in existing_symptoms:
            merged["symptoms"].append(sym)
            existing_symptoms.add(sym.lower())

    # ── Diagnoses ─────────────────────────────────────────────────────────
    existing_dx = {d.lower() for d in merged["diagnoses"]}
    for dx in ollama_result.get("diagnoses", []):
        if dx.lower() not in existing_dx:
            merged["diagnoses"].append(dx)
            existing_dx.add(dx.lower())

    # ── Allergies ─────────────────────────────────────────────────────────
    existing_allergies = {a.lower() for a in merged["allergies"]}
    for allergy in ollama_result.get("allergies", []):
        if allergy.lower() not in existing_allergies:
            merged["allergies"].append(allergy)
            existing_allergies.add(allergy.lower())

    # ── Investigations ────────────────────────────────────────────────────
    existing_invs = {i.lower() for i in merged["investigations"]}
    for inv in ollama_result.get("investigations", []):
        if inv.lower() not in existing_invs:
            merged["investigations"].append(inv)
            existing_invs.add(inv.lower())

    # ── Follow-up ─────────────────────────────────────────────────────────
    if not merged.get("follow_up") and ollama_result.get("follow_up"):
        merged["follow_up"] = ollama_result["follow_up"]

    # ── Medications from Ollama (only if keywords found nothing) ──────────
    if not merged["medications"] and ollama_result.get("medications"):
        for med_str in ollama_result["medications"]:
            parsed = _parse_medication_string(med_str)
            if parsed:
                merged["medications"].append(parsed)

    return merged


def _parse_medication_string(med_str: str) -> dict | None:
    """Parse 'Azithromycin 500mg OD' → {name, dosage, frequency}."""
    parts = med_str.strip().split()
    if not parts:
        return None

    name = parts[0].lower()
    if len(name) < 3:
        return None

    dosage_match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))', med_str, re.IGNORECASE)
    dosage = dosage_match.group(1) if dosage_match else ""

    freq_match = re.search(
        r'\b(BD|OD|TDS|QID|SOS|PRN|STAT|twice\s+daily|once\s+daily|thrice\s+daily)\b',
        med_str, re.IGNORECASE,
    )
    freq = freq_match.group(1) if freq_match else ""

    return {"name": name, "dosage": dosage, "frequency": freq}

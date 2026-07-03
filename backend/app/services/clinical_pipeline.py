"""Shared clinical extraction pipeline.

Used by both the production API (routes_notes.py) and the eval harness
(eval/run_eval.py) so they always exercise the same extraction path.

Returns the raw facts dict. SOAP generation and CDS are separate steps
that only the API route performs.
"""

import logging
from app.services.clinical_extractor import (
    ClinicalExtractorService,
    _INVESTIGATION_MAP,
    _KNOWN_MEDICATIONS,
    _canonical_med,
    _is_negated,
)

logger = logging.getLogger(__name__)
_extractor = ClinicalExtractorService()

# Medication form abbreviations — never valid drug names on their own
_MED_PREFIXES = {"tab", "cap", "syp", "inj", "tab.", "cap.", "syp.", "inj.", "rx"}

# Non-drug terms GLiNER occasionally labels as medications (advice/procedures/home remedies)
_NON_DRUG_TERMS = {
    "steam", "steam inhalation", "hot water", "cold water", "saline", "warm water",
    "salt water", "honey", "turmeric", "ginger", "lemon", "rest", "fluids",
    "hydration", "water", "ice", "gargle", "inhalation", "nebulization",
    # Hindi verbs/particles GLiNER sometimes tags as a drug span
    "badhake", "abhi", "pehle", "band", "shuru", "roko", "dena", "karna",
    "lena", "leni", "rakhna", "nahi", "mat", "hold", "se", "bhi", "ace",
    "ace inhibitor", "acid", "sulfate", "deficiency",
}


def _complete_compound(transcript_lower: str, fragment: str) -> str | None:
    """If a single-token GLiNER drug fragment ('acid') is part of a known
    multi-word drug that appears verbatim in the transcript ('folic acid'),
    return that compound. Otherwise None."""
    for med in _KNOWN_MEDICATIONS:
        if " " in med and fragment in med.split() and med in transcript_lower:
            return med
    return None


def _dedup_investigations(investigations: list[str]) -> list[str]:
    """Drop an investigation that is a strict word-subset of a more specific one
    already present, e.g. 'X-Ray' is removed when 'Chest X-Ray' is present."""
    result: list[str] = []
    for inv in investigations:
        inv_l = inv.lower()
        # Skip if a more specific investigation already covers this one
        if any(other.lower() != inv_l and inv_l in other.lower() for other in investigations):
            continue
        if inv not in result:
            result.append(inv)
    return result

# Vital-sign terms that GLiNER sometimes mislabels as investigations
_VITAL_TERMS = {
    "bp", "blood pressure", "temperature", "temp", "pulse", "hr",
    "heart rate", "rr", "respiratory rate", "spo2", "oxygen",
    "weight", "height", "bmi", "sugar", "glucose",
}


def run_health_pipeline(transcript: str) -> dict:
    """Extract structured clinical facts from a transcript.

    Layer 1 — ClinicalExtractorService (deterministic keyword/fuzzy, Hinglish maps)
    Layer 2 — GLiNER extractive NER, medications and investigations only.

    GLiNER MUST NOT add symptoms or diagnoses — those are keyword-map-only
    to prevent mislabelling (GLiNER labelled 'CBC' as symptom in early tests).
    GLiNER is extractive (span-only), so it cannot fabricate text not in the
    transcript, but it can misclassify entity types.
    """
    facts = _extractor.extract(transcript)
    facts["investigations"] = _dedup_investigations(facts["investigations"])

    try:
        from app.services import gliner_extractor
    except Exception:
        return facts

    if not gliner_extractor.is_available():
        return facts

    try:
        gliner_candidates = gliner_extractor.extract_candidates(transcript, threshold=0.5)
        facts["_gliner_candidates"] = gliner_candidates
        gliner_facts = gliner_extractor.extract(transcript, threshold=0.8)

        # ── Extractive safety gate (raw GLiNER output only) ──────────────────
        # GLiNER is extractive by design: every span must be a substring of the
        # transcript. This check verifies that guarantee and logs any violation.
        # We check gliner_facts (raw) before merge — Layer 1 uses canonical
        # names intentionally and is not subject to the same constraint.
        transcript_lower = transcript.lower()
        for field, items in gliner_facts.items():
            for item in items:
                if isinstance(item, str) and item.lower() not in transcript_lower:
                    logger.warning(
                        "GLiNER extractive-safety violation: %r not in transcript (field=%s)",
                        item, field,
                    )

        _inv_values = {v.lower() for v in _INVESTIGATION_MAP.values()}

        # ── Medications only — no symptoms, no diagnoses ──────────────────────
        # Layer 2 (GLiNER) is gated through the same safety checks as Layer 1:
        # negation, allowlist (canonicalisation), and compound completion. This
        # stops GLiNER from re-introducing a Hindi verb, a held drug, or a
        # compound fragment that Layer 1 already filtered out.
        allergen_names = {a.lower().split()[0] for a in facts["allergies"]}
        existing_meds = {m["name"].lower(): m for m in facts["medications"]}
        for raw in gliner_facts.get("medications", []):
            parts = raw.strip().split()
            if not parts:
                continue
            base_name = parts[0].lower().rstrip(".")
            raw_lower = raw.strip().lower()
            if base_name in _MED_PREFIXES or base_name in allergen_names:
                continue
            if raw_lower in _NON_DRUG_TERMS or base_name in _NON_DRUG_TERMS:
                continue
            # Patient safety: skip drugs the doctor explicitly withheld
            pos = transcript_lower.find(base_name)
            if pos != -1 and _is_negated(transcript, pos, pos + len(base_name)):
                continue
            # Allowlist gate (+ compound completion for fragments like 'acid')
            canon = _canonical_med(base_name)
            if not canon:
                canon = _complete_compound(transcript_lower, base_name)
            if not canon:
                continue
            if canon in existing_meds:
                med = existing_meds[canon]
                if not med.get("dose") and not med.get("dosage") and len(parts) > 1:
                    med["dose"] = parts[1]
                if not med.get("frequency") and len(parts) > 2:
                    med["frequency"] = " ".join(parts[2:])
            else:
                facts["medications"].append({"name": canon, "status": "active", "history": []})
                existing_meds[canon] = facts["medications"][-1]

        # ── Investigations — filter vital-sign terms ──────────────────────────
        existing_inv = {i.lower() for i in facts["investigations"]}
        for inv in gliner_facts.get("investigations", []):
            inv_lower = inv.lower()
            if inv_lower in _VITAL_TERMS:
                continue
            if not any(inv_lower in ei or ei in inv_lower for ei in existing_inv):
                facts["investigations"].append(inv)
                existing_inv.add(inv_lower)

        # Collapse generic investigations into their more specific form
        facts["investigations"] = _dedup_investigations(facts["investigations"])

        # ── Allergies ─────────────────────────────────────────────────────────
        _ALLERGY_FILLER = {"allergy", "allergic", "hai", "se", "ko", "nahi", "reaction"}
        existing_allergy = {a.lower() for a in facts["allergies"]}
        for allergy in gliner_facts.get("allergies", []):
            substance = allergy.lower().removeprefix("allergic to ").strip()
            # Reject spans that ARE the word "allergy" / filler words
            if substance in _ALLERGY_FILLER or substance in ("", "allergy"):
                continue
            # Reject multi-word spans where all words are filler (e.g. "se allergy")
            parts = substance.split()
            if all(p in _ALLERGY_FILLER for p in parts):
                continue
            if substance not in existing_allergy:
                facts["allergies"].append(substance)
                existing_allergy.add(substance)

        # ── Follow-up: prefer longer/more descriptive phrase ─────────────────
        gliner_fu = gliner_facts.get("follow_up", [])
        if not facts.get("follow_up") and gliner_fu:
            facts["follow_up"] = gliner_fu
        elif gliner_fu:
            for fu in gliner_fu:
                current_max = max((len(x) for x in facts["follow_up"]), default=0)
                if len(fu) > current_max:
                    facts["follow_up"] = [fu]
                    break

        logger.info("GLiNER merge: meds=%d, inv=%d",
                    len(facts["medications"]), len(facts["investigations"]))
    except Exception as exc:
        logger.warning("GLiNER enrichment skipped (non-fatal): %s", exc)

    return facts

"""Provenance-first clinical fact utilities.

This module keeps the existing legacy facts dict for compatibility while adding
evidence-backed fact records that can gate SOAP generation.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Optional

from app.schemas.consultation import EvidenceSpan, ExtractedFact
from app.services.clinical_extractor import (
    _DIAGNOSIS_MAP,
    _DURATION_RE,
    _INVESTIGATION_MAP,
    _KNOWN_MEDICATIONS,
    _SYMPTOM_MAP,
    _UNCERTAINTY_WORDS,
    _is_negated,
)

_YES_RE = re.compile(r"^\s*(yes|haan|ha|ji|ji haan|yeah|yep)\b", re.IGNORECASE)
_QUESTION_MARK_RE = re.compile(r"\?\s*$")
_CATEGORY_PLURAL = {
    "symptom": "symptoms",
    "medication": "medications",
    "vital": "vitals",
    "allergy": "allergies",
    "investigation": "investigations",
    "diagnosis": "diagnoses",
    "follow_up": "follow_up",
}
_AUTO_GLINER_CATEGORIES = {"medication", "investigation", "allergy", "follow_up"}
_VALID_CATEGORIES = set(_CATEGORY_PLURAL)


def _stable_id(*parts: Any) -> str:
    seed = "|".join(str(p) for p in parts)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _sentence_spans(text: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for idx, match in enumerate(re.finditer(r"[^.!?\n]+[.!?]?", text, flags=re.MULTILINE)):
        sentence = match.group(0).strip()
        if not sentence:
            continue
        leading_ws = len(match.group(0)) - len(match.group(0).lstrip())
        start = match.start() + leading_ws
        spans.append({"text": sentence, "start": start, "end": start + len(sentence), "index": idx})
    if not spans and text.strip():
        stripped = text.strip()
        start = text.index(stripped)
        spans.append({"text": stripped, "start": start, "end": start + len(stripped), "index": 0})
    return spans


def _clean_display_value(value: str) -> str:
    value = re.sub(r"\s+\('.*?'\)", "", value).strip()
    return value.split(" (")[0].strip()


def _raw_hint(value: str) -> Optional[str]:
    match = re.search(r"\('([^']+)'\)", value)
    return match.group(1) if match else None


def _find_sentence(sentences: list[dict[str, Any]], context: str, value: str) -> dict[str, Any]:
    if context:
        context_lower = context.strip().lower()
        for sentence in sentences:
            if sentence["text"].lower() == context_lower:
                return sentence
            if context_lower and context_lower in sentence["text"].lower():
                return sentence
    raw = _raw_hint(value) or _clean_display_value(value)
    raw_lower = raw.lower()
    for sentence in sentences:
        if raw_lower and raw_lower in sentence["text"].lower():
            return sentence
    return sentences[0] if sentences else {"text": "", "start": -1, "end": -1, "index": -1}


def _candidate_terms(category: str, normalized: str, raw_text: Optional[str] = None) -> list[str]:
    clean = _clean_display_value(str(normalized))
    terms = [t for t in [raw_text, _raw_hint(str(normalized)), clean, str(normalized)] if t]
    if category == "symptom":
        terms.extend(k for k, v in _SYMPTOM_MAP.items() if v.lower() == clean.lower())
    elif category == "diagnosis":
        terms.extend(k for k, v in _DIAGNOSIS_MAP.items() if v.lower() == clean.lower())
    elif category == "investigation":
        terms.extend(k for k, v in _INVESTIGATION_MAP.items() if v.lower() == clean.lower())
    return sorted(dict.fromkeys(terms), key=len, reverse=True)


def _make_span(
    transcript: str,
    sentence: dict[str, Any],
    category: str,
    normalized: str,
    raw_text: Optional[str] = None,
) -> EvidenceSpan:
    sentence_text = sentence["text"]
    local_start = -1
    matched = raw_text or _clean_display_value(str(normalized))
    for term in _candidate_terms(category, str(normalized), raw_text):
        if not term:
            continue
        found = sentence_text.lower().find(term.lower())
        if found >= 0:
            local_start = found
            matched = sentence_text[found:found + len(term)]
            break
    if local_start < 0:
        global_found = transcript.lower().find(str(matched).lower())
        if global_found >= 0:
            return EvidenceSpan(
                raw_text=transcript[global_found:global_found + len(str(matched))],
                source_sentence=sentence_text,
                sentence_index=sentence["index"],
                start_char=global_found,
                end_char=global_found + len(str(matched)),
            )
        return EvidenceSpan(
            raw_text=str(matched),
            source_sentence=sentence_text,
            sentence_index=sentence["index"],
            start_char=sentence["start"],
            end_char=sentence["start"],
        )
    start = sentence["start"] + local_start
    return EvidenceSpan(
        raw_text=matched,
        source_sentence=sentence_text,
        sentence_index=sentence["index"],
        start_char=start,
        end_char=start + len(matched),
    )


def _duration_span(sentences: list[dict[str, Any]], symptom_sentence_index: int) -> Optional[EvidenceSpan]:
    for sentence in sentences[symptom_sentence_index:symptom_sentence_index + 2]:
        match = _DURATION_RE.search(sentence["text"])
        if match:
            raw = match.group(0).strip()
            return EvidenceSpan(
                raw_text=raw,
                source_sentence=sentence["text"],
                sentence_index=sentence["index"],
                start_char=sentence["start"] + match.start(),
                end_char=sentence["start"] + match.end(),
            )
    return None


def _make_fact(
    transcript: str,
    sentences: list[dict[str, Any]],
    category: str,
    normalized: str,
    *,
    context: str = "",
    raw_text: Optional[str] = None,
    extractor: str = "rule",
    confidence: float = 0.95,
    certainty: str = "affirmed",
    review_status: str = "candidate",
    confirmed_by: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    evidence_spans: Optional[list[EvidenceSpan]] = None,
) -> ExtractedFact:
    sentence = _find_sentence(sentences, context, normalized)
    primary_span = _make_span(transcript, sentence, category, normalized, raw_text)
    spans = evidence_spans or [primary_span]
    if category == "symptom":
        duration = _duration_span(sentences, max(primary_span.sentence_index, 0))
        if duration and duration.raw_text not in {span.raw_text for span in spans}:
            spans.append(duration)
    first = spans[0]
    return ExtractedFact(
        id=_stable_id(category, normalized, first.start_char, first.end_char, extractor),
        category=category,  # type: ignore[arg-type]
        raw_text=first.raw_text,
        normalized_value=normalized,
        source_sentence=first.source_sentence,
        sentence_index=first.sentence_index,
        start_char=first.start_char,
        end_char=first.end_char,
        evidence_spans=spans,
        extractor=extractor,  # type: ignore[arg-type]
        confidence=round(float(confidence), 4),
        certainty=certainty,  # type: ignore[arg-type]
        review_status=review_status,  # type: ignore[arg-type]
        confirmed_by=confirmed_by if review_status == "confirmed" else None,
        metadata=metadata or {},
    )


def _append_unique(facts: list[ExtractedFact], fact: ExtractedFact) -> None:
    key = (fact.category, fact.normalized_value.lower(), fact.certainty)
    for existing in facts:
        existing_key = (existing.category, existing.normalized_value.lower(), existing.certainty)
        if existing_key == key and existing.review_status == "confirmed":
            return
    facts.append(fact)


def _span_matches_transcript(transcript: str, span: EvidenceSpan) -> bool:
    if span.start_char < 0 or span.end_char <= span.start_char:
        return False
    if span.end_char > len(transcript):
        return False
    return transcript[span.start_char:span.end_char].lower() == span.raw_text.lower()


def _has_valid_evidence(transcript: str, fact: ExtractedFact) -> bool:
    if fact.extractor == "doctor":
        return True
    return any(_span_matches_transcript(transcript, span) for span in fact.evidence_spans)


def _validate_evidence_backing(transcript: str, facts: list[ExtractedFact]) -> list[ExtractedFact]:
    """Prevent non-doctor facts without a real transcript span from being confirmed."""
    for fact in facts:
        if _has_valid_evidence(transcript, fact):
            continue
        fact.review_status = "candidate"
        fact.confirmed_by = None
        fact.confidence = min(fact.confidence, 0.49)
        fact.metadata = {
            **(fact.metadata or {}),
            "evidence_validation": "missing_or_invalid_transcript_span",
        }
    return facts


def _legacy_facts(transcript: str, facts: dict[str, Any], sentences: list[dict[str, Any]]) -> list[ExtractedFact]:
    contexts = facts.get("contexts") or {}
    extracted: list[ExtractedFact] = []

    for symptom in facts.get("symptoms") or []:
        value = str(symptom)
        _append_unique(extracted, _make_fact(transcript, sentences, "symptom", value, context=contexts.get(value, "")))

    for vital in facts.get("vitals") or []:
        value = str(vital)
        _append_unique(extracted, _make_fact(transcript, sentences, "vital", value, context=contexts.get(value, ""), extractor="regex"))

    for allergy in facts.get("allergies") or []:
        value = str(allergy)
        _append_unique(extracted, _make_fact(transcript, sentences, "allergy", value, context=contexts.get(value, ""), extractor="regex"))

    for investigation in facts.get("investigations") or []:
        value = str(investigation)
        _append_unique(extracted, _make_fact(transcript, sentences, "investigation", value, context=contexts.get(value, "")))

    for diagnosis in facts.get("diagnoses") or []:
        value = str(diagnosis)
        _append_unique(extracted, _make_fact(transcript, sentences, "diagnosis", value, context=contexts.get(f"dx:{value}", "")))

    for follow_up in facts.get("follow_up") or []:
        value = str(follow_up)
        _append_unique(extracted, _make_fact(transcript, sentences, "follow_up", value, extractor="regex"))

    for medication in facts.get("medications") or []:
        if not isinstance(medication, dict):
            continue
        name = str(medication.get("name") or "").strip()
        if not name:
            continue
        _append_unique(
            extracted,
            _make_fact(
                transcript,
                sentences,
                "medication",
                name,
                context=contexts.get(name, ""),
                extractor="regex",
                metadata={
                    "name": name,
                    "dosage": medication.get("dosage") or medication.get("dose") or "",
                    "frequency": medication.get("frequency") or "",
                    "duration": medication.get("duration") or "",
                },
            ),
        )

    return extracted


def _gliner_candidate_facts(transcript: str, facts: dict[str, Any], sentences: list[dict[str, Any]]) -> list[ExtractedFact]:
    extracted: list[ExtractedFact] = []
    for candidate in facts.get("_gliner_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        score = float(candidate.get("confidence") or candidate.get("score") or 0)
        if score < 0.5:
            continue
        category = str(candidate.get("category") or "").strip()
        if category not in _VALID_CATEGORIES or category == "vital":
            continue
        # Doctor-confirmation gate: every machine-extracted fact starts as a
        # candidate, regardless of model confidence. Only an explicit doctor
        # review (accept/edit) promotes it to confirmed.
        text = str(candidate.get("text") or candidate.get("raw_text") or "").strip()
        if not text or text.lower() not in transcript.lower():
            continue
        _append_unique(
            extracted,
            _make_fact(
                transcript,
                sentences,
                category,
                text,
                raw_text=text,
                extractor="gliner",
                confidence=score,
                review_status="candidate",
                confirmed_by=None,
                metadata={"label": candidate.get("label", ""), "score": score},
            ),
        )
    return extracted


def _scan_nonaffirmed(transcript: str, sentences: list[dict[str, Any]], existing: Iterable[ExtractedFact]) -> list[ExtractedFact]:
    present = {(fact.category, _clean_display_value(fact.normalized_value).lower(), fact.certainty) for fact in existing}
    results: list[ExtractedFact] = []
    term_maps = [("symptom", _SYMPTOM_MAP), ("diagnosis", _DIAGNOSIS_MAP)]

    for i, sentence in enumerate(sentences):
        text = sentence["text"]
        lower = text.lower()
        is_query = bool(_QUESTION_MARK_RE.search(text))
        is_uncertain = bool(_UNCERTAINTY_WORDS.search(text))
        for category, mapping in term_maps:
            for keyword, canonical in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
                match = re.search(rf"(?:^|\b){re.escape(keyword)}(?:\b|$)", lower)
                if not match:
                    continue
                certainty = "affirmed"
                if is_query:
                    certainty = "queried"
                elif is_uncertain:
                    certainty = "uncertain"
                elif _is_negated(lower, match.start(), match.end()):
                    certainty = "negated"
                else:
                    continue

                spans = [_make_span(transcript, sentence, category, canonical, keyword)]
                if certainty == "queried" and i + 1 < len(sentences) and _YES_RE.search(sentences[i + 1]["text"]):
                    answer = sentences[i + 1]
                    spans.append(EvidenceSpan(
                        raw_text=answer["text"],
                        source_sentence=answer["text"],
                        sentence_index=answer["index"],
                        start_char=answer["start"],
                        end_char=answer["end"],
                    ))
                    certainty = "affirmed"

                key = (category, canonical.lower(), certainty)
                if key in present:
                    continue
                fact = _make_fact(
                    transcript,
                    sentences,
                    category,
                    canonical,
                    raw_text=keyword,
                    extractor="rule",
                    confidence=0.7 if certainty != "affirmed" else 0.8,
                    certainty=certainty,
                    review_status="candidate",
                    confirmed_by=None,
                    evidence_spans=spans,
                )
                present.add(key)
                results.append(fact)
                break
    return results


def build_extracted_facts(transcript: str, facts: dict[str, Any]) -> list[ExtractedFact]:
    sentences = _sentence_spans(transcript)
    extracted = _legacy_facts(transcript, facts, sentences)
    for fact in _gliner_candidate_facts(transcript, facts, sentences):
        _append_unique(extracted, fact)
    for fact in _scan_nonaffirmed(transcript, sentences, extracted):
        _append_unique(extracted, fact)
    return _validate_evidence_backing(transcript, extracted)


def review_counts(extracted_facts: list[dict[str, Any]]) -> dict[str, int]:
    """Tally review states from stored fact dicts (memory_state['_extracted_facts']).

    Used by the export gate: FHIR requires zero remaining candidates; prescription
    and investigation orders require at least one confirmed fact.
    """
    counts = {"candidate": 0, "confirmed": 0, "rejected": 0}
    for fact in extracted_facts or []:
        status = fact.get("review_status")
        if status in counts:
            counts[status] += 1
    return counts


def facts_from_non_rejected(extracted_facts: list[ExtractedFact]) -> dict[str, Any]:
    """Like facts_from_confirmed but includes candidate facts too (opt-out workflow).

    In opt-out mode the doctor removes wrong facts; whatever is left (candidate OR
    confirmed) is implicitly approved and should feed SOAP, entities display, and FHIR.
    Only explicitly rejected facts are excluded.
    """
    facts: dict[str, Any] = {
        "symptoms": [],
        "medications": [],
        "vitals": [],
        "allergies": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {},
    }
    med_names: set[str] = set()
    for fact in extracted_facts:
        if isinstance(fact, dict):
            review_status = fact.get("review_status")
            certainty = fact.get("certainty", "affirmed")
            category = fact.get("category", "")
            normalized_value = fact.get("normalized_value", "")
            source_sentence = fact.get("source_sentence", "")
            metadata = fact.get("metadata") or {}
        else:
            review_status = fact.review_status
            certainty = fact.certainty
            category = fact.category
            normalized_value = fact.normalized_value
            source_sentence = fact.source_sentence
            metadata = fact.metadata if hasattr(fact, "metadata") and fact.metadata else {}
        if review_status == "rejected":
            continue
        if category == "medication":
            name = metadata.get("name") or normalized_value
            if name in med_names:
                continue
            med_names.add(str(name))
            facts["medications"].append({
                "name": name,
                "dosage": metadata.get("dosage") or "",
                "frequency": metadata.get("frequency") or "",
                "duration": metadata.get("duration") or "",
            })
        else:
            # Preserve negation/uncertainty in the flat SOAP-facing value — dropping
            # certainty here previously let a denied symptom (e.g. "No vomiting.")
            # render in the SOAP as a plain affirmed one ("...vomiting, cough.").
            display_value = normalized_value
            if certainty == "negated":
                display_value = f"{normalized_value} (denied)"
            elif certainty == "uncertain":
                display_value = f"{normalized_value} (uncertain)"
            plural_key = _CATEGORY_PLURAL.get(category)
            if plural_key and plural_key in facts and display_value not in facts[plural_key]:
                facts[plural_key].append(display_value)
            normalized_value = display_value
        facts["contexts"][normalized_value] = source_sentence
    return facts


def facts_from_confirmed(extracted_facts: list[ExtractedFact]) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "symptoms": [],
        "medications": [],
        "vitals": [],
        "allergies": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {},
    }
    med_names: set[str] = set()
    for fact in extracted_facts:
        # Support both ExtractedFact objects and plain dicts (stored as JSON in memory_state)
        if isinstance(fact, dict):
            review_status = fact.get("review_status")
            certainty = fact.get("certainty")
            category = fact.get("category", "")
            normalized_value = fact.get("normalized_value", "")
            source_sentence = fact.get("source_sentence", "")
            metadata = fact.get("metadata") or {}
        else:
            review_status = fact.review_status
            certainty = fact.certainty
            category = fact.category
            normalized_value = fact.normalized_value
            source_sentence = fact.source_sentence
            metadata = fact.metadata if hasattr(fact, "metadata") and fact.metadata else {}
        if review_status != "confirmed" or certainty != "affirmed":
            continue
        if category == "medication":
            name = metadata.get("name") or normalized_value
            if name in med_names:
                continue
            med_names.add(str(name))
            facts["medications"].append({
                "name": name,
                "dosage": metadata.get("dosage") or "",
                "frequency": metadata.get("frequency") or "",
                "duration": metadata.get("duration") or "",
            })
        else:
            plural_key = _CATEGORY_PLURAL.get(category)
            if plural_key and plural_key in facts and normalized_value not in facts[plural_key]:
                facts[plural_key].append(normalized_value)
        facts["contexts"][normalized_value] = source_sentence
    return facts


def build_soap_evidence(extracted_facts: list[ExtractedFact]) -> dict[str, list[str]]:
    confirmed = [fact for fact in extracted_facts if fact.review_status == "confirmed" and fact.certainty == "affirmed"]
    return {
        "S": [fact.id for fact in confirmed if fact.category in {"symptom", "allergy"}],
        "O": [fact.id for fact in confirmed if fact.category == "vital"],
        "A": [fact.id for fact in confirmed if fact.category == "diagnosis"],
        "P": [fact.id for fact in confirmed if fact.category in {"medication", "investigation", "follow_up"}],
    }


def doctor_fact_from_value(
    *,
    category: str,
    value: str,
    user_id: str,
    metadata: Optional[dict[str, Any]] = None,
) -> ExtractedFact:
    span = EvidenceSpan(
        raw_text=value,
        source_sentence="Doctor-entered correction",
        sentence_index=-1,
        start_char=-1,
        end_char=-1,
    )
    return ExtractedFact(
        id=_stable_id(category, value, user_id, "doctor"),
        category=category,  # type: ignore[arg-type]
        raw_text=value,
        normalized_value=value,
        source_sentence=span.source_sentence,
        sentence_index=-1,
        start_char=-1,
        end_char=-1,
        evidence_spans=[span],
        extractor="doctor",
        confidence=1.0,
        certainty="affirmed",
        review_status="confirmed",
        confirmed_by=user_id,
        metadata=metadata or {},
    )

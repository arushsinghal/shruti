"""Shared patient-history aggregation for the timeline view and the memory assistant.

Both features read the same doctor-confirmed source: `ConsultationSession.clinical_facts`
for sessions matching a patient name under one doctor. Confirmed facts only — this must
never surface candidate/rejected facts, same gate `facts_from_confirmed()` applies to
FHIR export.
"""

from __future__ import annotations

from typing import Any

from app.schemas.consultation import ConsultationSession
from app.services import provenance
from app.storage.repository import SessionRepository

repo = SessionRepository()


def _visit_summary(session: ConsultationSession) -> dict[str, Any]:
    # Build from doctor-confirmed facts only (memory_state['_extracted_facts']),
    # same source FHIR export uses. session.clinical_facts is the flat legacy
    # blob and may still hold candidates awaiting review — falling back to it
    # is only safe for pre-provenance sessions that never had extracted_facts.
    extracted = (session.memory_state or {}).get("_extracted_facts")
    if extracted is not None:
        facts = provenance.facts_from_confirmed(extracted)
    else:
        facts = session.clinical_facts or {}
    soap = session.soap_note or {}
    soap_summary = " ".join(str(soap.get(k, "")) for k in ("S", "O", "A", "P") if soap.get(k))
    return {
        "session_id": session.id,
        "date": session.created_at.isoformat() if session.created_at else "",
        "doctor_name": session.doctor_name or "",
        "specialty": session.specialty or "",
        "symptoms": facts.get("symptoms") or [],
        "medications": _medications_list(facts.get("medications")),
        "vitals": facts.get("vitals") or [],
        "diagnoses": _diagnoses_list(facts.get("diagnoses")),
        "allergies": facts.get("allergies") or [],
        "investigations": facts.get("investigations") or [],
        "follow_up": facts.get("follow_up") or [],
        "soap_summary": soap_summary,
    }


def _medications_list(meds: Any) -> list[dict[str, Any]]:
    """clinical_facts['medications'] is a dict keyed by med name in the live session
    state, but may already be a list in some call sites — normalize both shapes."""
    if isinstance(meds, dict):
        return [{"name": name, **(details or {})} for name, details in meds.items()]
    if isinstance(meds, list):
        return meds
    return []


def _diagnoses_list(diagnoses: Any) -> list[dict[str, Any]]:
    """clinical_facts['diagnoses'] is a flat list of strings (e.g. 'Dengue Fever
    (uncertain)'); the frontend timeline expects {text, display} objects, deduped
    against their '(uncertain)' variant."""
    if not isinstance(diagnoses, list):
        return []
    seen: list[str] = []
    for d in diagnoses:
        base = str(d).replace(" (uncertain)", "").strip()
        if base and base not in seen:
            seen.append(base)
    return [{"text": name, "display": name} for name in seen]


async def get_patient_sessions(user_id: str, patient_name: str) -> list[ConsultationSession]:
    """All of one doctor's sessions for a given patient name, most recent first,
    already scoped to user_id (the doctor) so no cross-doctor leakage is possible."""
    all_sessions = await repo.get_sessions_for_user(user_id)
    normalized = patient_name.strip().lower()
    return [
        s for s in all_sessions
        if (s.patient_name or "").strip().lower() == normalized
    ]


async def get_patient_graph(patient_id: str, requesting_user_id: str) -> dict[str, Any]:
    """Consent-gated, cross-clinic clinical history for one patient — the spine of
    the longitudinal patient graph.

    Aggregates confirmed active medications, allergies, and chronic conditions
    across EVERY clinic on the platform, keyed on the stable patient_id.

    Consent gate (enforced here, structurally, so the graph can never be read
    without policy): a doctor always sees the visits they recorded themselves.
    Visits from OTHER clinics are included only if the patient has cross-clinic
    consent on file. When other-clinic history exists but consent is not yet
    granted, it is withheld and `cross_clinic_history_available` is flagged so the
    UI can prompt the patient for consent (see Phase 3 patient-carried records).
    """
    sessions = await repo.get_sessions_for_patient(patient_id)
    consent = await repo.patient_has_cross_clinic_consent(patient_id)
    uid = str(requesting_user_id)

    own = [s for s in sessions if str(s.user_id) == uid]
    other = [s for s in sessions if str(s.user_id) != uid]
    visible = own + (other if consent else [])

    active_meds: dict[str, dict[str, Any]] = {}
    conditions: dict[str, dict[str, Any]] = {}
    allergies: dict[str, dict[str, Any]] = {}

    for s in visible:
        visit = _visit_summary(s)
        own_clinic = str(s.user_id) == uid
        for med in visit["medications"]:
            key = str(med.get("name", "")).strip().lower()
            if key and key not in active_meds:
                active_meds[key] = {**med, "last_seen": visit["date"], "from_other_clinic": not own_clinic}
        for dx in visit["diagnoses"]:
            text = dx if isinstance(dx, str) else dx.get("text", "")
            key = str(text).strip().lower()
            if key and key not in conditions:
                conditions[key] = {"text": text, "last_seen": visit["date"], "from_other_clinic": not own_clinic}
        for a in visit["allergies"]:
            key = str(a).strip().lower()
            if key and key not in allergies:
                allergies[key] = {"text": a, "last_seen": visit["date"], "from_other_clinic": not own_clinic}

    return {
        "patient_id": patient_id,
        "total_visits_visible": len(visible),
        "own_clinic_visits": len(own),
        "other_clinic_visits": len(other),
        "cross_clinic_consent": consent,
        # True when there is history from other clinics that consent would unlock.
        "cross_clinic_history_available": (len(other) > 0 and not consent),
        "active_medications": list(active_meds.values()),
        "allergies": list(allergies.values()),
        "chronic_conditions": list(conditions.values()),
    }


async def build_all_patients_summary(user_id: str) -> dict[str, Any]:
    """Prompt-ready summary of all confirmed sessions for a doctor, grouped by patient.
    Used by the memory assistant when no patient is scoped (dashboard context)."""
    all_sessions = await repo.get_sessions_for_user(user_id)
    by_patient: dict[str, list[ConsultationSession]] = {}
    for s in all_sessions:
        name = (s.patient_name or "Unknown").strip()
        by_patient.setdefault(name, []).append(s)
    visits = []
    for name, sessions in by_patient.items():
        for s in sessions:
            v = _visit_summary(s)
            v["patient_name"] = name
            visits.append(v)
    visits.sort(key=lambda v: v["date"], reverse=True)
    return {"patient_name": None, "total_visits": len(visits), "visits": visits,
            "active_medications": [], "chronic_conditions": [], "allergies": []}


async def build_patient_timeline(user_id: str, patient_name: str) -> dict[str, Any]:
    """Aggregated view for the timeline UI: all visits plus rolled-up active
    medications, chronic conditions, and allergies across visits."""
    sessions = await get_patient_sessions(user_id, patient_name)
    visits = [_visit_summary(s) for s in sessions]

    active_meds: dict[str, dict[str, Any]] = {}
    conditions: dict[str, dict[str, Any]] = {}
    allergies: set[str] = set()

    for visit in visits:
        for med in visit["medications"]:
            name = str(med.get("name", "")).strip().lower()
            if not name:
                continue
            if name not in active_meds:
                active_meds[name] = {**med, "last_seen": visit["date"]}
        for dx in visit["diagnoses"]:
            text = dx if isinstance(dx, str) else dx.get("text", "")
            key = str(text).strip().lower()
            if key and key not in conditions:
                conditions[key] = {"text": text} if isinstance(dx, str) else dx
        for a in visit["allergies"]:
            allergies.add(a)

    return {
        "patient_name": patient_name,
        "total_visits": len(visits),
        "visits": visits,
        "active_medications": list(active_meds.values()),
        "chronic_conditions": list(conditions.values()),
        "allergies": sorted(allergies),
    }


def format_history_for_prompt(timeline: dict[str, Any], max_visits: int = 25) -> str:
    """De-identified, prompt-ready summary of a patient's visit history.
    Used by the memory assistant (Phase 1: context-stuffing, no vector search) —
    the patient's name is deliberately NOT included; the caller resolves display
    identity in the UI layer after the model responds.
    """
    lines = [f"Patient history: {timeline['total_visits']} confirmed visit(s)."]
    if timeline["allergies"]:
        lines.append(f"Known allergies: {', '.join(timeline['allergies'])}.")
    if timeline["chronic_conditions"]:
        cond_names = [c.get("text", "") for c in timeline["chronic_conditions"]]
        lines.append(f"Chronic conditions on record: {', '.join(cond_names)}.")

    for visit in timeline["visits"][:max_visits]:
        meds = ", ".join(
            f"{m.get('name', '')} {m.get('dosage', '')}".strip()
            for m in visit["medications"]
        ) or "none recorded"
        dx = ", ".join(
            d if isinstance(d, str) else d.get("text", "") for d in visit["diagnoses"]
        ) or "none recorded"
        patient_prefix = f"[{visit['patient_name']}] " if visit.get("patient_name") else ""
        lines.append(
            f"- {patient_prefix}Visit {visit['session_id'][:8]} on {visit['date'][:10]}: "
            f"symptoms: {', '.join(visit['symptoms']) or 'none'}; "
            f"diagnoses: {dx}; medications: {meds}; "
            f"follow-up: {', '.join(visit['follow_up']) or 'none'}."
        )
    return "\n".join(lines)

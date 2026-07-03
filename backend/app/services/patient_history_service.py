"""Shared patient-history aggregation for the timeline view and the memory assistant.

Both features read the same doctor-confirmed source: `ConsultationSession.clinical_facts`
for sessions matching a patient name under one doctor. Confirmed facts only — this must
never surface candidate/rejected facts, same gate `facts_from_confirmed()` applies to
FHIR export.
"""

from __future__ import annotations

from typing import Any

from app.schemas.consultation import ConsultationSession
from app.storage.repository import SessionRepository

repo = SessionRepository()


def _visit_summary(session: ConsultationSession) -> dict[str, Any]:
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
        "diagnoses": facts.get("diagnoses") or [],
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


async def get_patient_sessions(user_id: str, patient_name: str) -> list[ConsultationSession]:
    """All of one doctor's sessions for a given patient name, most recent first,
    already scoped to user_id (the doctor) so no cross-doctor leakage is possible."""
    all_sessions = await repo.get_sessions_for_user(user_id)
    normalized = patient_name.strip().lower()
    return [
        s for s in all_sessions
        if (s.patient_name or "").strip().lower() == normalized
    ]


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
        lines.append(
            f"- Visit {visit['session_id'][:8]} on {visit['date'][:10]}: "
            f"symptoms: {', '.join(visit['symptoms']) or 'none'}; "
            f"diagnoses: {dx}; medications: {meds}; "
            f"follow-up: {', '.join(visit['follow_up']) or 'none'}."
        )
    return "\n".join(lines)

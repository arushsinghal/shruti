"""Doctor fact-review endpoints (the confirmation gate).

The deterministic pipeline in routes_notes.py produces every clinical fact as a
"candidate". The draft SOAP is opt-out: all non-rejected candidates appear
immediately so the doctor reviews the whole note and rejects anything wrong,
rather than confirming each fact one at a time. Explicitly accepting/editing a
fact here flips it to "confirmed" — structured clinical exports (FHIR,
investigation orders) hard-gate on that per-fact "confirmed" status, so nothing
reaches those exports without doctor sign-off, even though the human-readable
draft note shows candidates for review.
"""

from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.schemas.consultation import ExtractedFact, StatusEnum
from app.services import provenance
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.storage.repository import SessionRepository

router = APIRouter()
repo = SessionRepository()
memory = MemoryContextService()
soap_gen = SOAPGeneratorService()


class FactReviewRequest(BaseModel):
    action: str                                # accept | edit | reject
    normalized_value: Optional[str] = None
    edited_value: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AddFactRequest(BaseModel):
    category: str           # symptom | medication | vital | allergy | investigation | diagnosis | follow_up
    normalized_value: str
    source_sentence: str = ""


def _load_facts(session) -> list[ExtractedFact]:
    raw = (session.memory_state or {}).get("_extracted_facts") or []
    facts: list[ExtractedFact] = []
    for item in raw:
        try:
            facts.append(ExtractedFact(**item))
        except Exception:
            continue
    return facts


def _regenerate(session, facts: list[ExtractedFact]) -> dict[str, Any]:
    """Rebuild SOAP + state from non-rejected facts and persist.

    Uses facts_from_non_rejected (opt-out workflow): candidate facts are treated as
    implicitly approved for SOAP and display. Only rejected facts are dropped.
    facts_from_confirmed is still used for FHIR export (requires explicit confirmation).
    """
    non_rejected = provenance.facts_from_non_rejected(facts)
    full_state = memory.resolve_memory([non_rejected])
    soap = soap_gen.generate_soap(full_state)
    fact_dicts = [f.model_dump() for f in facts]
    session.clinical_facts = non_rejected
    session.memory_state = {**full_state, "_extracted_facts": fact_dicts}
    session.soap_note = soap
    return {
        "session_id": session.id,
        "facts": non_rejected,
        "soap": soap,
        "soap_evidence": provenance.build_soap_evidence(facts),
        "extracted_facts": fact_dicts,
        "source": "deterministic",
    }


@router.api_route("/sessions/{session_id}/facts/{fact_id}", methods=["PUT", "PATCH"])
async def review_fact(
    session_id: str,
    fact_id: str,
    body: FactReviewRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Accept / edit / reject a single candidate fact, then regenerate SOAP."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    facts = _load_facts(session)
    target = next((f for f in facts if f.id == fact_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Fact not found")

    if body.action == "reject":
        target.review_status = "rejected"
        target.confirmed_by = None
    elif body.action == "edit":
        new_value = body.normalized_value or body.edited_value
        if not new_value:
            raise HTTPException(status_code=400, detail="edit requires normalized_value")
        target.normalized_value = new_value
        target.raw_text = new_value
        target.extractor = "doctor"
        target.certainty = "affirmed"
        target.review_status = "confirmed"
        target.confirmed_by = user_id
        if body.metadata:
            target.metadata = {**target.metadata, **body.metadata}
        elif target.category == "medication":
            target.metadata = {**target.metadata, "name": new_value}
    elif body.action == "accept":
        target.review_status = "confirmed"
        target.confirmed_by = user_id
    else:
        raise HTTPException(status_code=400, detail="Unsupported review action")

    response = _regenerate(session, facts)
    await repo.update_session(session)
    return response


@router.post("/sessions/{session_id}/facts")
async def add_fact(
    session_id: str,
    body: AddFactRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Doctor manually adds a clinical fact that the extractor missed."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    facts = _load_facts(session)
    new_fact = ExtractedFact(
        id=str(uuid4()),
        category=body.category,
        raw_text=body.normalized_value,
        normalized_value=body.normalized_value,
        source_sentence=body.source_sentence,
        extractor="doctor",
        confidence=1.0,
        certainty="affirmed",
        review_status="confirmed",
        confirmed_by=user_id,
    )
    facts.append(new_fact)
    response = _regenerate(session, facts)
    await repo.update_session(session)
    return response


@router.post("/sessions/{session_id}/facts/finalize")
async def finalize_facts(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Confirm every remaining affirmed candidate in one action (bulk accept)."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    facts = _load_facts(session)
    confirmed = 0
    for fact in facts:
        if fact.review_status == "candidate" and fact.certainty == "affirmed":
            fact.review_status = "confirmed"
            fact.confirmed_by = user_id
            confirmed += 1

    response = _regenerate(session, facts)
    session.status = StatusEnum.complete
    await repo.update_session(session)
    response["confirmed"] = confirmed
    return response

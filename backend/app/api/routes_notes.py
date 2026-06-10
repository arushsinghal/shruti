import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.consultation import StatusEnum
from app.storage.repository import SessionRepository
from app.services.clinical_extractor import ClinicalExtractorService
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.services.cds_engine import CDSEngineService
from app.services.fhir_mapper import FHIRMapperService

logger = logging.getLogger(__name__)

router = APIRouter()
repo = SessionRepository()
extractor = ClinicalExtractorService()
memory = MemoryContextService()
soap_gen = SOAPGeneratorService()
cds_engine = CDSEngineService()
fhir_svc = FHIRMapperService()

class ProcessClinicalResponse(BaseModel):
    facts: dict[str, Any]
    state: dict[str, Any]
    soap: dict[str, Any]
    cds: list[dict[str, Any]]
    source: str = "local"


def _run_local_pipeline(transcript: str) -> tuple[dict, dict, dict, list]:
    """Deterministic local pipeline — always succeeds."""
    facts = extractor.extract(transcript)
    state = memory.resolve_memory([facts])
    soap_note = soap_gen.generate_soap(state)
    cds_suggestions = cds_engine.generate_cds(state)
    return facts, state, soap_note, cds_suggestions


@router.post("/sessions/{session_id}/process-clinical", response_model=ProcessClinicalResponse)
async def process_clinical(session_id: str):
    """Runs multilingual clinical NLP pipeline on transcribed consultation. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.transcript:
        raise HTTPException(status_code=400, detail="No transcript available for this session")

    try:
        facts, state, soap_note, cds_suggestions = _run_local_pipeline(session.transcript)
    except Exception as e:
        logger.error("Local pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Clinical processing error: {e}")

    session.clinical_facts = facts
    session.memory_state = state
    session.soap_note = soap_note
    session.cds_suggestions = cds_suggestions
    session.status = StatusEnum.complete

    await repo.update_session(session)

    return ProcessClinicalResponse(
        facts=facts,
        state=state,
        soap=soap_note,
        cds=cds_suggestions,
        source="local",
    )


@router.get("/sessions/{session_id}/fhir")
async def get_fhir_bundle(session_id: str):
    """Exports resolved clinical state as a standardized HL7 FHIR R4 JSON Bundle. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.memory_state:
        raise HTTPException(status_code=400, detail="Clinical facts have not been processed yet.")

    patient_name = session.patient_name or "Anonymous Patient"
    bundle = fhir_svc.generate_fhir_bundle(session_id, patient_name, session.memory_state)

    return bundle

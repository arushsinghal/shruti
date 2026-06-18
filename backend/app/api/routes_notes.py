import logging
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.routes_auth import get_current_user

from app.schemas.consultation import StatusEnum, ModeEnum
from app.storage.repository import SessionRepository
from app.services.clinical_extractor import ClinicalExtractorService
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.services.cds_engine import CDSEngineService
from app.services.fhir_mapper import FHIRMapperService
from app.services.fir_generator import FIRGeneratorService
from app.services.legal_generator import LegalGeneratorService
from app.services.ollama_extractor import OllamaExtractorService, merge_with_keywords

logger = logging.getLogger(__name__)

router = APIRouter()
repo = SessionRepository()
extractor = ClinicalExtractorService()
memory = MemoryContextService()
soap_gen = SOAPGeneratorService()
cds_engine = CDSEngineService()
fhir_svc = FHIRMapperService()
fir_gen = FIRGeneratorService()
legal_gen = LegalGeneratorService()
ollama = OllamaExtractorService()

class ProcessClinicalResponse(BaseModel):
    facts: dict[str, Any]
    state: dict[str, Any]
    soap: dict[str, Any]
    cds: list[dict[str, Any]]
    source: str = "local"


def _run_health_pipeline(transcript: str) -> tuple[dict, dict, dict, list]:
    """Clinical pipeline: keywords + optional Ollama enrichment → SOAP + CDS."""
    # Layer 1: deterministic keyword + fuzzy extraction (always runs)
    facts = extractor.extract(transcript)

    # Layer 2: Ollama semantic enrichment (runs only if Ollama is available)
    if ollama.is_available():
        try:
            ollama_facts = ollama.extract(transcript)
            facts = merge_with_keywords(facts, ollama_facts)
            logger.info("Ollama enrichment merged. Symptoms: %d, Diagnoses: %d",
                        len(facts["symptoms"]), len(facts["diagnoses"]))
        except Exception as e:
            logger.warning("Ollama enrichment skipped (non-fatal): %s", e)

    state = memory.resolve_memory([facts])
    soap_note = soap_gen.generate_soap(state)
    cds_suggestions = cds_engine.generate_cds(state)
    return facts, state, soap_note, cds_suggestions


def _run_fir_pipeline(transcript: str, session_id: str) -> tuple[dict, dict, dict, list]:
    """FIR document generation pipeline."""
    fir_doc = fir_gen.generate_fir(transcript, session_id)
    facts: dict = {"transcript_length": len(transcript), "offences": fir_doc.get("offences_alleged", [])}
    state: dict = {"mode": "government", "location": fir_doc.get("place_of_incident", ""), "complainant": fir_doc.get("complainant_name", "")}
    return facts, state, fir_doc, []


def _run_legal_pipeline(transcript: str, session_id: str) -> tuple[dict, dict, dict, list]:
    """Legal document generation pipeline."""
    legal_doc = legal_gen.generate_legal_doc(transcript, session_id)
    facts: dict = {"transcript_length": len(transcript), "sections_cited": legal_doc.get("legal_sections_cited", [])}
    state: dict = {"mode": "legal", "document_type": legal_doc.get("document_type", ""), "parties": [legal_doc.get("petitioner", ""), legal_doc.get("respondent", "")]}
    return facts, state, legal_doc, []


@router.post("/sessions/{session_id}/process-clinical", response_model=ProcessClinicalResponse)
async def process_clinical(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Runs Lipi NLP pipeline on transcription. Branches by session mode (health/government/legal/general). Research prototype only — output requires expert review."""
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.cloud_ai_consent:
        raise HTTPException(
            status_code=403,
            detail="Patient consent required before clinical processing. Confirm consent first.",
        )

    if not session.transcript:
        raise HTTPException(status_code=400, detail="No transcript available for this session")

    mode = session.mode

    try:
        if mode == ModeEnum.government:
            facts, state, doc, cds_suggestions = _run_fir_pipeline(session.transcript, session_id)
            source = "fir_engine"
        elif mode == ModeEnum.legal:
            facts, state, doc, cds_suggestions = _run_legal_pipeline(session.transcript, session_id)
            source = "legal_engine"
        else:
            # health or general — use clinical pipeline
            facts, state, doc, cds_suggestions = _run_health_pipeline(session.transcript)
            source = "local"
    except Exception as e:
        logger.error("Processing pipeline failed for mode=%s: %s", mode, e)
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

    session.clinical_facts = facts
    session.memory_state = state
    session.soap_note = doc
    session.cds_suggestions = cds_suggestions
    session.status = StatusEnum.complete

    await repo.update_session(session)

    # Delete raw audio after transcript + SOAP are safely stored (DPDPA retention policy).
    # Transcript text, diarized segments, SOAP note, and CDS remain in the DB.
    if session.audio_file_path:
        try:
            Path(session.audio_file_path).unlink(missing_ok=True)
            logger.info("Deleted audio file after processing: %s", session.audio_file_path)
        except Exception as exc:
            logger.warning("Audio file deletion failed (non-fatal): %s", exc)
        session.audio_file_path = None
        await repo.update_session(session)

    return ProcessClinicalResponse(
        facts=facts,
        state=state,
        soap=doc,
        cds=cds_suggestions,
        source=source,
    )


@router.get("/sessions/{session_id}/fhir")
async def get_fhir_bundle(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Exports resolved clinical state as a standardized HL7 FHIR R4 JSON Bundle. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.memory_state:
        raise HTTPException(status_code=400, detail="Clinical facts have not been processed yet.")

    patient_name = session.patient_name or "Anonymous Patient"
    bundle = fhir_svc.generate_fhir_bundle(session_id, patient_name, session.memory_state)

    return bundle

import asyncio
import json
import difflib
import uuid
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.routes_auth import get_current_user
from app.services.phi_scrubber import PHIScrubberService
from app.storage.db import db_connect

phi_scrubber = PHIScrubberService()

class SOAPFeedbackRequest(BaseModel):
    status: str
    original_soap: dict
    final_soap: dict
    categories: List[str]

class SOAPFeedbackResponse(BaseModel):
    success: bool
    feedback_id: int
    status: str
    categories: List[str]
    timestamp: str

ALLOWED_CATEGORIES = {
    "missing_symptom",
    "wrong_medication",
    "wrong_dosage",
    "formatting_issue",
    "language_issue",
    "diagnosis_issue",
    "hallucinated_fact",
    "other",
}

from app.schemas.consultation import StatusEnum, ModeEnum
from app.storage.repository import SessionRepository
from app.services.clinical_extractor import ClinicalExtractorService
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.services.cds_engine import CDSEngineService
from app.services.fhir_mapper import FHIRMapperService
from app.services.investigation_order_renderer import render_investigation_order_html
from app.services import provenance
from app.services.learning_service import learning_service
from app.services.memory_service import get_patient_memory
from app.services.patient_history_service import get_patient_graph, build_patient_timeline
from app.services.llm_client import LLMClientService

logger = logging.getLogger(__name__)

router = APIRouter()
repo = SessionRepository()
extractor = ClinicalExtractorService()
memory = MemoryContextService()
soap_gen = SOAPGeneratorService()
cds_engine = CDSEngineService()
fhir_svc = FHIRMapperService()
llm_client = LLMClientService()

# Task 31: per-session write locks — prevents concurrent process_clinical on the same session
_session_locks: dict[str, asyncio.Lock] = {}


def _get_session_lock(session_id: str) -> asyncio.Lock:
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]

class ProcessClinicalResponse(BaseModel):
    facts: dict[str, Any]
    state: dict[str, Any]
    soap: dict[str, Any]
    cds: list[dict[str, Any]]
    source: str = "local"
    # Per-fact provenance for the doctor confirmation gate (health mode).
    # Every fact starts as a "candidate"; SOAP/exports use confirmed facts only.
    extracted_facts: list[dict[str, Any]] = []
    soap_evidence: dict[str, list[str]] = {}


def _build_health_provenance(transcript: str, facts: dict) -> tuple[list[dict], dict, dict, dict]:
    """Convert deterministic extraction into reviewable candidate facts and SOAP.

    Returns (extracted_fact_dicts, resolved_state, initial_soap, soap_evidence).
    Uses opt-out model: all candidate facts appear in SOAP by default; doctor
    removes wrong ones on the review page rather than approving each individually.
    """
    extracted = provenance.build_extracted_facts(transcript, facts)
    extracted_dicts = [f.model_dump() for f in extracted]
    non_rejected = provenance.facts_from_non_rejected(extracted)
    resolved_state = memory.resolve_memory([non_rejected])
    initial_soap = soap_gen.generate_soap(resolved_state)
    soap_evidence = provenance.build_soap_evidence(extracted)
    return extracted_dicts, resolved_state, initial_soap, soap_evidence


def _run_health_pipeline(transcript: str, prior_history: dict | None = None) -> tuple[dict, dict, dict, list]:
    """Clinical pipeline: deterministic extraction → memory resolution → SOAP + CDS.

    Zero-LLM by policy. No generative model participates in transcript → facts → SOAP.
    Extraction is fully deterministic (keyword + fuzzy + regex via ClinicalExtractorService).

    prior_history, if given, is the consent-gated cross-clinic patient graph (see
    patient_history_service.get_patient_graph) — it only ever reaches the CDS engine,
    never SOAP generation, so a cross-visit safety alert can never be mistaken for
    something the patient said today.
    """
    facts = extractor.extract(transcript)
    state = memory.resolve_memory([facts])
    soap_note = soap_gen.generate_soap(state)
    cds_suggestions = cds_engine.generate_cds(state, prior_history=prior_history)
    return facts, state, soap_note, cds_suggestions


@router.post("/sessions/{session_id}/process-clinical", response_model=ProcessClinicalResponse)
async def process_clinical(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Runs Lipi NLP pipeline on transcription. Branches by session mode (health/general). Research prototype only — output requires expert review."""
    lock = _get_session_lock(session_id)
    if lock.locked():
        raise HTTPException(status_code=409, detail="Processing already in progress for this session")
    async with lock:
        return await _process_clinical_inner(session_id, current_user)


async def _process_clinical_inner(session_id: str, current_user: dict):
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.cloud_ai_consent:
        raise HTTPException(
            status_code=403,
            detail="Patient consent required before clinical processing. Confirm consent first.",
        )

    if not session.transcript:
        raise HTTPException(
            status_code=400,
            detail="No transcript yet. Use 'Direct Text' to paste the consultation notes, or re-record audio.",
        )

    mode = session.mode
    user_id_str = str(current_user["id"])
    extracted_dicts: list[dict[str, Any]] = []
    soap_evidence: dict[str, list[str]] = {}

    # Cross-visit patient graph for CDS (Phase 2) — consent-gated, resolved by
    # patient_id so it spans every clinic on the platform, not just this doctor's
    # own sessions. Non-fatal: a failure here must never block the consultation.
    prior_history: dict | None = None
    if session.patient_id and mode == ModeEnum.health:
        try:
            prior_history = await get_patient_graph(session.patient_id, user_id_str)
        except Exception as exc:
            logger.warning("Cross-visit patient graph fetch failed (non-fatal): %s", exc)

    try:
        # health or general — deterministic clinical pipeline
        facts, full_state, doc, cds_suggestions = _run_health_pipeline(session.transcript, prior_history)
        source = "local"
        state = full_state
        if mode == ModeEnum.health:
            # Opt-out review model: the draft SOAP is populated immediately from
            # non-rejected candidates (negated/uncertain facts keep a visible
            # certainty marker, never rendered as if affirmed) so the doctor
            # reviews the whole note and removes anything wrong before signing.
            # Structured export (FHIR, investigation orders) still hard-gates on
            # per-fact "confirmed" status — see routes_fact_review.py.
            extracted_dicts, _, draft_soap, soap_evidence = _build_health_provenance(
                session.transcript, facts
            )
            doc = draft_soap
            state = {**full_state, "_extracted_facts": extracted_dicts}
    except Exception as e:
        logger.error("Processing pipeline failed for mode=%s: %s", mode, e)
        raise HTTPException(status_code=500, detail="Clinical processing failed. Please try again.")

    # Memory-SOAP separation: fetch prior patient history AFTER building current-visit
    # state so it never merges into SOAP, CDS, or investigation orders.
    # prior_context is stored for UI display only — never touches SOAP generation paths.
    # Non-critical: failure here must never crash the clinical pipeline.
    if session.patient_name and mode == ModeEnum.health:
        try:
            prior_ctx = await get_patient_memory(
                session.patient_name, user_id_str, confirmed_only=True
            )
            if prior_ctx:
                state = {**state, "prior_context": prior_ctx}
        except Exception as exc:
            logger.warning("Prior context fetch failed (non-fatal): %s", exc)

    session.clinical_facts = facts
    session.memory_state = state
    session.soap_note = doc
    session.cds_suggestions = cds_suggestions
    session.status = StatusEnum.complete

    await repo.update_session(session)

    # Task 34: audit PHI access
    await repo.log_audit(session_id, user_id_str, "clinical_processing", "process_clinical")

    # Task 28: auto-generate assistant tasks on consultation complete
    await _auto_create_tasks(session_id, user_id_str, facts)
    await _write_billing_record(session_id, user_id_str)

    # Lab dispatch and follow-up are sent ONLY after doctor signs (routes_public.py:doctor_sign_and_send).
    # Sending them here (at consultation end, before review/sign) means the patient gets an
    # unreviewed note. Removed — do not re-add here.

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
        extracted_facts=extracted_dicts,
        soap_evidence=soap_evidence,
    )


async def _write_billing_record(session_id: str, user_id: str) -> None:
    """Write a per-consultation fee record to consultation_billing — distinct from
    billing_records, which tracks Lipi's own SaaS/plan billing. `id` is an
    auto-increment integer PK — never supply a UUID for it.
    """
    from app.utils.config import settings
    amount = settings.consultation_fee_rupees or 0
    if amount <= 0:
        return
    try:
        async with db_connect() as db:
            async with db.execute(
                "SELECT 1 FROM consultation_billing WHERE session_id = ?", (session_id,)
            ) as cur:
                if await cur.fetchone():
                    return
            await db.execute(
                "INSERT INTO consultation_billing (session_id, user_id, amount, currency, notes, created_at) "
                "VALUES (?, ?, ?, 'INR', 'Web consultation', ?)",
                (session_id, user_id, amount, datetime.utcnow()),
            )
            await db.commit()
    except Exception as exc:
        logger.warning("Billing record write failed: %s", exc)


async def _auto_create_tasks(session_id: str, user_id: str, facts: dict) -> None:
    """Task 28: create assistant_tasks rows based on what the pipeline extracted."""
    now = datetime.utcnow().isoformat()
    tasks_to_create: list[tuple] = []

    investigations = facts.get("investigations") or []
    if investigations:
        titles = ", ".join(str(i) for i in investigations[:3])
        suffix = f" (+{len(investigations)-3} more)" if len(investigations) > 3 else ""
        tasks_to_create.append((
            str(uuid.uuid4()), session_id, user_id, "order_investigations",
            f"Order investigations: {titles}{suffix}", now,
        ))

    follow_up = facts.get("follow_up")
    if follow_up:
        follow_up_text = follow_up[0] if isinstance(follow_up, list) else str(follow_up)
        tasks_to_create.append((
            str(uuid.uuid4()), session_id, user_id, "follow_up",
            f"Schedule follow-up: {follow_up_text}", now,
        ))

    allergies = facts.get("allergies") or []
    if allergies:
        allergy_text = ", ".join(str(a) for a in allergies[:2])
        tasks_to_create.append((
            str(uuid.uuid4()), session_id, user_id, "document_allergy",
            f"Document allergy in chart: {allergy_text}", now,
        ))

    tasks_to_create.append((
        str(uuid.uuid4()), session_id, user_id, "review_prescription",
        "Review and share prescription with patient", now,
    ))

    if not tasks_to_create:
        return

    async with db_connect() as db:
        for row in tasks_to_create:
            await db.execute(
                "INSERT INTO assistant_tasks (id, session_id, user_id, task_type, title, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'open', ?) "
                "ON CONFLICT (id) DO NOTHING",
                row,
            )
        await db.commit()


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

    extracted = session.memory_state.get("_extracted_facts")
    patient_name = session.patient_name or "Anonymous Patient"

    # Confirmation gate: if any facts are still pending doctor review, block export.
    # Doctor must accept or reject every candidate via /facts/{id} or /facts/finalize
    # before a FHIR bundle can be generated.
    if extracted is not None:
        unconfirmed = [f for f in extracted if f.get("review_status") == "candidate"]
        if unconfirmed:
            raise HTTPException(
                status_code=409,
                detail=f"{len(unconfirmed)} fact(s) pending doctor review. Confirm or reject all facts before exporting.",
            )

    # Build FHIR state from confirmed (non-rejected) facts.
    if extracted is not None:
        non_rejected = provenance.facts_from_non_rejected(extracted)
        state_for_fhir = memory.resolve_memory([non_rejected])
    else:
        state_for_fhir = session.memory_state

    bundle = fhir_svc.generate_fhir_bundle(session_id, patient_name, state_for_fhir)

    return bundle


@router.get("/sessions/{session_id}/investigation-order")
async def get_investigation_order(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Returns a printable HTML investigation order for the session.
    Only includes investigations already in the doctor-approved memory state.
    """
    from fastapi.responses import HTMLResponse
    user_id = str(current_user["id"])
    try:
        html = await render_investigation_order_html(session_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Investigation order generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate investigation order: {e}")
    return HTMLResponse(content=html)


class AssistantMessageTurn(BaseModel):
    role: str
    text: str


class AssistantMessageRequest(BaseModel):
    message: str
    history: List[AssistantMessageTurn] = []


class AssistantActionItem(BaseModel):
    action: str
    to_doctor: str = ""
    to_specialty: str = ""
    reason: str = ""
    urgency: str = "routine"
    policy_number: str = ""
    insurer_name: str = ""
    tpa_name: str = ""
    query_type: str = ""
    answer: str = ""


class AssistantActionResponse(BaseModel):
    actions: List[AssistantActionItem] = []
    clarifying_question: str = ""


def _slice_timeline_for_query(timeline: dict, query_type: str) -> dict:
    """Pulls only the piece of the patient timeline relevant to the asked
    question, so the narration prompt sees just what it needs — not the
    doctor's entire visit history for every question."""
    if query_type == "allergies":
        return {"allergies": timeline.get("allergies", [])}
    if query_type == "medications":
        return {"active_medications": timeline.get("active_medications", [])}
    if query_type == "chronic_conditions":
        return {"chronic_conditions": timeline.get("chronic_conditions", [])}
    if query_type == "bp_trend":
        return {
            "visits": [
                {"date": v.get("date"), "vitals": v.get("vitals")}
                for v in (timeline.get("visits") or [])
            ]
        }
    return {
        "total_visits": timeline.get("total_visits"),
        "active_medications": timeline.get("active_medications"),
        "chronic_conditions": timeline.get("chronic_conditions"),
        "allergies": timeline.get("allergies"),
    }


@router.post("/sessions/{session_id}/assistant", response_model=AssistantActionResponse)
async def classify_assistant_action(
    session_id: str,
    body: AssistantMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    """Maps a doctor's natural-language instruction (e.g. "fill the insurance
    form for me" or "has this patient's allergy status changed") to zero or
    more of the existing actions and extracts any parameters explicitly
    stated in the message or recent history. Never generates clinical
    content — classification only, plus (for patient_info) narration of
    already-confirmed history that never introduces a new fact. Document
    actions (prescription, investigation-order, referral, tpa-claim) still
    run through the same confirmation-gated endpoints the equivalent UI
    buttons use, so the doctor confirmation gate is never bypassed here."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    history = [{"role": t.role, "text": t.text} for t in body.history]
    result = llm_client.classify_action_intent(body.message, history=history)

    actions = result.get("actions") or []
    for item in actions:
        if item.get("action") == "patient_info" and session.patient_name:
            timeline = await build_patient_timeline(user_id, session.patient_name)
            query_type = item.get("query_type") or "summary"
            data_slice = _slice_timeline_for_query(timeline, query_type)
            item["answer"] = llm_client.narrate_patient_query(query_type, data_slice)

    return AssistantActionResponse(
        actions=[AssistantActionItem(**a) for a in actions],
        clarifying_question=result.get("clarifying_question", ""),
    )


@router.post("/sessions/{session_id}/feedback", response_model=SOAPFeedbackResponse)
async def post_soap_feedback(
    session_id: str,
    body: SOAPFeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submits doctor feedback and edit delta on the generated SOAP note."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if body.status not in ("accept", "edit", "reject"):
        raise HTTPException(status_code=400, detail="Invalid feedback status")
        
    for cat in body.categories:
        if cat not in ALLOWED_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category: {cat}")
            
    # Serialize original and final soap notes stably
    original_str = json.dumps(body.original_soap, sort_keys=True, indent=2)
    final_str = json.dumps(body.final_soap, sort_keys=True, indent=2)
    
    # Calculate unified diff
    diff_lines = list(difflib.unified_diff(
        original_str.splitlines(),
        final_str.splitlines(),
        fromfile='original_soap.json',
        tofile='final_soap.json',
        lineterm=''
    ))
    delta = "\n".join(diff_lines)
    
    # Scrub PHI
    phi_scrubbed_original = phi_scrubber.scrub(original_str)
    phi_scrubbed_final = phi_scrubber.scrub(final_str)
    phi_scrubbed_delta = phi_scrubber.scrub(delta)
    
    timestamp = datetime.utcnow().isoformat()
    
    categories_json = json.dumps(body.categories)
    
    feedback_id = await repo.save_feedback(
        session_id=session_id,
        user_id=user_id,
        status=body.status,
        original_soap=original_str,
        final_soap=final_str,
        delta=delta,
        phi_scrubbed_original_soap=phi_scrubbed_original,
        phi_scrubbed_final_soap=phi_scrubbed_final,
        phi_scrubbed_delta=phi_scrubbed_delta,
        categories=categories_json,
        timestamp=timestamp,
    )
    
    # Flywheel: if doctor edited the SOAP (not just accepted it), infer lexicon
    # corrections from the diff. "hallucinated_fact" category → false positives.
    if body.status == "edit" and diff_lines:
        if "hallucinated_fact" in body.categories:
            # Extract removed lines from the diff as false-positive signals
            removed = [l[1:].strip() for l in diff_lines if l.startswith("-") and not l.startswith("---")]
            clinic_id = str(current_user["clinic_id"]) if current_user.get("clinic_id") else None
            for term in removed:
                if term and len(term) > 2:
                    await learning_service.record_false_positive(
                        user_id=user_id,
                        surface_form=term[:200],
                        field="soap_section",
                        clinic_id=clinic_id,
                    )

    return SOAPFeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        status=body.status,
        categories=body.categories,
        timestamp=timestamp,
    )

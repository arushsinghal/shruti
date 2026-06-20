import hashlib
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from app.schemas.consultation import ConsultationSession, CreateSessionRequest, ModeEnum
from app.storage.repository import SessionRepository
from app.api.routes_auth import get_current_user

router = APIRouter()
repo = SessionRepository()


class GrantConsentRequest(BaseModel):
    consent_mode: str = "verbal"
    consent_text_version: str = "v1"


@router.post("/sessions", response_model=ConsultationSession, status_code=201)
async def create_session(
    body: CreateSessionRequest = CreateSessionRequest(),
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Initializes a new clinical consultation session. Research prototype only — output requires physician review."""
    return await repo.create_session(
        user_id=str(current_user["id"]),
        patient_name=body.patient_name,
        doctor_name=body.doctor_name,
        abha_number=body.abha_number,
        pmjay_beneficiary=body.pmjay_beneficiary,
        cloud_ai_consent=body.cloud_ai_consent,
        mode=body.mode,
    )


@router.get("/sessions", response_model=list[ConsultationSession])
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> list[ConsultationSession]:
    """Retrieves metadata of recent consultation sessions for deployment monitoring. Research prototype only — output requires physician review."""
    # TODO: push limit/offset into the SQL query (repository.list_sessions) to avoid
    # loading all rows into memory. Current approach slices in Python, which is safe for
    # early deployments (<500 sessions) but becomes a full-table scan as volume grows.
    # Next step: add LIMIT/OFFSET to the SELECT in repository.py and thread the params through.
    sessions = await repo.get_sessions_for_user(str(current_user["id"]))
    return sessions[offset : offset + limit]


@router.get("/sessions/{session_id}", response_model=ConsultationSession)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Retrieves a single consultation session metadata by ID. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id, str(current_user["id"]))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}/consent", response_model=ConsultationSession)
async def grant_consent(
    session_id: str,
    request: Request,
    body: GrantConsentRequest = GrantConsentRequest(),
    current_user: dict = Depends(get_current_user),
) -> ConsultationSession:
    """Records that the doctor has confirmed patient consent before this session's audio upload.
    Must be called before audio upload or clinical processing are permitted."""
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.cloud_ai_consent = True
    await repo.update_session(session)

    # Capture Consent Audit Logs
    timestamp = datetime.utcnow().isoformat()
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    # Hashing payload
    payload = {
        "consent_mode": body.consent_mode,
        "consent_text_version": body.consent_text_version,
        "session_id": session_id,
        "timestamp": timestamp,
        "user_id": user_id,
    }
    canonical_payload_json = json.dumps(payload, sort_keys=True)
    consent_hash = hashlib.sha256(canonical_payload_json.encode("utf-8")).hexdigest()

    await repo.log_consent(
        session_id=session_id,
        user_id=user_id,
        consent_mode=body.consent_mode,
        consent_text_version=body.consent_text_version,
        consent_payload_json=canonical_payload_json,
        consent_hash=consent_hash,
        timestamp=timestamp,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    reloaded_session = await repo.get_session(session_id, user_id)
    return reloaded_session or session



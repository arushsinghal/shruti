from fastapi import APIRouter, HTTPException

from app.schemas.consultation import ConsultationSession, CreateSessionRequest
from app.storage.repository import SessionRepository

router = APIRouter()
repo = SessionRepository()


@router.post("/sessions", response_model=ConsultationSession, status_code=201)
async def create_session(body: CreateSessionRequest = CreateSessionRequest()) -> ConsultationSession:
    """Initializes a new clinical consultation session. Research prototype only — output requires physician review."""
    return await repo.create_session(
        patient_name=body.patient_name,
        doctor_name=body.doctor_name,
        cloud_ai_consent=body.cloud_ai_consent,
    )


@router.get("/sessions", response_model=list[ConsultationSession])
async def list_sessions() -> list[ConsultationSession]:
    """Retrieves metadata of recent consultation sessions for deployment monitoring. Research prototype only — output requires physician review."""
    return await repo.list_sessions()


@router.get("/sessions/{session_id}", response_model=ConsultationSession)
async def get_session(session_id: str) -> ConsultationSession:
    """Retrieves a single consultation session metadata by ID. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


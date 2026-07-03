from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.services.clinical_memory_service import ClinicalMemoryError, query as memory_query

router = APIRouter()


class AssistantQueryRequest(BaseModel):
    question: str
    patient_name: str


@router.post("/assistant/query")
async def query_clinical_memory(
    body: AssistantQueryRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Ask the memory assistant about one patient's own confirmed visit history.
    Phase 1: single-patient scope only, no cross-patient search yet."""
    try:
        return await memory_query(
            user_id=str(current_user["id"]),
            doctor_name=current_user.get("full_name", ""),
            patient_name=body.patient_name,
            question=body.question,
        )
    except ClinicalMemoryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

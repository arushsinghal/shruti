from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    created = "created"
    audio_uploaded = "audio_uploaded"
    transcribed = "transcribed"
    extracted = "extracted"
    memory_resolved = "memory_resolved"
    soap_ready = "soap_ready"
    complete = "complete"


class ConsultationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    cloud_ai_consent: bool = False
    status: StatusEnum = StatusEnum.created
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    diarized_transcript: Optional[str] = None  # LLM-formatted Doctor/Patient dialogue
    clinical_facts: Optional[dict[str, Any]] = None
    memory_state: Optional[dict[str, Any]] = None
    soap_note: Optional[dict[str, Any]] = None
    cds_suggestions: Optional[list[dict[str, Any]]] = None


class CreateSessionRequest(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    cloud_ai_consent: bool = False

from __future__ import annotations

from datetime import datetime, timezone
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


class ModeEnum(str, Enum):
    health = "health"          # Doctor SOAP notes
    government = "government"  # Police FIR reports
    legal = "legal"            # Legal proceedings / affidavits
    general = "general"        # General transcription


class ConsultationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cloud_ai_consent: bool = False
    status: StatusEnum = StatusEnum.created
    mode: ModeEnum = ModeEnum.health
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    diarized_transcript: Optional[list[dict[str, Any]]] = None  # Speaker-labelled segments from Sarvam Batch ASR
    clinical_facts: Optional[dict[str, Any]] = None
    memory_state: Optional[dict[str, Any]] = None
    soap_note: Optional[dict[str, Any]] = None
    cds_suggestions: Optional[list[dict[str, Any]]] = None
    user_id: Optional[str] = None


class CreateSessionRequest(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    cloud_ai_consent: bool = False
    mode: ModeEnum = ModeEnum.health

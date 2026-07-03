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


class ConsentLogResponse(BaseModel):
    consent_mode: str
    consent_text_version: str
    consent_hash: str
    timestamp: str


class EvidenceSpan(BaseModel):
    """A single transcript span that backs an extracted fact.

    Every non-doctor fact must be traceable to a literal span of the transcript
    ("no proof → no fact"). start_char/end_char are offsets into the transcript;
    a value of -1 marks a doctor-entered correction with no transcript origin.
    """
    raw_text: str
    source_sentence: str
    sentence_index: int = -1
    start_char: int = -1
    end_char: int = -1


class ExtractedFact(BaseModel):
    """A deterministically-extracted clinical fact with provenance and review state.

    Defaults to review_status="candidate"/confirmed_by=None: NOTHING is treated as
    clinician-confirmed until a doctor explicitly accepts/edits it. Clinical exports
    (FHIR, prescription, investigation order) consume only confirmed+affirmed facts.
    """
    id: str
    category: str            # symptom | medication | vital | allergy | investigation | diagnosis | follow_up
    raw_text: str
    normalized_value: str
    source_sentence: str = ""
    sentence_index: int = -1
    start_char: int = -1
    end_char: int = -1
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    extractor: str = "rule"  # rule | regex | gliner | doctor | deterministic
    confidence: float = 0.0
    certainty: str = "affirmed"      # affirmed | negated | uncertain | queried
    review_status: str = "candidate"  # candidate | confirmed | rejected
    confirmed_by: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsultationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    abha_number: Optional[str] = None
    pmjay_beneficiary: bool = False
    specialty: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_age: Optional[str] = None
    patient_sex: Optional[str] = None
    patient_id: Optional[str] = None
    initiated_by: str = "doctor"
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
    consent_log: Optional[ConsentLogResponse] = None


class CreateSessionRequest(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    abha_number: Optional[str] = None
    pmjay_beneficiary: bool = False
    specialty: Optional[str] = None
    cloud_ai_consent: bool = False
    mode: ModeEnum = ModeEnum.health
    patient_phone: Optional[str] = None
    patient_age: Optional[str] = None
    patient_sex: Optional[str] = None
    whatsapp_number: Optional[str] = None

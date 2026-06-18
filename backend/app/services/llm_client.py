"""Optional Google Gemini 2.0 formatting client for Lipi.

Clinical extraction, memory resolution, and CDS are intentionally local-only.
This client is retained only for optional structured SOAP wording from already
resolved facts, and must never infer clinical facts.
"""

import json
import logging
from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.utils.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# The default model for fast, structured tasks
_MODEL_ID = "gemini-2.0-flash"


class ExtractedFact(BaseModel):
    value: str = Field(description="The canonical clinical term (e.g. 'fever', 'hypertension', 'penicillin')")
    source_quote: str = Field(description="The exact quote from the transcript proving this fact, for auditability.")

class MedicationFact(BaseModel):
    name: str = Field(description="Generic or brand name of the medication")
    dosage: str = Field(description="Dosage amount (e.g., '500mg')")
    frequency: str = Field(description="Frequency (e.g., 'BD', 'twice daily')")
    source_quote: str = Field(description="The exact quote from the transcript.")

class ClinicalExtractionSchema(BaseModel):
    symptoms: list[ExtractedFact]
    vitals: list[ExtractedFact]
    allergies: list[ExtractedFact]
    investigations: list[ExtractedFact]
    medications: list[MedicationFact]

class SoapNoteSchema(BaseModel):
    S: str = Field(description="Subjective: The patient's history, symptoms, and feelings.")
    O: str = Field(description="Objective: Vitals, physical exam findings, and lab results.")
    A: str = Field(description="Assessment: Diagnosis or differential diagnosis.")
    P: str = Field(description="Plan: Treatment, medications, investigations, and follow-up.")

class CDSSuggestion(BaseModel):
    suggestion: str = Field(description="The specific clinical recommendation (e.g., 'Order CBC').")
    rationale: str = Field(description="Why this is recommended based on the patient's state.")
    urgency: str = Field(description="One of: 'low', 'medium', 'high', 'critical'.")
    safety_label: str = Field(description="A short tag like 'drug-interaction' or 'missing-vitals'.")

class CDSSchema(BaseModel):
    suggestions: list[CDSSuggestion]


class LLMClientService:
    """Singleton wrapper for Google Gemini API."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY is missing! LLMClientService will fail if invoked.")

    def _generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """Call Gemini with 1 retry and enforce a specific Pydantic schema return."""
        if not self.client:
            raise ValueError("Gemini API key not configured.")

        last_exc: Exception = RuntimeError("Unknown error")
        for attempt in range(2):
            try:
                logger.info("Calling Gemini (%s) attempt %d/%d for schema: %s", _MODEL_ID, attempt + 1, 2, schema.__name__)
                response = self.client.models.generate_content(
                    model=_MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1,
                    ),
                )
                data = json.loads(response.text)
                return schema(**data)
            except Exception as e:
                last_exc = e
                logger.warning("Gemini attempt %d/2 failed for %s: %s", attempt + 1, schema.__name__, e)

        logger.error("All Gemini attempts failed for %s. Last error: %s", schema.__name__, last_exc)
        raise last_exc

    # --- Domain Specific Methods ---

    def extract_clinical_facts(self, transcript: str) -> dict:
        raise RuntimeError("Gemini clinical extraction is disabled by safety policy; use local extraction.")

    # Safety: Generated note requires physician 
    # review before any clinical use.
    # System never auto-finalizes records.
    def generate_soap_note(self, memory_state: dict) -> dict:
        prompt = f"""
        You are a clinical documentation formatter.
        Convert the structured patient state into a concise SOAP note.
        Do not infer diagnoses, dosages, follow-up instructions, or clinical facts.
        If a field is not present, write "not specified".
        The note requires physician review before clinical use.

        Patient State:
        {json.dumps(memory_state, indent=2)}
        """
        result = self._generate_structured(prompt, SoapNoteSchema)
        return {"S": result.S, "O": result.O, "A": result.A, "P": result.P}

    def generate_soap_from_transcript(self, transcript: str) -> dict:
        """Generate SOAP directly from raw transcript (Hindi/Hinglish/English).
        Used when local regex extraction returns empty results."""
        prompt = f"""You are a clinical scribe assistant for Indian doctors.
Extract a SOAP note from this doctor-patient consultation transcript.
The transcript may be in Hindi, Hinglish, or English.

Rules:
- S (Subjective): Patient's symptoms, complaints, duration in English
- O (Objective): Vitals, measurements, exam findings in English
- A (Assessment): Likely diagnosis or differential — physician must confirm
- P (Plan): Medications, investigations, follow-up mentioned in transcript

Only include what was explicitly said. Do not invent facts.
Write in English. This draft requires physician review before clinical use.

Transcript:
{transcript}
"""
        result = self._generate_structured(prompt, SoapNoteSchema)
        return {"S": result.S, "O": result.O, "A": result.A, "P": result.P}

    def generate_cds(self, memory_state: dict) -> list[dict]:
        raise RuntimeError("Gemini CDS generation is disabled by safety policy; use local CDS.")

    def diarize_transcript(self, raw_transcript: str) -> str:
        """Cloud transcript diarization is disabled for clinical privacy."""
        raise RuntimeError("Gemini diarization is disabled by privacy policy.")

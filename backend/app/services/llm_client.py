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
        if not self.client:
            return self._local_soap_fallback(memory_state)
        prompt = f"""
        You are a clinical documentation formatter.
        Convert the structured patient state into a concise SOAP note.
        Do not infer diagnoses, dosages, follow-up instructions, or clinical facts.
        If a field is not present, write "not specified".
        The note requires physician review before clinical use.

        Patient State:
        {json.dumps(memory_state, indent=2)}
        """
        try:
            result = self._generate_structured(prompt, SoapNoteSchema)
            return {"S": result.S, "O": result.O, "A": result.A, "P": result.P}
        except Exception as exc:
            logger.warning("Gemini SOAP formatting failed, using local fallback: %s", exc)
            return self._local_soap_fallback(memory_state)

    @staticmethod
    def _local_soap_fallback(memory_state: dict) -> dict:
        """Deterministic SOAP note from resolved memory_state — no LLM required."""
        symptoms = ", ".join(str(s) for s in memory_state.get("symptoms", [])) or "not specified"
        vitals = ", ".join(str(v) for v in memory_state.get("vitals", [])) or "not specified"
        diagnoses = ", ".join(str(d) for d in memory_state.get("diagnoses", [])) or "not specified"
        meds = ", ".join(
            m.get("name", str(m)) if isinstance(m, dict) else str(m)
            for m in memory_state.get("medications", [])
        ) or "not specified"
        follow_up = str(memory_state.get("follow_up") or "not specified")
        investigations = ", ".join(str(i) for i in memory_state.get("investigations", [])) or "not specified"
        return {
            "S": f"Chief complaint: {symptoms}.",
            "O": f"Vitals: {vitals}. Investigations: {investigations}.",
            "A": f"Assessment: {diagnoses}.",
            "P": f"Plan: Medications — {meds}. Follow-up: {follow_up}. Requires physician review.",
        }

    def generate_soap_from_transcript(self, transcript: str) -> dict:
        """DISABLED by zero-LLM safety policy.

        Generating SOAP directly from a raw transcript means the LLM infers
        clinical facts (symptoms, diagnoses, dosages) from unstructured speech —
        the exact thing Lipi's deterministic moat forbids. SOAP is produced only
        from locally-resolved memory_state. This method must never run.
        """
        raise RuntimeError(
            "Gemini transcript→SOAP is disabled by zero-LLM safety policy; "
            "use deterministic extraction + local SOAP generation."
        )

    def generate_cds(self, memory_state: dict) -> list[dict]:
        raise RuntimeError("Gemini CDS generation is disabled by safety policy; use local CDS.")

    def diarize_transcript(self, raw_transcript: str) -> str:
        """Cloud transcript diarization is disabled for clinical privacy."""
        raise RuntimeError("Gemini diarization is disabled by privacy policy.")

    def narrate_practice_insight(self, stats: dict) -> str:
        """Turn deterministically-computed doctor practice statistics into a
        plain-language sentence or two.

        Safety boundary, same class as generate_soap_note: Gemini receives
        only already-computed numbers and is explicitly instructed to
        describe them, never to judge, grade, or second-guess the doctor's
        clinical decisions. It must not recommend a change in practice or
        imply a number is good or bad — that judgment belongs to the doctor.
        """
        if not self.client:
            return self._local_practice_insight_fallback(stats)

        prompt = f"""
        You are summarizing a doctor's own prescribing statistics back to them.
        You are given only pre-computed numbers below. Write 1-2 short, plain
        sentences describing what changed, using neutral, factual language.

        Strict rules:
        - Do not judge whether a number is good, bad, appropriate, or concerning.
        - Do not recommend the doctor change anything.
        - Do not add any clinical interpretation not present in the numbers.
        - State only what the numbers show, nothing else.

        Statistics:
        {json.dumps(stats, indent=2)}
        """
        try:
            response = self.client.models.generate_content(
                model=_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            text = (response.text or "").strip()
            return text or self._local_practice_insight_fallback(stats)
        except Exception as exc:
            logger.warning("Gemini practice-insight narration failed, using local fallback: %s", exc)
            return self._local_practice_insight_fallback(stats)

    @staticmethod
    def _local_practice_insight_fallback(stats: dict) -> str:
        """Deterministic, templated narration — no LLM required."""
        top_dx = stats.get("top_diagnoses") or []
        current = stats.get("consultations_current_period", 0)
        prior = stats.get("consultations_prior_period", 0)
        parts = [f"{current} consultations this period, compared to {prior} the prior period."]
        if top_dx:
            name = top_dx[0].get("name", "")
            count = top_dx[0].get("count", 0)
            if name:
                parts.append(f"Most frequently treated: {name} ({count} cases).")
        return " ".join(parts)

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
_MODEL_ID = "gemini-2.5-flash"


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

class ActionItem(BaseModel):
    action: str = Field(description="One of: 'prescription', 'investigation_order', 'referral', 'tpa_claim', 'patient_info'.")
    to_doctor: str = Field(default="", description="For 'referral' only: the doctor's name being referred to, if explicitly stated. Empty string if not stated.")
    to_specialty: str = Field(default="", description="For 'referral' only: the specialty being referred to, if explicitly stated. Empty string if not stated.")
    reason: str = Field(default="", description="For 'referral' only: the stated reason for referral, if given. Empty string if not stated.")
    urgency: str = Field(default="routine", description="For 'referral' only: 'urgent' if the message indicates urgency, otherwise 'routine'.")
    policy_number: str = Field(default="", description="For 'tpa_claim' only: insurance policy number, if explicitly stated. Empty string if not stated.")
    insurer_name: str = Field(default="", description="For 'tpa_claim' only: insurer name, if explicitly stated. Empty string if not stated.")
    tpa_name: str = Field(default="", description="For 'tpa_claim' only: TPA name, if explicitly stated. Empty string if not stated.")
    query_type: str = Field(default="", description="For 'patient_info' only: one of 'allergies', 'medications', 'chronic_conditions', 'bp_trend', 'summary' — whichever the doctor is asking about.")

class ActionIntentSchema(BaseModel):
    actions: list[ActionItem] = Field(default_factory=list, description="Ordered list of the document/query actions requested, in the order they should run. A single message may request more than one (e.g. a referral and a TPA claim together). Leave empty if the message, read together with the conversation history, does not clearly request any of the five known actions.")
    clarifying_question: str = Field(default="", description="Fill this ONLY when the message seems to want one of the five actions but it is genuinely ambiguous which one — briefly say what's ambiguous (e.g. 'I'm not sure if you mean the referral or the insurance claim'), not just a bare question, and leave 'actions' empty. Leave blank in every other case, including when the message is unrelated to these five actions.")


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

    # Safety boundary: this is a command router, not a clinical model. It maps
    # a doctor's instruction (plus recent conversation history, so references
    # like "do that for him too" resolve) to a list of pre-built, already-
    # existing document actions and pulls out only values the doctor
    # explicitly stated. It never drafts clinical content, never infers a
    # value that wasn't said, and every action it returns still runs through
    # the same confirmation-gated document endpoints (409 if any fact is
    # unconfirmed) as the equivalent UI button. This is intent classification
    # across a short window of turns, not autonomy — there is no planning
    # loop, no tool-use round-trip, and no memory beyond the turns passed in.
    def classify_action_intent(self, message: str, history: list[dict] | None = None) -> dict:
        if not self.client:
            return {"actions": [], "clarifying_question": ""}

        history_block = ""
        if history:
            # Only the most recent turns matter for resolving references —
            # keep the prompt small rather than replaying the full thread.
            recent = history[-10:]
            lines = [
                f"{'Doctor' if t.get('role') == 'user' else 'Assistant'}: {t.get('text', '')}"
                for t in recent
            ]
            history_block = "Conversation so far:\n" + "\n".join(lines) + "\n\n"

        prompt = f"""
        You are a command router for a clinical documentation tool. A doctor
        is chatting with you about this specific consultation. Your ONLY job
        is to decide which of these five pre-built actions they want —
        possibly more than one in a single message — and pull out any
        details they explicitly stated for each. You do not generate
        clinical content, medical advice, or document text yourself — you
        only classify and extract values already present in the message or
        the conversation history below.

        Available actions:
        - "prescription": the already-signed prescription for this consultation
        - "investigation_order": the lab/investigation order for this consultation
        - "referral": a referral letter to another doctor (fields: to_doctor, to_specialty, reason, urgency)
        - "tpa_claim": an insurance/TPA claim document (fields: policy_number, insurer_name, tpa_name)
        - "patient_info": answer a question about this patient using their existing recorded history — never invents anything (field: query_type, one of "allergies", "medications", "chronic_conditions", "bp_trend", "summary")

        A single message can request more than one action (e.g. "refer to
        Dr Sharma and also file the insurance claim") — list each requested
        action in the order it should run.

        Use the conversation history to resolve references like "do that for
        him too" or "the same doctor as before" — pull the actual name or
        detail from an earlier turn if it is there.

        If the message seems to want one of these five actions but it is
        genuinely ambiguous which one, leave "actions" empty and set
        clarifying_question to a short sentence that states what's ambiguous
        (e.g. "I'm not sure if you mean the referral or the insurance
        claim") rather than a bare question. If the message is unrelated to
        these five actions entirely, leave both "actions" and
        "clarifying_question" empty.

        Only fill in a field if it was explicitly stated somewhere in the
        message or history below — never guess or invent a value.

        {history_block}Doctor's latest message: "{message}"
        """
        try:
            result = self._generate_structured(prompt, ActionIntentSchema)
            return result.model_dump()
        except Exception as exc:
            logger.warning("Action-intent classification failed, defaulting to no action: %s", exc)
            return {"actions": [], "clarifying_question": ""}

    def narrate_patient_query(self, query_type: str, data: dict) -> str:
        """Turns already-recorded, doctor-confirmed patient timeline data
        into a plain-language answer to a doctor's question about this
        patient.

        Safety boundary, same class as narrate_practice_insight and
        generate_soap_note: Gemini receives only pre-computed data already
        confirmed by a doctor across past visits, and describes it — it
        never infers a new clinical fact, never diagnoses, and never fills a
        gap the data doesn't answer. If the data is empty or doesn't cover
        the question, it must say so plainly rather than guessing.
        """
        if not self.client:
            return self._local_patient_query_fallback(query_type, data)

        prompt = f"""
        You are answering a doctor's question about one of their patients,
        using only the pre-recorded, doctor-confirmed data below. Do not
        infer, diagnose, or add any clinical interpretation not directly
        present in the data. If the data doesn't answer the question, say so
        plainly rather than guessing. Write 1-3 short, factual sentences.

        Question type: {query_type}
        Patient data:
        {json.dumps(data, indent=2, default=str)}
        """
        try:
            response = self.client.models.generate_content(
                model=_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            text = (response.text or "").strip()
            return text or self._local_patient_query_fallback(query_type, data)
        except Exception as exc:
            logger.warning("Patient-query narration failed, using local fallback: %s", exc)
            return self._local_patient_query_fallback(query_type, data)

    @staticmethod
    def _local_patient_query_fallback(query_type: str, data: dict) -> str:
        """Deterministic, templated answer — no LLM required."""
        if query_type == "allergies":
            allergies = data.get("allergies") or []
            return f"Recorded allergies: {', '.join(str(a) for a in allergies)}." if allergies else "No allergies recorded for this patient."
        if query_type == "medications":
            meds = data.get("active_medications") or []
            names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in meds]
            return f"Active medications: {', '.join(names)}." if names else "No active medications recorded."
        if query_type == "chronic_conditions":
            conditions = data.get("chronic_conditions") or []
            names = [c.get("display") or c.get("text") or str(c) if isinstance(c, dict) else str(c) for c in conditions]
            return f"Chronic conditions: {', '.join(names)}." if names else "No chronic conditions recorded."
        if query_type == "bp_trend":
            visits = data.get("visits") or []
            return f"{len(visits)} visit(s) on record with vitals logged." if visits else "No vitals recorded yet."
        total = data.get("total_visits", 0)
        return f"{total} visit(s) on record for this patient."

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

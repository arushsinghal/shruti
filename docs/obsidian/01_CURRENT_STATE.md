# Current State

Last initialized: 2026-06-26
Last verified against running code: 2026-07-02

## One-Line Definition

Lipi is an AI-native OPD administration service for Indian clinics, beginning with consultation capture and expanding into doctor-approved records, assistant workflow, patient timeline, follow-up memory, and admin outputs.

## Current Operating Position

Lipi should be treated as a doctor-assistive product. The doctor remains the final authority on clinical records, prescriptions, follow-up plans, and patient-facing outputs.

The current product thesis is not "AI scribe only." The wedge is consultation capture, but the destination is OPD administration memory and workflow.

## Current Safety Doctrine

- No proof -> no fact.
- Clinical extraction must be evidence-backed from transcript spans or structured user input.
- Doctor review is required before outputs are finalized.
- Ambiguous or unsupported clinical claims should be marked for confirmation or omitted.
- Gemini may be used only for final text formatting from structured inputs.
- Gemini must not create, infer, or resolve clinical facts.
- Clinical fact creation, memory resolution, and conflict detection should remain local and deterministic.

## Current ASR Doctrine

- Sarvam plain speech-to-text is the default transcription path.
- Diarization should be added only if real consultations prove it is needed.
- Do not train ASR before market proof.
- If ASR confidence or transcript quality is poor, the output should surface uncertainty rather than invent clinical meaning.

## Current Product Surface

Use the codebase as the source of truth before implementation. This vault should track concepts and decisions, not duplicate code.

Expected product surfaces:
- Consultation capture
- Transcript review
- Evidence-backed clinical fact extraction
- Doctor review and correction
- SOAP or clinical note formatting
- Patient timeline and memory
- Follow-up workflow
- Assistant/admin outputs
- Safety and audit trail
- Cost tracking per consultation

## Current Validation Bias

Validate the OPD workflow before building expensive automation. The most important proof is whether clinics repeatedly use Lipi to reduce real documentation and admin burden.

Priority proof:
- Doctor accepts or corrects structured facts quickly.
- Assistant can use the outputs for real follow-up and admin work.
- Patient timeline improves subsequent visits.
- Per-consultation cost supports the target pricing model.
- Audio quality and language mix are good enough with Sarvam plain STT.

## What Must Be Verified Before Code Work

- Which route, component, or service owns the behavior.
- Whether the behavior is already implemented.
- Whether existing tests cover the change.
- Whether the change touches patient data, clinical safety, or external APIs.
- Whether the change affects cost per consultation.

## Related Notes

- [[02_ARCHITECTURE_MAP]]
- [[05_VALIDATION_PLAN]]
- [[06_API_COSTS]]
- [[07_DECISIONS]]
- [[12_IMPLEMENTATION_GAP_REGISTER]]

# Architecture Map

## Architecture Principle

Lipi separates capture, evidence, memory, formatting, and review. Clinical facts must be grounded in the consultation record before they can appear in doctor-facing or patient-facing outputs.

## System Layers

### 1. Capture Layer

Purpose:
- Record or upload consultation audio.
- Generate transcript through Sarvam plain STT by default.
- Preserve enough metadata to audit source quality.

Rules:
- Diarization is optional and only justified by observed workflow need.
- ASR quality issues should be visible to the review workflow.
- Do not train ASR before market proof.

### 2. Evidence Layer

Purpose:
- Convert transcript text into candidate clinical facts with source evidence.
- Keep source snippets, spans, timestamps, or equivalent proof.

Rules:
- No proof -> no fact.
- Negation, uncertainty, and ambiguity must remain explicit.
- Clinical fact creation stays local and deterministic.
- Gemini must not create clinical facts.

### 3. Memory Layer

Purpose:
- Maintain patient timeline, prior facts, follow-up state, and unresolved references.
- Resolve current-visit facts against prior context only when evidence supports it.

Rules:
- Latest explicit doctor instruction wins.
- Superseded facts remain in audit history.
- Patient memory should improve continuity without hiding uncertainty.

### 4. Review Layer

Purpose:
- Let the doctor approve, correct, or reject extracted facts and generated outputs.
- Capture corrections for workflow learning without storing PHI in reusable knowledge.

Rules:
- Doctor review required.
- Corrections should be auditable.
- Patient-facing output should be based on reviewed facts.

### 5. Formatting Layer

Purpose:
- Turn structured, reviewed inputs into readable records, prescriptions, summaries, and follow-up material.

Rules:
- Gemini may format text only from structured inputs.
- Gemini output must not introduce new diagnoses, medications, findings, or certainty.
- If a field is missing, output "not specified" or omit according to the product surface.

### 6. Assistant/Admin Layer

Purpose:
- Convert doctor-approved clinical records into clinic operations.

Potential outputs:
- Prescription print or share flow
- Follow-up reminder
- Patient timeline update
- Referral or investigation note
- Billing/admin task
- Visit summary

## Data Flow

```text
audio
  -> Sarvam plain STT
  -> transcript
  -> evidence-backed local extraction
  -> structured facts with proof
  -> memory resolution and patient timeline
  -> doctor review
  -> formatted clinical/admin outputs
  -> follow-up and audit trail
  -> cost ledger
```

## Safety Boundary

Clinical fact boundary:
- Facts can only come from transcript evidence, reviewed structured inputs, or explicit doctor correction.
- LLMs do not cross this boundary.

Formatting boundary:
- Gemini can improve readability and structure.
- Gemini cannot add clinical content.

Operational boundary:
- Admin outputs depend on doctor-approved facts.
- Assistant workflow should not silently change clinical decisions.

## Current Implementation Pointers (verified 2026-07-02)

Read this before grepping the codebase — saves a full-repo read.

- **Capture layer**: `backend/app/services/sarvam_asr.py`, `sarvam_batch_asr.py`
- **Evidence layer**: `backend/app/services/clinical_extractor.py` (Layer 1, keyword/fuzzy/regex, ~1,918 curated entries) + `backend/app/services/medical_ontology.py` (~1,304 curated entries, ~3,222 total). `backend/app/services/provenance.py` builds per-fact certainty (`affirmed`/`negated`/`uncertain`/`queried`) and `facts_from_non_rejected()` propagates certainty into SOAP-facing display values (e.g. `"vomiting (denied)"`).
  - GLiNER (`backend/app/services/gliner_extractor.py`, local NER, no API) exists but is **not wired into the production path**. `routes_notes.py`'s own `_run_health_pipeline()` calls `ClinicalExtractorService.extract()` directly — it does not call `clinical_pipeline.py`'s `run_health_pipeline()`, which is the only place GLiNER is invoked. GLiNER is currently exercised only by `test_e2e.py`. `ENABLE_GLINER` is `False` by default and unset everywhere in deploy config.
- **Memory layer**: `backend/app/services/memory_service.py` (`resolve_memory`)
- **Review layer**: `backend/app/api/routes_fact_review.py`. Opt-out model, not the older strict-confirmation-gate model: all non-rejected candidates populate the draft SOAP immediately (with certainty markers); doctor removes what's wrong. Structured exports (FHIR, investigation orders) still hard-gate on explicit per-fact `confirmed` status via `provenance.facts_from_confirmed()`.
- **Formatting layer**: `backend/app/services/soap_generator.py` — currently **100% rule-based** (`_rule_based_soap()`), zero LLM calls in the live SOAP path. A Gemini-enhancement helper (`_gemini_enhance()`) exists in git history as something added and then deliberately removed in this session — do not reintroduce without discussing certainty-marker handling first, since `_gemini_enhance` had no instruction to preserve `(denied)`/`(uncertain)` markers.
  - `backend/app/services/llm_client.py`'s `narrate_practice_insight()` is a separate, narrower Gemini use: narrates doctor practice-pattern *numbers* in plain language, explicitly barred from judging/grading them. This is the one legitimate current Gemini touchpoint in the product.
- **CDS/safety layer**: `backend/app/services/cds_engine.py` — deterministic allergy cross-reactivity (9 drug classes) + 4 hardcoded drug-drug interactions + minimal symptom/vital rules. Real but narrow; see `21_FRONTIER_RESEARCH_DIRECTIONS.md` direction 2 for the expansion plan.
- **Assistant/Admin layer**: `backend/app/api/routes_reviewer.py` (review queue, ops stats), `routes_clinics.py` (WA Inbox / clinic triage + doctor assignment), `appointment_booking.py` (WhatsApp-driven booking, shares `doctor_availability` table with the Appointments frontend page), `routes_tpa.py` (insurance/TPA claim, gated on `session.status == 'complete'`).

**Known drift**: `provenance.py`, `clinical_pipeline.py`, and `gliner_extractor.py` are untracked in git as of 2026-07-02 — real code on disk, never committed. Do not assume `git log` reflects what's actually running.

## Source Of Truth

- Implementation: `backend/` and `frontend/`
- Project memory: `docs/obsidian/`
- Durable decisions: [[07_DECISIONS]]
- Cost assumptions: [[06_API_COSTS]]

## Related Notes

- [[01_CURRENT_STATE]]
- [[06_API_COSTS]]
- [[07_DECISIONS]]

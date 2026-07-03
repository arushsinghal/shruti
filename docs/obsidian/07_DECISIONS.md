# Decisions

## How To Use

Record durable decisions here. Keep each entry short, dated, and explicit about reversibility.

Template:

```text
## DXXX: Title

Date:
Status: Proposed | Accepted | Replaced
Decision:
Reason:
Implications:
Reversible:
Related:
```

## D001: Use Obsidian As Project Brain, Not Code Store

Date: 2026-06-26
Status: Accepted

Decision:
Use `docs/obsidian/` for project memory, strategy, architecture maps, decisions, validation, and costs. Do not dump full code into Obsidian.

Reason:
The vault should help humans and agents navigate Lipi without creating a stale duplicate of the implementation.

Implications:
Agents must inspect the real backend and frontend code before implementation.

Reversible:
Yes, but only if a better documentation system replaces it.

Related:
[[00_HOME]]

## D002: Position Lipi As AI-Native OPD Administration

Date: 2026-06-26
Status: Accepted

Decision:
Lipi is positioned as an AI-native OPD administration service for Indian clinics, not just an AI scribe.

Reason:
The capture wedge should lead to records, assistant workflow, patient timeline, follow-up memory, and admin outputs.

Implications:
Product strategy should evaluate downstream workflow value, not only transcription or note generation.

Reversible:
Partially. Positioning can narrow for a sales motion, but the product architecture should preserve the broader workflow path.

Related:
[[03_PRODUCT_STRATEGY]]

## D003: No Proof -> No Fact

Date: 2026-06-26
Status: Accepted

Decision:
Clinical facts require evidence from transcript spans, reviewed structured input, or explicit doctor correction.

Reason:
Clinical trust depends on provenance and auditability.

Implications:
Unsupported facts must be omitted or marked for confirmation. Evidence display is a core product requirement.

Reversible:
No for clinical facts.

Related:
[[02_ARCHITECTURE_MAP]]

## D004: Doctor Review Required

Date: 2026-06-26
Status: Accepted

Decision:
Doctor review is required before clinical outputs are finalized or treated as approved records.

Reason:
Lipi is doctor-assistive only and must not become autonomous clinical decision-making.

Implications:
Workflow design must optimize review speed while preserving explicit approval.

Reversible:
No for clinical output.

Related:
[[05_VALIDATION_PLAN]]

## D005: Gemini Formatting Only

Date: 2026-06-26
Status: Accepted

Decision:
Gemini may be used only for final text formatting from structured inputs. It must not create clinical facts, resolve memory, or detect conflicts.

Reason:
Patient data privacy and hallucination risk make LLM-based fact creation unacceptable for this product.

Implications:
Clinical extraction, memory resolution, and conflict detection remain local and deterministic.

Reversible:
Not without a separate safety review and explicit product decision.

Related:
[[01_CURRENT_STATE]]

## D006: Sarvam Plain STT Default

Date: 2026-06-26
Status: Accepted

Decision:
Use Sarvam plain speech-to-text as the default ASR path.

Reason:
The current priority is proving clinic workflow value, not optimizing every audio edge case.

Implications:
Track transcript quality and correction burden before adding more expensive audio processing.

Reversible:
Yes, if validation data shows another ASR path is materially better.

Related:
[[06_API_COSTS]]

## D010: Treat Evidence-Grounded Continual Learning As Future Research Direction

Date: 2026-06-27
Status: Accepted

Decision:
Develop Lipi's long-term technical moat as an evidence-grounded continual learning system for healthcare administration, not as unrestricted self-training or transcript memorization.

Reason:
Doctor corrections, assistant actions, task outcomes, and evidence spans can create reusable clinic and specialty playbooks while preserving clinical safety.

Implications:
Learning work should start with structured event logs, explicit memory candidates, scoped promotion, shadow evaluation, and safety gates. It must not silently create clinical facts or bypass doctor review.

Reversible:
Partially. The research direction can be narrowed, but safety boundaries remain non-negotiable.

Related:
[[10_CONTINUAL_LEARNING_SYSTEM]]

## D011: Use Service-First YC Framing

Date: 2026-06-27
Status: Accepted

Decision:
Pitch Lipi first as an AI-native OPD administration service, not as an abstract RL, recursive-agent, or frontier-model research project.

Reason:
The company becomes stronger when the research direction is tied to concrete clinic work Lipi completes: records, prescriptions, referrals, follow-ups, admin tasks, pre-auth readiness, and internal ops. It becomes weaker if the pitch leads with research jargon before proving the service wedge.

Implications:
Product and fundraising docs should say the learning loop is the moat behind the service. Claims about continual learning, RL, context engineering, or agentic systems must stay tied to reviewed work traces, doctor approval, assistant outcomes, and measurable workflow improvement.

Reversible:
Partially. External wording can adapt, but the internal rule remains service-first until the service wedge is proven.

Related:
[[03_PRODUCT_STRATEGY]]
[[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

## D007: Diarization Only If Needed

Date: 2026-06-26
Status: Accepted

Decision:
Diarization should be optional and added only when real usage shows it materially improves workflow or safety.

Reason:
Diarization adds cost and complexity. It should solve an observed problem.

Implications:
Pilot instrumentation should track speaker-confusion incidents.

Reversible:
Yes, if evidence supports enabling it by default.

Related:
[[05_VALIDATION_PLAN]]

## D008: Do Not Train ASR Before Market Proof

Date: 2026-06-26
Status: Accepted

Decision:
Do not train or fine-tune ASR before proving repeated market demand and workflow value.

Reason:
ASR training is expensive and premature if the product loop is not validated.

Implications:
Invest first in workflow proof, review UX, evidence display, and cost tracking.

Reversible:
Yes, after market proof and a clear ASR error analysis.

Related:
[[05_VALIDATION_PLAN]]

## D009: Track Cost Per Consultation

Date: 2026-06-26
Status: Accepted

Decision:
Track vendor and infrastructure cost per consultation as a first-class metric.

Reason:
Indian clinic pricing requires strict marginal cost discipline.

Implications:
Every external API path should be measurable by consultation.

Reversible:
No for pilot and pricing work.

Related:
[[06_API_COSTS]]

## D016: Do Not Wire GLiNER Into Production Extraction

Date: 2026-07-03
Status: Accepted

Decision:
Keep the deterministic, ontology-based extraction pipeline as the sole production extraction path. Do not wire GLiNER (or any neural NER/classification layer) into `routes_notes.py`'s live request path.

Reason:
GLiNER was proposed to close a gap in Hinglish classification (medication status, negation, etc.) that regex could not generalize across. Since that proposal, the hand-curated ontology has grown from ~3,222 to ~6,882 terms across all TSVs, shrinking the marginal gap GLiNER would close. No accuracy baseline was ever re-measured to confirm the originally estimated 60→78/100 gain still applies. Meanwhile GLiNER adds a 753MB model, cold-start latency, and an unverified merge/filter layer — real operational cost for an unmeasured, shrinking benefit. It also introduces a neural component into what is otherwise a fully deterministic, auditable extraction path, which weakens the "zero-LLM, every fact traces to an evidence span" architectural story that is the actual technical moat.

Implications:
`ENABLE_GLINER` stays `False`. `clinical_pipeline.py` (the only code path that calls GLiNER) remains exercised only by `test_e2e.py`, not production. Continue growing the ontology and hand-tuned regex (frequency patterns, brand names, Hinglish epistemic/temporal markers) as the primary way to close extraction gaps. If a future accuracy problem is specifically traced to something regex/ontology genuinely cannot express — not just "an LLM would probably help" — re-open this decision with a fresh, measured baseline before reconsidering.

Reversible:
Yes — reversible if a specific, measured extraction failure is found that the ontology approach cannot address and GLiNER's extractive-only guarantee (span must exist verbatim) can be preserved.

Related:
[[14_BUILD_PLAN]]
[[21_FRONTIER_RESEARCH_DIRECTIONS]]
[[12_IMPLEMENTATION_GAP_REGISTER]]

## D017: Clinical Memory Assistant Runs Only On India-Hosted Inference

Date: 2026-07-03
Status: Accepted

Decision:
The per-doctor clinical memory assistant (`docs/obsidian/27_CLINICAL_MEMORY_ASSISTANT_SPEC.md`) never sends patient data — raw or retrieved — to a foreign-hosted inference API, under any circumstance. Inference runs on Sarvam (Indian company, on-shore) only. This is enforced in code (`clinical_memory_service.py` has an import-time assertion that the call target is a Sarvam URL), not just documented as policy.

Reason:
ABDM's Health Data Management Policy is already in force and states plainly that no personal data may be stored beyond India's borders. Every patient record this feature touches is ABHA-linked health data under that policy. DPDP Act 2023 is more permissive (blacklist model, transfer provisions not even effective until May 2027) but does not override the stricter, already-binding ABDM rule. Draft DPDP Rules also signal health data may be named for mandatory in-India-only storage regardless of the future cross-border regime, so building on-shore now avoids a rebuild later.

Implications:
No `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or equivalent foreign provider key is ever read by `clinical_memory_service.py`. Phase 1 (shipped 2026-07-03) uses direct context-stuffing against Sarvam's chat API with no vector database. Phase 2 (cross-patient search) will add `pgvector` on the existing India-hosted Postgres instance, never a foreign vector-DB SaaS. The feature ships behind `memory_assistant_enabled` (default `False`) until Sarvam's model quality on retrieval-augmented clinical Q&A is benchmarked with a live test call.

Reversible:
No, not without a change in the underlying law/policy. This is a compliance floor, not a preference.

Related:
[[27_CLINICAL_MEMORY_ASSISTANT_SPEC]]
[[17_ABDM_DHIS_DSC_COMPLIANCE]]
[[10_CONTINUAL_LEARNING_SYSTEM]]

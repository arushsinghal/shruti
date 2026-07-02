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

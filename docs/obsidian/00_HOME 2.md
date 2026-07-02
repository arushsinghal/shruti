# Lipi Project Brain

## Purpose

This Obsidian vault is project memory for Lipi. Use it for strategy, architecture maps, decisions, validation plans, open questions, and operating cost tracking.

Code stays in `backend/` and `frontend/`. Do not copy full source files into Obsidian.

## Product North Star

Lipi is an AI-native OPD administration service for Indian clinics.

It starts with consultation capture and turns it into:
- Doctor-approved clinical records
- Assistant workflow
- Patient timeline
- Follow-up memory
- Admin outputs

Lipi is not just an AI scribe. The scribe is the first capture surface.

## Non-Negotiable Rules

- Clinical extraction remains evidence-backed.
- No proof -> no fact.
- Doctor review is required before clinical output is finalized.
- Gemini may format structured clinical content, but must not create clinical facts.
- Sarvam plain STT is the default ASR path.
- Diarization is used only if workflow proves it is needed.
- Cost per consultation must be tracked.
- Do not train ASR before market proof.
- Do not store secrets, patient data, logs, or full code dumps in Obsidian.

## Navigation

- [[01_CURRENT_STATE]] - what Lipi is and what must be verified before work
- [[02_ARCHITECTURE_MAP]] - system map, data flow, safety boundaries
- [[03_PRODUCT_STRATEGY]] - wedge, positioning, roadmap, non-goals
- [[04_COMPETITORS]] - competitor map and research prompts
- [[05_VALIDATION_PLAN]] - proof plan, pilot metrics, observation design
- [[06_API_COSTS]] - cost model and per-consultation ledger
- [[07_DECISIONS]] - durable decisions and reversibility
- [[08_OPEN_QUESTIONS]] - unresolved product, safety, market, technical questions
- [[09_STRATEGIC_ROADMAP]] - path from scribe wedge to AI-native healthcare services company
- [[10_CONTINUAL_LEARNING_SYSTEM]] - future research direction for evidence-grounded continual learning
- [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]] - OPD admin workflow build plan
- [[12_IMPLEMENTATION_GAP_REGISTER]] - consolidated built/not-built gap register and priority order

## How Use This Vault

Before strategy work, read [[03_PRODUCT_STRATEGY]], [[05_VALIDATION_PLAN]], [[08_OPEN_QUESTIONS]].
Before architecture work, read [[01_CURRENT_STATE]], [[02_ARCHITECTURE_MAP]], [[07_DECISIONS]].
Before learning-system, memory, or data-flywheel work, read [[10_CONTINUAL_LEARNING_SYSTEM]].
Before roadmap, pilot-readiness, or "what is left" work, read [[12_IMPLEMENTATION_GAP_REGISTER]].
Before cost, pricing, or vendor work, read [[06_API_COSTS]] and update assumptions with dated vendor evidence.

Before changing code, read only relevant docs from this vault, then inspect actual code paths. The codebase remains source of truth for implementation.

## Update Protocol

When adding notes:
- Link related pages with Obsidian links.
- Separate facts from assumptions.
- Add dates for time-sensitive claims.
- Prefer short decision records over long narrative.
- Keep PHI, secrets, logs, and full source code out of the vault.

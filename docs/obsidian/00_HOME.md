# Lipi Project Brain

This Obsidian vault is the internal project brain for Lipi. It is for humans and AI agents working on the repo.

Use it for strategy, architecture maps, decisions, validation plans, open questions, cost tracking, roadmap thinking, implementation gaps, and future research direction.

Do not use it as a code dump. Code stays in `backend/` and `frontend/`. Do not store secrets, PHI, raw patient transcripts, logs, or full source files here.

## Product North Star

Lipi is an AI-native OPD administration service for Indian clinics.

The first wedge is consultation capture, but the real product is the work that happens after a consultation:

- Doctor-approved clinical records.
- Evidence-backed facts.
- Prescription and SOAP output.
- Patient timeline and follow-up memory.
- Assistant-ready task queues.
- Investigation orders and referral letters.
- Admin outputs such as pre-auth readiness, reminders, and internal ops tracking.

Lipi is not just an AI scribe. The scribe is the capture surface. The service is the completed clinic work.

## Non-Negotiable Rules

- No proof -> no fact.
- Clinical extraction remains evidence-backed.
- Doctor review is required before clinical output is final.
- Gemini may format structured clinical content, but must not create clinical facts.
- Sarvam plain STT is the default ASR path.
- Diarization is used only when real workflow evidence shows it is needed.
- Track cost per consultation.
- Do not train ASR before market proof.
- Do not let patient memory silently become current-visit truth.
- Do not let product copy outrun what is actually implemented.

## Navigation

- [[01_CURRENT_STATE]] - current product state, safety doctrine, and implementation truth.
- [[02_ARCHITECTURE_MAP]] - system map, data flow, provenance, and safety boundaries.
- [[03_PRODUCT_STRATEGY]] - positioning, wedge, roadmap, YC framing, and non-goals.
- [[04_COMPETITORS]] - competitor map and research prompts.
- [[05_VALIDATION_PLAN]] - pilot proof plan and validation metrics.
- [[06_API_COSTS]] - cost model and per-consultation ledger assumptions.
- [[07_DECISIONS]] - durable decisions and reversibility.
- [[08_OPEN_QUESTIONS]] - unresolved product, safety, market, and technical questions.
- [[09_STRATEGIC_ROADMAP]] - path from scribe wedge to AI-native healthcare service company.
- [[10_CONTINUAL_LEARNING_SYSTEM]] - future research direction for evidence-grounded continual learning.
- [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]] - implementation plan for service-company surfaces.
- [[12_IMPLEMENTATION_GAP_REGISTER]] - honest built/not-built register and priority order.
- [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] - YC/research framing for on-the-job learning service agents.
- [[14_BUILD_PLAN]] - **active backlog**: full priority order, model routing (Opus vs Sonnet), research moat items, and what not to build yet. Start here for any implementation work.
- [[15_AUGNITO_TEARDOWN]] - detailed Augnito competitive teardown with YC interview answers. Verify time-sensitive claims before external use.
- [[16_FULL_APP_REVIEW]] - end-to-end code audit (security, clinical safety, product, YC readiness). Has a 2026-07-02 status update at the top — read that before the original 2026-06-28 findings below it, several are since resolved.
- [[17_ABDM_DHIS_DSC_COMPLIANCE]] - ABDM/DHIS government health-stack integration and DSC compliance technical spec.
- [[18_YC_PITCH_STRATEGY]] - working YC application draft, pricing, video script, seed deck outline. Has an explicit "Positioning — What to Say vs Not Say" table; read before any external-facing research/company-positioning claim.
- [[19_SERVICE_PIVOT]] - service-company pivot framing.
- [[20_PRODUCT_VISION]] - long-range product vision.
- [[21_FRONTIER_RESEARCH_DIRECTIONS]] - AMR surveillance, drug interaction modeling, pharmacogenomics, and ambient hardware research directions. Same product-first discipline as [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] applies. **Read this before any "should we become a medical AI research company" question** — it has the safe-claim/avoid-claiming line for every current direction and explicitly warns against research-jargon-first framing.
- [[22_OPUS_FRONTIER_RESEARCH]] - Opus's frontier R&D proposal: a research lab *inside* the product company, aimed at (1) solving hard Indian healthcare problems and (2) piping that R&D straight into features doctors use. Spine is the Ankit Gupta "AI Personalized Medicine" RFS — Lipi as India's agent harness for personalized primary care. Tracks: A personalized prescribing (sequencing-free pharmacogenomics), B early detection at first contact (TB etc.), C precision antibiotic use / AMR, D the trust substrate (Hinglish understanding, certified grounding, correction economics). **Corrected 2026-07-03: we never publish, even novel findings — this doc's own §8 "publication as byproduct" framing is superseded.** Research exists to make the product and Indian healthcare better, never for citation credibility; the moat is what the product does, not what gets written about it. Every track terminates in a doctor-gated feature, full stop. Pushes back on parts of [[21_FRONTIER_RESEARCH_DIRECTIONS]] and includes a Claude Science R&D-for-product playbook. Proposal only.
- [[23_EXECUTION_ROUTING]] - how to dispatch [[22_OPUS_FRONTIER_RESEARCH]]: three ready-to-paste Claude Science briefs (Indian pharmacogenomics evidence map, AMR leading-indicator + validation design, Hinglish epistemic×temporal schema), the continual-learning build-vs-research split, and one model-routing rule (Claude Science vs Fable vs Opus vs Sonnet) with a full dispatch table. Answers "should I use a mythos-class model for X or not" per work item.
- [[25_CLAUDE_SCIENCE_WORKFLOWS]] - **Six full-power Claude Science workflow commands.** Each pulls real data, runs real code, and outputs a file directly loadable into the codebase: Indian DDI database, PGx rules data contract, AMR gap computation, ICD-10 burden map, Hinglish NLP benchmark, CDSCO brand confusion map. Paste one per agent session inside the "healthcare" project. Supersedes the 3 briefs in [[23_EXECUTION_ROUTING]].
- [[26_CLAUDE_SCIENCE_PASTE_READY]] - **OPEN THIS WHEN YOU OPEN CLAUDE SCIENCE.** All 6 agent prompts formatted for immediate copy-paste, with model selection (Sonnet vs Opus), agent names, output file destinations, and the project-level Agent Context block to paste once at setup. No hunting through other docs.
- [[24_HOW_TO_MOVE_AHEAD]] - **START HERE WHEN CONFUSED.** Collapses product + research + revenue into one loop and four gated phases. States the vision once (billion-dollar Indian healthcare AI research company; OPD-as-product wedge, personalized medicine destination), shows you're at Phase 0, and names the exact five things to finish before anything else in the vault matters. The counterweight to [[22_OPUS_FRONTIER_RESEARCH]]: that doc is where you're going, this one is the next step.

## Read First By Task

Before coding, read only the docs relevant to the work, then inspect the real code path.

- **What to build next / active backlog**: read [[14_BUILD_PLAN]] first. It is the agreed priority order with model routing.
- Strategy or YC positioning: read [[03_PRODUCT_STRATEGY]], [[09_STRATEGIC_ROADMAP]], [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]].
- Architecture or pipeline changes: read [[01_CURRENT_STATE]], [[02_ARCHITECTURE_MAP]], [[07_DECISIONS]], then inspect backend files.
- Product roadmap or "what is left": read [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]], [[12_IMPLEMENTATION_GAP_REGISTER]], [[14_BUILD_PLAN]].
- Cost, pricing, vendor, or margin work: read [[06_API_COSTS]] and update assumptions with dated evidence.
- Learning, flywheel, or agentic research work: read [[10_CONTINUAL_LEARNING_SYSTEM]], [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]], [[14_BUILD_PLAN]] (P3 section).
- Research page, YC application research framing, or new research direction proposals: read [[21_FRONTIER_RESEARCH_DIRECTIONS]] first, it has the "safe claim" / "avoid claiming" lines for every current direction.
- Competitor positioning: read [[04_COMPETITORS]] and verify time-sensitive facts before using them externally.

## Update Protocol

- Separate facts, assumptions, and opinions.
- Add dates for time-sensitive claims.
- Link related notes with Obsidian links.
- Prefer short decision records over long unstructured narrative.
- Keep PHI, secrets, logs, and full code out of the vault.
- If docs and code disagree, code is the implementation truth and docs should be corrected.

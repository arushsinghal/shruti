# Frontier Research Directions

**Date:** 2026-07-01
**Status:** Future research directions. Not current product. Product-first discipline from [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] and [[20_PRODUCT_VISION]] applies to all of this.

Related:
- [[00_HOME]]
- [[03_PRODUCT_STRATEGY]]
- [[09_STRATEGIC_ROADMAP]]
- [[10_CONTINUAL_LEARNING_SYSTEM]]
- [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]
- [[20_PRODUCT_VISION]]

## Why This Doc Exists

Anthropic publicly launched Claude Science on 2026-06-30 (a research-workbench product, same posture as Claude Code but for scientific research: autonomous literature search, dataset discovery, code execution on compute clusters, 60+ pre-configured scientific databases, reproducible/auditable outputs). We have paid access to it starting 2026-07-01.

The edge it gives us is execution speed on research we are already positioned to do well, not a moat by itself. The moat is still what [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] already says it is: the evidence-backed data trace Lipi generates from real consultations, which most AI-native research tooling has nothing to point at until a product is live.

Rule carried over from [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]: research jargon last, and only when the audience asks. Everything below is labeled by what's real versus what's a direction.

## Already Shipped (not a research direction, a fact)

**Zero-hallucination clinical documentation.** Deterministic, evidence-linked extraction (`clinical_extractor.py`, `provenance.py`), not generative drafting. Every fact traces to a transcript sentence. Nothing is a clinical record until doctor confirmation. This differentiates directly from LLM-drafting competitors, including the named market leader Eka.Care (see [[09_STRATEGIC_ROADMAP]] for the competitive comparison; keep that framing internal, not on external-facing pages, until we want to name a competitor publicly).

## Already Documented, Cross-Referenced Here

- **Continual learning for OPD service work** — [[10_CONTINUAL_LEARNING_SYSTEM]]. Operational learning (clinic preferences, doctor style, payer rejection patterns), explicitly not clinical fact learning. Hard safety boundaries already defined there; do not restate them differently here.
- **Agentic service / evidence-backed work queue** — [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]. The experience ledger, clinic memory, skill library, and verifier layer architecture. This is the most fully specified research direction in the vault; new directions below should follow its safety-boundary discipline (candidate lessons proposed not auto-applied, scoped memory, rollback paths).

## New Directions (2026-07-01)

### 1. Antimicrobial resistance (AMR) surveillance gap analysis

India carries an estimated 250,000-300,000+ deaths a year attributable to antimicrobial resistance, the largest single-country burden in the world. Existing surveillance (ICMR's AMR Surveillance Network, WHO GLASS country data) is built almost entirely on hospital-lab culture-and-sensitivity data and is structurally blind to the 70-80% of antibiotic prescribing that happens in primary care, which is exactly where Lipi's consultation data already accumulates.

**What's real today:** nothing shipped. This is a research direction, not a result.

**First achievable step:** a sourced gap analysis using only public data (ICMR AMRSN reports, WHO GLASS India data, published Indian antibiogram studies) run through Claude Science, producing a short technical memo identifying exactly where the visibility gap is. Zero dependency on Lipi's own data maturing.

**Honest limitation:** a real surveillance signal needs lab culture-and-sensitivity data paired with prescribing data, not prescribing patterns alone. Prescribing data is a proxy, not the same signal microbiologists trust. Any external claim must say this plainly.

**Safe claim:** "We are researching where India's AMR surveillance has structural blind spots, using public data."
**Avoid claiming:** "We are building AMR surveillance infrastructure" (not until a lab-data partnership exists) or any specific death-reduction number tied to our own work.

### 2. India-specific drug interaction and dosing-safety modeling

Existing interaction checkers (including what most CDS engines license) are built on Western drug databases and formularies. They miss Indian brand-name confusion (the same molecule sold under many different brand names) and Indian dosing conventions.

**What's real today:** Lipi's current CDS engine is keyword and fuzzy-match based, not a real interaction model.

**First achievable step:** a model built from public pharmacology sources (CDSCO drug database, DrugBank, published interaction literature) wired directly into the existing CDS engine. This is the one direction here that is both a research result and a shippable product upgrade in the same build. Fastest path to a real result of anything on this list.

**Safe claim:** "We are building drug-interaction and dosing-safety checking grounded in Indian formularies and prescribing conventions."
**Avoid claiming:** any specific error-reduction percentage before we have measured one.

### 3. Personalized medicine and pharmacogenomics

This direction responds directly to a YC RFS by Ankit Gupta, "AI Personalized Medicine" (quoted below for reference; verify current text before citing externally, RFS pages change):

> "Intelligent agents are enabling a new level of personalization in medical care. We can now use an agent harness like Claude Code to analyze personalized health data, whether that be a diagnostic test, genome scan, EHR data, or wearables information to get highly accurate, user-specific suggestions. At the same time, two big revolutions in science are occurring. First, the cost of generating personalized diagnostics is plummeting... Second, the cost of printing n of 1 genetic therapies is plummeting... Abundant data and intelligence can help patients more accurately assess their disease risk and democratize access to treatments for the most serious illnesses."

**What's real today:** nothing shipped. Lipi captures EHR-shaped structured clinical data today; it does not capture genomic data.

**First achievable step, and the only part of the RFS actually buildable in India near-term:** pharmacogenomics-guided prescribing. When a patient has genomic test results (via a data partnership, not our own sequencing), analyze their actual genetic variants against what's being prescribed, flagging when a patient's specific metabolism changes the right drug or dose versus population-average dosing. Requires one thing we don't have yet: a data partnership with an existing Indian genomic diagnostics company (candidates: MedGenome, Strand Life Sciences, 4baseCare). Worth starting that conversation before the product build.

**Explicitly out of scope near-term:** the RFS's "n of 1 genetic therapy" half (mRNA-delivered individualized treatment). This requires biotech manufacturing and delivery infrastructure that does not exist in India at meaningful scale yet. Chasing this now would put us in "slide about the future" territory, not "shipped this quarter" territory. Do not claim this externally.

**Safe claim:** "We are researching pharmacogenomics-guided prescribing, pending a genomic-data partnership."
**Avoid claiming:** anything implying we do genetic sequencing, genetic therapy design, or currently have genomic data flowing.

### 4. Ambient hardware for the point of care

Using Lipi today still requires a screen (phone or laptop) present during the consultation. The research direction: a small, dedicated hardware device, not a phone or laptop, that sits with the doctor at the point of care and ambiently captures the consultation, feeding the same zero-hallucination pipeline with no typing or screen management mid-consult.

**What's real today:** nothing. This is the earliest-stage, most speculative direction on this list. No hardware has been designed, sourced, or prototyped.

**Open questions before this becomes a real research line, not just an idea:**
- Form factor: worn, deskside, or clip-on. Each has different privacy, battery, and connectivity tradeoffs in an Indian clinic setting.
- Data path: does audio ever leave the device unencrypted, and what's the offline-first story for clinics with unreliable connectivity.
- Cost: hardware bill-of-materials and distribution economics are a completely different cost structure than software, and this vault has no cost model for it yet (compare to [[06_API_COSTS]], which only covers the software path).
- Regulatory: a physical device capturing patient conversations likely has different consent and data-protection obligations than a software app the doctor opts into per-session.

**Safe claim:** "We are exploring what a dedicated ambient-capture hardware device for the point of care would need to solve, including privacy, connectivity, and cost, before committing to build one."
**Avoid claiming:** any specific device name, timeline, or "in development" language. This is pre-research, not even early research yet. Do not let external copy (research page, YC application, investor deck) imply more certainty than this section states.

### 5. Fine-tuned multilingual medical ASR

Sarvam's Saaras (the current default ASR path, see [[01_CURRENT_STATE]]) is a strong general-purpose Indic ASR, not a medical-domain model. It was not trained specifically on Indian clinical speech: doctor-patient code-switching, medical terminology in Hinglish, drug brand names spoken quickly, regional accent variation across specialties and states. Every transcription error at this layer becomes a downstream extraction risk, however good the deterministic extractor is at recovering from it.

**What's real today:** nothing shipped. Using Sarvam's general ASR as-is, unmodified.

**First achievable step:** fine-tune on Lipi's own accumulated, doctor-confirmed transcript corpus, where the "ground truth" is not a separately-labeled dataset but the doctor's own corrections during fact review, which already imply what the ASR should have heard. This is the ASR-layer equivalent of the correction flywheel already wired for extraction (see [[07_DECISIONS]] and [[09_STRATEGIC_ROADMAP]]) — a second, parallel flywheel at the transcription layer instead of the extraction layer.

**Honest limitation:** needs real data volume first, same gate as every other data-hungry direction in this vault (see [[24_HOW_TO_MOVE_AHEAD]] Phase 2). Fine-tuning ASR before there's a meaningful, diverse corpus of confirmed transcripts risks overfitting to a handful of doctors' voices and accents rather than generalizing. Also: any fine-tuning must run on India-hosted infrastructure and training data must never leave India, same constraint as [[27_CLINICAL_MEMORY_ASSISTANT_SPEC]] Section 0 and [[07_DECISIONS]] D017 — this compounds with Sarvam already being an on-shore partner, since fine-tuning their open components or partnering directly with them avoids ever standing up separate foreign infrastructure for this.

**Safe claim:** "We are exploring fine-tuning medical-domain ASR on our own doctor-confirmed transcript corpus, once volume supports it."
**Avoid claiming:** any current accuracy improvement from this direction — nothing has been trained yet.

### 6. A fine-tuned Indian clinical model for CDSS and the memory assistant

The deterministic CDS engine (`cds_engine.py`) is the actual safety moat and does not change: no LLM, generative or otherwise, ever decides what constitutes a drug interaction, an allergy risk, or a dosing hazard. That boundary is non-negotiable (see D003/D004 in [[07_DECISIONS]] and the whole zero-LLM extraction architecture this vault keeps reinforcing). What this direction is about is different: a fine-tuned, self-hosted model that (a) explains a deterministic alert in plain language once it has already fired — narration, never generation of new facts, the same pattern `narrate_practice_insight()` already uses for practice-insight numbers — and (b) powers the retrieval/synthesis layer in [[27_CLINICAL_MEMORY_ASSISTANT_SPEC]], eventually as a fine-tuned replacement for the general-purpose Sarvam-30B currently used there.

**What's real today:** the memory assistant (Phase 1) runs on unmodified, general-purpose Sarvam-30B via API, verified working 2026-07-03. No fine-tuning has happened. `cds_engine.py` remains 100% deterministic, unchanged, and this direction does not propose changing that.

**Sarvam-M is the right base model for this, not a generic open-weight model.** It's open-weight (self-hostable, eliminating per-token API cost at scale) and already Indic-tuned, which beats starting a fine-tune from a generic Llama/Qwen checkpoint. This is the concrete instance of [[10_CONTINUAL_LEARNING_SYSTEM]]'s "Stage 3: Distillation" — the teacher is the whole experienced Lipi system (deterministic extractors, doctor corrections, CDS alert history), the student is a fine-tuned Sarvam-M serving both consumers named above.

**First achievable step:** none yet — this is gated behind real data volume (same Phase 2 gate as Direction 5). The near-term, buildable-now piece is narrower: use Sarvam (API, not fine-tuned) to *narrate* deterministic CDS alerts in plain language, strictly forbidden from inventing a new alert or overriding a deterministic one. That's a small, safe, shippable slice of this direction available today, independent of fine-tuning.

**Honest limitation, stated plainly because it's the one people get wrong:** "is Sarvam on par with a frontier model for CDSS" is the wrong question. The right question is whether *any* generative model, on-shore or not, frontier or not, should make clinical safety determinations at runtime — and the answer, given this product's entire architecture and the reason doctors can trust it, is no. Sarvam-30B tested well (2026-07-03) on retrieval-and-synthesis over *provided* evidence (the memory assistant's actual job). That is not evidence it would be safe generating clinical facts from its own parametric knowledge, and nothing in this vault proposes testing that, because the deterministic engine exists specifically so that question never has to be answered under pressure.

**Safe claim:** "Our clinical safety layer stays fully deterministic; we're exploring a fine-tuned, self-hosted model to explain those alerts in plain language and to power retrieval over doctors' own confirmed history."
**Avoid claiming:** "AI-powered CDSS," "our model detects drug interactions," or anything implying a generative model makes or could make a clinical safety call.

### 7. Continual learning for the clinical memory assistant

[[27_CLINICAL_MEMORY_ASSISTANT_SPEC]] Phase 1 shipped and was live-verified 2026-07-03. It is retrieval, not continual learning in the technical sense — the model's weights never change, and it "feels" like it's getting smarter only because more of a patient's confirmed history becomes available to recall as visits accumulate. That distinction matters and must stay precise in any external communication (see the spec's own caution on this and [[10_CONTINUAL_LEARNING_SYSTEM]]'s new note under Stage 3).

**What's real today:** context-stuffing against Sarvam-30B, verified 2026-07-03 with real API calls against real patient data. Practical usable context ceiling through Sarvam's current API gateway is approximately 38,000-39,000 input tokens for both Sarvam-30B and Sarvam-105B (measured directly by binary-searching request size against the live API, not taken from published specs — third-party sources claimed 32K/128K respectively; the gateway enforces a lower, model-independent ceiling in practice today). At roughly 100 tokens per visit summary (measured from real test prompts), that ceiling comfortably fits several hundred visits for one patient, meaning Phase 1's single-patient scope will not hit this wall for the overwhelming majority of real patients. It becomes the binding constraint once Phase 2 (cross-patient search across a doctor's full patient base) is built, which is exactly why Phase 2 is scoped around `pgvector` retrieval instead of context-stuffing (see the spec, Section 5).

**Rough cost burn at Phase 1 scope:** roughly ₹0.003 per query (sub-paisa) at a realistic ~10-visit history per question, using Sarvam-30B with reasoning disabled. Even at generous usage (20 queries/doctor/day, 22 working days/month), that's roughly ₹1.30/doctor/month — negligible against Sarvam ASR cost and not yet worth a dedicated line in [[06_API_COSTS]], but should be added once the cost-per-consultation ledger is actually built (still not built as of this writing, see [[12_IMPLEMENTATION_GAP_REGISTER]]).

**The real continual-learning direction lives in Direction 6 above**, not here: this direction (7) is the retrieval mechanism that ships now and works within current model weights; Direction 6 is the actual weight-updating mechanism that requires real data volume first. Keep them conceptually and communicatively separate — conflating "the assistant recalls more history over time" with "the assistant is learning" is the exact overclaim this vault's discipline exists to prevent.

**Safe claim:** "The assistant's usefulness compounds with usage because more of a doctor's own confirmed history becomes retrievable over time — this is retrieval, and we're explicit that it's not model retraining."
**Avoid claiming:** "continual learning," "the AI learns from every consultation," or any language implying weight updates happen from this feature specifically. Reserve "continual learning" language for Direction 6, and only once something has actually been fine-tuned.

## Discipline Carried Forward From [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

Applies to all seven directions above, not just the ones it was originally written for:

- Product first, service delivery second, learning moat third, research jargon last, and only when the audience asks.
- Every external claim about a direction above should match its "Safe claim" line exactly, not an enthusiastic paraphrase of it.
- If docs and external copy (research page, pitch deck) disagree on what's shipped versus a direction, this doc is the source of truth; fix the external copy, not this doc.

## What To Do Next

1. Ship direction 2 (drug interaction modeling) first. Fastest to a real, shippable result, dual product/research value.
2. Start the genomic-diagnostics partnership conversation (direction 3) in parallel; it's an outreach task, not a build task, so it doesn't compete for engineering time.
3. Run the AMR public-data gap analysis (direction 1) using Claude Science once direction 2 ships, so there's already one shipped result to point to.
4. Direction 4 (hardware) stays a written direction only until the open questions above have real answers. Do not let it appear on external pages as more than "we are exploring this."
5. Direction 7 (memory assistant retrieval) is already shipped and live-verified — the buildable slice is done; treat it as "shipped," not "researching," in external copy from now on.
6. Directions 5 and 6 (fine-tuned ASR, fine-tuned clinical model) both wait on real data volume — the same Phase 2 gate as [[24_HOW_TO_MOVE_AHEAD]]. Do not start either before that gate opens. The one piece of direction 6 buildable now (Sarvam narrating already-fired deterministic CDS alerts) can start independently, whenever CDS alert volume makes it worth doing.

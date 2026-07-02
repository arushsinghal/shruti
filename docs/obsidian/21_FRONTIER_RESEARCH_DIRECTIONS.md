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

This is not exclusive access. It is available to any paid Claude subscriber. The edge it gives us is execution speed on research we are already positioned to do well, not a moat by itself. The moat is still what [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] already says it is: the evidence-backed data trace Lipi generates from real consultations, which most AI-native research tooling has nothing to point at until a product is live.

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

## Discipline Carried Forward From [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

Applies to all four new directions above, not just the ones it was originally written for:

- Product first, service delivery second, learning moat third, research jargon last, and only when the audience asks.
- Every external claim about a direction above should match its "Safe claim" line exactly, not an enthusiastic paraphrase of it.
- If docs and external copy (research page, pitch deck) disagree on what's shipped versus a direction, this doc is the source of truth; fix the external copy, not this doc.

## What To Do Next

1. Ship direction 2 (drug interaction modeling) first. Fastest to a real, shippable result, dual product/research value.
2. Start the genomic-diagnostics partnership conversation (direction 3) in parallel; it's an outreach task, not a build task, so it doesn't compete for engineering time.
3. Run the AMR public-data gap analysis (direction 1) using Claude Science once direction 2 ships, so there's already one shipped result to point to.
4. Direction 4 (hardware) stays a written direction only until the open questions above have real answers. Do not let it appear on external pages as more than "we are exploring this."

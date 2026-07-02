# 22 — Opus Frontier Research Directions

**Author:** Opus (Claude), acting as R&D-lab founder
**Date:** 2026-07-02
**Status:** Proposal for evaluation. Nothing here is shipped or claimed externally. Directions route to Claude Science (de-risk + design) → Fable/Opus (build into product) → back here (results).

**The two aims this doc serves — and nothing else:**
1. **Solve hard problems in Indian healthcare.** Real care outcomes for real patients, not papers.
2. **Feed that R&D directly back into the product doctors use.** Every research track must terminate in a feature a doctor touches in Lipi. If a direction can't name the feature it becomes, it's not ours.

**Corrected 2026-07-03: we never publish, even novel findings.** An earlier version of this doc (and §8 below) framed publication as an occasional byproduct worth taking for funding/trust. That's superseded — the research exists to make the product and Indian healthcare better, full stop, never for citation credibility. §8 below is kept for its historical reasoning but its conclusion no longer holds. This is a research **lab inside a product company**, not a research company with a product, and it never becomes one that publishes.

**Related:** [[00_HOME]] · [[10_CONTINUAL_LEARNING_SYSTEM]] · [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] · [[21_FRONTIER_RESEARCH_DIRECTIONS]] · [[20_PRODUCT_VISION]] · [[18_YC_PITCH_STRATEGY]]

**Discipline (from [[21_FRONTIER_RESEARCH_DIRECTIONS]] / [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]):** each track is labeled real vs. direction, carries a *Safe claim / Avoid claiming* line, and terminates in a doctor-gated product feature. Research jargon is for the audience that asks.

---

## 0. The unfair asset that powers all of this

Strip away the product. What Lipi *manufactures* as a byproduct of running an OPD service is a data object no hospital, EHR vendor, academic lab, or frontier-model company has:

> **A doctor-confirmed, provenance-linked, certainty-typed clinical observation, spoken in Hindi/Hinglish, at Indian primary-care first contact, with the physician's correction attached** — and, over time, stitched into a **longitudinal patient timeline**.

From `provenance.py` / `learning_service.py`, every fact already carries: `category`, `normalized_value` + exact evidence span, `certainty` ∈ {affirmed, negated, uncertain, queried}, `review_status` ∈ {candidate, confirmed, rejected}, and on edits a correction delta `(before, after, evidence, actor, scope, reason)`.

Four properties compound, and this is what makes *personalized* medicine possible in India where it otherwise isn't:

1. **Primary-care OPD is India's research dark zone** — 100M+ monthly visits, 70–80% of antibiotic prescribing, first-contact diagnosis, almost none of it structured. Lipi sits at first contact.
2. **Hindi/Hinglish clinical speech has no public corpus** — the language the personalization has to run on.
3. **Doctor confirmation is the most expensive supervision signal that exists** — a specialist's accept/reject/edit, for free, as work product.
4. **The longitudinal timeline is per-patient** — the substrate for *this patient*, not *the average patient*.

Every track below leans on at least one. If a proposed direction doesn't, it isn't Lipi's.

---

## 1. The spine: Lipi as India's agent harness for personalized primary care

Read the Ankit Gupta RFS literally. It describes an **agent harness that analyzes personalized health data — diagnostic tests, genome scans, EHR data, wearables — into user-specific suggestions**, riding two cost curves (diagnostics and n-of-1 therapies collapsing in price), and it explicitly invites startups to **support every step of the ecosystem**.

Map that onto Lipi and the position is almost embarrassingly direct:

| RFS ingredient | Lipi today | Lipi's near-term move |
|---|---|---|
| **EHR data** as personalization input | Already the core asset — longitudinal, confirmed, provenance-linked | Turn the timeline into per-patient prescribing + risk intelligence (Tracks A, B) |
| **Agent harness → user-specific suggestions** | Doctor-gated review UI + deterministic pipeline | A point-of-care agent that fuses the patient's whole record into a *personalized*, evidence-grounded suggestion for the doctor |
| **Cheap diagnostics entering market** | Not yet ingested | Be the integration layer that pulls a lab/point-of-care result into the same patient timeline |
| **Genome scans** | Not captured | Bridge via phenotype-first inference now (Track A / D6), genomic validation later — invert the dependency |
| **Wearables** | Not captured | Same integration layer; later horizon |
| **n-of-1 genetic therapy** | Out of scope (no Indian biotech infra — [[21_FRONTIER_RESEARCH_DIRECTIONS]] is right) | Lipi is the *decision + data layer* that identifies candidates, never the therapy maker (§4) |

**The thesis in one line:** *Lipi is the agent harness that turns India's most under-instrumented care setting — primary-care OPD — into personalized medicine, one doctor-gated suggestion at a time.* Personalized medicine in India will not arrive top-down from genome labs. It arrives at first contact, in the doctor's hand, on the record Lipi already holds. Everything below builds a piece of that harness and ships it.

---

## 2. The honest constraint that sets the order of work

Lipi has ~4 pilot clinics and near-zero cumulative volume. Most data-native tracks have *no data yet*. Worse (per [[16_FULL_APP_REVIEW]] F2, confirmed by grep): the correction write-path isn't wired — `routes_fact_review.py` never calls `record_correction()`/`record_false_positive()`. **The single most valuable asset for personalized medicine — the per-patient timeline and the correction stream — is being generated and discarded right now.**

Sequencing that follows from this:

- **Fix the leak first.** Wire the correction ledger + ensure the longitudinal timeline persists cleanly. Sonnet-level engineering, but it is the *fuel tank* for every personalized-medicine track. Every consultation run before it's wired is lost forever. Least glamorous, most urgent.
- **Front-load R&D that runs on public data.** Anything Claude Science can do on public sources *now* (Indian pharmacogenomic allele frequencies, AMR public-data analysis, Hinglish annotation design) has zero dependency on Lipi's data maturing, and de-risks the product features before we build them.
- **Stage the patient-data tracks** for when volume and follow-up exist. Name them now so we capture the fields we'll need.

Tracks tagged **[NOW]**, **[AS DATA FILLS]**, **[LONG-HORIZON]**.

---

## 3. The R&D tracks — each solves an Indian problem AND ships a feature

Every track below is written as: **Indian problem → the R&D (hard question + method) → the product feature it becomes → Claude Science role → data maturity → safe claim.**

---

### TRACK A — Personalized prescribing (the buildable core of personalized medicine)

**Indian problem.** OPD prescribing is *population-average*, not patient-specific. The same drug and dose go to the 40kg elderly diabetic with declining renal function and the 90kg adult. Patients who already failed a drug class get it again because no one remembers. Polypharmacy in the elderly is unmanaged. This is silent, everyday harm at population scale — and it is exactly the "user-specific suggestions" the RFS asks for.

**The R&D (hard part).** Two linked problems:
1. **Sequencing-free pharmacogenomic phenotyping** (the hard reframe of doc 21's Direction 3 — see §5). Infer drug-metabolizer *phenotype* from the pattern of prescribing → treatment failure / adverse event / dose change across follow-up visits, *without* a genome. For CYP2C19 (clopidogrel, PPIs, escitalopram), CYP2D6 (codeine, tramadol, many antidepressants), TPMT (azathioprine), metabolizer status shows up *phenotypically*. Indian populations have distinct allele frequencies and are badly under-characterized. Build the phenotype map from outcomes first; use genomics to *validate* later.
2. **Patient-specific dose/drug-choice modeling** from the individual's own longitudinal record — renal/hepatic proxies, age/weight, prior response, comorbidity, allergy — layered on population priors.

**The product feature.** At point of care, Lipi shows the doctor a *patient-specific* flag alongside the prescription: *"This patient's history suggests reduced clopidogrel response — consider alternative,"* or *"renal dosing indicated,"* or *"failed this class in March."* Doctor-gated, provenance-backed, never auto-prescribed. This is the CDS engine graduating from generic drug-interaction rules ([[cds_engine.py]], 4 hardcoded interactions today) to *personalized* prescribing intelligence. It's also the highest-willingness-to-pay feature in [[20_PRODUCT_VISION]] made real.

**Claude Science role.** NOW: synthesize Indian CYP2C19/CYP2D6/TPMT allele-frequency literature; identify which drug-gene pairs have strong enough phenotypic signal to infer from outcomes; design the phenotype-inference estimator and its confounders (adherence, drug quality/stock-outs, dose error). Output = the evidence-graded data contract the product feature is built against.

**Data maturity.** Literature/design NOW; the inference engine needs the follow-up loop (doc 20 Phase 3) live + volume — LONG-HORIZON for the full version, but a *rules-from-literature* v1 ships early.

**Safe claim:** *"We are building patient-specific prescribing guidance grounded in the patient's own record and Indian population evidence."*
**Avoid claiming:** individual genomic PGx guidance, that we sequence anything, or any clinical PGx recommendation before genomic validation. Most over-claimable track in the doc — hold the line.

---

### TRACK B — Personalized early detection at first contact

**Indian problem.** India's biggest killers present *late* at first contact and get missed: TB (world's largest burden, ~2.8M cases/yr — the persistent-cough patient gets repeat empirical antibiotics for weeks before anyone thinks TB), undiagnosed diabetes progressing to nephropathy, early cardiac risk. The diagnostic delay *is* the mortality. Primary care is where the signal first appears and where it's currently invisible.

**The R&D (hard part).** Turn the *longitudinal OPD trajectory* into an early-risk signal: e.g. recurrent cough syndrome + repeat antibiotic courses without resolution + weight/appetite mentions → TB-workup candidate; trajectory patterns → early nephropathy / cardiac risk. This is longitudinal risk modeling on confirmed first-contact data. As cheap diagnostics/wearables enter (the RFS cost curve), the same engine fuses them in — Lipi is the integration point.

**The product feature.** A doctor-facing *"consider workup"* flag on the patient's record — *"trajectory suggests TB workup / sputum test,"* never a diagnosis, never patient-facing. Aligns with the national TB program (NTEP), doesn't compete with it. Massive care asymmetry, so the D004 doctor-review boundary is absolute and both error rates must be characterized honestly.

**Claude Science role.** Literature synthesis on OPD diagnostic delay in India (TB first); design the trajectory-feature study and the validation approach (against confirmed outcomes via partner clinics / NTEP linkage where possible).

**Data maturity.** AS DATA FILLS — needs longitudinal timelines with return visits.

**Safe claim:** *"We are researching whether primary-care visit trajectories can surface workup candidates earlier for the doctor."*
**Avoid claiming:** that Lipi detects/diagnoses any disease; any sensitivity number pre-validation; anything patient-facing.

---

### TRACK C — Precision antibiotic use / AMR as community-level personalization

**Indian problem.** India carries the world's largest AMR death burden (~250k–300k/yr). Empirical antibiotic prescribing in primary care is blind — the doctor doesn't know what's failing *in their locality this month*. Lab-based surveillance (ICMR AMRSN, WHO GLASS) is lagging and hospital-biased.

**The R&D (hard part, the real upgrade of doc 21's Direction 1).** Test whether **empirical antibiotic escalation in primary care — first-line → second-line for the same syndrome, same patient or same locality, short window — is a *leading* indicator of local resistance that precedes culture-based surveillance.** Validate the prescribing-derived signal against AMRSN lab data where they overlap (this is the honest core: prescribing is a proxy, and the R&D *quantifies how good a proxy it is*).

**The product feature.** *Personalized-to-locality* empirical prescribing guidance in the CDS engine: *"first-line for this syndrome is showing rising failure in your area — consider X."* This is precision antibiotic prescribing — personalized medicine at the community level — shipped to the doctor. Also the strongest public-good story Lipi has.

**Claude Science role.** NOW (zero data dependency): the public-data visibility-gap computation (spec'd in doc 21) + design of the AMRSN validation study, including the confounders (seasonality, stock-outs, doctor idiosyncrasy, referral bias). Then the escalation-signal method once density exists.

**Data maturity.** Public-data half NOW; real signal needs geographic density — AS DATA FILLS.

**Safe claim:** *"We are researching whether primary-care prescribing behavior is a leading indicator of AMR, validated against public surveillance data, to give doctors better empirical guidance."*
**Avoid claiming:** that we *do* AMR surveillance; any death-reduction or lead-time number pre-measurement.

---

### TRACK D — The trust substrate that makes A, B, C accurate and safe

This is not a separate product; it's the accuracy-and-safety floor under everything above. Personalized suggestions built on mis-extracted Hinglish or ungrounded facts are *dangerous*, not helpful. So this track's "feature" is: **the personalization engine is trustworthy enough for a doctor to rely on.**

**D-1. Hinglish clinical understanding.** `[NOW]`
- *Problem:* the personalization runs on code-switched speech no model handles — *"pehle sugar high tha, ab control mein hai"* (historical vs. current), *"shayad BP high hai"* (hedged). Get the epistemic × temporal state wrong and Track A/B produce wrong personalized advice.
- *R&D:* joint modeling of epistemic state (already structured in `provenance.py`) × temporal state (historical/current/planned) over Hinglish, with doctor-confirmed labels.
- *Product:* fewer doctor corrections, faster review, and — critically — correct inputs to the personalization engine. Directly hardens the `provenance.py` logic that had the negated-symptom incident.
- *Claude Science:* annotation schema + eval protocol + baselines vs. frontier models.

**D-2. Certified grounding.** `[NOW]`
- *Problem:* a personalized prescribing suggestion built on a hallucinated fact is a liability. Lipi claims "zero hallucination by design" — turn it into a stress-tested guarantee.
- *R&D:* formalize "every asserted fact is entailed by a transcript span," bound the failure rate under distribution shift, build an adversarial benchmark that tries to break grounding.
- *Product:* the safety guarantee that lets personalization ship at all, and the regulatory/medico-legal moat (ABDM, insurers, later CDSCO-style clearance).
- *Claude Science:* formalize the guarantee; design the adversarial suite (homophone ASR errors, negation-scope traps, coreference across code-switch).

**D-3. Correction economics.** `[AS DATA FILLS]`
- *Problem:* we don't know how fast the system improves per doctor correction, or whether corrections in one specialty degrade another (catastrophic forgetting). Without this we can't tell when the personalization engine is reliable enough.
- *R&D:* measure the learning curve (corrections → extraction accuracy) by specialty/category/scope; probe forgetting; design PHI-safe federated aggregation over deltas (never raw PHI — doc 10 boundary).
- *Product:* tells us when to trust the engine, when to fine-tune vs. retrieve (answers doc 10's open questions with data), and quantifies the moat honestly.
- *Precondition:* wire the correction ledger (§2).

**Safe claim (whole track):** *"We are building the accuracy and safety foundation — Indian clinical language understanding and verifiable grounding — that personalized guidance requires."*
**Avoid claiming:** "certified/provably safe" before a written proof + passed adversarial suite; any accuracy number pre-measurement.

---

## 4. The genome / wearables / n-of-1 future — Lipi's honest place in the ecosystem

The RFS's second cost curve (n-of-1 genetic therapies, mRNA delivery) is real but its infrastructure does not exist in India at scale, and [[21_FRONTIER_RESEARCH_DIRECTIONS]] is right to keep therapy-making out of scope. Lipi's role, stated honestly and ambitiously: **Lipi is the data-and-decision layer of the ecosystem, not the therapy maker.** The RFS explicitly invites startups to "support every step" — Lipi supports the *first* step, the one that decides *who* needs personalized intervention and *what data* to gather, at the point of care.

As genome sequencing and point-of-care diagnostics get cheap in India (the RFS's first curve), Lipi is the integration harness that pulls those results into the patient timeline and turns them into a doctor-gated suggestion. Track A's phenotype-first inference is the bridge: build the phenotype map from outcomes now, and when genomic data arrives it *validates and sharpens* what Lipi already inferred — rather than Lipi waiting on a genome lab to begin.

**Safe claim:** *"As personalized diagnostics reach Indian primary care, Lipi is the integration and decision layer that turns them into doctor-gated, patient-specific guidance."*
**Avoid claiming:** that Lipi sequences genomes, designs therapies, or has genomic/wearable data flowing today.

---

## 5. Where I disagree with the current vault (pushback)

- **Pharmacogenomics dependency is backwards (doc 21, Direction 3).** Making a genomic-data partnership the *prerequisite* makes Lipi a downstream consumer of someone else's asset. Track A inverts it: infer phenotype from outcomes first, use genomics to validate. Stronger science, stronger product, stronger negotiating position — and it ships a feature without waiting on a partner.
- **AMR "gap analysis" undersells the asset (doc 21, Direction 1).** The gap analysis is a warm-up. The product-bearing, only-Lipi contribution is *prescribing-as-leading-indicator* feeding locality-personalized empirical guidance (Track C).
- **The correction flywheel was called a moat but was a leak (doc 09 §Technical Moats, doc 16 F2) — RESOLVED 2026-07-03.** It was generating the exact signal personalized medicine needs and discarding it. That write path is now wired (`record_correction()`/`record_false_positive()` called from every doctor action) — the precondition for Tracks A, B, D-3 is met, though the richer `LearningEvent`/`MemoryCandidate` schema those tracks eventually need is still future work.
- **Ambient hardware (doc 21, Direction 4) is not research — agreed, keep it off this list.** It's a BOM/product exploration; don't let it absorb R&D attention.
- **My own prior draft over-indexed on publication — corrected, then corrected again.** This version terminates every track in a doctor-facing feature. §8's original "publish selectively" framing has since been overturned too (2026-07-03): Lipi never publishes, even novel findings.

---

## 6. How to use Claude Science — as the R&D engine for the product, not a paper mill

Claude Science is for questions where **the answer is unknown and the method is unsettled** — used *upstream* to de-risk and design a product feature before Fable/Opus builds it. The pipeline for every track is the same:

> **Claude Science** (public-data analysis, literature synthesis, method + study design, confounder mapping) → produces the *evidence-graded data contract / study protocol* → **Fable/Opus** builds the doctor-facing feature against it → **results flow back here** and into the next Claude Science cycle.

Sequencing:

1. **Now, zero data dependency — run in parallel:**
   - **Track A literature half:** Indian CYP2C19/CYP2D6/TPMT allele frequencies + which drug-gene pairs are phenotypically inferable → the data contract for the personalized-prescribing feature.
   - **Track C public-data half:** AMR visibility-gap computation + AMRSN validation-study design → the protocol for locality-personalized antibiotic guidance.
   - **Track D-1 design half:** the epistemic×temporal Hinglish annotation schema + eval protocol → what Fable labels against.
   - **Track D-2:** formal grounding guarantee + adversarial suite design.
2. **After the correction ledger is wired + data fills:**
   - **Track D-3:** learning-curve + forgetting experiment design.
   - **Track A/B inference engines:** the phenotype estimator; the trajectory risk models.
3. **Long-horizon:** genomic-validation study design (Track A), diagnostic/wearable fusion (Track B).

**What to keep OFF Claude Science:** wiring the correction ledger (Sonnet); CDS interaction-data entry (Sonnet); the admin/TPA/WhatsApp product tracks (Fable/Opus). A research workbench is wasted on specified build work.

**What Claude Science needs from you each time:** the precise question, named public data sources, the confounders you already suspect, the target product feature, and the *safe-claim/avoid-claiming* line so its output stays inside the vault's honesty discipline.

---

## 7. Recommended portfolio (if you run three threads)

Chosen to span *ships-soon-into-product*, *biggest-Indian-problem*, and *the-personalized-medicine-spine*:

1. **Track A — personalized prescribing.** The direct answer to the Ankit Gupta RFS, the highest-value product feature, and the personalized-medicine core. Start the Claude Science literature/data-contract work now.
2. **Track C — precision antibiotic use / AMR.** India's largest burden; starts on public data now; ships as locality-personalized guidance.
3. **Track D-1 — Hinglish understanding.** The accuracy floor under A and B; improves the shipped product immediately.

Non-negotiable precondition under all three: **wire the correction ledger + persist the longitudinal timeline this month.** No fuel, no engine.

---

## 8. Publication stance — CORRECTED 2026-07-03: never publish

**Superseded.** The original version of this section argued for publishing selectively when it buys funding, doctor trust, or a partnership (e.g. a validated AMR result or a Hinglish benchmark). That reasoning is overturned: Lipi does not publish, even when a finding is genuinely novel. The research exists to make the product and Indian healthcare better — never for citation credibility or external validation. Any credibility Lipi earns comes from what the product visibly does for a doctor and a patient, not from a paper. Kept below for historical record of the reasoning that was rejected, not as current policy.

*Original text, for history:* "Publish only when it directly buys funding, doctor trust, or a partnership — e.g., a validated AMR leading-indicator result that helps a government or grant conversation, or a Hinglish benchmark that recruits collaborators. Never delay a product feature to shape a paper. Never claim a result externally before it clears the avoid-claiming line. Credibility serves the two aims in the header; it does not replace them."

---

## 9. Hard boundaries (unchanged, every track)

From [[10_CONTINUAL_LEARNING_SYSTEM]], [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]], [[07_DECISIONS]]:

- No proof → no fact. R&D never relaxes the clinical-fact evidence gate.
- Doctor review required before any clinical output is final (D004). No track produces patient-facing or autonomous clinical decisions — everything is a *suggestion to the doctor*.
- No training on raw PHI without a separate privacy/consent/compliance design. Learning is over de-identified deltas and behavioral/lexical signal.
- Personalized ≠ autonomous. Every personalized suggestion is doctor-gated and provenance-backed.
- Every external claim matches its *Safe claim* line, not an enthusiastic paraphrase.
- If a track can't point to one of the four unfair data properties in §0 *and* name the product feature it becomes, it isn't ours.

---

*Proposal only. Pick the portfolio; work routes Claude Science (design) → Fable/Opus (build into product) → back here (results).*

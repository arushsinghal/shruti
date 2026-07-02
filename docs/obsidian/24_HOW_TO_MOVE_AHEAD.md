# 24 — How To Move Ahead (Start Here When Confused)

**Author:** Opus (Claude)
**Date:** 2026-07-02
**Purpose:** One spine that unifies product + research + revenue into a single sequence, so there is never more than a handful of things to think about at once. If you feel scattered, read this doc and ignore the rest until the current phase's gate is passed.
**Related:** [[22_OPUS_FRONTIER_RESEARCH]] · [[23_EXECUTION_ROUTING]] · [[20_PRODUCT_VISION]] · [[18_YC_PITCH_STRATEGY]] · [[17_ABDM_DHIS_DSC_COMPLIANCE]]

---

## The vision, stated once

**A billion-dollar Indian healthcare AI research company — OPD-as-product is the wedge, personalized medicine is the destination.**

Not "a research company" and separately "a product." One thing:

> The OPD product is how we get the data. The data is how we do research nobody else can. The research is how the product becomes personalized medicine that nobody can copy. Revenue from the product pays for all of it.

## The one loop (this is the whole company)

```
   OPD product (doctors use it, we get paid)
              │  generates
              ▼
   Doctor-confirmed longitudinal data  ◄── the flywheel (must be wired!)
              │  enables
              ▼
   Research: personalized prescribing, AMR, early detection
              │  ships back as
              ▼
   Product features no competitor can build
              │  attracts more doctors →  back to top, bigger
```

**Correction (2026-07-02, same day):** an earlier version of this doc over-gated research behind "wait for population data to accumulate." That was wrong for most of it. There are two different kinds of personalization, and only one needs volume:

- **N=1 personalization** — literature-based rules applied to a patient's OWN already-extracted record (their age, their diagnoses, their prior meds, their prior visits). This needs **zero new data collection**. It works from visit 1 or 2 for that patient, today, for every patient in the system right now.
- **Population-level inference** — mining patterns *across many patients* (true phenotype inference from outcomes, true locality-level AMR trends). This is the only kind that genuinely needs volume, because the statistics require N.

Almost everything in [[22_OPUS_FRONTIER_RESEARCH]] is the first kind, or runs on public data. That means **most core research features ship as product code this week**, in parallel with the business steps below — not after months of data accumulation. See "Phase 0b" below for the full named list.

**Where you are right now:** before the first paid consultation, but NOT before you can ship research-derived features — those two things are independent.

---

## The four phases (you are in Phase 0)

Each phase has: what the PRODUCT does, what the DATA/infra does, what RESEARCH does, and the GATE that lets you move to the next phase. Do not work on a later phase's items. That is the discipline that removes the confusion.

---

### PHASE 0 — Prove the loop exists (NOW → next ~6 weeks)

The goal is not scale. The goal is to prove one full turn of the loop is possible: one doctor pays, one record earns DHIS, the data starts being captured, and research design is queued.

**Product / business (only Arush can do these — highest leverage in the company):**
1. **Charge the 4 doctors ₹2,000/month.** This week. ₹0 → any number changes what the company *is*.
2. **Register on sandbox.abdm.gov.in, get ABDM credentials.** This unblocks the single strongest asset (government-paid distribution). It's a signup, not code.
3. **Ship TPA claim packet v1** (the revenue-recovery feature from [[20_PRODUCT_VISION]]) — this is what makes a consult worth ₹1,500 instead of ₹150.

**Data / infra (executor — this is the bridge between product and research):**
4. **Wire the correction flywheel** — `record_correction()` in `routes_fact_review.py` + longitudinal timeline persistence. This is a *product* task that is *also* the precondition for ALL research. It serves both agendas at once. It is the most important build in the company right now because everything downstream is empty until it's done. → **Sonnet** (see [[23_EXECUTION_ROUTING]]).

**Research (zero cost to product — runs entirely in parallel, only needs Arush to paste 3 prompts):**
5. **Paste the 3 Claude Science briefs** from [[23_EXECUTION_ROUTING]] Part 1 — Indian pharmacogenomics evidence map, AMR public-data + validation design, Hinglish schema. These run on PUBLIC data, need no product data, and produce the design/data-contracts for later. They do not compete for engineering time because they're literature/design, not build.

**GATE to Phase 1 (all five, then move on):**
- ✅ ≥1 doctor paying
- ✅ ABDM sandbox credentials in hand
- ✅ TPA claim v1 shipped
- ✅ correction flywheel wired (data now being captured, not discarded)
- ✅ 3 Claude Science briefs delivered (research designs sitting ready)

Business steps 1–3 are on Arush's critical path and don't block engineering. Step 4 (flywheel) is the precondition for the *population-level* research only (Phase 2). None of the above blocks Phase 0b below — build it in parallel, this week.

---

### PHASE 0b — Core research features, ship this week (parallel to Phase 0, not after it)

All 13 of these run on public evidence and/or each patient's own already-extracted record. None need population volume. None wait for the flywheel wiring, ABDM, or revenue. Build them now.

**Personalized prescribing safety — N=1, uses existing extracted facts (age, diagnoses, meds), no genomic data needed:**
1. **G6PD high-risk-drug flag** — primaquine, dapsone, nitrofurantoin, sulfonamides, high-dose aspirin → caution + screening suggestion. Public epidemiology only.
2. **HLA-B\*15:02 carbamazepine/phenytoin SJS-risk flag** — elevated Indian/Asian population risk. Public data only.
3. **CYP2C19–clopidogrel non-response caution** — surfaced on clopidogrel post-cardiac-event prescriptions. Public data only.
4. **Renal-dose-adjustment engine** — reads existing diagnosis facts (CKD, nephropathy) + age → flags renally-cleared drugs.
5. **Hepatic-dose-adjustment engine** — same pattern for liver disease.
6. **Elderly/polypharmacy caution engine** — Beers-criteria-style, adapted to Indian formulary.
7. **"Patient failed this drug/class before" flag** — cross-references that one patient's own visit history, works from visit 2 onward.

**Drug safety and coding — pure data engineering, public sources:**
8. **Drug-drug interaction expansion** — CDS engine from 4 hardcoded interactions to dozens, CDSCO/DrugBank sourced.
9. **ICD-10 coverage expansion** — top Indian OPD diagnoses, public lookup table.

**Early detection — N=1, uses that one patient's own timeline, no population data needed:**
10. **Antibiotic-escalation flag, per-patient** — "this patient already failed first-line for this syndrome."
11. **TB-risk trajectory flag, per-patient** — recurrent cough + repeat unresolved antibiotic courses in one patient's own record.

**Extraction accuracy — hardens all of the above:**
12. **Hinglish epistemic×temporal extraction upgrade** — rule engineering on the existing deterministic extractor to correctly separate historical ("pehle tha") from current findings.

**Research artifact, runs standalone:**
13. **AMR visibility-gap script** — pure public-data pull + computation (AMRSN, WHO GLASS). Ships as a script regardless of anything else; informs the design of #10/#11's future population-level version.

**Sequencing:** items 1–3 and 8 need the Claude Science evidence synthesis (Brief 1, Brief 2 in [[23_EXECUTION_ROUTING]]) done first so the rules are correctly sourced — that's a same-day literature pass, paste the briefs today. Items 4–7, 10–12 can start immediately on existing code. Item 13 runs standalone immediately.

**Executor:** Opus for the safety-judgment items (1–7, 10–11), Sonnet for pure data entry (8–9), Opus/Fable for the extraction upgrade (12), Sonnet or Claude Science for the script (13). See [[23_EXECUTION_ROUTING]] for the full routing rule.

**What genuinely cannot ship this week:** only the *population-level* phenotype-inference engine (mining metabolizer patterns across many patients) and the true *locality-level* AMR leading-indicator (across many clinics). Both need real N — not because of a policy gate, but because the statistics require it. Everything else above has no such requirement.

---

### PHASE 1 — Scale the wedge, fill the tank (months ~1–6)

**Product:** get to 20–50 paying clinics on the OPD product (SOAP + TPA + patient follow-up loop). This is simultaneously your revenue engine AND your data engine — every consultation now fills the flywheel that used to leak.

**Data:** volume crosses the threshold where the correction stream and the longitudinal timeline become usable for the *population-level* research (the part Phase 0b couldn't ship).

**Research:** the Phase 0b features (already live since Phase 0) are now running across many more patients and clinics — more coverage, more real-world tuning of the literature-based rules, more Hinglish examples hardening extraction.

**GATE to Phase 2:**
- ✅ meaningful MRR (revenue thesis proven, YC-ready)
- ✅ data volume past the point where correction-economics can be measured
- ✅ Phase 0b features live across the full paying clinic base, not just pilots

---

### PHASE 2 — The research moat compounds (months ~6–18)

Now there is data, so the *data-native* research runs — the stuff no competitor can do because they don't have the data:

- **Correction economics / scaling law** (how fast we improve per doctor correction) → tells us when to fine-tune vs. retrieve.
- **Sequencing-free pharmacogenomic phenotype inference** (Track A full) → personalized prescribing that learns from real Indian outcomes.
- **TB / early-detection trajectory signals** (Track B).
- **AMR leading-indicator** goes live as locality-personalized antibiotic guidance (Track C).

**Product:** personalized-medicine features competitors literally cannot build. This is where "AI research company" becomes *true* rather than aspirational — the research is now producing an ever-deepening moat.

**This is where the billion-dollar valuation logic actually kicks in:** you're no longer "an AI scribe." You're the personalized-primary-care intelligence layer for India, with a data moat that gets deeper every month and a government subsidy paying your distribution.

---

### PHASE 3 — The research-company identity, fully realized (18+ months)

- **Distillation** of doctor-corrected traces into a specialized Indian primary-care model (the foundation-model bet).
- **Integration layer** for cheap diagnostics / genome / wearables as they arrive — Lipi as the agent harness in the Ankit Gupta ecosystem ([[22_OPUS_FRONTIER_RESEARCH]] §4).

This is the "billion-dollar Indian healthcare AI research company" in full. You do not think about this now. It is the destination, printed here only so Phases 0–2 are built to reach it.

---

## The two jobs, kept separate so you don't collide with your own team

**Arush's job (do not delegate — these are the value-unlock steps):**
- Phase 0: charge the doctors, get ABDM creds, paste the 3 briefs.
- Ongoing: sales, doctor relationships, co-founder, funding, the ABDM/DHIS regulatory path.

**Executors' job (dispatch per [[23_EXECUTION_ROUTING]]):**
- Now: Sonnet wires the flywheel; Fable/Opus ship TPA v1.
- Later phases: as the gates open, per the dispatch table.

You (Arush) are the bottleneck on the *business* steps and nobody else can do them. The build and research steps have executors. Don't spend your scarce time on build; spend it on revenue + distribution + credentials, which only you can move.

---

## The one risk to keep naming

The research is intoxicating; charging four doctors ₹2,000 and filling an ABDM form is not. **The failure mode is doing the exciting research first and never proving the boring loop.** If revenue never comes, you have a research lab with no company under it. The order is fixed: **prove the loop → then the research makes you frontier.** Never the reverse.

---

## If you remember only one thing

> Two tracks run in parallel, not in sequence. Arush: pay, credentials, TPA v1. Engineering: wire the flywheel AND ship the 13 Phase 0b research features this week, using public evidence and each patient's own existing record — none of it needs to wait for volume. Only the population-level inference work (true phenotype mining, true locality AMR trends) waits for real N, and that's Phase 2, not now.

*This doc is the counterweight to [[22_OPUS_FRONTIER_RESEARCH]]. That doc is where you're going; this doc is the next step. When in doubt, this one wins.*

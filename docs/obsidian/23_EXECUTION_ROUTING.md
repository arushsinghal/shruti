# 23 — Execution Routing: Claude Science Briefs, Continual Learning, Model Assignment

**Author:** Opus (Claude)
**Date:** 2026-07-02
**Purpose:** Turn [[22_OPUS_FRONTIER_RESEARCH]] into things you can actually dispatch. Three ready-to-paste Claude Science briefs, the continual-learning build-vs-research split, and one rule for which model does what.
**Related:** [[22_OPUS_FRONTIER_RESEARCH]] · [[10_CONTINUAL_LEARNING_SYSTEM]] · [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

---

## Part 0 — The one routing rule (read first)

There are four executors. They are not interchangeable. Assign by *what kind of hard the task is*:

| Executor | Use it for | Do NOT use it for |
|---|---|---|
| **Claude Science** | The answer is unknown *and* the method is unsettled. Literature synthesis, public-data analysis, study/estimator design, confounder mapping. Produces a **data contract or study protocol**, not code. | Anything already specified. Build work. Data entry. |
| **Fable (mythos-class)** | One large build where *cross-file coherence over a big surface* is the bottleneck. Whole subsystems architected in one pass. | Research design. Narrow single-file changes (overkill). |
| **Opus** | Judgment-heavy, safety-sensitive engineering. Anything touching the clinical-fact boundary, memory scoping, promotion policy, personalized-prescribing wiring. | Pure research design (that's Claude Science). |
| **Sonnet** | Narrow, fully-specified engineering. Ledger wiring, CRUD, one test, a lookup table, data entry. | Anything requiring a safety judgment call. |

**The mistake to avoid:** sending research design to Fable, or sending build work to Claude Science. A mythos-class model is Karpathy — you don't hand him CRUD, and you don't ask a research workbench to write your API routes.

---

## Part 1 — The three Claude Science briefs (paste each verbatim)

Each is self-contained. Paste one per Claude Science session. Each ends with the *safe-claim guardrail* so its output stays inside the vault's honesty discipline.

---

### BRIEF 1 — Track A: Indian pharmacogenomic evidence for personalized prescribing

```
CONTEXT
I run Lipi, an AI-native primary-care (OPD) service in India. We hold longitudinal,
doctor-confirmed clinical records: diagnoses, prescriptions, and follow-up outcomes.
We want to build a POINT-OF-CARE, DOCTOR-GATED feature that flags patient-specific
prescribing risks. We do NOT have genomic data. We want to (a) know which drug-gene
pairs matter most for INDIAN populations, and (b) know which of those produce a
PHENOTYPIC signal we could infer from prescribing→outcome patterns without sequencing.

THE QUESTION
For the Indian population specifically, produce an evidence-graded map of the
highest-value pharmacogenomic drug-gene interactions for primary-care prescribing.
For each pair, tell me:
  1. The gene/variant and its allele frequency in Indian subpopulations (cite sources;
     flag where Indian data is thin or extrapolated from other populations).
  2. The affected drug(s) commonly prescribed in Indian OPD.
  3. The clinical consequence of the variant (e.g. reduced efficacy, toxicity, SJS risk).
  4. Evidence level (use CPIC 1A/1B/2A/2B and PharmGKB levels).
  5. CRITICAL: whether the metabolizer/risk status is PHENOTYPICALLY OBSERVABLE from
     prescribing→outcome data alone (treatment failure, adverse event, dose change on
     follow-up) — i.e. could we infer likely status WITHOUT a genome? Rate the strength
     of that phenotypic signal and name the observable outcome that would carry it.

PAIRS TO PRIORITIZE (India-relevant; add others you find stronger)
  - CYP2C19 × clopidogrel (efficacy); × PPIs; × escitalopram/citalopram
  - CYP2D6 × codeine/tramadol; × tricyclics/SSRIs
  - NUDT15 and TPMT × azathioprine/6-MP  (NUDT15 is more relevant in South Asians than TPMT — verify)
  - CYP2C9 / VKORC1 × warfarin
  - HLA-B*15:02 × carbamazepine (SJS/TEN risk — check Indian frequency)
  - HLA-B*57:01 × abacavir
  - G6PD deficiency × primaquine/dapsone/nitrofurantoin (high India relevance; often
    already testable/known — treat as a special high-value case)

SOURCES TO USE
CPIC guidelines, PharmGKB, published Indian pharmacogenomics literature, Indian Genome
Variation Consortium / IndiGen / GenomeIndia allele-frequency data, and any Indian
hospital PGx studies. Name every source. Where Indian-specific data is missing, say so
explicitly rather than substituting Western frequencies silently.

OUTPUT I WANT
A ranked table (highest product+care value first) that becomes the DATA CONTRACT for a
prescribing-flag feature: for each pair, the rule we'd encode, the evidence level, the
Indian allele frequency (or "unknown — needs local data"), and the phenotypic-signal
strength. Plus a short section: which 3 pairs should ship FIRST as literature-based
rules (no inference needed), and which need our outcome data to mature before we attempt
phenotype inference.

CONFOUNDERS TO ADDRESS in the phenotype-inference section
adherence, drug quality / counterfeit / stock-outs, fixed-dose-combination prescribing
(India-specific), dose error, and OTC self-medication before the visit.

SAFE-CLAIM GUARDRAIL (respect in all outputs)
Frame everything as decision SUPPORT for a doctor, never autonomous prescribing. Do not
imply we sequence anything. Do not state a clinical PGx recommendation as validated for
Indian patients unless the Indian evidence supports it — grade honestly.
```

---

### BRIEF 2 — Track C: AMR as a leading indicator + validation design

```
CONTEXT
I run Lipi, an AI-native primary-care (OPD) service in India. We will accumulate
structured, doctor-confirmed data linking SYNDROME → ANTIBIOTIC PRESCRIBED → FOLLOW-UP
OUTCOME, with locality, at primary-care first contact. India has the world's largest
AMR death burden, and existing surveillance (ICMR AMRSN, WHO GLASS) is hospital-lab
based — lagging and blind to the ~70-80% of antibiotic use that happens in primary care.

THE TWO QUESTIONS
1. PUBLIC-DATA GAP ANALYSIS (do this now, zero dependency on my data):
   Using only public data, quantify the primary-care visibility gap in Indian AMR
   surveillance. What fraction of Indian antibiotic consumption is primary-care/OTC vs.
   hospital? What fraction of AMRSN/GLASS surveillance samples come from primary care vs.
   hospital? Compute the mismatch programmatically and state the uncertainty honestly.
2. VALIDATION-STUDY DESIGN (the real research):
   Design a study to test the hypothesis: "Empirical antibiotic ESCALATION in primary
   care (first-line → second-line for the same syndrome, same patient or same locality,
   within a short window) is a LEADING indicator of local antimicrobial resistance that
   precedes culture-based surveillance." The design must specify how to validate the
   prescribing-derived signal against AMRSN lab-confirmed resistance in districts where
   they overlap, including lead-time estimation. Prescribing is a PROXY — the study's job
   is to quantify how good a proxy it is.

SOURCES TO USE
ICMR AMRSN annual reports, WHO GLASS India country data, India's National Action Plan on
AMR (NAP-AMR), NCDC, ICMR treatment guidelines, and published studies on Indian
antibiotic consumption (including the Lancet/GRAM-type consumption estimates). Name
every source and its year.

CONFOUNDERS TO ADDRESS
seasonality (monsoon-linked infection surges), drug stock-outs, individual doctor
prescribing idiosyncrasy, referral bias (sicker patients escalate for non-resistance
reasons), OTC antibiotic access before the visit, and fixed-dose-combination prescribing.

OUTPUT I WANT
(a) A runnable analysis + short memo on the visibility gap with sourced numbers and
uncertainty ranges. (b) A study protocol for the leading-indicator validation:
hypothesis, signal definition, the AMRSN validation approach, confounder controls,
negative controls, and what a positive/negative result would look like. (c) A one-line
statement of the PRODUCT feature this enables: locality-personalized empirical antibiotic
guidance to the doctor.

SAFE-CLAIM GUARDRAIL
Do not claim we DO AMR surveillance. No death-reduction or lead-time number until
measured. Prescribing is a proxy — say so everywhere. Output is guidance to a doctor.
```

---

### BRIEF 3 — Track D-1: Hinglish clinical understanding — annotation schema + eval

```
CONTEXT
I run Lipi, an AI-native primary-care service in India. Our clinical extraction runs on
CODE-SWITCHED Hindi-English (Hinglish) consultation speech. Getting negation, uncertainty,
and TIME wrong produces wrong downstream clinical facts (and, soon, wrong personalized
prescribing advice). Our pipeline already structures an EPISTEMIC axis per fact:
{affirmed, negated, uncertain, queried}. What no one has built is a benchmark or a model
for the joint EPISTEMIC × TEMPORAL state of clinical facts in Hinglish speech.

Examples of the hard cases:
  - "pehle sugar high tha, ab control mein hai"  (historical high; current controlled)
  - "shayad BP thoda high hai"  (hedged, present — should be 'uncertain', never affirmed)
  - "dard nahi hai ab, pehle tha"  (current negation + past affirmation, same symptom)
  - "sugar check karwa lo"  (planned/ordered, not a current finding)

THE TASK (this is a DESIGN brief — no product data needed to start)
1. Design an annotation schema for clinical facts in Hinglish that jointly captures:
   - epistemic state: affirmed / negated / uncertain / queried
   - temporal state: historical / current / planned
   - and the interaction (e.g. historical-affirmed vs current-negated of the same entity)
   Make it annotatable by a clinically-trained annotator with a written guideline and
   inter-annotator-agreement protocol.
2. Design the evaluation protocol: metrics, held-out split strategy, and how to measure
   whether a system gets the epistemic×temporal state right (not just entity detection).
3. Design a baseline experiment comparing frontier LLMs against our rule-based extractor
   on this task, on synthetic + (later) real Hinglish. State your prior on where frontier
   models will FAIL (I expect: temporal resolution and code-switched negation scope).

SOURCES TO USE
Clinical negation/assertion literature (NegEx, ConText, the i2b2/n2c2 assertion and
temporal-relation challenges, THYME/SemEval clinical temporal work), and code-switching
NLP literature. Adapt, don't reinvent — tell me what transfers to Hinglish and what breaks.

OUTPUT I WANT
The annotation guideline (tag set + decision rules + examples), the IAA protocol, the
eval metric definitions, and the baseline experiment design. This becomes the spec Fable
uses to build the labeling tool and run the benchmark.

SAFE-CLAIM GUARDRAIL
No accuracy claim before it's measured on a held-out set. Frame as improving extraction
accuracy and safety, which feeds doctor-gated output.
```

---

## Part 2 — Continual learning: what's code, what's research, who builds it

Continual learning (the [[10_CONTINUAL_LEARNING_SYSTEM]] vision) is **~80% engineering with a research spine**. The instinct to reach for a mythos-class model for "continual learning" is the trap — most of it is disciplined plumbing, and the genuinely hard parts go to Claude Science, not Fable.

### 2A. The build layer (CODE — no research needed)

These are specified in doc 10's "First Implementation Tickets" and are engineering. Build order = dependency order.

| # | Component | What it is | Executor | Why |
|---|---|---|---|---|
| 1 | **Wire the correction ledger** | Call `record_correction()` / `record_false_positive()` from `routes_fact_review.py` for drug dose/frequency edits; add one test proving a correction lands in `fact_corrections`. | **Sonnet** | Narrow, fully specified. ~50 lines. THE urgent one — the tank is empty until this ships. |
| 2 | **LearningEvent ledger** | Persist the full `(before, after, evidence, actor, scope, reason)` delta on every fact/task/document edit. | **Sonnet→Opus** | Schema is specified in doc 10; scope-tagging needs a little judgment. |
| 3 | **Longitudinal timeline persistence** | Ensure the per-patient timeline stitches cleanly across visits (this is the substrate for personalized medicine). | **Opus** | Cross-patient isolation is a safety concern — judgment. |
| 4 | **Scoped memory stores** | Doctor / clinic / specialty preference stores with scope, confidence, rollback. | **Opus** | Scoping decisions are where unsafe generalization creeps in. |
| 5 | **Retrieval context pack** | Inject only the relevant few memories into the next consultation/task. | **Fable or Opus** | The one place a mythos-class model earns its keep — coherent multi-part build (retrieval + scoping + injection + eval). |
| 6 | **Shadow-mode playbooks** | Candidate lessons that propose, never auto-act. | **Opus** | Must not cross the clinical-fact boundary. |
| 7 | **Promotion + eval workflow** | Scope→confidence→reviewer→rollback; the flywheel dashboard. | **Opus** | Promotion policy is safety-critical (one wrong correction must not go global). |
| 8 | **Ops console** | Where Lipi humans complete/inspect service tasks while the system learns. | **Fable/Opus** | Frontend + backend surface; coherence-heavy. |

**Hard boundary on all of it (doc 10 / [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]):** learning improves *extraction, vocabulary, workflow, formatting, routing* — never clinical facts, doses, diagnoses, or safety rules. No auto-promotion of anything clinical. No raw PHI in reusable memory.

### 2B. The research spine (CLAUDE SCIENCE — genuinely open questions)

These are the science hiding inside doc 10. They are NOT build work. Send to Claude Science *after* the ledger is wired and some data exists.

| Research question | Why it's real research | Feeds which product decision |
|---|---|---|
| **Correction economics / scaling law** — how much does extraction improve per doctor correction, by specialty/category/scope? | No one has a clean provenance-linked correction stream to measure this on. | When is the personalization engine reliable enough to ship? When to fine-tune vs. retrieve? (doc 10 open Qs) |
| **Catastrophic forgetting across specialties** — does updating on cardiology degrade pulmonology extraction? | Open continual-learning problem; Lipi has *natural* task boundaries with gold labels. | Whether to keep per-specialty models or one shared model. |
| **PHI-safe federated aggregation** — how to learn across clinics without moving PHI. | Nontrivial privacy + ML design. | The compliance-safe path to a shared learning system. |
| **Minimum viable memory object** — smallest lesson that measurably reduces edits. | doc 10's own open question. | What the memory schema should actually store. |
| **Distillation design (Stage 3)** — turning corrected traces into a cheaper specialized model, PHI-free. | This is the foundation-model bridge. | Whether/when to train a specialized Indian primary-care model. |

### 2C. So — Fable/mythos or not, for continual learning?

**Mostly not.** Direct answer:

- **The urgent thing (wire the ledger): Sonnet.** Don't waste a mythos-class model on 50 lines.
- **Most of the build (memory, promotion, shadow, safety): Opus.** It's judgment-heavy but specified — Opus is the right tier.
- **Use Fable for exactly one thing:** if you want the whole **retrieval + scoped-memory + ops-console subsystem architected in a single coherent pass** (component 5 + 7 + 8 together), that cross-file coherence over a big surface is what a mythos-class model is for. Otherwise Opus builds it incrementally.
- **The research spine: Claude Science, never Fable.** Designing the scaling-law experiment or the forgetting probe is unsettled-method work — that's the workbench, not the builder.

One-liner: **Sonnet fixes the leak, Opus builds the machine, Fable optionally casts the big subsystem in one pour, Claude Science answers whether the machine is learning.**

---

## Part 3 — Full dispatch map (everything in one table)

| Work item | Kind | Executor | When |
|---|---|---|---|
| Wire correction ledger (`record_correction`) | Build | **Sonnet** | NOW — precondition for everything |
| LearningEvent delta ledger | Build | Sonnet→Opus | NOW |
| Longitudinal timeline persistence | Build | Opus | NOW |
| Brief 1 — Indian PGx evidence map | Research | **Claude Science** | NOW |
| Brief 2 — AMR gap + validation design | Research | **Claude Science** | NOW |
| Brief 3 — Hinglish schema + eval | Research | **Claude Science** | NOW |
| Personalized-prescribing flag v1 (literature rules) | Build | **Opus** | after Brief 1 |
| AMR locality-guidance feature | Build | Opus | after Brief 2 + data |
| Hinglish labeling tool + benchmark run | Build | **Fable** | after Brief 3 |
| Scoped memory + retrieval + ops console | Build | **Fable** (or Opus incremental) | after ledger |
| Promotion/shadow/eval workflow | Build | Opus | after memory stores |
| Correction economics / forgetting studies | Research | **Claude Science** | after ledger + data |
| Phenotype-inference engine (Track A full) | Research→Build | Claude Science → Opus | LONG-HORIZON |
| Distillation / specialized model | Research→Build | Claude Science → Fable | LONG-HORIZON |
| CDS interaction data entry (Track E) | Build | **Sonnet** | anytime |
| Admin/TPA/WhatsApp product tracks | Build | **Fable** | separate track |

---

*The gate under all of it: no research direction and no learned behavior crosses the clinical-fact boundary. Everything terminates in a doctor-gated suggestion. See [[22_OPUS_FRONTIER_RESEARCH]] §9 and [[07_DECISIONS]].*

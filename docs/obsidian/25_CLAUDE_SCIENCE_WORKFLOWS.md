# 25 — Claude Science Workflow Commands (Full-Power Briefs)

**Author:** Opus (Claude)
**Date:** 2026-07-02
**Purpose:** Six self-contained Claude Science workflow commands. Each one pulls real data, runs real code, and outputs a file you can directly load into the codebase or the research vault. Paste one per Claude Science agent session inside the "healthcare" project.
**Related:** [[23_EXECUTION_ROUTING]] · [[22_OPUS_FRONTIER_RESEARCH]] · [[24_HOW_TO_MOVE_AHEAD]]

---

## How to use these

1. Open Claude Science → your "healthcare" project
2. Click "+ New Agent" for each brief below
3. Paste the full brief verbatim — do not summarize or shorten
4. Each agent runs autonomously and produces an artifact
5. Download the artifact and hand it to the build executor

The Agent Context you set at the project level already carries Lipi's background. Each brief below is a standalone workflow command on top of that context.

---

## BRIEF A — Drug-Drug Interaction Database for Indian OPD

**What it produces:** A Python file (`_indian_ddi.py`) containing a `_DRUG_INTERACTIONS` list in the exact format used by `backend/app/services/cds_engine.py`, with 50-100 clinically significant interactions sourced from DrugBank, CDSCO, and published Indian pharmacovigilance literature. Drop-in replacement for the current 4-entry list.

```
WORKFLOW — execute in order:

Step 1: PULL DATA SOURCES
  a. Query DrugBank (drugbank.ca) or its public open-data export for all drug-drug
     interaction records with severity = "major" or "moderate".
  b. Pull the CDSCO Pharmacovigilance Programme of India (PvPI) adverse event reports
     (available at cdsco.gov.in or via published PVPI annual reports on PubMed).
  c. Pull the WHO Essential Medicines List for India and the NPPA ceiling-priced drug
     list to establish which drugs are actually prescribed in Indian OPD settings.
     Source: mohfw.gov.in / who.int/publications

Step 2: FILTER TO INDIAN OPD RELEVANCE
  Write Python code to:
  a. Filter DrugBank interactions to only include drug pairs where BOTH drugs appear
     in the Indian essential medicines list OR the NPPA formulary.
  b. Add Indian brand-name variants for each generic (e.g. "pantoprazole" also matches
     "pantop", "pan-d", "pantodac" — use the CDSCO brand database or published
     Indian brand equivalence tables from PubMed).
  c. Rank by: (severity=major → high urgency) + (both drugs in top Indian OPD prescribing
     categories: antibiotics, antihypertensives, antidiabetics, NSAIDs, anticoagulants,
     cardiac drugs, antiepileptics, antidepressants).
  d. Keep top 80 pairs by combined severity + Indian OPD relevance score.

Step 3: MAP TO OUTPUT FORMAT
  Output must exactly match this Python structure (from cds_engine.py):

  _DRUG_INTERACTIONS: list[dict[str, object]] = [
      {
          "left": {"generic_name", "brand_name_1", "brand_name_2"},   # set of strings
          "right": {"generic_name", "brand_name_1"},                  # set of strings
          "urgency": "critical" | "high" | "medium",
          "suggestion": "DRUG INTERACTION ALERT: [short description]",
          "rationale": "[1-2 sentence clinical rationale with source]",
      },
      ...
  ]

  Rules for the output:
  - All strings lowercase
  - Include Indian brand name variants in every set (not just generics)
  - Rationale must cite the specific source (DrugBank record ID, PVPI report year,
    or PubMed PMID)
  - urgency=critical only for pairs with documented life-threatening outcomes
  - urgency=high for serious but manageable interactions
  - urgency=medium for interactions requiring monitoring

Step 4: VERIFY + DEDUPLICATE
  Write Python code to check:
  - No pair appears twice (in either left-right order)
  - Every drug name is lowercase
  - No set is empty
  - Every rationale string is < 300 characters

OUTPUT ARTIFACT:
  File: _indian_ddi.py
  Contents: just the _DRUG_INTERACTIONS list, importable as a Python module.
  No other code. No explanatory text inside the file.
  Add a module docstring: "Auto-generated Indian OPD drug interaction database.
  Sources: DrugBank [version/date], CDSCO PvPI [year], [any PubMed PMIDs cited]."

SAFE-CLAIM GUARDRAIL:
  Every rationale must include its source. Do not generate interaction rules that
  are not in DrugBank or published literature. This feeds a doctor-gated alert system
  — false alerts are harmful. If evidence is weak, set urgency=medium and say so in
  the rationale.
```

---

## BRIEF B — Indian Pharmacogenomics Rules Data Contract

**What it produces:** A Python file (`_pgx_rules.py`) containing evidence-graded prescribing safety rules for Indian primary care, sourced from CPIC, PharmGKB, IndiGen, and GenomeIndia. Directly feeds the PGx flag layer we are building in `cds_engine.py`.

```
WORKFLOW — execute in order:

Step 1: PULL ALLELE FREQUENCY DATA
  a. Query PharmGKB (pharmgkb.org) for all drug-gene pairs with CPIC level 1A or 1B
     evidence. Pull the full gene-drug pair table programmatically via their API or
     published data downloads.
  b. Pull IndiGen allele frequency data (the 1,029-Indian-genome study, published in
     Cell 2019, PMID 31626772). Extract allele frequencies for:
       - CYP2C19 *2, *3, *17
       - CYP2D6 *4, *5, *10, *41
       - CYP2C9 *2, *3
       - VKORC1 -1639G>A
       - HLA-B*15:02
       - HLA-B*57:01
       - NUDT15 *3
       - TPMT *2, *3A, *3C
       - G6PD deficiency (use ICMR/published Indian prevalence — not IndiGen)
  c. Cross-reference with GenomeIndia Consortium data (2024, Science) where available
     for updated South Asian frequencies.
  d. For any variant where Indian-specific data is absent, mark explicitly as
     "NO_INDIAN_DATA — using South/East Asian proxy from [source]" — do not silently
     substitute.

Step 2: COMPUTE INFERENCE SIGNAL STRENGTH
  For each drug-gene pair, write Python code to score:
  - Indian population frequency of the risk allele (from Step 1)
  - Phenotypic observability: can poor metabolizer / risk carrier status be inferred
    from prescribing outcomes alone (treatment failure, dose escalation, adverse event
    on follow-up)? Score 0-3:
      0 = not observable (variant has no clear clinical phenotype in primary care)
      1 = weakly observable (some signal but many confounders)
      2 = moderately observable (dose change / switch documented)
      3 = strongly observable (treatment failure / ADR clearly maps to variant)
  - Primary care actionability: does the clinical action (dose change, drug switch,
    test-before-prescribe) happen at OPD level or only in a hospital?

Step 3: RANK AND SELECT
  Rank all pairs by: (CPIC level weight) × (Indian frequency) × (actionability).
  Select top 15 pairs. For each, produce:
  - The prescribing rule in plain Python conditional logic
  - The evidence grade and source
  - The Indian allele frequency (or "NO_INDIAN_DATA" marker)
  - The observability score with rationale

Step 4: OUTPUT FORMAT
  File: _pgx_rules.py

  Each rule as a Python dict:

  _PGX_RULES: list[dict] = [
      {
          "rule_id": "PGX_001",
          "gene": "G6PD",
          "variant": "deficiency",
          "trigger_drugs": {"primaquine", "dapsone", "nitrofurantoin", "rasburicase"},
          "indian_frequency": "4-14% depending on region (ICMR surveys)",
          "indian_frequency_source": "PMID XXXXXXX",
          "cpic_level": "1A",
          "urgency": "high",
          "alert": "G6PD deficiency risk: {drug} can cause haemolytic anaemia in G6PD-deficient patients. Consider G6PD screening, especially in patients from malaria-endemic regions.",
          "observability_score": 3,
          "observability_note": "Haemolysis after primaquine is a well-documented phenotypic signal",
          "needs_genomic_data": False,
          "ships_now": True,
      },
      ...
  ]

  Add a second list _PGX_RULES_NEEDS_DATA for pairs where Indian data is genuinely
  missing and the rule should not ship until we have outcome data.

SAFE-CLAIM GUARDRAIL:
  No rule ships with "Indian frequency" unless the source is Indian-specific data.
  If only South Asian or global data exists, the rule gets needs_genomic_data=True
  and a note. Frame all alerts as suggestions to a doctor, never as autonomous decisions.
```

---

## BRIEF C — AMR Surveillance Gap: Actual Computation

**What it produces:** A reproducible Python/R notebook (`amr_gap_analysis.ipynb`) that actually pulls public data and computes the surveillance blind spot, with charts and sourced numbers. Also produces `amr_study_protocol.md`.

```
WORKFLOW — execute in order:

Step 1: PULL AND PARSE AMR DATA SOURCES
  Write Python code to fetch and parse:
  a. WHO GLASS India country data — download from who.int/glass/results
     Extract: number of surveillance sites, specimen types, AMR rates by pathogen,
     year coverage (2016-2023).
  b. ICMR AMRSN annual reports (2017-2023) — fetch PDFs from icmr.nic.in,
     parse tables for: number of sentinel sites, specimen sources (hospital lab
     vs primary care), pathogen panels.
  c. Indian antibiotic consumption estimates — use published GRAM/Lancet estimates
     for India (PMID 29276051 and follow-up) and WHO/IQVIA consumption data.
     Extract: total DDD (defined daily doses) per capita, split by healthcare tier
     if available.
  d. NCDC AMR data (ncdc.mohfw.gov.in) — any primary care sentinel sites listed.

Step 2: COMPUTE THE SURVEILLANCE GAP
  Write Python code to compute:
  a. Estimated fraction of total Indian antibiotic consumption that occurs in:
     - Tertiary hospital settings
     - Secondary hospital settings
     - Primary care / community pharmacy / OTC
     Express as percentages with confidence intervals from multiple sources.
  b. Fraction of AMRSN/GLASS surveillance specimens sourced from:
     - Hospital microbiology labs (inpatient)
     - Hospital outpatient
     - Primary care / community
     Express as count and percentage.
  c. THE GAP NUMBER: (% consumption in primary care) - (% surveillance from primary care)
     This is the core finding. Quantify uncertainty.

Step 3: GENERATE CHARTS
  Produce using matplotlib/seaborn:
  a. Stacked bar: antibiotic consumption by healthcare tier vs surveillance coverage by tier
  b. Time series: AMRSN sentinel site count 2017-2023 (are they expanding to primary care?)
  c. Map sketch: states with AMRSN sites vs states with high primary care antibiotic use

Step 4: STUDY DESIGN
  Produce amr_study_protocol.md with:
  - Hypothesis (verbatim): "Empirical antibiotic escalation in primary care is a leading
    indicator of local AMR that precedes culture-based surveillance"
  - Signal definition: first-line → second-line switch for same syndrome, same patient
    or same locality cluster, within 30 days
  - Validation approach: match Lipi locality prescribing signals to AMRSN districts
    where they overlap; estimate lead time
  - Statistical power calculation: how many patient-episodes needed to detect a
    locality-level correlation with AMRSN resistance rates at p<0.05
  - Negative controls: seasonal prescription spikes unrelated to resistance
  - Confounders to adjust for (OTC access, stock-outs, referral bias)

OUTPUT ARTIFACTS:
  1. amr_gap_analysis.ipynb — fully reproducible notebook with all fetched data,
     computed numbers, and charts. Every number cites its source inline.
  2. amr_gap_summary.md — the one-page finding: THE GAP NUMBER with uncertainty,
     the 3 charts, and 2-sentence statement of what Lipi is positioned to fill.
  3. amr_study_protocol.md — the study design document.

SAFE-CLAIM GUARDRAIL:
  The gap number is a proxy calculation from imperfect data — state uncertainty
  explicitly. Do not claim Lipi "does AMR surveillance." The study protocol is a
  design, not a result.
```

---

## BRIEF D — ICD-10 Indian Disease Burden Map

**What it produces:** A Python file (`_indian_icd10.py`) with the top 150 Indian OPD diagnoses mapped to ICD-10 codes, ranked by actual disease burden, directly importable into the codebase.

```
WORKFLOW — execute in order:

Step 1: PULL DISEASE BURDEN DATA
  a. Pull India-specific data from the IHME Global Burden of Disease (GBD) study
     (healthdata.org/research-analysis/gbd) for:
     - Top causes by DALYs (disability-adjusted life years) for India, 2019 and 2023
     - Filter to: outpatient-manageable conditions (exclude trauma surgery,
       in-hospital-only conditions)
  b. Pull the National Family Health Survey (NFHS-5, 2019-21) data on disease
     prevalence in India — particularly: diabetes, hypertension, anaemia, TB,
     malaria, dengue, typhoid, respiratory infections, skin diseases.
  c. Pull published Indian OPD epidemiology studies from PubMed to cross-validate
     (search: "India outpatient department morbidity pattern" — filter 2015-2024).
  d. Pull WHO ICD-10 mapping tables for all identified conditions.

Step 2: CONSTRUCT RANKED LIST
  Write Python code to:
  a. Merge GBD + NFHS + OPD literature into a unified disease list
  b. Score each condition by: (DALY burden) × (OPD manageability score 0-1) ×
     (primary care frequency)
  c. Rank top 150 by combined score
  d. Map each to its ICD-10 code (include both ICD-10-CM and ICD-10-WHO versions)
  e. Add Hinglish common names for the top 50 (e.g. "bukhar" for fever, "sugar" for
     diabetes, "BP" for hypertension) — these are the terms doctors actually say

Step 3: OUTPUT FORMAT
  File: _indian_icd10.py

  _INDIAN_OPD_DIAGNOSES: list[dict] = [
      {
          "rank": 1,
          "icd10_code": "J06.9",
          "icd10_desc": "Acute upper respiratory infection, unspecified",
          "common_names": ["URTI", "cold", "cough", "upper respiratory"],
          "hinglish_names": ["bukhar", "khansi", "sardi"],
          "burden_rank_india": 1,
          "source": "GBD 2019 India / NFHS-5",
      },
      ...
  ]

  Also produce _ICD10_LOOKUP: dict[str, str] mapping every common name / Hinglish
  name to its ICD-10 code. This is the lookup the clinical extractor uses.

SAFE-CLAIM GUARDRAIL:
  Every rank must cite its source. Do not invent disease burden numbers.
```

---

## BRIEF E — Hinglish Clinical NLP: Annotation Schema + Baseline Benchmark

**What it produces:** An annotation guideline document, a synthetic test set, and actual baseline experiment results comparing rule-based vs LLM approaches on epistemic×temporal classification.

```
WORKFLOW — execute in order:

Step 1: LITERATURE SYNTHESIS (computational)
  Pull and parse from PubMed and ACL Anthology:
  a. NegEx (Chapman 2001) and ConText (Harkema 2009) — the canonical negation/
     temporality algorithms for clinical text. Extract their tag sets and decision rules.
  b. i2b2/n2c2 2010 Assertion Classification shared task — pull the annotation
     guidelines and IAA results. What tag set did they use? What was hardest?
  c. THYME corpus temporal annotation guidelines (Styler 2014, PMID 25977556) —
     extract temporal relation types relevant to clinical facts.
  d. Code-switching NLP literature: pull papers on Hindi-English code-switching
     NLP (ACL/EMNLP 2018-2024). What features break when you switch languages
     mid-sentence? What transfers from English clinical NLP?
  Write a synthesis: what transfers to Hinglish, what breaks, what is new.

Step 2: DESIGN THE ANNOTATION SCHEMA
  Based on Step 1, produce annotation_schema.md with:
  - Full tag set: epistemic (affirmed/negated/uncertain/queried) ×
    temporal (historical/current/planned) — 12 combinations, some impossible
  - Decision rules with Hinglish examples for each tag
  - Hard cases section: 20 examples where the right tag is non-obvious, with gold
    labels and rationale
  - Inter-annotator agreement protocol: how to measure Cohen's κ for this joint tag

Step 3: GENERATE SYNTHETIC TEST SET
  Write Python code to generate 200 synthetic Hinglish clinical sentences covering:
  - All 12 epistemic×temporal combinations (as many as are clinically plausible)
  - At least 30 sentences with temporal shift ("pehle tha, ab nahi")
  - At least 20 with code-switched negation ("no fever tha")
  - At least 20 with hedged/uncertain present ("shayad BP high hai")
  - At least 20 with planned/ordered items ("ECG karwa lo")
  Each sentence must have: sentence text, entity, gold_epistemic, gold_temporal, rationale.
  Save as synthetic_test_set.json.

Step 4: RUN BASELINE EXPERIMENTS
  Write Python code to:
  a. Implement a rule-based baseline using NegEx + ConText logic adapted to Hinglish
     (negation words in both Hindi and English, temporal cue words in both languages)
  b. Run it on the synthetic_test_set.json
  c. Compute: precision, recall, F1 per tag combination
  d. Identify the 5 hardest failure modes (where the rule-based baseline fails most)
  e. Document a prompt for a frontier LLM to attempt the same task (so Arush can
     run it through Claude Opus for comparison)

OUTPUT ARTIFACTS:
  1. annotation_schema.md — the full annotation guideline
  2. synthetic_test_set.json — 200 labelled sentences
  3. baseline_results.json — precision/recall/F1 by tag
  4. hinglish_nlp_gaps.md — the 5 failure modes, which become the spec for
     Opus to upgrade the deterministic extractor

SAFE-CLAIM GUARDRAIL:
  The synthetic test set is not a real validation — say so. Baseline results on
  synthetic data establish a floor, not a ceiling. Real validation requires
  annotated real transcripts.
```

---

## BRIEF F — CDSCO Brand-Name Confusion Map

**What it produces:** A Python file (`_indian_brands.py`) mapping Indian brand names to generic molecules for the 200 most-prescribed drugs in Indian OPD. Enables the CDS engine to match brand-name prescriptions to interaction rules.

```
WORKFLOW — execute in order:

Step 1: PULL CDSCO DATA
  a. Fetch the CDSCO drug database from cdsco.gov.in — the list of approved
     fixed-dose combinations (FDCs) and single-ingredient drugs with their
     brand names and manufacturers.
  b. Pull the NPPA (National Pharmaceutical Pricing Authority) ceiling-price drug
     list — these are the most commonly sold drugs in India.
  c. Supplement with published Indian drug formulary studies from PubMed that list
     common brand-to-generic mappings (search: "India brand name generic equivalent
     OPD prescribing").

Step 2: BUILD THE CONFUSION MAP
  Write Python code to:
  a. For each generic molecule in the top 200 Indian OPD drugs:
     - Find all CDSCO-approved brand names
     - Find all common misspellings / abbreviations (e.g. "Augmentin" → "amoxyclav",
       "pan-d" → "pantoprazole + domperidone")
     - Flag FDCs where the brand name does not clearly indicate the components
       (e.g. "Combiflam" = ibuprofen + paracetamol — the brand name alone is opaque)
  b. Identify the top 20 highest-risk confusion pairs:
     - Same brand prefix, different molecules (e.g. "Betnesol" vs "Betadine")
     - FDCs where one component has a major interaction but the brand name
       doesn't signal it
  c. Compute: for each generic in our _DRUG_INTERACTIONS list, how many Indian
     brand name variants exist that we are currently NOT matching?

Step 3: OUTPUT FORMAT
  File: _indian_brands.py

  _BRAND_TO_GENERIC: dict[str, str] = {
      "crocin": "paracetamol",
      "dolo": "paracetamol",
      "combiflam": "ibuprofen+paracetamol",
      "augmentin": "amoxicillin+clavulanic acid",
      "pan-d": "pantoprazole+domperidone",
      ...
  }

  _FDC_COMPONENTS: dict[str, list[str]] = {
      "combiflam": ["ibuprofen", "paracetamol"],
      "pan-d": ["pantoprazole", "domperidone"],
      ...
  }

  _HIGH_RISK_CONFUSION: list[dict] = [
      {
          "brand": "combiflam",
          "risk": "Contains ibuprofen — interacts with anticoagulants. Brand name does not signal NSAID content.",
          "components": ["ibuprofen", "paracetamol"],
      },
      ...
  ]

SAFE-CLAIM GUARDRAIL:
  Only include brand-to-generic mappings where the source is CDSCO or published
  literature. Do not infer brand-generic mappings. Missing data = missing entry,
  not a guess.
```

---

## After Claude Science delivers these artifacts

| Artifact | Goes into | Who wires it |
|---|---|---|
| `_indian_ddi.py` | `cds_engine.py` — replaces 4-entry list | Opus (me) |
| `_pgx_rules.py` | New PGx flag layer in `cds_engine.py` | Opus (me) |
| `amr_gap_analysis.ipynb` + summary | `docs/obsidian/22_OPUS_FRONTIER_RESEARCH.md` Track C | Arush reviews |
| `_indian_icd10.py` | Clinical extractor + SOAP generator | Sonnet |
| `annotation_schema.md` + `hinglish_nlp_gaps.md` | Hinglish extractor upgrade spec | Opus (me) |
| `_indian_brands.py` | `cds_engine.py` — brand matching layer | Sonnet |

Run all 6 in parallel as separate agents in the same Claude Science project. They are fully independent.

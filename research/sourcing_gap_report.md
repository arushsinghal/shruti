# Sourcing / Gap-Flag Report — Indian OPD Top-150 ICD-10 Diagnosis Map

**File covered:** `_indian_icd10.py` (150 entries, 435 lookup terms, 12 documented ambiguous terms)
**Generated:** 2026-07-02
**Purpose:** Per project output-discipline rules — every number in the diagnosis map must trace to
an explicit source, and every gap must be flagged, not silently filled. This report is the audit
trail for `_indian_icd10.py`.

## 1. Headline numbers — what's cited vs. inferred

| Field | Cited to a real India-specific source | Clinical-judgment / inferred placeholder |
|---|---|---|
| `burden_score` (drives rank) | 31 / 150 entries (21%) | 119 / 150 entries (79%) — labelled `"clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number"` |
| `encounter_freq` | 13 / 150 entries (9%) | 137 / 150 entries have `encounter_freq: None` (no fabricated frequency) |
| `hinglish_names` (top 50 only, per spec) | 0 / 50 (0%) — **see §4, this is an expected literature gap, not a shortfall** | 50 / 50, all marked `hinglish_source="inferred"` |
| `opd_manageability` | 0 / 150 — **this entire field is clinical judgment by construction**, not a literature quantity | 150 / 150, explicitly documented as such in the file header and every entry comment |

**Bottom line for a doctor reading this file: only about 1 in 5 entries' rank is backed by a
citable Indian burden-of-disease number. The rest of the list is real (these are genuine, common
Indian OPD diagnoses) but their *rank position* is a clinical-knowledge estimate, not measured
data.** Do not present `OPD_score` to end users as a validated epidemiological ranking.

## 2. Why STEP 1's literal data pull could not be done as specified

The task asked to "download or query" IHME's GBD 2021 India results via their API. In practice:
- IHME's GBD Results Tool (the `healthdata.org` interface referenced) is an **interactive web
  application**, not a public REST API endpoint reachable from this environment's network
  allowlist. No India-specific GBD 2019/2021 all-cause DALY ranking paper equivalent to the 2017
  "Nations within a nation" Lancet paper was located either — most recent India GBD papers found
  are single-disease deep dives, not an all-cause ranked table.
- **Substitution made:** the India State-Level Disease Burden Initiative (ICMR/PHFI/IHME
  collaboration, GBD **1990–2016**, published *Lancet* 2017) supplied the exact top-5 ranked
  individual causes and top-10 causes (as a set, not fully rank-ordered 6th–10th) for India. This is
  the most authoritative India-specific, individually-ranked GBD-derived source we could retrieve,
  but it is **2016 data, not 2021**, and only the *top 5* have a precise numeric rank; ranks 6–10 are
  known only as a set membership.
- Condition-specific companion papers (cardiovascular, diabetes, cancer, mental disorders — all
  part of the same GBD India collaboration, 2016/2017 data) supplied percentage-of-subtotal shares
  for individual causes within their respective disease groups.

## 3. NFHS-5 prevalence — what was found and what's missing

Found (with exact citation in `burden_source`/`encounter_source` fields): anaemia (children, women,
men, adolescents, pregnant women — PIB "Anaemia Mukt Bharat" release, cross-checked against
PMC10860231), diarrhoea in under-5s (national fact sheet + independent unit-level re-analyses,
which disagree slightly: 7.2% vs 7.3–8.4% depending on source/sample), ARI in under-5s
(PMID 37280601), and hypertension (**no single official NFHS-5 national headline % could be
located verbatim** — two different proxies are given instead: a third-party average across the 22
Phase-1 state fact sheets, and an independent academic re-analysis using international BP
thresholds that are NOT the same cut-offs NFHS-5's own report uses).

**Explicit gaps (NFHS-5 data NOT found, per the original brief's request list):** diabetes/blood-
glucose national headline %, TB symptom prevalence, malaria, dengue, chikungunya, typhoid, skin
disease, and reproductive-tract-infection symptom prevalence. Where the brief asked for these and
no NFHS-5 figure exists, `_indian_icd10.py` entries for those conditions use the clinical-knowledge
placeholder tier instead of a fabricated NFHS-5 number — flagged accordingly in `burden_source`.

## 4. Hinglish/vernacular terms — this is the most important gap in the whole deliverable

A dedicated literature sub-agent ran 20+ PubMed searches (health literacy, lay illness vocabulary,
explanatory models, idioms of distress, culture-bound syndromes, folk illness terms) specifically
looking for a published Hindi/Hinglish term-to-condition glossary usable for the top-50 annotation
task. **None was found.** Two partial hits confirm vernacular terms for hypertension/eclampsia
(Kannada, PMID 27358068) and somatic depression idioms (Goa, PMID 17074394) exist in the qualitative
literature, but neither publishes a directly reusable, transliterated term list.

**Consequence: all 50 `hinglish_names` entries in the top-50 are `hinglish_source="inferred"`
(general Hindi/Hinglish vernacular medical knowledge, in the register the user's own worked examples
used — e.g. "bukhar", "sugar", "BP"), not literature-derived.** Zero are `"published"`. This should
be read as a genuine finding about the state of the published literature, not a shortcut — and it is
exactly the gap the OPD literature sub-agent flagged as a research opportunity: **Lipi's own
doctor-confirmed transcript corpus is a novel, proprietary source for building a validated
vernacular-term lexicon that does not currently exist in the public literature.**

## 5. OPD morbidity-pattern literature used

Seven published Indian OPD/primary-care morbidity studies were retrieved and used for
`encounter_freq`/`burden_score` on 13 entries (fever, heartburn/acid-peptic disease, vertigo,
osteoarthritis, neuritis, fungal skin infection, dental problems, cataract, diabetes, hypertension,
acid peptic disease, arthritis, chronic back pain): PMID 29302540, 38709793, 39736942, 30309742,
32349770, 29302544, 31041230. These are mostly Odisha/Telangana/Tamil Nadu/Karnataka studies (no
truly nationally-representative OPD morbidity survey was found) — **geographic generalizability to
all of India is unverified and should be treated as a limitation**, not an assumption.

## 6. OPD_score methodology — a documented deviation from the literal brief

The brief specified `OPD_score = GBD_DALY_rank_India × OPD_manageability × encounter_frequency`.
Implemented literally, a raw DALY **rank** (where 1 = highest burden) would make rank-1 conditions
score *lowest*, inverting the intended meaning. This was substituted with:

```
OPD_score = burden_score (0-100, higher = more burden) × opd_manageability (0/0.5/1.0)
            × encounter_multiplier (1.0 + literature_frequency_fraction, or 1.0 if no literature found)
```

`burden_score` derivation is tiered by source quality (documented per-entry in `burden_source`):
exact GBD rank (rank 1→100 … rank 5→80) > GBD top-10 set membership (75) > GBD cause-group %-of-total
(scaled) > GBD subtype %-of-group-total (scaled down) > NFHS-5/OPD-literature prevalence % (capped at
100) > clinical-knowledge placeholder tiers (40/25/15/8, explicitly uncited). **This heuristic has
not been validated against a ground-truth Indian OPD registry and should not be described to doctors
or patients as a measured epidemiological ranking — it is a triage aid for which diagnoses a
primary-care NLP extractor should be built to recognize first.**

## 7. ICD-10-CM vs ICD-10-WHO divergence

53 / 150 entries (35%) have different `icd10_cm` and `icd10_who` codes — mostly because ICD-10-CM
adds specificity (7th-character injury extensions, confirmed-vs-unspecified TB, laterality) that
ICD-10-WHO's simpler structure doesn't require. All divergent entries are flagged in the `notes`
field where the difference has clinical significance (e.g. TB confirmation status, stroke coding,
self-harm coding).

## 8. Duplicate ICD-10-CM codes (flagged per validation spec, not treated as errors)

Four ICD-10-CM codes are shared by two distinct canonical entries in the list — all are
legitimate pediatric/adult or acute/general variants of the same underlying code, not accidental
collisions:
- `R50.9` — "Fever in children (unspecified)" and "Fever of unknown/viral origin"
- `J06.9` — "Acute pharyngotonsillitis with fever (viral)" and "Acute respiratory infection (upper, in children)"
- `B82.9` — "Intestinal worm infestation" and "Worm infestation (pediatric)"
- `J03.90` — "Acute tonsillopharyngitis (pediatric)" and "Tonsillitis (acute)"

A downstream clinical extractor consuming this file should collapse each pair to one code but may
want to keep them as separate *recognition* entries (different phrasing/age context maps to the same
billing code).

## 9. Ambiguous lookup terms (12 found — flagged in `_AMBIGUOUS_LOOKUP_TERMS`)

Some patient-facing terms genuinely map to more than one diagnosis depending on clinical context
(age, accompanying symptoms, duration) — mirroring the ambiguity the original brief itself flagged
for "bukhar" (URTI vs fever). `_DIAGNOSIS_LOOKUP` resolves each such term to its highest-`OPD_score`
(most common) candidate by default; `_AMBIGUOUS_LOOKUP_TERMS` lists every candidate so a downstream
extractor can disambiguate using transcript context rather than silently guessing:
`kamzori`, `joint pain`, `saans phoolna`, `purani khansi`, `kamar dard`, `gardan dard`, `acidity`,
`gastritis`, `pet mein jalan`, `pinworm`, `jaundice`, `peeliya`.

## 10. Recommended next steps for Lipi

1. **Do not ship `OPD_score` ranks to doctors as an epidemiological claim.** Present them internally
   as an NLP-recognition-priority ordering only, with the citation-coverage caveat above visible to
   whoever owns the extractor.
2. **Treat the Hinglish gap as a product opportunity, not a blocker.** Lipi's own doctor-confirmed
   transcripts are exactly the corpus needed to build the vernacular-term lexicon the literature
   lacks — every `hinglish_source="inferred"` entry in this file is a candidate for replacement with
   a transcript-derived, doctor-validated term once that corpus analysis is run.
3. **Re-run GBD/NFHS-5 sourcing once genuine API/bulk-download access is available** (e.g. an
   IHME GBD Results Tool bulk export or GBD 2021 India-specific paper, if/when published) to raise
   the 21%-cited baseline for `burden_score`.
4. **Validate `opd_manageability` with an actual doctor panel** — it is currently a single analyst's
   clinical-judgment call per condition, not adjudicated by Lipi's own OPD physicians.

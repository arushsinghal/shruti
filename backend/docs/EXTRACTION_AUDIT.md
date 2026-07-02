# Lipi Clinical Extraction — Architecture Audit & Redesign Plan

Status: Pre-pilot review. Scope: extraction quality + SOAP correctness ONLY.
Reviewer stance: adversarial senior multilingual clinical NLP architect.

---

## 1. Current pipeline risks & failure modes (grounded in code)

| # | Risk | Location | Severity | Why it matters |
|---|------|----------|----------|----------------|
| R1 | **Eval measures a different pipeline than doctors use.** GLiNER merge lives in `routes_notes._run_health_pipeline`; eval harness calls `ClinicalExtractorService.extract()` directly. | `routes_notes.py:75-150` vs `eval/run_eval.py:54-56` | **Critical** | Every metric you report is for a pipeline doctors never run. Regressions in the merge layer are invisible to eval. |
| R2 | **Fuzzy diagnosis matching at ratio ≥ 88.** An ASR-garbled or coincidental token can map to a real diagnosis. | `clinical_extractor.py:940-964` | **Critical** | Independent hallucination path, unrelated to Ollama. "appendix-like" token → "appendicitis". Diagnoses must never be fuzzy. |
| R3 | **Free-text diagnosis label capture.** `_DIAGNOSIS_LABEL_RE` grabs arbitrary text after "diagnosis:"/"impression:". | `clinical_extractor.py:1233-1242` | High | Injects non-validated free text as a diagnosis. |
| R4 | **SOAP infers a diagnosis the clinician never said.** `_SYMPTOM_IMPRESSIONS` maps symptom constellations → "likely viral URTI" in the Assessment. | `soap_generator.py` (added today) | High | Violates "conservative diagnoses" + "SOAP must not invent". Hedging text does not make it extraction. |
| R5 | **Whole-sentence uncertainty skip.** Any sentence with maybe/shayad/suspected is dropped entirely. | `clinical_extractor.py:998-1000` | High | "Bukhar hai, shayad dengue" silently loses the fever. Recall loss, no audit trail. |
| R6 | **Negation is char-window, not clause-scoped.** 40-char pre / 25-char post windows. | `clinical_extractor.py:851-870` | High | Fails on lists ("bukhar, khansi, zukaam nahi"), long-distance negation, and Hindi post-posed negation beyond 25 chars. A missed negation = active wrong symptom = unsafe. |
| R7 | **No per-fact evidence/metadata.** Output is flat string lists; `contexts` is a lossy dict keyed by display string. | `clinical_extractor.py:973-983` | High | No span offsets, no language, no negated/temporality/confidence. Collisions when a value repeats. Lost entirely on the routes merge. No auditability. |
| R8 | **Vitals coverage gaps.** No fasting/random glucose, no weight; requirement explicitly lists "sugar fasting 160". | `clinical_extractor.py:1052-1100` | Medium | Misses a core OPD vital. |
| R9 | **Phantom GT fields.** `labs`, `advice`, `red_flags` are scored but never produced. | `eval/run_eval.py:69-71` | Medium | Structural recall=0 pollutes metrics; hides real signal. |
| R10 | **Medication temporality not modeled.** Only name/dosage/frequency. No current/new/stopped/advised, no route, no duration. | `clinical_extractor.py:1151-1216` | Medium | Requirement #7 unmet. "Metformin band kar do" (stop) looks identical to "Metformin start karo". Safety-relevant. |
| R11 | **Transliteration double-pass re-extracts.** Symptoms/diagnoses re-run on raw Devanagari after running on transliterated text. | `clinical_extractor.py:1016-1023` | Medium | Can double-add or bypass negation context computed on the processed string. |
| R12 | **GLiNER merge uses denylist filters.** Vital-term and med-prefix denylists in the merge. | `routes_notes.py:90-130` | Medium | Denylists leak on unseen terms; English-leaning model under-fires on pure Hindi. |

---

## 2. Is the Sonnet patch directionally correct?

**Yes — but incomplete.**

Correct: removing generative (Ollama) enrichment from symptoms and diagnoses is exactly right. Generative models cannot guarantee transcript-grounding, and high-risk categories must be deterministic.

Incomplete, because the same class of failure still has three open doors:
- **R2** fuzzy diagnosis matching is a non-LLM hallucination path that survived the patch.
- **R3** free-text diagnosis label capture survived.
- **R4** the new SOAP `_SYMPTOM_IMPRESSIONS` re-introduced inference at the *rendering* layer — you closed the front door (Ollama) and opened a side window (SOAP).
- **R1** eval can't see the GLiNER path, so you cannot prove the patch held.

Verdict: right direction, not yet safe for doctors. Close R2/R3/R4 and unify the eval path (R1) before pilot.

---

## 3. LLM-safe vs deterministic field policy

| Field | Policy | Rule |
|-------|--------|------|
| Symptoms | **Deterministic + lexicon-gated** | Exact/transliteration match against curated bilingual lexicon. Fuzzy only ≥ 92 AND canonical ∈ lexicon. |
| Diagnoses | **Deterministic, explicit-only** | Exact lexicon match OR explicit assessment language stated by clinician. No fuzzy. No inference. Empty if not stated. |
| Negation status | **Deterministic** | Clause-scoped rule engine. Never a model. |
| Vitals / lab **values** | **Deterministic regex only** | A model may NEVER emit a number. |
| Red flags | **Deterministic + lexicon-gated** | Curated red-flag phrase set. |
| Medication dosage/frequency/duration/route | **LLM/GLiNER allowed, evidence-gated** | Extractive only; span must verbatim-match transcript or it is dropped. |
| Investigation names | **LLM/GLiNER allowed, evidence-gated** | Same gate. |
| Follow-up phrases | **LLM/GLiNER allowed, evidence-gated** | Same gate; conditional routing deterministic. |
| Section hint (S/O/A/P) | **LLM allowed, advisory only** | Never changes whether a fact exists. |

Hard rule: a generative/zero-shot model may only **propose spans**. Proposals are (a) offset-verified as verbatim substrings, and (b) for symptoms/diagnoses/values, intersected with the deterministic lexicon/regex. A proposal outside that is rejected.

---

## 4. Proposed extraction schema (per fact)

```json
{
  "original_text": "gala kharab",
  "normalized_value": "sore throat",
  "category": "symptom",
  "language": "hinglish",
  "source_sentence": "mujhe gala kharab hai aur halka bukhar bhi",
  "evidence_span": [6, 17],
  "confidence": 0.95,
  "negated": false,
  "temporality": "current",
  "section_hint": "S",
  "safety_flags": []
}
```

- `category`: symptom | diagnosis | medication | vital | lab | allergy | investigation | follow_up | red_flag
- `language`: hindi | english | hinglish (of the original_text span)
- `evidence_span`: `[start, end]` char offsets into `source_sentence`; MUST satisfy `source_sentence[start:end] == original_text`
- `temporality`: current | historical | conditional | uncertain
- `negated`: true | false | null (null = ambiguous → excluded from active SOAP)
- `safety_flags`: e.g. `allergy_med_conflict`, `value_out_of_range`, `dose_missing`

Top-level output: `{ "facts": [ <fact>, ... ], "meta": { "extractor_version", "transcript_hash" } }`. The flat lists (`symptoms`, etc.) become **views** derived from `facts`, for backward compatibility with the SOAP renderer and eval.

---

## 5. Hallucination-prevention contract (the extractor MUST obey)

1. **Span verity.** Every fact carries `evidence_span` and `source_sentence[span] == original_text`. If not, the fact is dropped. No exceptions.
2. **No model-authored high-risk categories.** Symptoms, diagnoses, and all numeric values are produced only by deterministic lexicon/regex. Models may propose; proposals are gated by lexicon ∩ offset-verify.
3. **No numbers from models.** Vitals, labs, dosages: regex over transcript only.
4. **Conservative diagnoses.** A diagnosis appears only if (a) an exact lexicon term is present and un-negated, or (b) explicit clinician assessment language ("lagta hai X", "X ka case hai", "impression: X"). Otherwise the diagnoses view is empty.
5. **Fail-safe ambiguity.** If negation or temporality is ambiguous, set `negated=null` / `temporality=uncertain` and EXCLUDE from active SOAP. Uncertain never becomes an active symptom.
6. **SOAP renders, never computes.** The renderer consumes only `negated=false, temporality=current, confidence≥τ` facts. It may not infer, aggregate, or synthesize a new clinical statement. Assessment lists only explicitly stated diagnoses; if none: "No diagnosis stated by clinician."
7. **Determinism.** Same transcript ⇒ identical output. No sampling/temperature anywhere in the path.
8. **Full traceability.** Every SOAP line maps to ≥ 1 `evidence_span`.

---

## 6. Multilingual negation & temporality strategy (Hindi/Hinglish)

**Replace char-windows with clause scoping.**

1. **Clause segmentation** on connectors: `aur`, `and`, `lekin`, `but`, `par`, `phir`, `,`, `।`. Negation scope = the clause, not a fixed character count.
2. **Negation cues**
   - Pre-posed (English): `no, not, denies, without, never`.
   - Pre-posed (Hindi): `koi … nahi`, `bilkul nahi`.
   - **Post-posed (Hindi — the common case):** `nahi, nahin, nhi, mat, na`, and resolution verbs `band ho gaya, theek ho gaya, ruk gaya`. Hindi negates after the finding: "dard **nahi** hai", "ulti **nahi** ho rahi". Scan to clause end, not 25 chars.
3. **List propagation.** A single negation distributes across a coordinated list: "bukhar, khansi, ya zukaam **nahi**" → all three negated. Conversely "fever hai lekin chest pain **nahi**" → fever active, chest pain negated (contrastive reset on `lekin`).
4. **Temporality cues**
   - current: `hai, ho raha hai, since <dur>`
   - historical: `tha, ho gaya tha, pehle, last week, purana` → not an active finding
   - conditional: `agar … toh`, `if … then` → routes to follow_up/plan, NOT an active finding
   - uncertain: `shayad, lagta hai (without commitment), maybe, suspected, ?`
5. **Conditional = follow-up bridge (requirement #9c).** "agar fever continue kare toh CBC kara lena" → `follow_up` fact with `temporality=conditional`, NOT an active investigation now.
6. **Uncertainty no longer drops the sentence (fixes R5).** Mark the *specific* fact `temporality=uncertain, confidence low`, exclude from active SOAP, retain sibling facts in the sentence.

---

## 7. Per-field extraction rules

### Medications (requirement #7)
Capture: `name, dosage, frequency, duration, route, status (current|new|stopped|advised), evidence_text`.
- name: lexicon (`_KNOWN_MEDICATIONS`) exact, fuzzy ≥ 90.
- dosage/frequency/duration/route: regex adjacency to the name within the clause; GLiNER may propose, gated by span-verify.
- status cues: new (`start karo, shuru, de raha hun, prescribe`), stopped (`band karo, stop, roko`), continue/current (`continue, jari rakho, le rahe ho`), advised (`zaroorat pade toh, sos`).
- Allergy cross-check: if a med name == an allergy, set `safety_flags:["allergy_med_conflict"]` and do not silently treat the allergen as a prescribed drug.

### Vitals / labs (requirement #8)
Preserve value + unit verbatim. Patterns: BP `\d{2,3}\s*(/|over|by)\s*\d{2,3}`; Temp `\d{2,3}(\.\d)?\s*(F|C|°)`; SpO2; Pulse; RR; **glucose** `(fasting|random|pp|fbs|rbs)\s*(sugar)?\s*\d{2,3}`; weight `\d{2,3}\s*kg`. Numbers only from regex. Out-of-physiologic-range → `safety_flags:["value_out_of_range"]` (flag, don't drop).

### Diagnoses (requirement #6)
Exact lexicon term un-negated, OR explicit assessment language. No fuzzy, no constellation inference, no free-text label capture. Empty if not stated.

### Follow-up (requirement #9)
Capture absolute ("3 din baad aana", "follow up after 3 days") and conditional ("agar … toh …"). Normalize Hindi numerals + units to "after N days/weeks/months". Conditional follow-ups keep their trigger text.

### Red flags
Curated bilingual phrase set (e.g. `saans lene mein takleef / breathlessness`, `seene mein dard / chest pain`, `behoshi / loss of consciousness`, `khoon / bleeding`, `daura / seizure`). Emitted as `red_flag` facts with high salience; never inferred.

---

## 8. Golden test transcripts (20)

Full transcripts + expected JSON are in `eval/golden/` (to be created in Phase 1). Distribution: 7 Hindi-heavy (G01–G07), 7 Hinglish/code-mixed (G08–G14), 6 English-heavy Indian OPD (G15–G20). Each ground-truth file uses the eval-consumable field view (symptoms/medications/vitals/diagnoses/negated_findings/follow_up/allergies/investigations) plus a `negation_checks` block for the regression assertions in §10.

The 20 cases and their expected high-risk fields are tabulated in `EXTRACTION_GOLDEN.md` (companion file). Two are shown in full rich-schema form there as exemplars (G03 Hindi, G10 Hinglish); the remaining 18 give field-level ground truth (the format the harness consumes). This split is deliberate: the rich per-item schema is for unit-verifying the extractor contract; the field-level GT is for precision/recall scoring at scale.

Coverage guaranteed across the set:
- gala kharab (G09), pairon mein dard (G09), no chest pain (G16), vomiting nahi hai (G11), explicit-vs-absent diagnosis (G05 explicit / G09 absent), "3 din baad aana" (G03), conditional follow-up "agar fever continue kare toh CBC" (G12), fasting sugar value (G18), medication stop vs start (G14), allergy-as-non-medication (G15).

---

## 9. Expected structured JSON

Lives alongside each transcript in `eval/golden/G<NN>_gt.json`. Schema = §4 for exemplars, field-view for the rest. Generated and committed in Phase 1 so they are diffable and reviewable, not pasted here where they cannot be executed.

---

## 10. Regression tests (must all pass to ship)

| ID | Assertion |
|----|-----------|
| RT1 | "gala kharab" ⇒ symptom **sore throat**; NEVER gallbladder. |
| RT2 | "pairon mein dard" ⇒ symptom **leg pain**; NEVER ear pain. |
| RT3 | "no chest pain" ⇒ chest pain `negated=true`; absent from active symptoms. |
| RT4 | "vomiting nahi hai" ⇒ vomiting `negated=true`; absent from active symptoms. |
| RT5 | "appendicitis" absent from input ⇒ never in diagnoses. |
| RT6 | No explicit diagnosis stated ⇒ diagnoses view is empty (no constellation inference). |
| RT7 | "3 din baad aana" ⇒ follow_up captured, normalized "after 3 days". |
| RT8 | "agar fever continue kare toh CBC kara lena" ⇒ follow_up conditional; CBC NOT an active investigation. |
| RT9 | "Metformin band kar do" ⇒ medication status=stopped, not new. |
| RT10 | "BP 140 over 90" / "sugar fasting 160" ⇒ exact value+unit preserved. |
| RT11 | Determinism: same transcript twice ⇒ byte-identical facts. |
| RT12 | Span verity: every emitted fact's evidence_span verbatim-matches source_sentence. |

RT3, RT4, RT5, RT6, RT12 are **hard safety gates** — any failure blocks pilot.

---

## 11. Pilot-readiness thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Medication name precision | ≥ 0.97 | False meds are unacceptable. |
| Medication name recall | ≥ 0.90 | Misses are recoverable by physician edit. |
| Medication dosage exact-match (on matched) | ≥ 0.90 | Wrong dose is a safety event. |
| Diagnosis precision | ≥ 0.98 | Near-zero false diagnoses. |
| Diagnosis recall | not gated | Conservative-by-design; empty is acceptable. |
| Negation accuracy | ≥ 0.95 | Missed negation = active wrong symptom. |
| Follow-up recall | ≥ 0.85 | Core OPD value. |
| Vitals value accuracy (value+unit) | ≥ 0.95 | Verbatim fidelity. |
| **Hard gate** | 0 fabricated diagnoses, 0 negation-flip-to-active, 0 span-verity failures across golden set | Any one blocks pilot. |

---

## 12. Implementation phases (small, Sonnet-safe)

- **Phase 0 — Unify the measured pipeline (no behavior change).** Make eval call the production path (or move GLiNER merge into the extractor). Doctors and eval must run the same code. Add the 20 golden cases + 12 regression tests against the *current* pipeline to get a baseline.
- **Phase 1 — Evidence-gating + schema + close the three doors.** Introduce the §4 fact schema with span-verify. Remove fuzzy diagnosis (R2), remove free-text diagnosis label capture (R3), remove SOAP constellation inference (R4). SOAP renders explicit diagnoses only. Wire RT1–RT12.
- **Phase 2 — Clause-scoped negation & temporality.** Replace char-window negation (R6) with the §6 engine. Replace whole-sentence uncertainty skip (R5) with per-fact confidence. Conditional → follow-up routing.
- **Phase 3 — Medication temporality + vitals expansion.** status/route/duration (R10); glucose/weight vitals (R8); allergy-med conflict flag.
- **Phase 4 (optional) — Evidence-gated generative proposal layer.** A model proposes spans for recall on unseen surface forms only; gated by lexicon ∩ offset-verify. Never for values.

Each phase ends green on the golden set before the next begins.

---

## 13. Exact prompt for Sonnet — Phase 1

> You are modifying Lipi's clinical extractor. Scope: Phase 1 only. Do NOT touch negation internals, medication temporality, or vitals coverage — those are later phases.
>
> Preconditions: Phase 0 is done — `eval/golden/` has 20 cases and `tests/test_extraction_regression.py` has RT1–RT12, and eval runs the same pipeline doctors run.
>
> Make exactly these changes:
> 1. Introduce a per-fact schema: `{original_text, normalized_value, category, language, source_sentence, evidence_span, confidence, negated, temporality, section_hint, safety_flags}`. Build the existing flat lists (`symptoms`, `medications`, …) as views derived from `facts` so the SOAP renderer and eval keep working.
> 2. Enforce span verity: for every fact, assert `source_sentence[evidence_span[0]:evidence_span[1]] == original_text`; if it fails, drop the fact. Add a unit test.
> 3. Remove `_fuzzy_extract_diagnoses` and its call site. Diagnoses come only from exact lexicon match or explicit assessment language.
> 4. Remove the free-text `_DIAGNOSIS_LABEL_RE` capture that accepts arbitrary text after a label. Keep only matches whose captured text intersects the diagnosis lexicon.
> 5. In `soap_generator.py`, delete `_SYMPTOM_IMPRESSIONS` and the constellation-inference branch. Assessment shows only explicitly stated diagnoses; if none, render exactly: "No diagnosis stated by clinician — physician to assess."
> 6. SOAP renderer must consume only facts with `negated == false and temporality == 'current'`.
>
> Constraints: deterministic only — no LLM, no Ollama, no GLiNER changes in this phase. No new dependencies. Every change must keep RT1–RT12 green and must not lower any metric in §11 on the golden set. Run `python -m eval.run_eval --dir eval/golden` and `pytest tests/test_extraction_regression.py` before and after; paste both outputs. If any regression-test or metric regresses, stop and report — do not work around it.
>
> Deliverable: the diff, the before/after eval output, and a one-paragraph confirmation that RT3/RT4/RT5/RT6/RT12 (the hard safety gates) pass.

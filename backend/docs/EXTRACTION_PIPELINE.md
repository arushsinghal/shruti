# Lipi Clinical Extraction Pipeline

**Branch:** `pilot-prod-hardening`  
**Last updated:** Sprint 2 (Extraction Safety)

---

## What this is

Lipi converts spoken doctor–patient consultations into structured SOAP notes. The extraction pipeline is the core: it reads a transcript (English / Hindi / Hinglish) and outputs symptoms, vitals, medications, investigations, allergies, follow-up instructions, and diagnoses — with no generative model in the loop.

**Safety constraint (non-negotiable):** Every output value must be an extractive span from the transcript or a canonical alias of one. The pipeline must never fabricate or infer clinical facts.

---

## Pipeline architecture

```
Transcript
    │
    ▼
[Layer 1] ClinicalExtractorService          backend/app/services/clinical_extractor.py
    │  Deterministic keyword/regex + spaCy negation
    │  Produces: symptoms, vitals, medications, investigations,
    │            allergies, follow_up, diagnoses
    │
    ▼
[Layer 2] GLiNER (optional, additive only)   backend/app/services/clinical_pipeline.py
    │  Zero-shot extractive NER
    │  Model: urchade/gliner_medium-v2.1
    │  Fields: medications, investigations, allergies, follow_up ONLY
    │  Safety gate: every output must be a substring of the transcript
    │
    ▼
Merged facts  →  SOAP generator  →  CDS alerts  →  API response
```

### Layer 1 — Deterministic extraction

`ClinicalExtractorService.extract(transcript)` in [clinical_extractor.py](../app/services/clinical_extractor.py):

| Field | Method |
|-------|--------|
| Symptoms | Bilingual keyword lexicon + transliteration map (bukhar→fever, khansi→cough, …). Negation-aware. |
| Vitals | Regex patterns: temperature (°C/°F), BP, SpO₂, pulse, weight, blood glucose |
| Medications | Regex: `<name> <dosage> <frequency>` with frequency alias map (BD/TDS/OD/…) |
| Investigations | Keyword list (CBC, CRP, X-ray, …) + GLiNER fallback |
| Allergies | "allergic to / allergy: <X>" patterns |
| Follow-up | "come back / follow up in / review after" patterns + Hindi equivalents |
| Diagnoses | Exact lexicon match with explicit assessment language (no fuzzy, no inference) |

### Layer 2 — GLiNER augmentation

`run_pipeline(transcript)` in [clinical_pipeline.py](../app/services/clinical_pipeline.py) wraps both layers and applies the **extractive safety gate**:

```python
# Every GLiNER output must appear verbatim in the transcript
for field, items in gliner_facts.items():
    for item in items:
        if item.lower() not in transcript.lower():
            logger.warning("GLiNER extractive-safety violation: %r (field=%s)", item, field)
```

GLiNER **cannot** add symptoms or diagnoses. Those fields are Layer 1 only.

---

## Sprint 2 fixes (Extraction Safety)

Five classes of bugs fixed. All covered by regression tests in `tests/test_services.py`.

### 1. Diabetes context leak (Task 1)

**Bug:** `"sugar": "Diabetes Mellitus"` in `_DIAGNOSIS_MAP` fired on "fasting sugar 160", injecting a false diagnosis.

**Fix:**
- Removed `"sugar"` from `_DIAGNOSIS_MAP` entirely.
- Added a pre/post context window check (`_is_context_mention`) so phrases like "known case of diabetes on metformin" or "on treatment for diabetes" do not populate the diagnoses field. Only explicit assessment-language mentions are kept.

**Test class:** `TestSprint2DiabetesContextLeak` (5 tests)

### 2. Vitals regex gaps (Task 2)

Three separate regex failures:

| Symptom | Before | After |
|---------|--------|-------|
| Temperature | `(?:degree\s*)?` — missed "38.5 degrees Celsius" (plural) | `(?:degrees?\s*)?` |
| BP | `(?:/\|over)` — missed "140 by 90" | `(?:/\|over\|by)` |
| Blood glucose | Pattern required glucose keyword immediately before number — missed "fasting sugar **today is** 160" | Added `[^.;]{0,20}?` to allow intervening words |

**Test class:** `TestSprint2VitalsRegex` (5 tests)

### 3. Follow-up decimal truncation (Task 3)

**Bug:** Pattern `[^\.\n;,]+` stopped at the `.` in "if fever above **39.5**", capturing only "39".

**Fix:** Changed character class to `(?:[^\n;,]|\.(?=\d))+` — a `.` is allowed only when immediately followed by a digit.

**Test class:** `TestSprint2FollowupTruncation` (4 tests)

### 4. GLiNER extractive safety gate (Task 4)

**Bug:** No runtime check that GLiNER outputs were actual transcript spans. A fabricated value could enter the merged result silently.

**Fix:** Post-GLiNER loop (shown above) logs a WARNING for every value that does not appear in the transcript. Gate runs on `gliner_facts` (raw GLiNER output) before merge, so Layer 1 canonical names (e.g. "Fasting Blood Glucose") are not checked — only GLiNER's own output is.

**Test class:** `TestSprint2GLiNERSafety` (5 tests)

---

## Eval harness

```
backend/eval/
├── run_eval.py        # runner: calls run_pipeline(), computes field-level F1
└── cases/
    ├── case_T1.txt + case_T1_gt.json   # Basic English OPD
    ├── case_T2.txt + case_T2_gt.json   # Hindi/Hinglish (bukhar→fever)
    ├── case_T3.txt + case_T3_gt.json   # SAFETY: diabetes context → diagnoses must be []
    ├── case_T4.txt + case_T4_gt.json   # Vitals edge cases (degrees plural, "by", glucose)
    ├── case_T5.txt + case_T5_gt.json   # Decimal follow-up ("if fever above 39.5")
    └── case_T6.txt + case_T6_gt.json   # Allergy safety (penicillin in allergies only)
```

Run:
```bash
cd backend
python eval/run_eval.py
```

Expected output (Sprint 2 baseline):
```
T1  F1=1.00   Basic English OPD
T2  F1=1.00   Hindi/Hinglish
T3  F1=1.00   Diabetes context safety
T4  F1=1.00   Vitals edge cases
T5  F1=1.00   Decimal follow-up
T6  F1=1.00   Allergy safety
```

Case T3 and T6 are **safety cases** — a regression there means patient-harming output, not just a metric drop.

---

## Running the test suite

```bash
cd backend
pytest tests/test_services.py -v
```

103 tests total. Key test classes:

| Class | Tests | What it covers |
|-------|-------|----------------|
| `TestSprint2DiabetesContextLeak` | 5 | Context guard for diagnoses |
| `TestSprint2VitalsRegex` | 5 | Temperature plural, BP "by", glucose gaps |
| `TestSprint2FollowupTruncation` | 4 | Decimal in follow-up strings |
| `TestSprint2GLiNERSafety` | 5 | Extractive safety gate |

---

## Files changed in Sprint 2

| File | What changed |
|------|-------------|
| `app/services/clinical_extractor.py` | Removed `"sugar"` from diagnosis map; added `_is_context_mention` context guard; fixed temperature/BP/glucose regex; fixed follow-up decimal pattern |
| `app/services/clinical_pipeline.py` | Added GLiNER extractive safety gate (pre-merge check) |
| `tests/test_services.py` | Added 19 Sprint 2 regression tests (84 → 103 total) |
| `eval/cases/case_T1–T6.*` | 6 golden eval cases created |

---

## What is NOT in this pipeline

These constraints are hard rules — do not add them:

- **No generative/LLM model** in the clinical extraction path (no Ollama, no GPT, no Gemini)
- **No CDS (clinical decision support)** logic in the extractor itself
- **No symptom inference** — if the doctor did not say it, it does not appear
- **GLiNER is additive only** for medications, investigations, allergies, follow-up — not symptoms or diagnoses
- **Diagnoses require explicit assessment language** — "known case of X" or "on treatment for X" is not a new diagnosis

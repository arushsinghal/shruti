# Lipi Learning Flywheel Design

## What the flywheel is

Doctor corrections feed back into the extraction system to make it better over time:

```
Doctor corrects a fact  -->  correction stored in fact_corrections
                        -->  aggregated into extraction_knowledge (candidate)
                        -->  promoted after multi-clinic confirmation
                        -->  injected into extractor as overlay rules
                        -->  fewer corrections needed next time
```

Each cycle reduces the correction rate. The flywheel accelerates as more clinics onboard — each clinic's corrections benefit all others.

## Privacy-by-construction guarantee

The `extraction_knowledge` table stores **vocabulary facts**, not patient data:

| Column | Example value | PHI risk |
|---|---|---|
| `knowledge_type` | `asr_correction` | None |
| `canonical_value` | `paracetamol` | None |
| `surface_form` | `paracetemol` | None |
| `field` | `medications` | None |

Key + canonical_value pairs are drug names, symptom synonyms, or ASR transcription patterns. A correction like `paracetemol -> paracetamol` is a fact about ASR behaviour, not a clinical observation about a patient.

The table has **no patient-identifying columns** (no name, phone, Aadhaar, ABHA, or address fields). This is PHI-free by structural design, not by post-hoc scrubbing.

## Confidence scoring formula

Confidence uses a Bayesian update with a base prior:

```
confidence = (BASE_PRIOR * PRIOR_WEIGHT + confirmations) / (PRIOR_WEIGHT + confirmations + rejections)
```

Where:
- `BASE_PRIOR = 0.3` (initial belief)
- `PRIOR_WEIGHT = 2.0` (how strongly we weight the prior)

A single confirmation starts at 0.3. Each independent confirmation from a new user raises confidence. Rejections lower it. The formula is smooth and monotonic — no cliff effects.

Per-user idempotency: the same user confirming the same correction twice does not increment the count. The `confirming_users` JSON array tracks who has confirmed.

## Multi-clinic confirmation requirement

Auto-promotion requires **all three** conditions:
1. `confidence >= 0.9`
2. `unique_clinics >= 3` (independent clinic environments)
3. `confirmations >= 3` (independent users)

This prevents a single noisy clinic from polluting the knowledge base.

## extraction_knowledge table schema

```sql
CREATE TABLE extraction_knowledge (
    id              INTEGER PRIMARY KEY,
    knowledge_type  TEXT NOT NULL,           -- e.g. 'asr_correction', 'symptom_synonym'
    canonical_value TEXT NOT NULL,           -- correct/standard form
    surface_form    TEXT NOT NULL,           -- what ASR/doctor actually said
    field           TEXT NOT NULL,           -- 'medications', 'symptoms', etc.
    confidence      REAL NOT NULL DEFAULT 0.3,
    confirmations   INTEGER NOT NULL DEFAULT 1,
    rejections      INTEGER NOT NULL DEFAULT 0,
    unique_clinics  INTEGER NOT NULL DEFAULT 1,
    status          TEXT NOT NULL DEFAULT 'candidate',  -- candidate | promoted | rejected
    confirming_users TEXT NOT NULL DEFAULT '[]',        -- JSON array of user IDs
    promoted_at     TEXT,
    promoted_by     TEXT,
    rejected_at     TEXT,
    rejected_by     TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    UNIQUE (knowledge_type, canonical_value, surface_form)
);
```

## How promotion works

**Automatic:** When a `record_correction()` call causes confidence to cross 0.9 AND the entry has 3+ unique clinics AND 3+ confirmations, the entry is auto-promoted. Status becomes `promoted`, confidence is set to 1.0, and `promoted_at`/`promoted_by` are recorded.

**Manual:** An admin calls `admin_approve(entry_id)`. This promotes immediately regardless of confidence or clinic count. Used for known-good corrections that don't yet have enough organic confirmations.

Promoted entries are loaded by `load_promoted_knowledge()` and injected as overlay rules into the clinical extractor. The overlay maps `surface_form -> canonical_value` per field.

## How demotion works

`admin_reject(entry_id)` sets status to `rejected` instantly. Rejected entries:
- Cannot receive new confirmations (record_correction returns None)
- Are excluded from the extractor overlay
- Can be restored via `admin_revert()` back to `candidate` status

Rejection is reversible. Revert clears `rejected_at` and `rejected_by`.

## The YC narrative

> Our model improves with usage, yet patient data never enters the learning loop.

Every doctor correction teaches the system. But what gets stored is `paracetemol -> paracetamol` (ASR vocabulary) or `bukhar -> fever` (Hinglish synonym) — never "Patient X has condition Y." The extraction_knowledge table is structurally incapable of containing PHI.

This means:
- The knowledge base can be shared across clinics without consent issues
- It can be exported, audited, and versioned as a plain data file
- Regulatory review is straightforward: show the table, it contains only medical vocabulary

The flywheel compounds: 10 clinics produce a better extraction model than 1, which reduces corrections for clinic 11. This is the network effect that makes Lipi harder to replicate over time.

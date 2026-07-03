# Lipi — Technical Specification

**Version:** June 2026  
**Status:** Pilot-ready  
**Audience:** Founder, accelerator reviewers, technical due-diligence

---

## 1. What Lipi Is

Lipi is an AI clinical scribe for Indian OPD (outpatient) doctors.

A doctor speaks during a consultation. Lipi transcribes the audio, extracts
structured clinical data, generates a SOAP note, flags drug safety alerts,
and produces a printable prescription — all without sending patient data to
any external server.

**Core guarantee:** No patient data ever leaves the clinic's device or network.

---

## 2. Architecture in One Picture

```
Doctor's phone / tablet (PWA)
        │
        │  Audio (WebSocket or upload)
        ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                      │
│  Audio → ASR → Transcript → Clinical Extractor      │
│                                    │                 │
│                              Memory Context          │
│                            /       │       \         │
│                         SOAP      CDS     FHIR       │
│                          Note   Alerts   Bundle      │
│                                   │                  │
│                            Prescription PDF          │
│                                                      │
│  SQLite (default) / PostgreSQL (production)         │
└─────────────────────────────────────────────────────┘
        │
        │  React/TypeScript SPA (served from same server)
        ▼
Doctor's browser (dashboard, consultation, review)
```

Everything runs on a single machine. No cloud dependency required.

---

## 3. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python 3.12 + FastAPI | Async, fast, typed |
| Database | SQLite (default) / PostgreSQL | Dual-support via custom wrapper |
| Frontend | React 19 + TypeScript + Tailwind | Fast, typed, maintainable |
| Build | Vite 8 | Sub-second HMR, builds to `backend/dist/` |
| ASR | Sarvam AI (cloud, opt-in) / local Whisper | India-language support |
| Clinical NLP | GLiNER + custom rule engine | Extractive only — no generative model |
| Mobile | PWA (Progressive Web App) | Installable on Android/iOS, no app store |
| Package manager | uv (Python) + npm (Node) | Fast, reproducible |

---

## 4. The Clinical Pipeline (most important section)

This is Lipi's core. It converts raw speech into structured clinical data.

### 4.1 What "extractive only" means

Lipi never generates or invents clinical content. Every output is a span
extracted from the transcript. If the doctor didn't say it, it doesn't appear.

This is a deliberate safety constraint. Generative models (GPT, Gemini, etc.)
can hallucinate drug names, dosages, or diagnoses. Lipi's pipeline cannot —
it can only fail to extract something, never fabricate it.

### 4.2 Pipeline steps

```
Transcript
    │
    ▼
clinical_extractor.py          ← rule-based + GLiNER
    │
    │  Produces raw "facts":
    │  { medications: [...], diagnoses: [...],
    │    symptoms: [...], vitals: [...],
    │    allergies: [...], follow_up: [...] }
    │
    ▼
memory_context.py              ← merges multiple fact sets,
    │                             resolves corrections,
    │                             adds ICD-10 codes
    │
    │  Produces "state" (single merged view of the patient)
    │
    ├──► soap_generator.py     → SOAP note (Subjective/Objective/Assessment/Plan)
    │
    ├──► cds_engine.py         → drug safety alerts
    │
    ├──► fhir_mapper.py        → HL7 FHIR R4 Bundle (international standard)
    │
    └──► icd10_mapper.py       → WHO ICD-10 codes on all diagnoses
```

### 4.3 GLiNER (the NLP model)

GLiNER is a Named Entity Recognition model. It reads the transcript and marks
spans like "500mg", "amoxicillin", "hypertension". It does NOT generate text —
it only draws boxes around words that already exist.

Every GLiNER output is post-filtered: only spans that appear verbatim in the
transcript are kept. This is the extractive guarantee.

### 4.4 What the pipeline cannot do

- Cannot invent medications
- Cannot infer diagnoses not mentioned
- Cannot translate between languages (handled by ASR layer)
- Cannot correct a doctor who misspoke

---

## 5. Drug Safety (CDS Engine)

CDS = Clinical Decision Support. File: `backend/app/services/cds_engine.py`

### 5.1 What it checks

| Check | Example | Alert level |
|-------|---------|-------------|
| Direct allergy | Patient allergic to penicillin, prescribed penicillin V | Critical |
| Cross-reactivity | Patient allergic to penicillin, prescribed amoxicillin | Critical |
| Cross-class | Patient allergic to penicillin, prescribed ceftriaxone | Critical |
| Missing dosage | Metformin prescribed with no dose | Medium |
| Missing frequency | Atorvastatin prescribed with no schedule | Medium |
| Fever workup | Fever mentioned, no CBC/blood test ordered | Low |
| Diabetes monitoring | Diabetes documented, no HbA1c | Medium |
| BP alert | BP ≥ 140/xx detected in vitals | High |

### 5.2 Cross-reactivity drug classes covered

Penicillins, cephalosporins, sulfonamides, NSAIDs/aspirin, fluoroquinolones,
macrolides, statins, ACE inhibitors. Covers the drug families most commonly
prescribed in Indian OPD.

### 5.3 What CDS does NOT do

- No generative model
- No internet lookup
- No drug-drug interaction checking (beyond same-class)
- No dosage range validation (future work)

All CDS logic is deterministic. Given the same inputs, it always produces
the same outputs. Auditable, explainable, no black box.

---

## 6. Patient Memory

File: `backend/app/services/memory_service.py`

Lipi remembers clinical facts across visits. If a patient was seen last month
with a penicillin allergy, the next consultation surfaces that allergy
automatically — and CDS fires if a penicillin-class drug is prescribed.

### 6.1 What is stored

- Known allergies
- Current medications
- Prior diagnoses
- Recorded vitals
- Investigations ordered
- Symptoms mentioned
- Visit count

### 6.2 Storage

Local database only (SQLite or PostgreSQL). Never synced externally.
Keyed by patient name (normalized to lowercase).

### 6.3 How it shows up

When a doctor opens a consultation for a returning patient, a card appears
at the top of the screen showing prior allergies, diagnoses, and medications.
This is read-only context — the doctor decides what to act on.

---

## 7. ICD-10 Coding

File: `backend/app/services/icd10_mapper.py`

Every diagnosis is automatically tagged with its WHO ICD-10 code.

Example:
- "Diabetes Mellitus" → E11.9 (Type 2 diabetes mellitus without complications)
- "Hypertension" → I10 (Essential primary hypertension)
- "Pneumonia" → J18.9 (Pneumonia, unspecified organism)

~90 diagnoses covered, prioritised for Indian OPD patterns.

These codes flow into the FHIR export, enabling interoperability with hospital
systems, ABDM (India's national health stack), and insurance claims.

---

## 8. FHIR Export

File: `backend/app/services/fhir_mapper.py`

Every completed consultation produces a valid HL7 FHIR R4 Bundle containing:

| Resource | Contents |
|----------|----------|
| Patient | Name |
| Encounter | Date, type (ambulatory) |
| Condition (encounter-diagnosis) | Diagnoses with ICD-10 codes |
| Condition (problem-list) | Symptoms |
| MedicationRequest | Each medication with dose + frequency |
| AllergyIntolerance | Allergies |
| Observation (vital-signs) | Vitals |

FHIR R4 is the international standard for health data exchange. This makes
Lipi compatible with ABDM, Epic, Cerner, and most hospital EMR systems.

---

## 9. Prescription PDF

Endpoint: `GET /api/sessions/{id}/prescription`

Returns a styled HTML page that the browser renders and the doctor prints
or saves as PDF. Contains:

- Clinic header (teal, Lipi branding)
- Patient name, doctor name, date
- Safety alert banner (if any critical CDS alerts fired)
- Known allergies
- Diagnoses with ICD-10 codes
- Medications table (name, dose, frequency)
- Follow-up instructions
- Doctor signature line

Works on mobile. No PDF library dependency — uses browser's native print.

**Known gap:** Doctor's MCI registration number and clinic address not yet
on the prescription. Required for legal validity in India. Planned next.

---

## 10. SOAP Note

File: `backend/app/services/soap_generator.py`

Standard clinical note format used by doctors worldwide:

- **S (Subjective):** What the patient said (symptoms, complaints)
- **O (Objective):** Measurable data (vitals, investigations)
- **A (Assessment):** Diagnoses
- **P (Plan):** Medications, follow-up, referrals

Generated from the resolved memory state. Deterministic — same state always
produces the same note structure.

---

## 11. Mobile (PWA)

Files: `frontend/public/manifest.webmanifest`, `frontend/public/sw.js`

Lipi is installable on Android and iOS as a Progressive Web App — no app
store required. Doctor opens the URL in Chrome on Android, taps "Add to
Home Screen", and gets a native-feeling app icon.

### 11.1 PWA features

| Feature | Implementation |
|---------|---------------|
| Installable icon | manifest.webmanifest with 192px + 512px icons |
| Offline shell | Network-first service worker, caches app shell |
| Screen wake lock | `navigator.wakeLock.request('screen')` during recording |
| Standalone mode | No browser chrome, feels native |

### 11.2 Wake Lock

When a doctor starts recording, Lipi requests a screen wake lock. The phone
screen stays on throughout the consultation without requiring taps. Released
automatically when recording stops.

### 11.3 Audio recording

Uses browser's `MediaRecorder` API. Audio captured in chunks, sent via
WebSocket to the backend in real time. Transcript appears as the doctor speaks.

---

## 12. Data Storage

### 12.1 Schema (key tables)

```sql
sessions
  id TEXT PRIMARY KEY
  patient_name TEXT
  doctor_name TEXT
  created_at DATETIME
  status TEXT          -- created → transcribed → extracted → complete
  mode TEXT            -- health | government | legal | general
  transcript TEXT
  clinical_facts JSON
  memory_state JSON    -- resolved merged state
  soap_note JSON
  cds_suggestions JSON
  user_id TEXT

patient_memory
  id INTEGER PRIMARY KEY
  patient_name TEXT UNIQUE   -- normalized lowercase
  visit_count INTEGER
  medications JSON
  diagnoses JSON
  allergies JSON
  investigations JSON
  symptoms JSON
  vitals JSON
  last_updated DATETIME

soap_feedback
  id INTEGER PRIMARY KEY
  session_id TEXT
  status TEXT
  original_soap JSON
  final_soap JSON
  categories JSON
  timestamp DATETIME
```

### 12.2 Dual database support

Lipi supports SQLite (default, zero configuration) and PostgreSQL (production).
The same async abstraction (`DBConnection` / `ExecuteWrapper`) handles both.
Switch by setting `DATABASE_URL` in the environment.

---

## 13. Authentication

JWT-based authentication. Doctors log in with email + password. Sessions are
scoped to the authenticated user — a doctor cannot see another doctor's sessions.

Passwords hashed with bcrypt. Tokens signed with `python-jose`.

---

## 14. What Lipi Does NOT Do

These are intentional constraints, not gaps:

| Capability | Status | Reason |
|-----------|--------|--------|
| Generative AI in clinical path | Never | Hallucination risk |
| Patient data to external servers | Never | Privacy, DPDP Act compliance |
| Regional language translation | Not yet | Scope for post-pilot |
| ABDM integration | Not yet | Requires production infra |
| WhatsApp prescription delivery | Not yet | Scope |
| Drug-drug interaction checking | Not yet | Requires drug database license |
| Dosage range validation | Not yet | Future |
| Billing / claims | Out of scope | Different product |

---

## 15. Deployment (How to Run)

### Local development

```bash
# Backend (Python)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8001

# Frontend (builds into backend/dist/)
cd frontend
npm install
npm run build        # production build
# OR
npm run dev          # development with HMR on port 5173
```

### Doctor pilot (same WiFi)

```bash
# On Mac, find your local IP
ifconfig | grep "inet 192"   # e.g. 192.168.68.103

# Start backend accessible on network
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001

# Doctor opens on Android
http://192.168.68.103:8001
# Chrome → "Add to Home Screen"
```

### Environment variables

```
DATABASE_URL=          # omit for SQLite, set for PostgreSQL
SECRET_KEY=            # JWT signing key
SARVAM_API_KEY=        # for cloud ASR (optional, local ASR works without it)
```

---

## 16. Safety Model

Lipi is a documentation tool. It assists doctors — it does not replace them.

| Principle | Implementation |
|-----------|---------------|
| Extractive only | No generative model in any clinical output path |
| Doctor always reviews | SOAP note and prescription shown before printing |
| CDS is advisory | Alerts shown, doctor decides whether to act |
| Audit trail | All sessions stored with original transcript |
| PHI scrubbing | `phi_scrubber.py` removes identifiable data before feedback logging |
| Non-fatal errors | Memory upsert failures are logged but never crash a consultation |

CDS alerts use language like "Verify tolerance before prescribing" — never
"Do not prescribe." The doctor makes every clinical decision.

---

## 17. Competitive Position

| Competitor | Gap Lipi fills |
|-----------|---------------|
| Nuance DAX (Microsoft) | US-only, cloud-only, $$$, no Indian drug names |
| Suki AI | US-only, requires EHR integration |
| Nabla | European focus, no ABDM |
| Generic Indian EMRs | Typing-based, no voice, no AI |

Lipi's moat: local-first (no cloud dependency), Indian OPD drug vocabulary,
ABDM-ready FHIR, works on a ₹15,000 Android phone.

---

## 18. File Map

```
clinical-decision-support-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_notes.py       # core clinical endpoints + prescription
│   │   │   ├── routes_sessions.py    # session CRUD
│   │   │   ├── routes_audio.py       # audio upload + WebSocket ASR
│   │   │   └── routes_auth.py        # JWT auth
│   │   ├── services/
│   │   │   ├── clinical_extractor.py # rule-based NLP extraction
│   │   │   ├── gliner_extractor.py   # GLiNER NER model
│   │   │   ├── clinical_pipeline.py  # orchestrates extraction
│   │   │   ├── memory_context.py     # merges facts, adds ICD-10
│   │   │   ├── memory_service.py     # patient memory persistence
│   │   │   ├── cds_engine.py         # drug safety alerts
│   │   │   ├── icd10_mapper.py       # WHO ICD-10 lookup
│   │   │   ├── fhir_mapper.py        # FHIR R4 export
│   │   │   ├── soap_generator.py     # SOAP note generation
│   │   │   └── phi_scrubber.py       # PHI removal for feedback
│   │   ├── storage/
│   │   │   ├── db.py                 # SQLite/PostgreSQL abstraction
│   │   │   └── repository.py         # session CRUD
│   │   └── schemas/
│   │       └── consultation.py       # Pydantic models
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Consultation.tsx      # main recording + results page
    │   │   ├── Dashboard.tsx         # session list
    │   │   └── Review.tsx            # SOAP note review + FHIR export
    │   ├── components/
    │   │   ├── AudioUploader.tsx     # recording with wake lock
    │   │   └── ClinicalResults.tsx  # structured output display
    │   └── lib/
    │       └── api.ts                # typed API client
    └── public/
        ├── manifest.webmanifest      # PWA manifest
        ├── sw.js                     # service worker
        └── icons/                    # app icons
```

---

*Last updated: June 2026. Built by Arush Singhal.*

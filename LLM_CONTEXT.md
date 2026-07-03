# Lipi — LLM onboarding context

Paste this into any LLM conversation to give it full context on the Lipi codebase without needing to read every file.

---

## Prompt

You are working on **Lipi**, an AI clinical scribe for Indian OPD doctors. The codebase is at the root of this repo. Here is everything you need to know:

### What it does
Doctor dictates in Hindi/Hinglish/English during a consultation. Lipi records audio, transcribes via Sarvam ASR (model `saaras:v3`), extracts clinical facts locally (no LLM), generates a SOAP note + Indian-format prescription, and shares it via WhatsApp. Doctor reviews and edits facts before SOAP generation. All clinical NLP runs locally — patient data never goes to external LLMs for extraction.

### Stack
- **Backend:** Python 3.12, FastAPI, Pydantic v2, aiosqlite + asyncpg (dual SQLite/PostgreSQL), uvicorn
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Framer Motion
- **ASR:** Sarvam AI API (`saaras:v3`), Whisper fallback
- **NLP:** spaCy `en_core_web_sm`, GLiNER (NER), rapidfuzz (fuzzy match)
- **LLM:** Gemini `gemini-2.0-flash` — ONLY for SOAP text formatting, never extraction
- **Auth:** JWT (python-jose + bcrypt)
- **Deploy:** Docker multi-stage, Render (Singapore), branch `master`

### Run commands
```
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
cd backend && uv run python -m pytest tests/ -v
cd frontend && npx tsc --noEmit
```

### Architecture (backend)

```
API Layer (all under /api prefix):
  routes_auth.py      → JWT login/register, NMC validation, onboarding completion
  routes_sessions.py  → Session CRUD, consent, patient data deletion
  routes_audio.py     → Audio upload, Sarvam/local ASR transcription
  routes_notes.py     → Clinical pipeline, facts editing, prescription, follow-ups, audit logs
  routes_analytics.py → Usage metrics, billing, practice stats
  routes_clinics.py   → Multi-clinic management
  routes_ws.py        → WebSocket realtime transcription
  routes_public.py    → Unauthenticated prescription download (token-gated)

Service Layer:
  clinical_pipeline.py    → Orchestrator: calls extractor + GLiNER, merges results
  clinical_extractor.py   → 4-layer local extraction (see below)
  gliner_extractor.py     → GLiNER NER model (Layer 3)
  memory_context.py       → Cross-visit memory resolution, ICD-10 mapping
  soap_generator.py       → SOAP note with Indian Rx format (Tab./Syp./Inj., OD/BD/TDS)
  cds_engine.py           → Drug alerts: direct allergy + cross-reactive class checking
  phi_scrubber.py         → PHI removal (names, phones, emails, Aadhaar, ABHA, MRN/UHID, address-pincodes) — runs BEFORE DB storage
      learning_service.py     → Learning flywheel: correction aggregation, confidence scoring, admin review
  sarvam_asr.py           → Sarvam cloud ASR (realtime + chunk modes)
  sarvam_batch_asr.py     → Batch ASR for large files
  local_asr.py            → Whisper fallback
  prescription_renderer.py → HTML prescription generation
  whatsapp_service.py     → Twilio WhatsApp send
  fhir_mapper.py          → FHIR R4 bundle export
  llm_client.py           → Gemini API (SOAP formatting only)

Storage Layer:
  db.py           → DDL for 16 tables, init_db(), migrations (SQLite + PostgreSQL)
  repository.py   → SessionRepository: all async DB operations
```

### 16 database tables
`sessions`, `users`, `doctor_profiles`, `clinics`, `clinic_members`, `patient_memory`, `audit_log`, `usage_events`, `extraction_feedback`, `soap_feedback`, `consent_logs`, `follow_up_reminders`, `billing_records`, `practice_settings`, `fact_corrections`, `extraction_knowledge`

### Learning flywheel
`fact_corrections` stores raw doctor corrections. `extraction_knowledge` aggregates them into reusable knowledge with Bayesian confidence scoring. `LearningService` handles ingestion, auto-promotion (confidence >= 0.9 + 3 clinics), and admin review. Promoted entries inject into the extractor as overlay rules (surface_form -> canonical_value). The knowledge table is PHI-free by construction — only drug names, symptom synonyms, and ASR patterns.

### Clinical extraction pipeline (4 layers, all local)

```
Layer 0: ASR normalization   → _normalize_asr_text(): rejoin split words, fix 50+ drug misspellings
Layer 1: Keyword maps        → Hindi + Hinglish + Devanagari + English symptom/med dictionaries
Layer 2: Fuzzy matching      → rapidfuzz catches remaining ASR spelling errors
Layer 3: GLiNER NER          → gliner_extractor.py entity recognition, merged with L1+L2
```

### Extraction output shape (this is the facts dict)
```python
{
  "symptoms": ["fever", "cough"],
  "medications": [{"name": "paracetamol", "dosage": "500mg", "frequency": "TDS", "duration": "5 days"}],
  "vitals": ["BP 120/80"],
  "allergies": ["penicillin"],
  "diagnoses": [],
  "investigations": [],
  "follow_up": ["Follow up in 3 days"]
}
```

### Pipeline data flow
```
run_health_pipeline(transcript) → facts dict (extraction only)

In routes_notes.py, the full chain:
  transcript → run_health_pipeline() → facts
  facts → memory.resolve_memory([facts]) → state (meds become dict keyed by name)
  state → soap_gen.generate_soap(state) → {"S": "...", "O": "...", "A": "...", "P": "..."}
  state → cds_engine.generate_cds(state) → [alert dicts]
```

### Critical conventions you MUST follow

1. **SOAP keys are single uppercase letters:** `{"S", "O", "A", "P"}` — NOT `subjective`, `objective`, `assessment`, `plan`
2. **Indian prescription format:** `Tab. Paracetamol 500mg PO TDS x 5 days`. Form prefix inferred (Tab./Syp./Inj./Inh.). Frequencies: "twice daily" → BD, "raat ko" → HS
3. **PHI scrubbed BEFORE storage** — not just on export
4. **NMC number regex:** `^[A-Z]{2,3}-?\d{4,7}$` (format only, no registry API)
5. **ABHA number:** 14 digits after stripping dashes/spaces (format only)
6. **Auth flow:** Register → Login (JWT) → Onboarding (NMC + specialization required) → Dashboard
7. **ProtectedRoute** redirects to `/onboarding` if `onboarding_complete` is false
8. **CDS drug safety:** Direct allergy-drug conflicts (critical urgency) + cross-reactive class alerts (penicillin↔cephalosporin, NSAIDs, statins, ACE inhibitors)
9. **Session modes:** `health` (clinical scribe) or `legal` (medico-legal docs)

### Frontend architecture
```
Pages (protected):
  Dashboard.tsx       → Session list, create (health/legal mode + ABHA + consent)
  Consultation.tsx    → Record audio → review facts (FactsReviewEditor) → generate SOAP
  ReviewNote.tsx      → Final SOAP note, prescription print, WhatsApp share, follow-up
  Analytics.tsx       → Practice metrics, billing, clinic management
  AuditLogs.tsx       → Audit trail viewer
  DoctorProfile.tsx   → Profile management

Key components:
  AudioUploader.tsx        → Recording + upload + WebSocket realtime
  FactsReviewEditor.tsx    → Editable facts with "flag issue" feedback
  ClinicalResults.tsx      → SOAP display, FHIR export, sub-documents
  ShareWhatsappModal.tsx   → WhatsApp prescription share
  PrescriptionPrint.tsx    → Printable Indian-format prescription
  FollowUpReminderModal.tsx → Schedule follow-up reminders

Shared:
  lib/api.ts          → 30+ typed API functions (axios)
  context/AuthContext.tsx → JWT state, user object with nmc_number/onboarding_complete
  types/clinical.ts   → ConsultationSession, SessionMode, Specialty, ProcessClinicalResponse
```

### Safety rules (non-negotiable)
1. Never hallucinate — if not in transcript, write "not specified"
2. All CDS output: `safety_label = "doctor_review_required"` always
3. Never auto-prescribe or claim diagnosis certainty
4. Allergy-medication conflicts = urgency: critical
5. Patient data never sent to external LLMs for extraction
6. Doctor is final authority

### Tests (148 total)
- `test_e2e.py` (36) — full pipeline, Hindi extraction, SOAP quality, NMC/ABHA
- `test_services.py` (77) — extractor edge cases, negation, vitals, medications
- `test_routes.py` (23) — API endpoints
- `test_whatsapp_sharing.py` (5) — WhatsApp flow
- `test_doctor_product_metrics.py` (4) — analytics
- `test_phase2a.py` (3) — governance

### Key env vars
`SARVAM_API_KEY`, `GEMINI_API_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL` (PostgreSQL) or `SQLITE_DB`, `ASR_MODE` (cloud/local/stub), `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, `PUBLIC_BASE_URL`

### What NOT to do
- Don't use lowercase SOAP keys (`subjective` etc.) — always `S/O/A/P`
- Don't send patient data to LLMs for extraction — all NLP is local
- Don't skip PHI scrubbing before DB writes
- Don't hardcode secrets — use pydantic-settings
- Don't add `safety_label` values other than `"doctor_review_required"`

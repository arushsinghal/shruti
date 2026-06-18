# CLAUDE.md

## gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__Claude_in_Chrome__*` tools directly.

### Available skills

/office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /setup-gbrain, /retro, /investigate, /document-release, /document-generate, /codex, /cso, /autoplan, /plan-devex-review, /devex-review, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn

---

## Project
Multilingual Doctor Voice-to-SOAP Clinical Decision Support System.
Healthcare documentation tool. Doctor-assistive only — never autonomous.

## Stack
- Backend: Python, FastAPI, Pydantic v2, aiosqlite, uvicorn
- Frontend: React + Vite + TypeScript + Tailwind CSS
- LLM: Google Gemini API — package: google-generativeai — model: gemini-2.0-flash — key: GEMINI_API_KEY — always request JSON via response_mime_type="application/json"
- ASR: Sarvam API — endpoint: https://api.sarvam.ai/speech-to-text — key: SARVAM_API_KEY — stub if key missing
- Storage: SQLite via aiosqlite
- Never hardcode secrets. Always read from environment via pydantic-settings.

## Directory layout
backend/
  app/
    main.py
    api/
      routes_health.py
      routes_sessions.py
      routes_audio.py
      routes_notes.py
    services/
      sarvam_asr.py
      clinical_extractor.py
      memory_context.py
      soap_generator.py
      cds_engine.py
    schemas/
      consultation.py
      clinical_fact.py
      medication.py
      soap.py
      cds.py
    storage/
      db.py
      repository.py
    utils/
      config.py
  prompts/
    clinical_extraction.txt
    memory_resolver.txt
    soap_generation.txt
    cds_suggestions.txt
  uploads/
  samples/
    transcript_demo.txt
    transcript_simple.txt

frontend/
  src/
    App.tsx
    main.tsx
    pages/
      Dashboard.tsx
      Consultation.tsx
      ReviewNote.tsx
    components/
      AudioUploader.tsx
      TranscriptViewer.tsx
      ClinicalFactPanel.tsx
      MemoryTimeline.tsx
      SOAPNoteEditor.tsx
      CDSSuggestions.tsx
    lib/
      api.ts
    types/
      clinical.ts

## API endpoints
GET  /health
POST /sessions
GET  /sessions/{id}
POST /sessions/{id}/audio
POST /sessions/{id}/transcribe
POST /sessions/{id}/extract
POST /sessions/{id}/resolve-memory
POST /sessions/{id}/generate-soap
POST /sessions/{id}/generate-cds
GET  /sessions/{id}/final-note

## Session status flow
created → audio_uploaded → transcribed → extracted → memory_resolved → soap_ready → complete

## Key data models

ConsultationSession: id, patient_name?, doctor_name?, created_at, status, transcript, clinical_facts, memory_state, soap_note, cds_suggestions

ClinicalFact: id, category, value, status (active|superseded|uncertain|negated), confidence, source_text, timestamp_order, supersedes?, requires_confirmation

Medication: name, dose, route, frequency, duration, timing, indication, status, source_text, history[]

MemoryState: active_facts, superseded_facts, uncertain_facts, unresolved_references, audit_trail

SOAPNote: subjective{chief_complaint, hpi, symptoms, allergies, current_medications}, objective{vitals, exam, labs, imaging}, assessment{diagnosis, differentials, impression, severity}, plan{medications, investigations, lifestyle, follow_up, red_flags, referrals}

CDSSuggestion: suggestion, rationale, urgency (low|medium|high|critical), evidence_from_transcript[], safety_label (always "doctor_review_required")

## Memory-aware context rules
- Latest explicit doctor instruction always wins
- Earlier instruction → status: superseded, stored in history with reason
- Indirect references ("that one", "same dose", "make it evening") → resolve to most recent relevant fact
- Negations override positives ("no fever" overrides "has fever")
- Uncertainty preserved ("possible", "maybe", "rule out") → status: uncertain
- Final SOAP note shows only active facts
- Full audit trail always preserved internally

## Safety rules (non-negotiable)
1. Never hallucinate — if not in transcript write "not specified"
2. Never claim diagnosis certainty unless doctor stated it explicitly
3. All CDS output safety_label = "doctor_review_required" always
4. Never auto-prescribe
5. Flag allergy-medication conflicts as urgency: critical
6. Ambiguous doses → requires_confirmation: true
7. Doctor is final authority on everything

## Prompt files
Each prompt file must contain: task description, input schema, output schema (JSON), safety constraints, and one example. Prompts call Gemini with response_mime_type="application/json".

## Code rules
- Pydantic v2 models everywhere in backend
- Type hints on all Python functions
- TypeScript types for all frontend data
- No hardcoded values
- aiosqlite for all DB operations (async)
- CORS enabled for localhost:5173 in dev
- requirements.txt must include: fastapi, uvicorn[standard], pydantic-settings, aiosqlite, google-generativeai, python-multipart, python-dotenv

## Milestones
M1: FastAPI skeleton + React skeleton + health check + session CRUD + README
M2: Audio upload endpoint + Sarvam ASR service + stub transcript + transcript UI
M3: Clinical extraction prompt + Gemini call + structured facts + facts UI
M4: Memory resolver prompt + Gemini call + memory state + timeline UI  ← core differentiator
M5: SOAP generation prompt + Gemini call + editable SOAP UI + export
M6: CDS prompt + Gemini call + urgency-sorted suggestions UI + safety disclaimer
M7: Sample transcripts + error handling + loading states + one-click demo mode + README polish

## Build one milestone at a time. Confirm it runs before moving to next.
## LLM usage policy — UPDATED DECISION
LLM (Gemini) is NOT used for clinical extraction, memory resolution, or conflict detection.
Reason: patient data privacy + hallucination risk unacceptable in clinical context.

All clinical NLP runs fully locally:
- spaCy + en_core_sci_sm: biomedical named entity recognition
- negspaCy: negation detection ("no fever" → negated, "denies vomiting" → negated)
- Python regex: dose patterns (500mg), frequency (twice daily, TID), vitals (38.5°C)
- Pure Python state machine: memory resolution, supersession, conflict detection

LLM MAY be used only for final SOAP note text formatting (optional, clearly labeled).
Even then, input is fully structured — LLM only formats, never infers clinical facts.

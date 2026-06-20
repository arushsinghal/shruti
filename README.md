# Clinical Decision Support System

Multilingual Doctor Voice-to-SOAP Clinical Decision Support System.
A doctor-assistive documentation tool — never autonomous.

## Stack

- **Backend**: Python, FastAPI, Pydantic v2, aiosqlite
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Clinical NLP**: Local spaCy + deterministic rule engine
- **LLM**: Optional formatting only; clinical extraction/CDS stay local
- **ASR**: Sarvam API (speech-to-text)
- **Storage**: SQLite via aiosqlite

## Environment Setup

Create `backend/.env`:

```
GEMINI_API_KEY=your_gemini_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

Keys are optional for local demo mode. Clinical extraction, memory resolution, SOAP drafting, and CDS alerts run locally.

## Running the Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --reload-exclude .venv
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

## Core API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/sessions` | Create a new consultation session |
| GET | `/sessions` | List all sessions |
| GET | `/sessions/{id}` | Get a session by ID |
| POST | `/sessions/{id}/audio` | Upload consultation audio |
| POST | `/sessions/{id}/transcribe` | Transcribe uploaded audio |
| POST | `/sessions/{id}/transcript` | Submit transcript text directly |
| POST | `/sessions/{id}/process-clinical` | Run local clinical extraction, SOAP, and CDS |
| GET | `/sessions/{id}/fhir` | Export an HL7 FHIR bundle |

## Milestones

| # | Description | Status |
|---|-------------|--------|
| M1 | FastAPI skeleton + React skeleton + health check + session CRUD | ✅ Complete |
| M2 | Audio upload + Sarvam ASR + transcript UI | Complete |
| M3 | Local clinical extraction + facts UI | Complete |
| M4 | Local memory/state resolver + source context | Complete |
| M5 | SOAP generation + editable SOAP UI + export | Complete |
| M6 | Local CDS engine + urgency-sorted suggestions | Complete |
| M7 | Sample transcripts + error handling + demo mode | Complete |

## Evaluation Harness

Lipi includes an offline evaluation harness to measure extraction precision, recall, and F1-score without running the web app or making HTTP calls.

### Usage

1. **Describe Mode** (print extracted fields from a transcript):
   ```bash
   cd backend
   uv run python -m eval.run_eval --transcript samples/transcript_demo.txt
   ```

2. **Ground Truth Comparison** (evaluate single transcript against a ground-truth JSON):
   ```bash
   cd backend
   uv run python -m eval.run_eval --transcript samples/transcript_demo.txt --ground-truth samples/transcript_demo_gt.json
   ```

3. **Batch Directory Mode** (evaluate multiple transcripts in a folder against ground truth):
   ```bash
   cd backend
   uv run python -m eval.run_eval --dir samples/ --output samples/eval_results.json
   ```

---

## Observation Sprint Kit

To coordinate real-world clinic pilots (e.g. 14-day OPD observation sprints), Lipi provides a ready-to-use template kit under the `observation_sprint/` folder:

- **Instructions**: [sprint_instructions.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/sprint_instructions.md)
- **Checklist**: [14_day_checklist.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/14_day_checklist.md)
- **Consent Scripts**: [patient_consent_script.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/patient_consent_script.md) & [doctor_consent_script.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/doctor_consent_script.md)
- **Tracking Sheets**: CSV templates for consultation metadata and per-field extraction failure logs.

---

## Privacy & Safety Controls

1. **Patient Consent Gate**: Audio uploads, manual text submissions, and NLP processing are strictly blocked until doctor confirms patient verbal consent in the UI (`cloud_ai_consent=true`).
2. **Local PHI Scrubber**: Patient names, email addresses, phone numbers, and absolute dates are detected and scrubbed locally before transcript text is saved to the database.
3. **Instant Audio Deletion**: Under DPDPA compliance guidelines, raw audio files are automatically unlinked (deleted) from servers immediately after clinical notes are successfully generated.
4. **Assistive Warning**: All CDS suggestions carry a safety label `"doctor_review_required"`. The doctor remains the final medical authority and must review all draft outputs.


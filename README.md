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

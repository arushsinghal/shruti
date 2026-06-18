# Lipi
Assisting rural clinicians with safe, multilingual documentation at the point of care.

> Research Prototype | Not a certified medical device

## Research Motivation
In rural India, the doctor-to-patient ratio stands at 1:1,457. Clinicians in high-throughput settings spend 30-40% of each consultation on manual documentation, directly reducing time available for patient care. Existing clinical NLP tools do not support Hindi, Hinglish, or low-connectivity offline environments. Lipi is a research prototype exploring whether safe, structured clinical documentation can be achieved at the edge, in the languages clinicians actually speak.

## What This System Does
Lipi processes oral consultations to generate structured clinical records through a multi-stage pipeline:
- **Multilingual Speech Ingestion**: Captures live microphone streaming or audio file uploads and utilizes speech-to-text models (such as the Sarvam API or edge-safe Whisper models) to transcribe consultations spoken in English, Hindi, or mixed Hinglish.
- **Local PHI De-identification**: Scrubs Protected Health Information (including patient names, phone numbers, email addresses, dates, and locations) locally for privacy-preserving review and export.
- **Rule-Based Clinical Extraction**: Runs a local, deterministic NLP engine using spaCy and negation-aware regular expressions to identify symptoms, vitals, allergies, investigations, and medications.
- **Memory Resolution**: Tracks patient state changes, resolving doctor self-corrections and negation scopes over the course of a single session.
- **SOAP Note Synthesis**: Organizes extracted facts into standard Subjective, Objective, Assessment, and Plan (SOAP) summaries.
- **Clinical Decision Support (CDS) Alerts**: Evaluates safety parameters, flagging drug-allergy interactions, elevated vitals, and missing dosage parameters.
- **Standard Interoperable Export**: Compiles the final verified data into standard HL7 FHIR R4 JSON bundles for integration with national health registries.
- **Human-in-the-Loop Verification**: Requires explicit physician review and digital signature before finalizing any clinical documentation.

## System Architecture
The prototype is built on a modular, decoupled architecture to ensure offline functionality:
- **API Layer**: Python-based FastAPI application exposing asynchronous endpoints for audio ingestion, transcription, clinical extraction, and FHIR generation.
- **Ingestion & Streaming**: Native WebSockets protocol for real-time browser-to-server audio chunk transmission.
- **ASR Pipeline**: Integrated with the Sarvam API for multi-dialect transcription, featuring concurrent audio segmentation via `pydub` and `ffmpeg` to bypass length constraints.
- **Extraction & Heuristics**: Local `spaCy` (using the `en_core_web_sm` model) for sentence parsing and semantic grouping, coupled with specialized regex patterns for dialect mapping.
- **Clinical Documentation Engine**: Uses a local deterministic pipeline for extraction, memory resolution, SOAP drafting, and CDS alerts. Cloud LLM use is not required for clinical NLP.
- **Data Storage**: Local SQLite database operated asynchronously using `aiosqlite` to store session state, transcripts, and audit logs.

## Research Limitations
- Negation detection degrades on code-switched Hinglish where language transitions disrupt syntactic dependency parsing
- Local rule-based extraction has limited recall and should be reviewed against the transcript
- Not validated in live clinical settings
- Not a certified medical device
- Edge routing decisions not yet formally optimized

## Open Research Questions
1. How can we robustly parse negation scopes and resolve coreferences in low-resource, code-switched clinical dialogue where standard syntactic dependency parsers fail?
2. How can local clinical extraction improve recall while preserving auditability and privacy?
3. How can field deployments measure time returned to physicians without disrupting clinical workflow?

## Setup & Installation

### Prerequisites
- Python 3.10+
- `uv` (Fast Python package installer)
- `ffmpeg` (for audio segment processing)

### Installation Steps
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
3. Create the environment configuration file `backend/.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   SARVAM_API_KEY=your_sarvam_api_key
   ```
   *Note: Environment keys are optional for running the deterministic local edge NLP model.*

### Running the Server
Start the FastAPI development server:
```bash
uv run uvicorn app.main:app --reload --reload-exclude .venv
```
- Interactive API documentation is available at: `http://localhost:8000/docs`
- Health check endpoint: `http://localhost:8000/health`

## Disclaimer
This is a research prototype developed for academic purposes. It is not a certified medical device and has not been clinically validated. All clinical decisions must be made by qualified medical practitioners.

## License
MIT License

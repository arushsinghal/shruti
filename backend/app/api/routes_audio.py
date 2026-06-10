import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.schemas.consultation import StatusEnum
from app.services.sarvam_asr import SarvamASRService
from app.services.local_asr import LocalASRService
from app.storage.repository import SessionRepository
from app.utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
repo = SessionRepository()
asr = SarvamASRService()
local_asr = LocalASRService()

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = Path(settings.data_dir) if settings.data_dir else _BACKEND_DIR
_UPLOADS_DIR = _DATA_DIR / "uploads"
_ALLOWED_SUFFIXES = {".mp3", ".wav", ".m4a", ".webm"}


class AudioUploadResponse(BaseModel):
    session_id: str
    file_path: str
    status: str


class TranscribeResponse(BaseModel):
    transcript: str
    language_detected: str
    is_stub: bool
    diarized_transcript: str | None = None


class TextTranscriptRequest(BaseModel):
    transcript: str


@router.post("/sessions/{session_id}/audio", response_model=AudioUploadResponse)
async def upload_audio(session_id: str, file: UploadFile = File(...)) -> AudioUploadResponse:
    """Ingests raw consultation audio files for processing within the research pipeline. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    suffix = Path(file.filename or "audio.bin").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(_ALLOWED_SUFFIXES))}",
        )

    dest_dir = _UPLOADS_DIR / session_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / (file.filename or f"audio{suffix}")

    contents = await file.read()
    dest_path.write_bytes(contents)
    logger.info("Saved audio to %s (%d bytes)", dest_path, len(contents))

    session.status = StatusEnum.audio_uploaded
    session.audio_file_path = str(dest_path)
    await repo.update_session(session)

    return AudioUploadResponse(
        session_id=session_id,
        file_path=str(dest_path),
        status=session.status.value,
    )


@router.post("/sessions/{session_id}/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(session_id: str) -> TranscribeResponse:
    """Transcribes uploaded audio files using selected ASR models (cloud/local) for study. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == StatusEnum.created:
        raise HTTPException(status_code=400, detail="Upload audio before transcribing")
    if not session.audio_file_path:
        raise HTTPException(status_code=400, detail="No audio file path recorded for this session")

    try:
        if settings.asr_mode == "edge":
            result = await local_asr.transcribe(session.audio_file_path)
        else:
            result = await asr.transcribe(session.audio_file_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.transcript = result["transcript"]

    # Keep transcript handling local-first. Cloud LLM diarization is intentionally
    # disabled for clinical privacy; the physician can edit speaker attribution
    # directly in the review workflow.
    diarized = None

    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    return TranscribeResponse(
        transcript=result["transcript"],
        language_detected=result["language_code"],
        is_stub=result["is_stub"],
        diarized_transcript=diarized,
    )


@router.post("/sessions/{session_id}/transcript", response_model=TranscribeResponse)
async def submit_text_transcript(session_id: str, body: TextTranscriptRequest) -> TranscribeResponse:
    """Saves manual text transcripts to bypass speech-to-text layer for comparative evaluation. Research prototype only — output requires physician review."""
    session = await repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session.transcript = body.transcript

    # Keep transcript handling local-first. Cloud LLM diarization is intentionally
    # disabled for clinical privacy; the physician can edit speaker attribution
    # directly in the review workflow.
    diarized = None

    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    return TranscribeResponse(
        transcript=body.transcript,
        language_detected="en",
        is_stub=False,
        diarized_transcript=diarized,
    )

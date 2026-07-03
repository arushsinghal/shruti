import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from app.schemas.consultation import StatusEnum
from app.services.phi_scrubber import PHIScrubberService
from app.services.sarvam_asr import SarvamASRService
from app.services.sarvam_batch_asr import SarvamBatchASRService
from app.services.local_asr import LocalASRService
from app.storage.repository import SessionRepository
from app.utils.config import settings
from app.utils.rate_limit import limiter
from app.api.routes_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
repo = SessionRepository()
realtime_asr = SarvamASRService()
batch_asr = SarvamBatchASRService()
local_asr = LocalASRService()
phi_scrubber = PHIScrubberService()

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = Path(settings.data_dir) if settings.data_dir else _BACKEND_DIR
_UPLOADS_DIR = _DATA_DIR / "uploads"
_ALLOWED_SUFFIXES = {".mp3", ".wav", ".m4a", ".webm", ".ogg"}
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB — Sarvam limit is ~60 s of audio
MAGIC_BYTES: dict[str, list[bytes]] = {
    ".mp3": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    ".wav": [b"RIFF"],
    ".m4a": [b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftyp"],
    ".webm": [b"\x1a\x45\xdf\xa3"],
    ".ogg": [b"OggS"],  # WhatsApp voice notes are Opus-encoded OGG
}


class AudioUploadResponse(BaseModel):
    session_id: str
    file_path: str
    status: str


class DiarizedSegment(BaseModel):
    speaker_id: str
    role: str                   # "Professional" | "Client"
    transcript: str
    start_time_seconds: float
    end_time_seconds: float


class TranscribeResponse(BaseModel):
    transcript: str
    language_detected: str
    is_stub: bool
    diarized_segments: Optional[list[DiarizedSegment]] = None
    # Human-readable formatted version for UI display
    diarized_transcript: Optional[str] = None


class TextTranscriptRequest(BaseModel):
    transcript: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_diarized_transcript(segments: list[dict]) -> str:
    """Build a human-readable speaker-labelled transcript string for UI display.

    Example output:
        [Professional] Patient ko bukhar hai teen din se...
        [Client] Haan, penicillin se rash aaya tha.
        [Professional] Paracetamol 500mg twice daily start karo.
    """
    lines = []
    for seg in segments:
        role = seg.get("role", "Speaker")
        text = seg.get("transcript", "").strip()
        if text:
            lines.append(f"[{role}] {text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/audio", response_model=AudioUploadResponse)
async def upload_audio(
    session_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
) -> AudioUploadResponse:
    """Upload raw consultation audio. Accepts MP3, WAV, M4A, WebM."""
    session = await repo.get_session(session_id, str(current_user["id"]))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.cloud_ai_consent:
        raise HTTPException(
            status_code=403,
            detail="Patient consent required before audio upload. Confirm consent first.",
        )

    suffix = Path(file.filename or "audio.bin").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(_ALLOWED_SUFFIXES))}",
        )

    header = await file.read(16)
    await file.seek(0)
    valid = False
    for magic in MAGIC_BYTES.get(suffix, []):
        if header[: len(magic)] == magic:
            valid = True
            break

    dest_dir = _UPLOADS_DIR / session_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    import uuid as _uuid
    dest_path = dest_dir / f"{_uuid.uuid4().hex}{suffix}"

    total = 0
    with open(dest_path, "wb") as out:
        while chunk := await file.read(65536):
            total += len(chunk)
            if total > _MAX_UPLOAD_BYTES:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Audio file too large. Maximum is {_MAX_UPLOAD_BYTES // (1024*1024)} MB.",
                )
            out.write(chunk)
    if not valid and suffix in MAGIC_BYTES:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File content does not match declared type '{suffix}'.")
    logger.info("Saved audio to %s (%d bytes)", dest_path, total)

    session.status = StatusEnum.audio_uploaded
    session.audio_file_path = str(dest_path)
    await repo.update_session(session)

    return AudioUploadResponse(
        session_id=session_id,
        file_path=str(dest_path),
        status=session.status.value,
    )


@router.post("/sessions/{session_id}/transcribe", response_model=TranscribeResponse)
@limiter.limit("30/minute")
async def transcribe_audio(
    request: Request,
    session_id: str,
    language_code: str = Query(default="hi-IN", description="BCP-47 language hint. Default hi-IN for best Hindi/Hinglish accuracy."),
    diarize: bool = Query(default=False, description="Enable speaker diarization (slower, ~60s). Default off for live dictation."),
    num_speakers: int = Query(default=2, ge=1, le=10, description="Expected number of speakers. Only used when diarize=true."),
    professional_speaker_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
) -> TranscribeResponse:
    """Transcribe uploaded audio.

    Default: real-time Sarvam STT (saarika:v2) — returns in 2-5 seconds.
    With diarize=true: Sarvam Batch API with speaker separation — returns in ~60 seconds.
    """
    session = await repo.get_session(session_id, str(current_user["id"]))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == StatusEnum.created:
        raise HTTPException(status_code=400, detail="Upload audio before transcribing")
    if not session.audio_file_path:
        raise HTTPException(status_code=400, detail="No audio file path recorded for this session")

    try:
        if settings.asr_mode == "edge":
            result = await local_asr.transcribe(session.audio_file_path)
            segments = [{
                "speaker_id": "speaker_1", "role": "Professional",
                "transcript": result["transcript"],
                "start_time_seconds": 0.0, "end_time_seconds": 0.0,
            }]
            plain_transcript = result["transcript"]
            language_detected = result["language_code"]
            is_stub = result.get("is_stub", False)

        elif diarize:
            # Batch mode: speaker diarization, ~60s
            result = await batch_asr.transcribe_with_diarization(
                audio_path=session.audio_file_path,
                language_code=language_code,
                num_speakers=num_speakers,
                professional_speaker_id=professional_speaker_id,
            )
            segments = result["diarized_segments"]
            plain_transcript = result["transcript"]
            language_detected = result["language_code"]
            is_stub = result["is_stub"]

        else:
            # Real-time mode: fast, high accuracy, no diarization — best for live dictation
            result = await realtime_asr.transcribe(session.audio_file_path, language_code)
            plain_transcript = result["transcript"]
            language_detected = result["language_code"]
            is_stub = result.get("is_stub", False)
            segments = [{
                "speaker_id": "speaker_1", "role": "Professional",
                "transcript": plain_transcript,
                "start_time_seconds": 0.0, "end_time_seconds": 0.0,
            }]

    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="ASR service timed out. Please retry.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Scrub PHI from transcript text before DB storage.
    # Note: audio was already sent to Sarvam in the clear (STT requires raw audio).
    # This scrub removes identifiers from the stored text so downstream processing
    # (clinical extraction, future LLM calls) never sees patient names/contacts.
    plain_transcript = phi_scrubber.scrub(plain_transcript)
    scrubbed_segments = [
        {**seg, "transcript": phi_scrubber.scrub(seg.get("transcript", ""))}
        for seg in segments
    ]

    # Persist both the plain transcript and the structured segments
    session.transcript = plain_transcript
    session.diarized_transcript = scrubbed_segments
    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    return TranscribeResponse(
        transcript=plain_transcript,
        language_detected=language_detected,
        is_stub=is_stub,
        diarized_segments=[DiarizedSegment(**s) for s in scrubbed_segments],
        diarized_transcript=_format_diarized_transcript(scrubbed_segments),
    )


@router.post("/sessions/{session_id}/transcript", response_model=TranscribeResponse)
async def submit_text_transcript(
    session_id: str,
    body: TextTranscriptRequest,
    current_user: dict = Depends(get_current_user),
) -> TranscribeResponse:
    """Submit a manual text transcript, bypassing audio upload and ASR.

    The submitted text is treated as a single Professional speaker segment.
    Physicians can edit speaker attribution directly in the review workflow.
    """
    session = await repo.get_session(session_id, str(current_user["id"]))
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.cloud_ai_consent:
        raise HTTPException(
            status_code=403,
            detail="Patient consent required before submitting transcript. Confirm consent first.",
        )

    scrubbed_text = phi_scrubber.scrub(body.transcript)

    # Wrap the manual text as a single Professional segment
    segments = [
        {
            "speaker_id": "speaker_1",
            "role": "Professional",
            "transcript": scrubbed_text,
            "start_time_seconds": 0.0,
            "end_time_seconds": 0.0,
        }
    ]

    session.transcript = scrubbed_text
    session.diarized_transcript = segments
    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    return TranscribeResponse(
        transcript=scrubbed_text,
        language_detected="en",
        is_stub=False,
        diarized_segments=[DiarizedSegment(**s) for s in segments],  # type: ignore
        diarized_transcript=_format_diarized_transcript(segments),
    )


# ---------------------------------------------------------------------------
# Intake voice-extract (no session required)
# ---------------------------------------------------------------------------

def _extract_intake_fields(transcript: str) -> dict:
    """Extract structured patient intake fields from a Hinglish/Hindi/English transcript."""
    import re
    fields: dict = {}
    t = transcript

    # Name: "naam X hai" / "naam hai X" / "patient ka naam X"
    name_pats = [
        r'(?:naam|name)\s+(?:hai\s+)?([A-Za-z][A-Za-z\s]{1,35}?)(?=\s+(?:hai|hain|ka|ki|ke|\d|age|umar|saal|year)|[,.]|$)',
        r'patient\s+(?:ka\s+naam\s+)?([A-Za-z][A-Za-z\s]{1,35}?)(?=\s+(?:hai|hain|ka|ki|ke|\d|age|umar|saal|year)|[,.]|$)',
    ]
    for pat in name_pats:
        m = re.search(pat, t, re.I)
        if m:
            candidate = m.group(1).strip().title()
            if 2 <= len(candidate) <= 40 and not any(c.isdigit() for c in candidate):
                fields['patient_name'] = candidate
                break

    # Age: "N saal" / "N years" / "age N"
    age_m = re.search(r'(\d{1,3})\s*(?:saal|sal|year|varsh|baras|उम्र)', t, re.I)
    if not age_m:
        age_m = re.search(r'(?:age|umar|umra)\s+(?:is\s+)?(\d{1,3})', t, re.I)
    if age_m:
        age = int(age_m.group(1))
        if 0 < age < 120:
            fields['patient_age'] = str(age)

    # Sex
    if re.search(r'\b(male|purush|aadmi|mard|ladka)\b', t, re.I):
        fields['patient_sex'] = 'M'
    elif re.search(r'\b(female|mahila|aurat|ladki|girl|woman)\b', t, re.I):
        fields['patient_sex'] = 'F'

    # Chief complaint: common complaint patterns
    cc_pats = [
        r'(?:complaint|problem|takleef|pareshani|symptom)[:\s]+([^.!?\n]{3,100})',
        r'(?:bukhaar|fever|dard|pain|khasi|cough|ulti|vomit|sar|sir|pait|pet|chest|saans|chakkar)\b[^.!?\n]{0,80}',
    ]
    for pat in cc_pats:
        m = re.search(pat, t, re.I)
        if m:
            cc = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else m.group(0).strip()
            if len(cc) >= 3:
                fields['chief_complaint'] = cc[:120]
                break

    return fields


@router.post("/intake/voice-extract")
async def intake_voice_extract(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Transcribe assistant intake audio via Sarvam and extract patient fields.

    No session is created. Returns raw transcript and extracted fields so the
    assistant can review and correct before submitting the intake form.
    """
    if current_user.get("role") != "assistant":
        raise HTTPException(status_code=403, detail="Only assistants can use voice intake.")

    suffix = Path(file.filename or "audio.bin").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported type '{suffix}'. Use mp3, wav, m4a, or webm.")

    import os
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        while chunk := await file.read(65536):
            tmp.write(chunk)

    try:
        result = await realtime_asr.transcribe(tmp_path, language_code="hi-IN")
        transcript = result.get("transcript", "")
        fields = _extract_intake_fields(transcript)
        return {
            "transcript": transcript,
            "language_detected": result.get("language_code", "hi-IN"),
            "is_stub": result.get("is_stub", False),
            **fields,
        }
    finally:
        os.unlink(tmp_path)

"""Sarvam ASR service — converts uploaded audio to transcript text via the Sarvam speech-to-text API.

Supports:
- Automatic language detection (language_code="unknown")
- Audio chunking for files > 29 seconds via pydub + ffmpeg
- Graceful fallback to a deterministic stub transcript
"""
import asyncio
import io
import logging
from pathlib import Path
from typing import List

import httpx

from app.utils.config import settings

logger = logging.getLogger(__name__)

_STUB_TRANSCRIPT = (
    "Patient is a 34-year-old male presenting with fever since two days. "
    "Temperature was 38.5 C. BP is 150/90. Start paracetamol 500 mg twice daily. "
    "Patient says he had rash with penicillin last year. "
    "Note that allergy — penicillin allergy confirmed. "
    "Also check CBC and CRP. Follow up in three days. "
    "No chest pain, no vomiting. Also a headache and nausea. "
    "Allergic to penicillin."
)

_SARVAM_URL = "https://api.sarvam.ai/speech-to-text"

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False
    logger.warning("pydub not installed — audio chunking disabled. Install with: uv add pydub")


class SarvamASRService:
    """Wraps the Sarvam API (https://api.sarvam.ai/speech-to-text).

    Falls back to a fixed stub transcript when SARVAM_API_KEY is absent
    or when API limits are exceeded. Includes audio chunking for long files.
    """

    async def transcribe(self, audio_path: str, language_code: str = "unknown") -> dict:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file on disk.
            language_code: Sarvam language hint. Defaults to "unknown" for auto-detection.
                           Set to "hi-IN" to force Hindi, "en-IN" to force English, etc.

        Returns:
            dict with keys: transcript, language_code, is_stub
        """
        if not settings.sarvam_api_key:
            logger.warning("SARVAM_API_KEY not set — returning stub transcript")
            return self._stub_response(language_code)

        path = Path(audio_path)
        logger.info("Transcribing file: %s (language_code=%s)", audio_path, language_code)

        # --- Audio Chunking for long files ---
        if HAS_PYDUB:
            try:
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
                logger.info("Audio duration: %d ms", duration_ms)

                if duration_ms > 29_000:
                    logger.info("Audio > 29s — splitting into 25s chunks")
                    chunks = self._chunk_audio(audio, chunk_length_ms=25_000)
                    logger.info("Created %d chunks", len(chunks))

                    tasks = [
                        self._transcribe_chunk(chunk, path.suffix.lower(), language_code, idx)
                        for idx, chunk in enumerate(chunks)
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    transcripts: list[str] = []
                    detected_lang = language_code
                    for i, res in enumerate(results):
                        if isinstance(res, Exception):
                            logger.error("Chunk %d failed: %s", i, res)
                        elif isinstance(res, dict):
                            if res.get("text"):
                                transcripts.append(res["text"])
                            if res.get("language_code") and detected_lang == "unknown":
                                detected_lang = res["language_code"]
                        elif isinstance(res, str) and res:
                            transcripts.append(res)

                    if not transcripts:
                        logger.warning("All chunks failed — falling back to stub")
                        return self._stub_response(language_code)

                    return {
                        "transcript": " ".join(transcripts),
                        "language_code": detected_lang,
                        "is_stub": False,
                    }
            except Exception as e:
                logger.error("Chunking failed: %s — falling through to single-file attempt", e)

        # --- Single request (short files or chunking unavailable) ---
        return await self._transcribe_single_file(path, language_code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _transcribe_single_file(self, path: Path, language_code: str) -> dict:
        """Send a single audio file to the Sarvam API."""
        mime = _mime_for(path.suffix.lower())
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with path.open("rb") as fh:
                    response = await client.post(
                        _SARVAM_URL,
                        headers={"api-subscription-key": settings.sarvam_api_key},
                        files={"file": (path.name, fh, mime)},
                        data={"language_code": language_code},
                    )

            if response.status_code != 200:
                logger.error("Sarvam API error %d: %s", response.status_code, response.text)
                logger.warning("Falling back to stub transcript")
                return self._stub_response(language_code)

            body = response.json()
            detected = body.get("language_code", language_code)
            logger.info("Sarvam ASR OK — detected language: %s", detected)
            return {
                "transcript": body.get("transcript", ""),
                "language_code": detected,
                "is_stub": False,
            }
        except Exception as e:
            logger.error("Network/parsing error: %s", e)
            return self._stub_response(language_code)

    def _chunk_audio(self, audio: "AudioSegment", chunk_length_ms: int) -> List:
        """Split audio into non-overlapping chunks of `chunk_length_ms` ms."""
        chunks = []
        for start in range(0, len(audio), chunk_length_ms):
            chunks.append(audio[start : start + chunk_length_ms])
        return chunks

    async def _transcribe_chunk(
        self, chunk: "AudioSegment", suffix: str, language_code: str, chunk_idx: int
    ) -> dict:
        """Export a pydub chunk to memory and POST it to the Sarvam API."""
        logger.info("  → Transcribing chunk %d …", chunk_idx)

        buf = io.BytesIO()
        export_fmt = suffix.lstrip(".")
        if export_fmt == "m4a":
            export_fmt = "mp4"
        if export_fmt not in ("mp3", "wav", "mp4"):
            export_fmt = "wav"

        chunk.export(buf, format=export_fmt)
        buf.seek(0)

        mime = _mime_for(suffix)
        filename = f"chunk_{chunk_idx}{suffix}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                _SARVAM_URL,
                headers={"api-subscription-key": settings.sarvam_api_key},
                files={"file": (filename, buf, mime)},
                data={"language_code": language_code},
            )

        if response.status_code != 200:
            logger.error("Chunk %d error %d: %s", chunk_idx, response.status_code, response.text)
            return {"text": "", "language_code": language_code}

        body = response.json()
        return {
            "text": body.get("transcript", ""),
            "language_code": body.get("language_code", language_code),
        }

    @staticmethod
    def _stub_response(language_code: str) -> dict:
        return {
            "transcript": _STUB_TRANSCRIPT,
            "language_code": language_code,
            "is_stub": True,
        }


def _mime_for(suffix: str) -> str:
    return {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".webm": "audio/webm",
    }.get(suffix, "application/octet-stream")

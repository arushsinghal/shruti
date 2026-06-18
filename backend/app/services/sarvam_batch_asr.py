"""Sarvam Batch ASR service — diarized transcription via the Sarvam Batch API.

5-step async pipeline:
  1. Initiate job  → receive job_id
  2. Get presigned upload URL
  3. PUT audio to presigned URL (Azure Blob / GCS)
  4. Start the job
  5. Poll status → download result JSON → parse speaker segments

Returns speaker-labelled segments with timestamps.
Falls back to stub when API key is absent or any step fails.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

import httpx

from app.utils.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.sarvam.ai"
_POLL_INTERVAL_SECONDS = 5
_MAX_POLL_ATTEMPTS = 60  # 5 minutes maximum wait

# Stub used when SARVAM_API_KEY is absent or the batch job fails.
# Mirrors a realistic Hindi/Hinglish clinical consultation so the rest of
# the pipeline (extractor, SOAP generator, CDS) still runs meaningfully.
from typing import Any

_STUB_SEGMENTS: list[dict[str, Any]] = [
    {
        "speaker_id": "speaker_1",
        "role": "Professional",
        "transcript": (
            "Patient ko teen din se bukhar hai. Temperature 38.5 C. "
            "BP 150 over 90. Penicillin se allergy hai na? Note karo."
        ),
        "start_time_seconds": 0.0,
        "end_time_seconds": 7.5,
    },
    {
        "speaker_id": "speaker_2",
        "role": "Client",
        "transcript": "Haan, penicillin se rash aaya tha pehle.",
        "start_time_seconds": 7.8,
        "end_time_seconds": 10.2,
    },
    {
        "speaker_id": "speaker_1",
        "role": "Professional",
        "transcript": (
            "Theek hai. Paracetamol 500mg twice daily start karo. "
            "CBC aur CRP bhi karwa lo. Follow up teen din mein."
        ),
        "start_time_seconds": 10.5,
        "end_time_seconds": 16.8,
    },
    {
        "speaker_id": "speaker_2",
        "role": "Client",
        "transcript": "Aur sir mein bhi dard hai thoda, nausea bhi.",
        "start_time_seconds": 17.0,
        "end_time_seconds": 19.6,
    },
    {
        "speaker_id": "speaker_1",
        "role": "Professional",
        "transcript": (
            "Headache aur nausea note karo. Chest pain nahin hai? "
            "Vomiting? Theek hai, abhi ke liye yehi karo."
        ),
        "start_time_seconds": 19.9,
        "end_time_seconds": 25.1,
    },
]


class SarvamBatchASRService:
    """Wraps the Sarvam Batch Speech-to-Text API for diarized transcription.

    Usage:
        service = SarvamBatchASRService()
        result = await service.transcribe_with_diarization(
            audio_path="/path/to/audio.mp3",
            language_code="unknown",   # auto-detect
            num_speakers=2,            # optional hint
        )
        # result["diarized_segments"] → list of speaker-labelled segments
        # result["transcript"]        → plain concatenated text
    """

    async def transcribe_with_diarization(
        self,
        audio_path: str,
        language_code: str = "unknown",
        num_speakers: Optional[int] = 2,
        professional_speaker_id: Optional[str] = None,
    ) -> dict:
        """Transcribe audio and return speaker-labelled segments.

        Args:
            audio_path:             Path to audio file on disk.
            language_code:          BCP-47 code or "unknown" for auto-detection.
            num_speakers:           Hint for expected number of speakers.
                                    Defaults to 2 (professional + client).
            professional_speaker_id: Override which Sarvam speaker_id maps to
                                    the professional role. Defaults to whichever
                                    speaker appears first in the transcript.

        Returns:
            {
                "transcript":        str,        # plain concatenated text
                "diarized_segments": list[dict], # speaker-labelled segments
                "language_code":     str,
                "is_stub":           bool,
            }
        """
        if not settings.sarvam_api_key:
            logger.warning("SARVAM_API_KEY not set — returning stub diarized transcript")
            return self._stub_response(language_code)

        path = Path(audio_path)
        filename = path.name

        try:
            # Steps 1-4 share a single client (short HTTP calls)
            async with httpx.AsyncClient(timeout=30.0) as client:
                job_id = await self._initiate_job(client, language_code, num_speakers)
                logger.info("Batch job initiated: %s", job_id)

                upload_url = await self._get_upload_url(client, job_id, filename)
                logger.info("Presigned URL obtained for %s", filename)

            # Step 3 uses a separate client with a longer timeout for the PUT
            await self._upload_audio(upload_url, path)
            logger.info("Audio uploaded successfully")

            async with httpx.AsyncClient(timeout=30.0) as client:
                await self._start_job(client, job_id)
                logger.info("Job started: %s", job_id)

            # Step 5: long-poll until complete
            result_json = await self._poll_and_download(job_id)
            logger.info("Job completed and results downloaded: %s", job_id)

            segments = self._parse_segments(result_json, professional_speaker_id)
            plain_transcript = " ".join(s["transcript"] for s in segments)
            detected_lang = result_json.get("language_code", language_code)

            return {
                "transcript": plain_transcript,
                "diarized_segments": segments,
                "language_code": detected_lang,
                "is_stub": False,
            }

        except Exception as exc:
            logger.error("Batch ASR pipeline failed: %s — falling back to stub", exc)
            return self._stub_response(language_code)

    # ------------------------------------------------------------------
    # Step 1 — Initiate job
    # ------------------------------------------------------------------

    async def _initiate_job(
        self,
        client: httpx.AsyncClient,
        language_code: str,
        num_speakers: Optional[int],
    ) -> str:
        """POST /speech-to-text/job/v1 — create a new batch job."""
        job_params: dict = {
            "language_code": language_code,
            "model": "saaras:v3",        # v3 supports all 23 Indian languages
            "with_timestamps": True,
            "with_diarization": True,
        }
        if num_speakers is not None:
            job_params["num_speakers"] = num_speakers

        response = await client.post(
            f"{_BASE_URL}/speech-to-text/job/v1",
            headers={"api-subscription-key": settings.sarvam_api_key},
            json={"job_parameters": job_params},
        )
        response.raise_for_status()
        return response.json()["job_id"]

    # ------------------------------------------------------------------
    # Step 2 — Get presigned upload URL
    # ------------------------------------------------------------------

    async def _get_upload_url(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        filename: str,
    ) -> str:
        """POST /speech-to-text/job/v1/upload-files — get presigned PUT URL."""
        response = await client.post(
            f"{_BASE_URL}/speech-to-text/job/v1/upload-files",
            headers={"api-subscription-key": settings.sarvam_api_key},
            json={"job_id": job_id, "files": [filename]},
        )
        response.raise_for_status()
        data = response.json()
        url = data.get("upload_urls", {}).get(filename, {}).get("file_url")
        if not url:
            raise ValueError(f"No presigned URL returned for '{filename}': {data}")
        return url

    # ------------------------------------------------------------------
    # Step 3 — Upload audio to presigned URL
    # ------------------------------------------------------------------

    async def _upload_audio(self, presigned_url: str, path: Path) -> None:
        """PUT raw audio bytes to the cloud storage presigned URL."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            audio_bytes = path.read_bytes()
            response = await client.put(
                presigned_url,
                content=audio_bytes,
                headers={
                    "Content-Type": "application/octet-stream",
                    "x-ms-blob-type": "BlockBlob",
                },
            )
            response.raise_for_status()

    # ------------------------------------------------------------------
    # Step 4 — Start job
    # ------------------------------------------------------------------

    async def _start_job(self, client: httpx.AsyncClient, job_id: str) -> None:
        """POST /speech-to-text/job/v1/{job_id}/start."""
        response = await client.post(
            f"{_BASE_URL}/speech-to-text/job/v1/{job_id}/start",
            headers={"api-subscription-key": settings.sarvam_api_key},
        )
        response.raise_for_status()

    # ------------------------------------------------------------------
    # Step 5 — Poll status and download results
    # ------------------------------------------------------------------

    async def _poll_and_download(self, job_id: str) -> dict:
        """Poll job status until Completed, then fetch and return result JSON."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(1, _MAX_POLL_ATTEMPTS + 1):
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)

                status_resp = await client.get(
                    f"{_BASE_URL}/speech-to-text/job/v1/{job_id}/status",
                    headers={"api-subscription-key": settings.sarvam_api_key},
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
                job_state = status_data.get("job_state", "")

                logger.info(
                    "Batch job %s — state: %s (poll %d/%d)",
                    job_id, job_state, attempt, _MAX_POLL_ATTEMPTS,
                )

                if job_state == "Completed":
                    return await self._download_result(client, job_id, status_data)

                if job_state == "Failed":
                    raise RuntimeError(
                        f"Sarvam batch job {job_id} failed: {status_data}"
                    )
                # else: Running / Accepted — keep polling

        raise TimeoutError(
            f"Batch job {job_id} did not complete within "
            f"{_MAX_POLL_ATTEMPTS * _POLL_INTERVAL_SECONDS}s"
        )

    async def _download_result(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        status_data: dict,
    ) -> dict:
        """Download the result JSON from the completed job."""
        # Collect output filenames from job_details
        output_files = [
            output["file_name"]
            for detail in status_data.get("job_details", [])
            for output in detail.get("outputs", [])
            if output.get("file_name")
        ]
        if not output_files:
            raise ValueError(f"Job {job_id} completed but returned no output files")

        # Request download URLs
        dl_resp = await client.post(
            f"{_BASE_URL}/speech-to-text/job/v1/download-files",
            headers={"api-subscription-key": settings.sarvam_api_key},
            json={"job_id": job_id, "files": output_files},
        )
        dl_resp.raise_for_status()
        dl_data = dl_resp.json()

        # Fetch the first result file
        first_file = output_files[0]
        download_url = (
            dl_data.get("download_urls", {})
            .get(first_file, {})
            .get("file_url")
        )
        if not download_url:
            raise ValueError(f"No download URL returned for '{first_file}'")

        result_resp = await client.get(download_url, timeout=30.0)
        result_resp.raise_for_status()
        return result_resp.json()

    # ------------------------------------------------------------------
    # Parse diarization output → Lipi speaker segments
    # ------------------------------------------------------------------

    def _parse_segments(
        self,
        result_json: dict,
        professional_speaker_id: Optional[str],
    ) -> list[dict]:
        """Convert Sarvam diarization entries to Lipi's speaker-segment format.

        Sarvam returns generic speaker IDs (speaker_1, speaker_2).
        We map the first-appearing speaker to "Professional" and all
        others to "Client", unless overridden by professional_speaker_id.

        Output segment schema:
            {
                "speaker_id":          "speaker_1",
                "role":                "Professional" | "Client",
                "transcript":          "text of this segment",
                "start_time_seconds":  0.0,
                "end_time_seconds":    4.2,
            }
        """
        entries = (
            result_json
            .get("diarized_transcript", {})
            .get("entries", [])
        )

        if not entries:
            # No diarization data — wrap plain transcript as single segment
            plain = result_json.get("transcript", "")
            return [{
                "speaker_id": "speaker_1",
                "role": "Professional",
                "transcript": plain,
                "start_time_seconds": 0.0,
                "end_time_seconds": 0.0,
            }]

        # Determine professional speaker: explicit override or first speaker in entries
        if professional_speaker_id is None:
            professional_speaker_id = entries[0].get("speaker_id", "speaker_1")

        return [
            {
                "speaker_id": entry.get("speaker_id", "speaker_1"),
                "role": (
                    "Professional"
                    if entry.get("speaker_id") == professional_speaker_id
                    else "Client"
                ),
                "transcript": entry.get("transcript", ""),
                "start_time_seconds": entry.get("start_time_seconds", 0.0),
                "end_time_seconds": entry.get("end_time_seconds", 0.0),
            }
            for entry in entries
        ]

    # ------------------------------------------------------------------
    # Stub fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _stub_response(language_code: str) -> dict:
        plain = " ".join(s["transcript"] for s in _STUB_SEGMENTS)
        return {
            "transcript": plain,
            "diarized_segments": _STUB_SEGMENTS,
            "language_code": language_code,
            "is_stub": True,
        }

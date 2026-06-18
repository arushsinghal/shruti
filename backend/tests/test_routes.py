"""Route-level integration tests for consent enforcement and audio retention.

These tests hit the FastAPI app directly via httpx.AsyncClient with an
in-memory SQLite database so they do not touch production data.
"""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

import app.storage.db as db_module
from app.main import app
from app.schemas.consultation import StatusEnum
from app.storage.repository import SessionRepository


from app.api.routes_auth import get_current_user


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    """Point every route test at a fresh, temporary SQLite file."""
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_routes.db")
    await db_module.init_db()
    app.dependency_overrides[get_current_user] = lambda: {"id": "test_user_id", "username": "test_user"}
    yield
    db_module._DB_PATH = original
    app.dependency_overrides.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ── Helper ────────────────────────────────────────────────────────────────────

async def _create_session(ac: AsyncClient, consent: bool = False) -> str:
    r = await ac.post("/api/sessions", json={"cloud_ai_consent": consent, "mode": "health"})
    assert r.status_code == 201
    return r.json()["id"]


# ── Consent gate — audio upload ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_audio_upload_blocked_without_consent(ac):
    session_id = await _create_session(ac, consent=False)
    r = await ac.post(
        f"/api/sessions/{session_id}/audio",
        files={"file": ("clip.wav", b"RIFF", "audio/wav")},
    )
    assert r.status_code == 403
    assert "consent" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_audio_upload_allowed_after_consent_patch(ac):
    session_id = await _create_session(ac, consent=False)

    # Grant consent via PATCH endpoint
    r = await ac.patch(f"/api/sessions/{session_id}/consent")
    assert r.status_code == 200
    assert r.json()["cloud_ai_consent"] is True

    # Upload should now pass the consent gate (may fail later for other reasons,
    # but must NOT return 403)
    r = await ac.post(
        f"/api/sessions/{session_id}/audio",
        files={"file": ("clip.wav", b"RIFF", "audio/wav")},
    )
    assert r.status_code != 403, "consent gate must not block after consent is granted"


@pytest.mark.anyio
async def test_audio_upload_allowed_when_session_created_with_consent(ac):
    session_id = await _create_session(ac, consent=True)
    r = await ac.post(
        f"/api/sessions/{session_id}/audio",
        files={"file": ("clip.wav", b"RIFF", "audio/wav")},
    )
    assert r.status_code != 403


# ── Consent gate — clinical processing ───────────────────────────────────────

@pytest.mark.anyio
async def test_process_clinical_blocked_without_consent(ac):
    session_id = await _create_session(ac, consent=False)
    r = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert r.status_code == 403
    assert "consent" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_process_clinical_allowed_after_consent_patch(ac):
    session_id = await _create_session(ac, consent=False)

    # Grant consent
    await ac.patch(f"/api/sessions/{session_id}/consent")

    # Processing should now pass the consent gate (will fail with 400 because
    # there is no transcript yet — but must NOT return 403)
    r = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert r.status_code != 403, "consent gate must not block after consent is granted"
    assert r.status_code == 400  # "No transcript available" is the expected next error


# ── PATCH consent endpoint ────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_consent_patch_404_for_unknown_session(ac):
    r = await ac.patch("/api/sessions/nonexistent-id/consent")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_consent_patch_is_idempotent(ac):
    """Granting consent twice should succeed both times."""
    session_id = await _create_session(ac, consent=False)
    r1 = await ac.patch(f"/api/sessions/{session_id}/consent")
    r2 = await ac.patch(f"/api/sessions/{session_id}/consent")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["cloud_ai_consent"] is True


# ── Audio retention — deleted after SOAP generation ───────────────────────────

async def _session_with_transcript(ac: AsyncClient, tmp_path: Path) -> tuple[str, Path]:
    """Create a consented session with a transcript and a real audio file on disk.
    Returns (session_id, audio_path)."""
    session_id = await _create_session(ac, consent=True)

    # Create a fake audio file so deletion can be verified
    audio_dir = tmp_path / "uploads" / session_id
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "recording.wav"
    audio_file.write_bytes(b"RIFF fake audio content")

    # Wire the transcript and audio path directly via the repository
    repo = SessionRepository()
    session = await repo.get_session(session_id, "test_user_id")
    session.transcript = "Patient has fever and cough. BP 130/80."
    session.audio_file_path = str(audio_file)
    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    return session_id, audio_file


@pytest.mark.anyio
async def test_audio_file_exists_before_processing(tmp_path, ac):
    _, audio_file = await _session_with_transcript(ac, tmp_path)
    assert audio_file.exists()


@pytest.mark.anyio
async def test_audio_file_deleted_after_process_clinical(tmp_path, ac):
    session_id, audio_file = await _session_with_transcript(ac, tmp_path)

    r = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert r.status_code == 200

    assert not audio_file.exists(), "raw audio must be deleted after SOAP generation"


@pytest.mark.anyio
async def test_audio_file_path_cleared_after_deletion(tmp_path, ac):
    session_id, _ = await _session_with_transcript(ac, tmp_path)

    await ac.post(f"/api/sessions/{session_id}/process-clinical")

    repo = SessionRepository()
    updated = await repo.get_session(session_id, "test_user_id")
    assert updated.audio_file_path is None, "audio_file_path must be cleared after deletion"


@pytest.mark.anyio
async def test_missing_audio_file_does_not_crash_processing(ac):
    """Processing must succeed even when audio_file_path points to a nonexistent file."""
    session_id = await _create_session(ac, consent=True)

    repo = SessionRepository()
    session = await repo.get_session(session_id, "test_user_id")
    session.transcript = "Patient has fever."
    session.audio_file_path = "/tmp/lipi_nonexistent_test_audio.wav"
    session.status = StatusEnum.transcribed
    await repo.update_session(session)

    r = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_soap_note_available_after_audio_deletion(tmp_path, ac):
    """SOAP note remains in the response even after audio is deleted."""
    session_id, _ = await _session_with_transcript(ac, tmp_path)

    r = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert r.status_code == 200

    body = r.json()
    assert body["soap"] is not None, "SOAP note must survive audio deletion"
    assert body["facts"] is not None


# ── Session CRUD ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_session_returns_201(ac):
    r = await ac.post("/api/sessions", json={"patient_name": "Ravi", "doctor_name": "Dr. Mehta", "mode": "health"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"]
    assert body["patient_name"] == "Ravi"
    assert body["doctor_name"] == "Dr. Mehta"
    assert body["cloud_ai_consent"] is False
    assert body["status"] == "created"


@pytest.mark.anyio
async def test_create_session_defaults(ac):
    r = await ac.post("/api/sessions", json={})
    assert r.status_code == 201
    body = r.json()
    assert body["patient_name"] is None
    assert body["mode"] == "health"
    assert body["cloud_ai_consent"] is False


@pytest.mark.anyio
async def test_get_session_returns_session(ac):
    session_id = await _create_session(ac)
    r = await ac.get(f"/api/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["id"] == session_id


@pytest.mark.anyio
async def test_get_session_404_for_unknown(ac):
    r = await ac.get("/api/sessions/does-not-exist")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_list_sessions_returns_created_sessions(ac):
    id1 = await _create_session(ac)
    id2 = await _create_session(ac)
    r = await ac.get("/api/sessions")
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()}
    assert id1 in ids
    assert id2 in ids


@pytest.mark.anyio
async def test_list_sessions_pagination_limit(ac):
    for _ in range(5):
        await _create_session(ac)
    r = await ac.get("/api/sessions?limit=3&offset=0")
    assert r.status_code == 200
    assert len(r.json()) <= 3


@pytest.mark.anyio
async def test_list_sessions_pagination_offset(ac):
    """Offset beyond total returns empty list, not an error."""
    r = await ac.get("/api/sessions?limit=10&offset=9999")
    assert r.status_code == 200
    assert r.json() == []


# ── File size limit ───────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_audio_upload_rejects_oversized_file(ac):
    session_id = await _create_session(ac, consent=True)
    oversized = b"X" * (26 * 1024 * 1024)  # 26 MB > 25 MB limit
    r = await ac.post(
        f"/api/sessions/{session_id}/audio",
        files={"file": ("big.wav", oversized, "audio/wav")},
    )
    assert r.status_code == 413


@pytest.mark.anyio
async def test_audio_upload_accepts_small_file(ac):
    session_id = await _create_session(ac, consent=True)
    small = b"RIFF" + b"\x00" * 100
    r = await ac.post(
        f"/api/sessions/{session_id}/audio",
        files={"file": ("small.wav", small, "audio/wav")},
    )
    # Should pass size check; may fail extension-dependent or other checks but not 413
    assert r.status_code != 413

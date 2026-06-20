import pytest
import json
import hashlib
from httpx import AsyncClient, ASGITransport
from app.storage.db import db_connect
import app.storage.db as db_module
from app.main import app
from app.api.routes_auth import get_current_user


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    """Point every route test at a fresh, temporary SQLite file."""
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_routes_p2a.db")
    await db_module.init_db()
    app.dependency_overrides[get_current_user] = lambda: {"id": "test_user_id", "username": "test_user"}
    yield
    db_module._DB_PATH = original
    app.dependency_overrides.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_consent_logs_creation(ac: AsyncClient):
    # 1. Create a session
    res = await ac.post("/api/sessions", json={"patient_name": "Rohan Verma", "mode": "health"})
    assert res.status_code == 201
    session_id = res.json()["id"]

    # 2. Grant consent with specific mode/version
    payload = {"consent_mode": "written", "consent_text_version": "v2"}
    patch_res = await ac.patch(
        f"/api/sessions/{session_id}/consent",
        json=payload,
        headers={"user-agent": "test-agent"}
    )
    assert patch_res.status_code == 200
    session_data = patch_res.json()
    assert session_data["cloud_ai_consent"] is True
    assert session_data["consent_log"] is not None
    assert session_data["consent_log"]["consent_mode"] == "written"
    assert session_data["consent_log"]["consent_text_version"] == "v2"
    assert len(session_data["consent_log"]["consent_hash"]) == 64

    # 3. Check DB entry directly
    async with db_connect() as db:
        async with db.execute("SELECT session_id, consent_mode, consent_hash, user_agent FROM consent_logs WHERE session_id = ?", (session_id,)) as cur:
            row = await cur.fetchone()
            assert row is not None
            assert row[0] == session_id
            assert row[1] == "written"
            assert row[3] == "test-agent"


@pytest.mark.anyio
async def test_soap_feedback_submission(ac: AsyncClient):
    # 1. Create a session and grant consent
    res = await ac.post("/api/sessions", json={"patient_name": "Sita Sen", "mode": "health"})
    session_id = res.json()["id"]
    # Grant consent
    await ac.patch(f"/api/sessions/{session_id}/consent")

    # 2. Post SOAP feedback
    original_soap = {"subjective": {"chief_complaint": "Patient Sita Sen has fever"}}
    final_soap = {"subjective": {"chief_complaint": "Patient Sita Sen has high fever and body ache"}}
    
    feedback_payload = {
        "status": "edit",
        "original_soap": original_soap,
        "final_soap": final_soap,
        "categories": ["missing_symptom", "other"]
    }
    
    feedback_res = await ac.post(f"/api/sessions/{session_id}/feedback", json=feedback_payload)
    assert feedback_res.status_code == 200
    res_data = feedback_res.json()
    assert res_data["success"] is True
    assert res_data["status"] == "edit"
    assert "missing_symptom" in res_data["categories"]
    
    # 3. Check DB for PHI scrubbing & delta
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT original_soap, final_soap, delta,
                   phi_scrubbed_original_soap, phi_scrubbed_final_soap, phi_scrubbed_delta,
                   categories
            FROM soap_feedback WHERE session_id = ?
            """,
            (session_id,)
        ) as cur:
            row = await cur.fetchone()
            assert row is not None
            # Check original is stored
            orig_stored = json.loads(row[0])
            assert "Sita Sen" in orig_stored["subjective"]["chief_complaint"]
            
            # Check PHI scrubbed version has redacted name
            scrubbed_orig = json.loads(row[3])
            assert "[REDACTED_NAME]" in scrubbed_orig["subjective"]["chief_complaint"]
            assert "Sita Sen" not in scrubbed_orig["subjective"]["chief_complaint"]
            
            # Check delta contains differences
            delta_str = row[2]
            assert "chief_complaint" in delta_str
            
            # Check categories JSON list
            cats = json.loads(row[6])
            assert "missing_symptom" in cats


@pytest.mark.anyio
async def test_expanded_analytics(ac: AsyncClient):
    # 1. Fetch analytics (should not crash even with entries)
    res = await ac.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "overview" in data
    assert "accepted_notes" in data["overview"]
    assert "edited_notes" in data["overview"]
    assert "rejected_notes" in data["overview"]
    assert "estimated_hours_saved" in data["overview"]
    assert "consent_logs_recorded" in data["overview"]
    assert "top_correction_categories" in data

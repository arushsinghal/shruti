import pytest
from httpx import ASGITransport, AsyncClient

import app.storage.db as db_module
from app.api.routes_auth import get_current_user
from app.main import app
from app.schemas.consultation import StatusEnum
from app.services.whatsapp_service import WhatsAppService
from app.storage.repository import SessionRepository


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_doctor_product_metrics.db")
    await db_module.init_db()
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test_user_id",
        "username": "test_user",
        "full_name": "Dr. Test",
    }
    yield
    db_module._DB_PATH = original
    app.dependency_overrides.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def mock_follow_up(monkeypatch):
    async def fake_send_follow_up(phone_number: str, doctor_name: str, follow_up_text: str):
        return {
            "success": True,
            "provider": "mock-test",
            "to": phone_number,
            "doctor_name": doctor_name,
            "message": follow_up_text,
        }

    monkeypatch.setattr(WhatsAppService, "send_follow_up_reminder", fake_send_follow_up)


@pytest.mark.anyio
async def test_health_session_persists_specialty(ac):
    response = await ac.post(
        "/api/sessions",
        json={"mode": "health", "specialty": "dermatology", "patient_name": "Test Patient"},
    )

    assert response.status_code == 201
    assert response.json()["specialty"] == "dermatology"


@pytest.mark.anyio
async def test_usage_event_and_billing_appear_in_analytics(ac):
    created = await ac.post(
        "/api/sessions",
        json={"mode": "health", "specialty": "pediatrics", "patient_name": "Test Patient"},
    )
    session_id = created.json()["id"]

    await ac.post(
        f"/api/sessions/{session_id}/usage-event",
        json={"event_type": "note_printed", "metadata": {"surface": "test"}},
    )
    billing = await ac.post(
        "/api/billing-records",
        json={"clinic_name": "Pilot Clinic", "plan_name": "Pilot", "amount_inr": 5000, "status": "paid"},
    )
    assert billing.status_code == 201

    analytics = await ac.get("/api/analytics/dashboard")

    assert analytics.status_code == 200
    body = analytics.json()
    assert body["overview"]["notes_printed"] == 1
    assert body["overview"]["revenue_total_inr"] == 5000
    assert any(item["name"] == "pediatrics" for item in body["specialty_mix"])


@pytest.mark.anyio
async def test_follow_up_reminder_requires_consent(ac):
    created = await ac.post("/api/sessions", json={"mode": "health", "patient_name": "Test Patient"})
    session_id = created.json()["id"]

    response = await ac.post(
        f"/api/sessions/{session_id}/send-follow-up",
        json={"phone_number": "+919876543210", "consent": False, "follow_up_text": "Review in 3 days"},
    )

    assert response.status_code == 400
    assert "consent" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_follow_up_reminder_updates_analytics(ac):
    created = await ac.post("/api/sessions", json={"mode": "health", "patient_name": "Test Patient"})
    session_id = created.json()["id"]
    repo = SessionRepository()
    session = await repo.get_session(session_id, "test_user_id")
    session.status = StatusEnum.complete
    session.soap_note = {"P": "Follow-up: Review in 3 days."}
    await repo.update_session(session)

    response = await ac.post(
        f"/api/sessions/{session_id}/send-follow-up",
        json={"phone_number": "+919876543210", "consent": True, "follow_up_text": "Review in 3 days"},
    )
    assert response.status_code == 200

    analytics = await ac.get("/api/analytics/dashboard")
    assert analytics.json()["overview"]["follow_up_reminders_sent"] == 1

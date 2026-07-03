from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

import app.storage.db as db_module
from app.api.routes_auth import get_current_user
from app.main import app
from app.schemas.consultation import StatusEnum
from app.services.whatsapp_service import WhatsAppService
from app.storage.repository import SessionRepository
from app.utils.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_whatsapp_sharing.db")
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
def mock_whatsapp(monkeypatch):
    async def fake_send_message(phone_number: str, doctor_name: str, secure_link: str):
        return {
            "success": True,
            "provider": "mock-test",
            "to": phone_number,
            "doctor_name": doctor_name,
            "secure_link": secure_link,
        }

    monkeypatch.setattr(WhatsAppService, "send_message", fake_send_message)


async def _create_shareable_session(ac: AsyncClient, patient_name: str = "Sita Verma") -> str:
    response = await ac.post(
        "/api/sessions",
        json={
            "patient_name": patient_name,
            "doctor_name": "Mehta",
            "cloud_ai_consent": True,
            "mode": "health",
        },
    )
    assert response.status_code == 201
    session_id = response.json()["id"]

    repo = SessionRepository()
    session = await repo.get_session(session_id, "test_user_id")
    assert session is not None
    session.status = StatusEnum.complete
    session.soap_note = {"S": "Fever", "O": "Temp 101 F", "A": "Viral fever", "P": "Paracetamol"}
    session.memory_state = {
        "medications": {
            "paracetamol": {
                "dosage": "500 mg",
                "frequency": "twice daily",
                "duration": "3 days",
            }
        },
        "diagnoses": ["Viral fever"],
        "vitals": ["Temp 101 F"],
        "allergies": [],
        "follow_up": ["Review if fever persists"],
    }
    await repo.update_session(session)
    return session_id


async def _share(ac: AsyncClient, session_id: str, consent: bool = True):
    return await ac.post(
        f"/api/sessions/{session_id}/share-whatsapp",
        json={"phone_number": "+919876543210", "consent": consent},
    )


@pytest.mark.anyio
async def test_share_whatsapp_requires_explicit_consent(ac):
    session_id = await _create_shareable_session(ac)

    response = await _share(ac, session_id, consent=False)

    assert response.status_code == 400
    assert "consent" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_share_token_cannot_be_used_as_download_token(ac):
    session_id = await _create_shareable_session(ac)
    share_response = await _share(ac, session_id)
    assert share_response.status_code == 200
    share_token = share_response.json()["token"]

    download_response = await ac.get(f"/api/public/download/{share_token}")

    assert download_response.status_code == 401


@pytest.mark.anyio
async def test_share_whatsapp_reports_provider_failure(ac, monkeypatch):
    async def failing_send_message(phone_number: str, doctor_name: str, secure_link: str):
        return {
            "success": False,
            "provider": "twilio",
            "error": "twilio_error",
            "detail": "template rejected",
        }

    monkeypatch.setattr(WhatsAppService, "send_message", failing_send_message)
    session_id = await _create_shareable_session(ac)

    response = await _share(ac, session_id)

    assert response.status_code == 502
    assert "template rejected" in response.json()["detail"]


@pytest.mark.anyio
async def test_tampered_share_token_is_rejected(ac):
    session_id = await _create_shareable_session(ac)
    share_response = await _share(ac, session_id)
    assert share_response.status_code == 200
    token = share_response.json()["token"]
    tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")

    response = await ac.post(
        f"/api/public/verify-access/{tampered_token}",
        json={"initials": "S.V."},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_expired_share_token_is_rejected(ac):
    session_id = await _create_shareable_session(ac)
    expired_token = jwt.encode(
        {
            "sub": session_id,
            "session_id": session_id,
            "scope": "patient_prescription_share",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await ac.post(
        f"/api/public/verify-access/{expired_token}",
        json={"initials": "S.V."},
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_verified_patient_can_download_prescription(ac):
    session_id = await _create_shareable_session(ac)
    share_response = await _share(ac, session_id)
    assert share_response.status_code == 200
    share_token = share_response.json()["token"]

    verify_response = await ac.post(
        f"/api/public/verify-access/{share_token}",
        json={"initials": "S.V."},
    )
    assert verify_response.status_code == 200
    download_token = verify_response.json()["download_token"]

    download_response = await ac.get(f"/api/public/download/{download_token}")

    assert download_response.status_code == 200
    assert "Sita Verma" in download_response.text
    assert "Paracetamol" in download_response.text


@pytest.mark.anyio
async def test_public_prescription_html_escapes_dynamic_fields(ac):
    patient_name = "<script>alert(1)</script>"
    session_id = await _create_shareable_session(ac, patient_name=patient_name)
    share_response = await _share(ac, session_id)
    assert share_response.status_code == 200

    verify_response = await ac.post(
        f"/api/public/verify-access/{share_response.json()['token']}",
        json={"patient_name": patient_name},
    )
    assert verify_response.status_code == 200

    download_response = await ac.get(f"/api/public/download/{verify_response.json()['download_token']}")

    assert download_response.status_code == 200
    assert "<script>alert(1)</script>" not in download_response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in download_response.text

import pytest

import app.storage.db as db_module
from app.services.cds_engine import CDSEngineService
from app.services.memory_service import get_patient_memory, upsert_patient_memory
from app.services.sarvam_asr import SarvamASRService
from app.utils.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def isolated_db(tmp_path):
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_security_hardening.db")
    await db_module.init_db()
    yield
    db_module._DB_PATH = original


@pytest.mark.anyio
async def test_patient_memory_is_scoped_by_doctor(isolated_db):
    await upsert_patient_memory(
        "Sita Verma",
        "session_a",
        "doctor_a",
        {"allergies": ["penicillin"]},
    )
    await upsert_patient_memory(
        "Sita Verma",
        "session_b",
        "doctor_b",
        {"allergies": ["sulfa"]},
    )

    doctor_a_memory = await get_patient_memory("Sita Verma", "doctor_a")
    doctor_b_memory = await get_patient_memory("Sita Verma", "doctor_b")

    assert [item["value"] for item in doctor_a_memory["allergies"]] == ["penicillin"]
    assert [item["value"] for item in doctor_b_memory["allergies"]] == ["sulfa"]


@pytest.mark.anyio
async def test_sarvam_missing_key_fails_closed_without_stub(monkeypatch, tmp_path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"not-real-audio")
    monkeypatch.setattr(settings, "sarvam_api_key", "")
    monkeypatch.setattr(settings, "allow_stub_asr", False)

    with pytest.raises(RuntimeError, match="SARVAM_API_KEY not set"):
        await SarvamASRService().transcribe(str(audio_path))


@pytest.mark.anyio
async def test_sarvam_missing_key_uses_stub_only_when_enabled(monkeypatch, tmp_path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"not-real-audio")
    monkeypatch.setattr(settings, "sarvam_api_key", "")
    monkeypatch.setattr(settings, "allow_stub_asr", True)

    result = await SarvamASRService().transcribe(str(audio_path))

    assert result["is_stub"] is True


def test_cds_flags_common_drug_drug_interaction():
    suggestions = CDSEngineService().generate_cds({
        "medications": {
            "ibuprofen": {"dosage": "400 mg", "frequency": "BD"},
            "warfarin": {"dosage": "5 mg", "frequency": "OD"},
        },
        "allergies": [],
        "symptoms": [],
        "vitals": [],
        "investigations": [],
        "diagnoses": [],
    })

    assert any(item.get("alert_type") == "drug_drug_interaction" for item in suggestions)
    assert suggestions[0]["safety_label"] == "doctor_review_required"

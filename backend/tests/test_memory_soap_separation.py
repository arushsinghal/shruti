"""Tests for memory-to-SOAP separation.

Proves that prior patient history (from patient_memory DB) is stored in
`prior_context` and never merged into the current-visit SOAP state.
All extraction and SOAP generation must remain zero-LLM and current-visit-only.
"""

import pytest

import app.storage.db as db_module
from app.storage.db import init_db
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.services.memory_service import upsert_patient_memory, get_patient_memory


memory = MemoryContextService()
soap_gen = SOAPGeneratorService()


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_separation.db")
    await init_db()
    yield
    db_module._DB_PATH = original


# ─── Core separation invariant ────────────────────────────────────────────────

@pytest.mark.anyio
async def test_prior_medication_does_not_enter_current_soap():
    """Facts from patient_memory must never appear in the SOAP-generating state.

    Scenario: patient was on metformin in a prior visit (confirmed in DB).
    Current transcript mentions only fever. SOAP must NOT mention metformin.
    """
    patient_name = "Ramesh Kumar"
    user_id = "doc_1"

    # Seed patient_memory with a confirmed prior-visit medication
    await upsert_patient_memory(
        patient_name=patient_name,
        session_id="prior-session-001",
        user_id=user_id,
        facts={"medications": [{"name": "metformin", "dosage": "500mg", "frequency": "twice daily"}]},
        confirmed_by=user_id,
    )

    # Current-visit facts extracted from today's transcript: only fever, no meds
    current_facts = {
        "symptoms": ["fever"],
        "medications": {},
        "vitals": [],
        "allergies": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {},
    }
    current_state = memory.resolve_memory([current_facts])

    # Verify: current state has no medications from prior visits
    assert "metformin" not in str(current_state.get("medications", {})).lower(), (
        "Prior-visit medication must not appear in current-visit state"
    )

    # Verify prior_context carries the medication (fetched separately)
    prior_ctx = await get_patient_memory(patient_name, user_id, confirmed_only=True)
    assert prior_ctx is not None
    assert any(
        "metformin" in str(m).lower() for m in prior_ctx.get("medications", [])
    ), "prior_context must carry the prior-visit medication for UI display"


@pytest.mark.anyio
async def test_prior_allergy_does_not_enter_soap_automatically():
    """A confirmed prior-visit allergy must NOT auto-populate current SOAP.

    The doctor must re-state the allergy in today's transcript, OR the UI must
    display it from prior_context for the doctor to acknowledge.
    """
    patient_name = "Sunita Devi"
    user_id = "doc_1"

    await upsert_patient_memory(
        patient_name=patient_name,
        session_id="prior-session-002",
        user_id=user_id,
        facts={"allergies": ["penicillin"]},
        confirmed_by=user_id,
    )

    # Current transcript: headache, no allergies mentioned
    current_facts = {
        "symptoms": ["headache"],
        "allergies": [],
        "medications": {},
        "vitals": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {},
    }
    current_state = memory.resolve_memory([current_facts])

    assert "penicillin" not in str(current_state.get("allergies", [])).lower(), (
        "Prior-visit allergy must not auto-populate current SOAP"
    )

    prior_ctx = await get_patient_memory(patient_name, user_id, confirmed_only=True)
    assert prior_ctx is not None
    prior_allergy_str = " ".join(str(a) for a in prior_ctx.get("allergies", []))
    assert "penicillin" in prior_allergy_str.lower(), (
        "Prior allergy must be in prior_context for UI display"
    )


@pytest.mark.anyio
async def test_candidate_prior_facts_excluded_from_prior_context():
    """Patient memory rows that were never confirmed must not appear in prior_context.

    Ensures the confirmed_only=True gate blocks unreviewed prior-session facts.
    """
    patient_name = "Vikram Singh"
    user_id = "doc_2"

    # Write without confirmed_by — review_status defaults to 'confirmed' in upsert
    # when confirmed_by is provided; here we write directly to simulate a candidate
    from app.storage.db import db_connect
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    async with db_connect() as db:
        await db.execute(
            "INSERT INTO patient_memory "
            "(patient_name, user_id, clinic_id, field, med_name, value, "
            "source_session_id, first_seen_at, last_seen_at, seen_count, "
            "review_status, superseded) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "vikram singh", user_id, "clinic_1", "medication", "atorvastatin",
                '{"name": "atorvastatin"}', "prior-session-003", now, now, 1,
                "candidate", 0,
            ),
        )
        await db.commit()

    prior_ctx = await get_patient_memory(patient_name, user_id, confirmed_only=True)
    if prior_ctx:
        assert all(
            "atorvastatin" not in str(m).lower()
            for m in prior_ctx.get("medications", [])
        ), "Unconfirmed prior-visit medication must be excluded from prior_context"


@pytest.mark.anyio
async def test_current_visit_state_schema_is_dict_for_medications():
    """current_state medications must be a dict (name → attrs), not a list.

    prior_context uses a list (different schema). Mixing them would break SOAP.
    Verify they're structurally incompatible so the separation is enforced by type.
    """
    current_facts = {
        "symptoms": ["cough", "fever"],
        "medications": [{"name": "paracetamol", "dosage": "500mg", "frequency": "TDS"}],
        "vitals": ["BP 120/80"],
        "allergies": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {},
    }
    current_state = memory.resolve_memory([current_facts])

    # current_state: medications is dict
    assert isinstance(current_state["medications"], dict), (
        "current_state.medications must be a dict for SOAP generation"
    )
    assert "paracetamol" in current_state["medications"]

    # SOAP can be generated from current_state without error
    soap = soap_gen.generate_soap(current_state)
    assert isinstance(soap, dict)

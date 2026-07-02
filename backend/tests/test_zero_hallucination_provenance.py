import pytest
from httpx import ASGITransport, AsyncClient

import app.storage.db as db_module
from app.api.routes_auth import get_current_user
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_zero_hallucination.db")
    await db_module.init_db()
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "doctor_1",
        "username": "doctor_1",
        "full_name": "Dr. Provenance",
    }
    yield
    db_module._DB_PATH = original
    app.dependency_overrides.clear()


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def _process_transcript(ac: AsyncClient, transcript: str) -> dict:
    created = await ac.post("/api/sessions", json={"mode": "health", "cloud_ai_consent": True})
    assert created.status_code == 201
    session_id = created.json()["id"]
    submitted = await ac.post(f"/api/sessions/{session_id}/transcript", json={"transcript": transcript})
    assert submitted.status_code == 200
    processed = await ac.post(f"/api/sessions/{session_id}/process-clinical")
    assert processed.status_code == 200, processed.text
    body = processed.json()
    body["session_id"] = session_id
    return body


@pytest.mark.anyio
async def test_process_clinical_returns_candidates_and_gates_soap(ac):
    """The real deterministic extractor feeds the provenance gate: every fact is a
    candidate with certainty preserved. Lipi uses an opt-out review model — the
    draft SOAP is populated immediately from non-rejected candidates so the doctor
    reviews the whole note (removing anything wrong) rather than confirming each
    fact one at a time; only explicit rejection removes a fact from the draft.
    Negated/uncertain facts must still render with their certainty visible, never
    silently as if affirmed."""
    body = await _process_transcript(
        ac,
        "Patient has fever for 3 days. No vomiting. Possible dengue. Any cough? Yes. "
        "BP 150/90. Start paracetamol 500mg twice daily. Follow up in 3 days.",
    )

    facts = body["extracted_facts"]
    assert facts
    # Doctor-confirmation gate: nothing is auto-confirmed.
    assert all(f["review_status"] == "candidate" for f in facts)
    assert all(f["source_sentence"] for f in facts)

    # Affirmed deterministic facts are present as candidates.
    assert any(f["normalized_value"].lower().startswith("fever") for f in facts)

    # Negation and uncertainty are surfaced with the correct certainty, not dropped.
    vomiting = [f for f in facts if f["normalized_value"].lower() == "vomiting"]
    assert vomiting and vomiting[0]["certainty"] == "negated"

    dengue = [f for f in facts if "dengue" in f["normalized_value"].lower()]
    assert dengue and dengue[0]["certainty"] == "uncertain"

    # "Any cough? Yes" is an affirmed symptom backed by two spans (question + answer).
    cough = [f for f in facts if f["normalized_value"].lower() == "cough"]
    assert cough and cough[0]["certainty"] == "affirmed"
    assert len(cough[0]["evidence_spans"]) == 2

    # Opt-out draft: affirmed candidates appear in the SOAP immediately.
    soap_text = "\n".join(body["soap"].values()).lower()
    assert "fever" in soap_text
    assert "cough" in soap_text
    assert "dengue" in soap_text
    # Negated/uncertain facts still appear (so the doctor can reject them if wrong)
    # but must never read as plain affirmed findings.
    assert "vomiting (denied)" in soap_text
    assert "dengue fever (uncertain)" in soap_text


@pytest.mark.anyio
async def test_accepting_candidate_fact_regenerates_supported_soap(ac):
    """Opt-out draft: "cough" is already visible pre-acceptance (candidate, in the
    draft SOAP for the doctor to review). Explicitly accepting it flips
    review_status to "confirmed" and attributes it to the confirming doctor —
    that per-fact confirmation state is what FHIR/structured export gates on."""
    body = await _process_transcript(ac, "Any cough? Yes. BP 120/80.")
    session_id = body["session_id"]
    cough = next(f for f in body["extracted_facts"] if f["normalized_value"].lower() == "cough")
    assert "cough" in "\n".join(body["soap"].values()).lower()
    assert cough["review_status"] == "candidate"

    reviewed = await ac.patch(
        f"/api/sessions/{session_id}/facts/{cough['id']}",
        json={"action": "accept"},
    )
    assert reviewed.status_code == 200, reviewed.text
    updated = reviewed.json()
    assert "cough" in updated["soap"]["S"].lower()
    accepted = next(f for f in updated["extracted_facts"] if f["id"] == cough["id"])
    assert accepted["review_status"] == "confirmed"
    assert accepted["confirmed_by"] == "doctor_1"


@pytest.mark.anyio
async def test_editing_candidate_fact_marks_doctor_source(ac):
    body = await _process_transcript(ac, "Any cough? Yes.")
    session_id = body["session_id"]
    cough = next(f for f in body["extracted_facts"] if f["normalized_value"].lower() == "cough")

    reviewed = await ac.patch(
        f"/api/sessions/{session_id}/facts/{cough['id']}",
        json={"action": "edit", "normalized_value": "productive cough"},
    )
    assert reviewed.status_code == 200, reviewed.text
    updated = reviewed.json()
    edited = next(f for f in updated["extracted_facts"] if f["id"] == cough["id"])
    assert edited["extractor"] == "doctor"
    assert edited["normalized_value"] == "productive cough"
    assert "productive cough" in updated["soap"]["S"].lower()


@pytest.mark.anyio
async def test_exports_blocked_until_facts_confirmed(ac):
    """Tasks 7-9: FHIR / investigation order are hard-gated on doctor confirmation."""
    body = await _process_transcript(
        ac,
        "Patient has fever. BP 120/80. CBC karwao. Start paracetamol 500mg twice daily.",
    )
    session_id = body["session_id"]

    # Before review: candidates remain → FHIR and investigation order are blocked.
    assert (await ac.get(f"/api/sessions/{session_id}/fhir")).status_code == 409
    assert (await ac.get(f"/api/sessions/{session_id}/investigation-order")).status_code == 409

    # Doctor confirms every candidate.
    finalize = await ac.post(f"/api/sessions/{session_id}/facts/finalize")
    assert finalize.status_code == 200
    assert finalize.json()["confirmed"] >= 1

    # After confirmation: exports unlock.
    assert (await ac.get(f"/api/sessions/{session_id}/fhir")).status_code == 200
    assert (await ac.get(f"/api/sessions/{session_id}/investigation-order")).status_code == 200


@pytest.mark.anyio
async def test_gliner_candidates_are_review_gated_and_threshold_filtered(ac):
    """GLiNER candidates are converted to review-gated facts: sub-threshold ones are
    dropped and high-confidence ones are still candidates (never auto-confirmed)."""
    from app.services import provenance

    transcript = "Patient says mystery syndrome and throat irritation. Start azithromycin."
    facts = {
        "symptoms": [], "medications": [], "vitals": [], "allergies": [],
        "investigations": [], "diagnoses": [], "follow_up": [], "contexts": {},
        "_gliner_candidates": [
            {"text": "mystery syndrome", "label": "diagnosis", "category": "diagnosis", "confidence": 0.95},
            {"text": "azithromycin", "label": "medication or drug", "category": "medication", "confidence": 0.85},
            {"text": "lowspan", "label": "medication or drug", "category": "medication", "confidence": 0.49},
        ],
    }
    extracted = provenance.build_extracted_facts(transcript, facts)
    names = {f.normalized_value.lower() for f in extracted}

    # Sub-threshold (0.49) candidate is dropped entirely.
    assert "lowspan" not in names
    # High-confidence GLiNER facts remain candidates — the gate never auto-confirms.
    azithro = next(f for f in extracted if f.normalized_value.lower() == "azithromycin")
    assert azithro.review_status == "candidate"
    mystery = next(f for f in extracted if f.normalized_value.lower() == "mystery syndrome")
    assert mystery.review_status == "candidate"
    # And none of them carry a confirming doctor id.
    assert azithro.confirmed_by is None and mystery.confirmed_by is None

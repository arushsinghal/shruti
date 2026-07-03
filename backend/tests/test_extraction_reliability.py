from app.services.clinical_extractor import ClinicalExtractorService
from app.services.provenance import build_extracted_facts


def test_allergy_phrase_does_not_create_medication() -> None:
    extractor = ClinicalExtractorService()

    for transcript in (
        "Patient allergic to penicillin.",
        "Penicillin allergy.",
        "Patient ko penicillin se allergy hai.",
    ):
        result = extractor.extract(transcript)
        assert "penicillin" in result["allergies"]
        med_names = [med["name"].lower() for med in result["medications"]]
        assert not any("penicillin" in name for name in med_names)


def test_unsupported_non_doctor_fact_is_candidate_only() -> None:
    facts = {
        "symptoms": ["fever"],
        "medications": [],
        "vitals": [],
        "allergies": [],
        "investigations": [],
        "diagnoses": [],
        "follow_up": [],
        "contexts": {"fever": "No matching sentence"},
    }

    extracted = build_extracted_facts("Patient has cough.", facts)
    fever = next(fact for fact in extracted if fact.normalized_value == "fever")

    assert fever.review_status == "candidate"
    assert fever.confirmed_by is None
    assert fever.confidence <= 0.49
    assert fever.metadata["evidence_validation"] == "missing_or_invalid_transcript_span"

"""Comprehensive test suite for the Lipi backend.

Run with:
    cd backend && uv run python -m pytest tests/ -v
"""

import pytest
import json


# ======================================================================
# 1. Clinical Extractor Tests
# ======================================================================

from app.services.phi_scrubber import PHIScrubberService
from app.services.clinical_extractor import ClinicalExtractorService

phi = PHIScrubberService()
extractor = ClinicalExtractorService()

class TestPHIScrubber:
    def test_scrub_names(self):
        text = "Patient John Doe came in to see Dr. Smith today."
        result = phi.scrub(text)
        assert "John Doe" not in result
        assert "Smith" not in result
        assert "[REDACTED_NAME]" in result

    def test_scrub_contact(self):
        text = "Call me at 555-123-4567 or email test@example.com."
        result = phi.scrub(text)
        assert "555" not in result
        assert "test@example.com" not in result
        assert "[REDACTED_PHONE]" in result
        assert "[REDACTED_EMAIL]" in result

    def test_scrub_preserves_clinical_content(self):
        """PHI scrubbing must not destroy symptoms, medications, or vitals."""
        text = "Patient has fever and cough. BP 140/90. Prescribed paracetamol 500mg twice daily."
        result = phi.scrub(text)
        assert "fever" in result
        assert "cough" in result
        assert "140/90" in result
        assert "paracetamol" in result
        assert "500mg" in result

    def test_scrub_removes_title_name(self):
        """'Dr. Sharma' and 'Patient Priya' patterns are scrubbed."""
        text = "Dr. Sharma examined Patient Priya today."
        result = phi.scrub(text)
        assert "Sharma" not in result
        assert "Priya" not in result

    def test_scrub_empty_string(self):
        assert phi.scrub("") == ""

    def test_clinical_duration_preserved_3_days(self):
        result = phi.scrub("Patient has fever for 3 days.")
        assert "3 days" in result, "clinical duration must survive PHI scrubbing"

    def test_clinical_duration_preserved_2_weeks(self):
        result = phi.scrub("Pain for 2 weeks.")
        assert "2 weeks" in result

    def test_clinical_duration_preserved_yesterday(self):
        result = phi.scrub("Cough since yesterday.")
        assert "yesterday" in result

    def test_clinical_duration_preserved_since_morning(self):
        result = phi.scrub("Vomiting since morning.")
        assert "morning" in result

    def test_clinical_duration_preserved_4_hours(self):
        result = phi.scrub("Headache for 4 hours.")
        assert "4 hours" in result

    def test_clinical_duration_preserved_1_month(self):
        result = phi.scrub("Symptoms for 1 month.")
        assert "1 month" in result

    def test_absolute_birthdate_scrubbed(self):
        result = phi.scrub("Patient born on 12/05/1985.")
        assert "1985" not in result
        assert "[REDACTED_DATE]" in result

    def test_calendar_appointment_date_scrubbed(self):
        result = phi.scrub("Appointment on March 4.")
        assert "March 4" not in result
        assert "[REDACTED_DATE]" in result

    def test_scrub_transcript_pipeline_integration(self):
        """Simulates what the pipeline does: scrub Sarvam output before clinical extraction.
        PHI identifiers must be removed; symptoms, vitals, medications must survive.

        Phone pattern note: the regex covers US-format (NNN-NNN-NNNN). Indian mobile
        numbers (98765-43210) are not matched by the current regex — a known gap to
        address when the phone regex is extended for Indian formats.
        """
        raw_transcript = (
            "Patient Ramesh Kumar, call 555-123-4567. "
            "He has bukhar aur khasi. BP is 130/80. "
            "Prescribe paracetamol 500 mg twice daily."
        )
        scrubbed = phi.scrub(raw_transcript)

        # PHI removed
        assert "Ramesh Kumar" not in scrubbed
        assert "555-123-4567" not in scrubbed
        assert "[REDACTED_PHONE]" in scrubbed

        # Clinical content survives scrubbing and is correctly extracted
        facts = extractor.extract(scrubbed)
        assert "fever" in facts["symptoms"], "bukhar should survive scrubbing"
        assert "cough" in facts["symptoms"], "khasi should survive scrubbing"
        assert any("130/80" in v for v in facts["vitals"]), "BP should survive scrubbing"
        assert any(m["name"] == "paracetamol" for m in facts["medications"])


class TestClinicalExtractor:
    """Tests for deterministic clinical fact extraction."""

    def test_extract_english_symptoms(self):
        transcript = "Patient has fever and headache since yesterday."
        result = extractor.extract(transcript)
        assert any("fever" in s for s in result["symptoms"])
        assert any("headache" in s for s in result["symptoms"])

    def test_extract_hindi_symptoms(self):
        transcript = "Patient ko bukhar hai aur khasi bhi hai."
        result = extractor.extract(transcript)
        assert "fever" in result["symptoms"], "bukhar should map to fever"
        assert "cough" in result["symptoms"], "khasi should map to cough"

    def test_extract_hinglish_mixed(self):
        transcript = "Dard ho raha hai. Also nausea and vomiting."
        result = extractor.extract(transcript)
        assert "pain" in result["symptoms"]
        assert "nausea" in result["symptoms"]
        assert "vomiting" in result["symptoms"]

    def test_extract_bp_vitals(self):
        transcript = "BP is 150/90 today."
        result = extractor.extract(transcript)
        assert any("150/90" in v for v in result["vitals"])

    def test_extract_temperature_vitals(self):
        transcript = "Temperature was 38.5 C during examination."
        result = extractor.extract(transcript)
        assert any("38.5" in v for v in result["vitals"])

    def test_extract_allergies(self):
        transcript = "Patient is allergic to penicillin."
        result = extractor.extract(transcript)
        assert "penicillin" in result["allergies"]

    def test_extract_medications(self):
        transcript = "Prescribed paracetamol 500 mg twice daily."
        result = extractor.extract(transcript)
        assert len(result["medications"]) >= 1
        med = result["medications"][0]
        assert med["name"] == "paracetamol"
        assert "500" in med["dosage"]

    def test_extract_investigations(self):
        transcript = "Order a CBC and an X-Ray."
        result = extractor.extract(transcript)
        assert "CBC" in result["investigations"]
        assert "X-Ray" in result["investigations"]

    def test_uncertainty_filter(self):
        transcript = "Maybe the patient has fever. He definitely has a headache."
        result = extractor.extract(transcript)
        assert "fever" not in result["symptoms"], "uncertain 'maybe' sentence should be filtered"
        assert "headache" in result["symptoms"]

    def test_context_attribution(self):
        transcript = "Patient has severe cough."
        result = extractor.extract(transcript)
        assert "cough" in result["contexts"]
        assert "cough" in result["contexts"]["cough"].lower()

    def test_empty_transcript(self):
        result = extractor.extract("")
        assert result["symptoms"] == []
        assert result["medications"] == []

    def test_no_duplicates(self):
        transcript = "Patient has fever. The fever is high."
        result = extractor.extract(transcript)
        assert result["symptoms"].count("fever") == 1

    def test_medication_false_positive_filter(self):
        """Words like 'the', 'for', 'start' should not be detected as med names."""
        transcript = "Start paracetamol 500 mg daily."
        result = extractor.extract(transcript)
        med_names = [m["name"] for m in result["medications"]]
        assert "start" not in med_names
        assert "paracetamol" in med_names

    def test_extract_medications_without_dosage(self):
        transcript = "I will prescribe some antibiotics and painkiller."
        result = extractor.extract(transcript)
        med_names = [m["name"] for m in result["medications"]]
        assert "antibiotics" in med_names
        assert "painkiller" in med_names

    def test_dentist_transcript(self):
        transcript = "Definitely a cavity close to the root canal. Prescribe painkiller."
        result = extractor.extract(transcript)
        assert "cavity" in result["symptoms"]
        assert "Root Canal Treatment" in result["investigations"]
        assert any(m["name"] == "painkiller" for m in result["medications"])



# ======================================================================
# 2. Memory Context Tests
# ======================================================================

from app.services.memory_context import MemoryContextService

memory = MemoryContextService()


class TestMemoryContext:
    """Tests for the clinical state resolution engine."""

    def test_resolve_basic_facts(self):
        facts = [{
            "symptoms": ["fever", "cough"],
            "medications": [{"name": "paracetamol", "dosage": "500 mg", "frequency": "BD"}],
            "vitals": ["BP 130/80"],
            "allergies": ["penicillin"],
            "investigations": ["CBC"],
            "contexts": {"fever": "Patient has fever"},
        }]
        state = memory.resolve_memory(facts)
        assert "fever" in state["symptoms"]
        assert "cough" in state["symptoms"]
        assert "paracetamol" in state["medications"]
        assert state["medications"]["paracetamol"]["dosage"] == "500 mg"
        assert "penicillin" in state["allergies"]

    def test_resolve_dedup(self):
        facts = [
            {"symptoms": ["fever"], "medications": [], "vitals": [], "allergies": [], "investigations": [], "contexts": {}},
            {"symptoms": ["fever"], "medications": [], "vitals": [], "allergies": [], "investigations": [], "contexts": {}},
        ]
        state = memory.resolve_memory(facts)
        assert state["symptoms"].count("fever") == 1

    def test_resolve_medication_override(self):
        facts = [
            {"symptoms": [], "medications": [{"name": "amox", "dosage": "250 mg", "frequency": "BD"}],
             "vitals": [], "allergies": [], "investigations": [], "contexts": {}},
            {"symptoms": [], "medications": [{"name": "amox", "dosage": "500 mg", "frequency": "TDS"}],
             "vitals": [], "allergies": [], "investigations": [], "contexts": {}},
        ]
        state = memory.resolve_memory(facts)
        assert state["medications"]["amox"]["dosage"] == "500 mg"
        assert state["medications"]["amox"]["frequency"] == "tds"

    def test_context_merge(self):
        facts = [{
            "symptoms": ["fever"],
            "medications": [],
            "vitals": [],
            "allergies": [],
            "investigations": [],
            "contexts": {"fever": "Patient has high fever"},
        }]
        state = memory.resolve_memory(facts)
        assert state["contexts"]["fever"] == "Patient has high fever"


# ======================================================================
# 3. SOAP Generator Tests
# ======================================================================

from app.services.soap_generator import SOAPGeneratorService

soap_gen = SOAPGeneratorService()


class TestSOAPGenerator:
    """Tests for deterministic SOAP note generation."""

    def test_basic_soap(self):
        state = {
            "symptoms": ["fever", "cough"],
            "medications": {"paracetamol": {"dosage": "500 mg", "frequency": "BD"}},
            "vitals": ["BP 130/80"],
            "allergies": ["penicillin"],
            "investigations": ["CBC"],
        }
        soap = soap_gen.generate_soap(state)
        assert "S" in soap and "O" in soap and "A" in soap and "P" in soap
        assert "fever" in soap["S"].lower()
        assert "penicillin" in soap["S"].lower()
        assert "130/80" in soap["O"]
        assert "paracetamol" in soap["P"].lower()

    def test_empty_state_soap(self):
        state = {"symptoms": [], "medications": {}, "vitals": [], "allergies": [], "investigations": []}
        soap = soap_gen.generate_soap(state)
        assert "no subjective" in soap["S"].lower() or "no" in soap["S"].lower()

    def test_fever_assessment(self):
        state = {"symptoms": ["fever"], "medications": {}, "vitals": [], "allergies": [], "investigations": []}
        soap = soap_gen.generate_soap(state)
        assert "not specified" in soap["A"].lower()
        assert "physician" in soap["A"].lower()


# ======================================================================
# 4. CDS Engine Tests
# ======================================================================

from app.services.cds_engine import CDSEngineService

cds_engine = CDSEngineService()


class TestCDSEngine:
    """Tests for Lipi safety checks."""

    def test_fever_suggestion(self):
        state = {
            "symptoms": ["fever"],
            "medications": {},
            "vitals": [],
            "allergies": [],
        }
        suggestions = cds_engine.generate_cds(state)
        texts = [s["suggestion"].lower() for s in suggestions]
        assert any("cbc" in t or "malaria" in t or "dengue" in t for t in texts)

    def test_allergy_cross_check(self):
        state = {
            "symptoms": [],
            "medications": {"penicillin": {"dosage": "500 mg", "frequency": "BD"}},
            "vitals": [],
            "allergies": ["penicillin"],
        }
        suggestions = cds_engine.generate_cds(state)
        assert any(s["urgency"] == "critical" for s in suggestions)

    def test_elevated_bp_warning(self):
        state = {
            "symptoms": [],
            "medications": {},
            "vitals": ["BP 150/90"],
            "allergies": [],
        }
        suggestions = cds_engine.generate_cds(state)
        texts = [s["suggestion"].lower() for s in suggestions]
        assert any("blood pressure" in t or "bp" in t for t in texts)

    def test_missing_dosage_warning(self):
        state = {
            "symptoms": [],
            "medications": {"amoxicillin": {"dosage": "", "frequency": "BD"}},
            "vitals": [],
            "allergies": [],
        }
        suggestions = cds_engine.generate_cds(state)
        texts = [s["suggestion"].lower() for s in suggestions]
        assert any("dosage" in t for t in texts)


# ======================================================================
# 5. FHIR Mapper Tests
# ======================================================================

from app.services.fhir_mapper import FHIRMapperService

fhir_svc = FHIRMapperService()


class TestFHIRMapper:
    """Tests for HL7 FHIR R4 bundle generation."""

    def _sample_state(self):
        return {
            "symptoms": ["fever", "cough"],
            "medications": {"paracetamol": {"dosage": "500 mg", "frequency": "BD"}},
            "vitals": ["BP 130/80"],
            "allergies": ["penicillin"],
            "investigations": ["CBC"],
        }

    def test_bundle_structure(self):
        bundle = fhir_svc.generate_fhir_bundle("test-123", "John Doe", self._sample_state())
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert "entry" in bundle
        assert len(bundle["entry"]) > 0

    def test_patient_resource(self):
        bundle = fhir_svc.generate_fhir_bundle("test-123", "John Doe", self._sample_state())
        patients = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient"]
        assert len(patients) == 1
        assert patients[0]["resource"]["name"][0]["text"] == "John Doe"

    def test_condition_resources(self):
        bundle = fhir_svc.generate_fhir_bundle("test-123", "John Doe", self._sample_state())
        conditions = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Condition"]
        assert len(conditions) == 2  # fever + cough

    def test_medication_resources(self):
        bundle = fhir_svc.generate_fhir_bundle("test-123", "John Doe", self._sample_state())
        meds = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "MedicationRequest"]
        assert len(meds) == 1
        assert "paracetamol" in meds[0]["resource"]["medicationCodeableConcept"]["text"].lower()

    def test_allergy_resources(self):
        bundle = fhir_svc.generate_fhir_bundle("test-123", "John Doe", self._sample_state())
        allergies = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "AllergyIntolerance"]
        assert len(allergies) == 1


# ======================================================================
# 6. Integration / Pipeline Tests
# ======================================================================

class TestFullPipeline:
    """End-to-end tests: transcript → extract → memory → SOAP → CDS."""

    def test_english_pipeline(self):
        transcript = (
            "Patient is a 34-year-old male presenting with fever since two days. "
            "Temperature was 38.5 C. BP is 150/90. Start paracetamol 500 mg twice daily. "
            "Allergic to penicillin. Also check CBC and CRP."
        )
        facts = extractor.extract(transcript)
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        cds = cds_engine.generate_cds(state)

        # Facts
        assert "fever" in state["symptoms"]
        assert "penicillin" in state["allergies"]
        assert any("150/90" in v for v in state["vitals"])
        assert "paracetamol" in state["medications"]
        assert "CBC" in state["investigations"]

        # SOAP
        assert "fever" in soap["S"].lower()
        assert "150/90" in soap["O"]
        assert "paracetamol" in soap["P"].lower()

        # CDS
        assert len(cds) >= 1

    def test_hindi_pipeline(self):
        transcript = (
            "Patient ko bukhar hai do din se. Khasi bhi hai. "
            "BP 140/90 hai. Paracetamol 500 mg do baar dein. "
            "Penicillin se allergy hai."
        )
        facts = extractor.extract(transcript)
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)

        assert "fever" in state["symptoms"], "bukhar should extract as fever"
        assert "cough" in state["symptoms"], "khasi should extract as cough"
        assert any("140/90" in v for v in state["vitals"])
        assert "fever" in soap["S"].lower()

    def test_empty_pipeline(self):
        facts = extractor.extract("")
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        assert "no subjective" in soap["S"].lower() or "no" in soap["S"].lower()


# ======================================================================
# 8. Config — ALLOWED_ORIGINS validator
# ======================================================================

class TestAllowedOriginsConfig:
    def test_default_origins_include_localhost(self):
        from app.utils.config import settings
        assert any("localhost" in o for o in settings.allowed_origins)

    def test_parse_comma_separated_string(self):
        from app.utils.config import Settings
        s = Settings(allowed_origins="https://a.example.com,https://b.example.com")  # type: ignore[call-arg]
        assert s.allowed_origins == ["https://a.example.com", "https://b.example.com"]

    def test_parse_strips_whitespace(self):
        from app.utils.config import Settings
        s = Settings(allowed_origins=" https://a.com , https://b.com ")  # type: ignore[call-arg]
        assert s.allowed_origins == ["https://a.com", "https://b.com"]

    def test_list_passthrough(self):
        from app.utils.config import Settings
        s = Settings(allowed_origins=["https://c.com"])  # type: ignore[call-arg]
        assert s.allowed_origins == ["https://c.com"]

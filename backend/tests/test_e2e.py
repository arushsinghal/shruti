"""End-to-end tests for the Lipi clinical pipeline.

Run with:
    cd backend && uv run python -m pytest tests/test_e2e.py -v
"""

import pytest
import re
from app.services.clinical_extractor import ClinicalExtractorService
from app.services.clinical_pipeline import run_health_pipeline
from app.services.memory_context import MemoryContextService
from app.services.soap_generator import SOAPGeneratorService
from app.services.cds_engine import CDSEngineService
from app.services.phi_scrubber import PHIScrubberService

extractor = ClinicalExtractorService()
memory = MemoryContextService()
soap_gen = SOAPGeneratorService()
cds_engine = CDSEngineService()
phi = PHIScrubberService()


# ======================================================================
# E2E: Full pipeline — transcript in, SOAP + CDS out
# ======================================================================

class TestFullPipeline:
    """Tests the complete extraction → memory → SOAP → CDS pipeline."""

    DEMO_TRANSCRIPT = """Doctor: Patient ki age kya hai?
Patient: 32 saal.
Doctor: Kya problem hai aaj?
Patient: Doctor sahab, 4 din se bukhaar chal raha hai. Temperature ghar pe naap liya tha, 39 degree tha.
Doctor: Aur koi takleef?
Patient: Khasi bhi hai, gale mein bhi dard hai. Naak bhi beh rahi hai. Sar dard bhi ho raha hai.
Doctor: BP legate hain... 128 over 82. Temperature abhi 38.6 degree Celsius.
Patient: Doctor, mujhe penicillin se reaction hua tha pehle.
Doctor: Tab Azithromycin 500 mg OD for 5 days. Tab Paracetamol 500 mg TDS.
CBC karwa lo. Follow up in 3 days."""

    def _run_full(self):
        facts = run_health_pipeline(self.DEMO_TRANSCRIPT)
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        cds = cds_engine.generate_cds(state)
        return {"facts": facts, "state": state, "soap": soap, "cds": cds}

    def test_pipeline_extracts_all_entity_types(self):
        result = self._run_full()
        facts = result["facts"]
        assert len(facts["symptoms"]) >= 3, f"Expected >=3 symptoms, got {facts['symptoms']}"
        assert len(facts["medications"]) >= 2, f"Expected >=2 meds, got {facts['medications']}"
        assert len(facts["vitals"]) >= 1, f"Expected >=1 vitals, got {facts['vitals']}"
        assert len(facts["allergies"]) >= 1, f"Expected >=1 allergies, got {facts['allergies']}"

    def test_pipeline_generates_soap(self):
        result = self._run_full()
        soap = result["soap"]
        assert "S" in soap
        assert "O" in soap
        assert "A" in soap
        assert "P" in soap

    def test_pipeline_generates_cds(self):
        result = self._run_full()
        cds = result["cds"]
        assert isinstance(cds, list)

    def test_pipeline_hindi_symptoms_mapped(self):
        result = self._run_full()
        symptoms = [s.split(" (")[0] for s in result["facts"]["symptoms"]]
        assert "fever" in symptoms, f"bukhaar should map to fever, got {symptoms}"
        assert "cough" in symptoms, f"khasi should map to cough, got {symptoms}"
        assert "headache" in symptoms, f"sar dard should map to headache, got {symptoms}"

    def test_pipeline_medications_have_dosage(self):
        result = self._run_full()
        meds = result["facts"]["medications"]
        azithro = [m for m in meds if "azithromycin" in m["name"].lower()]
        assert len(azithro) >= 1, f"Azithromycin not found in {meds}"
        assert azithro[0].get("dosage"), "Azithromycin should have dosage"

    def test_pipeline_penicillin_allergy(self):
        result = self._run_full()
        allergies = [a.lower() for a in result["facts"]["allergies"]]
        assert any("penicillin" in a for a in allergies)

    def test_pipeline_follow_up_extracted(self):
        result = self._run_full()
        follow_up = result["facts"].get("follow_up", [])
        assert len(follow_up) >= 1, f"Expected follow-up, got {follow_up}"
        assert any("3" in str(f) for f in follow_up), "Should mention 3 days"


# ======================================================================
# E2E: ASR normalization — misspelled input still extracts correctly
# ======================================================================

class TestASRNormalization:
    """Tests that the ASR normalization layer fixes common speech-to-text errors."""

    def test_split_drug_name_rejoined(self):
        result = extractor.extract("Patient ko parace tamol 500mg diya")
        meds = [m["name"].lower() for m in result["medications"]]
        assert any("paracetamol" in m for m in meds), f"Split 'parace tamol' not rejoined, got {meds}"

    def test_misspelled_drug_corrected(self):
        result = extractor.extract("Prescribe paracetemol 650mg twice daily")
        meds = [m["name"].lower() for m in result["medications"]]
        assert any("paracetamol" in m for m in meds), f"Misspelled 'paracetemol' not corrected, got {meds}"

    def test_split_azithromycin(self):
        result = extractor.extract("Tab azithro mycin 500 mg OD")
        meds = [m["name"].lower() for m in result["medications"]]
        assert any("azithromycin" in m for m in meds), f"Split 'azithro mycin' not rejoined, got {meds}"

    def test_dosage_spacing_normalized(self):
        result = extractor.extract("Give paracetamol 500 mg twice daily")
        meds = result["medications"]
        assert len(meds) >= 1
        para = [m for m in meds if "paracetamol" in m["name"].lower()]
        assert len(para) >= 1

    def test_clean_transcript_no_regression(self):
        result = extractor.extract("Prescribe Paracetamol 500mg TDS and Azithromycin 500mg OD")
        meds = [m["name"].lower() for m in result["medications"]]
        assert any("paracetamol" in m for m in meds)
        assert any("azithromycin" in m for m in meds)


# ======================================================================
# E2E: Hindi/Hinglish symptom extraction
# ======================================================================

class TestHindiExtraction:
    """Tests Hindi and Hinglish clinical term extraction."""

    def test_bukhar_maps_to_fever(self):
        result = extractor.extract("Patient ko bukhar hai")
        assert "fever" in result["symptoms"]

    def test_khasi_maps_to_cough(self):
        result = extractor.extract("Khasi bhi chal rahi hai")
        assert "cough" in result["symptoms"]

    def test_sar_dard_maps_to_headache(self):
        result = extractor.extract("Sar dard ho raha hai")
        assert "headache" in result["symptoms"]

    def test_pet_dard_maps_to_abdominal_pain(self):
        result = extractor.extract("Pet mein dard hai")
        assert "abdominal pain" in result["symptoms"]

    def test_ulti_maps_to_vomiting(self):
        result = extractor.extract("Ulti aa rahi hai")
        assert "vomiting" in result["symptoms"]

    def test_hindi_follow_up_hafta(self):
        result = extractor.extract("1 hafte baad aana")
        follow_up = result.get("follow_up", [])
        assert any("1 week" in f.lower() or "week" in f.lower() for f in follow_up), f"hafta not mapped, got {follow_up}"

    def test_hindi_follow_up_din(self):
        result = extractor.extract("3 din baad aana")
        follow_up = result.get("follow_up", [])
        assert any("3 day" in f.lower() or "day" in f.lower() for f in follow_up), f"din not mapped, got {follow_up}"

    def test_pluralization_1_week(self):
        result = extractor.extract("1 hafte baad aana")
        follow_up = result.get("follow_up", [])
        matching = [f for f in follow_up if "week" in f.lower()]
        if matching:
            assert "weeks" not in matching[0].lower(), f"Should be 'week' not 'weeks' for 1, got {matching[0]}"


# ======================================================================
# E2E: Vitals extraction
# ======================================================================

class TestVitalsExtraction:
    def test_bp_extracted(self):
        result = extractor.extract("BP 140/90 mmHg")
        assert any("140/90" in v for v in result["vitals"])

    def test_temperature_celsius(self):
        result = extractor.extract("Temperature 38.5 C")
        assert any("38.5" in v for v in result["vitals"])

    def test_pulse_rate(self):
        result = extractor.extract("Pulse 88 bpm")
        assert any("88" in v for v in result["vitals"])

    def test_spo2(self):
        result = extractor.extract("SpO2 97%")
        assert any("97" in v for v in result["vitals"])


# ======================================================================
# E2E: CDS alerts fire correctly
# ======================================================================

class TestCDSAlerts:
    def test_penicillin_allergy_conflict(self):
        facts = extractor.extract(
            "Patient has penicillin allergy. Prescribe amoxicillin 500mg."
        )
        state = memory.resolve_memory([facts])
        cds = cds_engine.generate_cds(state)
        critical = [c for c in cds if c.get("urgency") == "critical"]
        assert len(critical) >= 1, f"Expected allergy-drug conflict alert, got {cds}"

    def test_high_bp_alert(self):
        facts = extractor.extract("BP 180/110. Patient has headache.")
        state = memory.resolve_memory([facts])
        cds = cds_engine.generate_cds(state)
        assert any("hypertensive" in str(c).lower() or "bp" in str(c).lower() or "180" in str(c) for c in cds), \
            f"Expected high BP alert, got {cds}"


# ======================================================================
# E2E: PHI scrubbing does not destroy clinical content
# ======================================================================

class TestPHIScrubPipeline:
    def test_scrub_then_extract_preserves_clinical(self):
        raw = "Patient Ramesh Kumar has bukhar and khasi. BP 130/80. Give paracetamol 500mg."
        scrubbed = phi.scrub(raw)
        assert "Ramesh" not in scrubbed
        facts = extractor.extract(scrubbed)
        assert "fever" in facts["symptoms"]
        assert "cough" in facts["symptoms"]
        assert any("130/80" in v for v in facts["vitals"])
        assert any("paracetamol" in m["name"].lower() for m in facts["medications"])


# ======================================================================
# E2E: SOAP note quality
# ======================================================================

class TestSOAPQuality:
    def test_soap_has_all_four_sections(self):
        facts = extractor.extract("Patient has fever. Give paracetamol 500mg TDS. BP 120/80. Follow up in 5 days.")
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        for key in ["S", "O", "A", "P"]:
            assert key in soap, f"SOAP missing {key}"
            assert isinstance(soap[key], str)

    def test_soap_subjective_has_symptoms(self):
        facts = extractor.extract("Patient complains of headache and nausea for 2 days.")
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        subj = soap.get("S", "").lower()
        assert "headache" in subj or "nausea" in subj or "presents" in subj, \
            f"Subjective should mention symptoms, got: {subj}"

    def test_soap_objective_has_vitals(self):
        facts = extractor.extract("BP 120/80. Temperature 37.5 C. Patient has mild cough.")
        state = memory.resolve_memory([facts])
        soap = soap_gen.generate_soap(state)
        obj = soap.get("O", "").lower()
        assert "120/80" in obj or "37.5" in obj or "vitals" in obj, \
            f"Objective should include vitals, got: {obj}"


# ======================================================================
# E2E: NMC number validation
# ======================================================================

class TestNMCValidation:
    def test_valid_formats(self):
        valid = ["MH-12345", "KA-1234", "DL-12345", "TN12345", "AP-1234567"]
        pattern = re.compile(r'^[A-Z]{2,3}-?\d{4,7}$', re.IGNORECASE)
        for nmc in valid:
            assert pattern.match(nmc), f"{nmc} should be valid"

    def test_invalid_formats(self):
        invalid = ["12345", "M-123", "MHKA-123", "", "MH-", "MH-12345678"]
        pattern = re.compile(r'^[A-Z]{2,3}-?\d{4,7}$', re.IGNORECASE)
        for nmc in invalid:
            assert not pattern.match(nmc), f"{nmc} should be invalid"


# ======================================================================
# E2E: ABHA number validation
# ======================================================================

class TestABHAValidation:
    def test_valid_14_digit(self):
        abha = "91123456789012"
        clean = re.sub(r'[\s-]', '', abha)
        assert len(clean) == 14 and clean.isdigit()

    def test_valid_with_dashes(self):
        abha = "91-1234-5678-9012"
        clean = re.sub(r'[\s-]', '', abha)
        assert len(clean) == 14 and clean.isdigit()

    def test_invalid_short(self):
        abha = "9112345678"
        clean = re.sub(r'[\s-]', '', abha)
        assert len(clean) != 14

    def test_invalid_alpha(self):
        abha = "91-1234-ABCD-9012"
        clean = re.sub(r'[\s-]', '', abha)
        assert not clean.isdigit()

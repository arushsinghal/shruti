import uuid
from datetime import datetime, timezone


_VITAL_LOINC = {
    "bp": {"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"},
    "blood pressure": {"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"},
    "temperature": {"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"},
    "temp": {"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"},
    "heart rate": {"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"},
    "pulse": {"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"},
    "spo2": {"system": "http://loinc.org", "code": "59408-5", "display": "Oxygen saturation"},
    "oxygen": {"system": "http://loinc.org", "code": "59408-5", "display": "Oxygen saturation"},
    "weight": {"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"},
    "height": {"system": "http://loinc.org", "code": "8302-2", "display": "Body height"},
}


def _vital_code(vital_text: str) -> dict:
    lower = vital_text.lower()
    for key, coding in _VITAL_LOINC.items():
        if key in lower:
            return {"coding": [coding], "text": vital_text}
    return {"text": vital_text}


class FHIRMapperService:
    """
    Converts internal deterministic clinical state into HL7 FHIR R4 JSON resources.
    This enables interoperability with ABDM, Epic, Cerner, and similar systems.
    """

    def generate_fhir_bundle(
        self,
        session_id: str,
        patient_name: str,
        state: dict,
        dhis_category: str = "Cat2",
        dsc_id: str = "",
    ) -> dict:
        bundle_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        patient_id = "pat-" + session_id[:8]
        encounter_id = "enc-" + session_id[:8]
        composition_id = "comp-" + session_id[:8]

        # Task 36: ABDM NHA R4 profile URLs
        _ABDM_COMPOSITION_PROFILE = "https://nrces.in/ndhm/fhir/r4/StructureDefinition/OPConsultRecord"
        _ABDM_PATIENT_PROFILE = "https://nrces.in/ndhm/fhir/r4/StructureDefinition/Patient"

        # DHIS category tag for NHA incentive claim (Cat1=discharge/lab, Cat2=OPD)
        meta_tags = []
        if dhis_category in ("Cat1", "Cat2"):
            meta_tags.append({
                "system": "https://healthid.abdm.gov.in/dhis/category",
                "code": dhis_category,
                "display": "Discharge/Diagnostic" if dhis_category == "Cat1" else "OPD Consultation",
            })
        if dsc_id:
            meta_tags.append({
                "system": "https://healthid.abdm.gov.in/dhis/dsc",
                "code": dsc_id,
                "display": "DSC ID",
            })

        composition = {
            "resourceType": "Composition",
            "id": composition_id,
            "meta": {
                "profile": [_ABDM_COMPOSITION_PROFILE],
                **({"tag": meta_tags} if meta_tags else {}),
            },
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34133-9",
                        "display": "Summary of episode note",
                    },
                    {
                        # ABDM NHA SNOMED code for outpatient consultation
                        "system": "http://snomed.info/sct",
                        "code": "371530004",
                        "display": "Clinical consultation report",
                    },
                ]
            },
            "subject": {"reference": f"urn:uuid:{patient_id}"},
            "date": now_str,
            "author": [{"display": "Unknown Physician"}],
            "title": "OPD Consultation Note",
            "section": [
                {
                    "title": "Clinical Note",
                    "text": {"status": "generated", "div": "<div>See structured data</div>"},
                }
            ],
        }

        patient_identifier = state.get("abha_number")
        patient_resource: dict = {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": {"profile": [_ABDM_PATIENT_PROFILE]},
            "name": [{"text": patient_name or "Anonymous Patient", "use": "official"}],
            "active": True,
        }
        if patient_identifier:
            # ABDM ABHA number format: XX-XXXX-XXXX-XXXX
            patient_resource["identifier"] = [
                {
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                                "display": "Medical Record Number",
                            }
                        ]
                    },
                    "system": "https://healthid.ndhm.gov.in",
                    "value": patient_identifier,
                }
            ]

        entries = [
            {
                "fullUrl": f"urn:uuid:{composition_id}",
                "resource": composition,
            },
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": patient_resource,
            },
            {
                "fullUrl": f"urn:uuid:{encounter_id}",
                "resource": {
                    "resourceType": "Encounter",
                    "id": encounter_id,
                    "status": "finished",
                    "class": {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "ambulatory",
                    },
                    "subject": {"reference": f"urn:uuid:{patient_id}"},
                    "period": {"start": now_str},
                },
            },
        ]

        for symptom in state.get("symptoms", []):
            condition_text = str(symptom)
            cond_id = str(uuid.uuid4())
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{cond_id}",
                    "resource": {
                        "resourceType": "Condition",
                        "id": cond_id,
                        "clinicalStatus": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                    "code": "active",
                                }
                            ]
                        },
                        "code": {
                            "coding": [{"system": "http://snomed.info/sct", "display": condition_text}],
                            "text": condition_text,
                        },
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                    },
                }
            )

        meds = state.get("medications", {})
        for med_name, details in meds.items():
            med_id = str(uuid.uuid4())
            dosage_instruction = []
            dosage_text = f"{details.get('dosage', '')} {details.get('frequency', '')}".strip()
            if dosage_text:
                dosage_instruction.append({"text": dosage_text})
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{med_id}",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": med_id,
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {"text": med_name},
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                        "authoredOn": now_str,
                        "dosageInstruction": dosage_instruction,
                    },
                }
            )

        for vital in state.get("vitals", []):
            vital_text = str(vital)
            obs_id = str(uuid.uuid4())
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{obs_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": obs_id,
                        "status": "final",
                        "code": _vital_code(vital_text),
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                        "effectiveDateTime": now_str,
                        "valueString": vital_text,
                    },
                }
            )

        for allergy in state.get("allergies", []):
            allergy_text = str(allergy)
            allergy_id = str(uuid.uuid4())
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{allergy_id}",
                    "resource": {
                        "resourceType": "AllergyIntolerance",
                        "id": allergy_id,
                        "clinicalStatus": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                                    "code": "active",
                                }
                            ]
                        },
                        "code": {
                            "coding": [{"system": "http://snomed.info/sct", "display": allergy_text}],
                            "text": allergy_text,
                        },
                        "patient": {"reference": f"urn:uuid:{patient_id}"},
                        "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                    },
                }
            )

        for investigation in state.get("investigations", []):
            order_text = str(investigation)
            order_id = str(uuid.uuid4())
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{order_id}",
                    "resource": {
                        "resourceType": "ServiceRequest",
                        "id": order_id,
                        "status": "active",
                        "intent": "order",
                        "code": {"text": order_text},
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                        "authoredOn": now_str,
                    },
                }
            )

        return {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "document",
            "timestamp": now_str,
            "entry": entries,
        }

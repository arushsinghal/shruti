import uuid
from datetime import datetime, timezone

class FHIRMapperService:
    """
    Converts internal deterministic clinical state into HL7 FHIR R4 JSON resources.
    This enables interoperability with ABDM, Epic, Cerner, etc.
    """

    def generate_fhir_bundle(self, session_id: str, patient_name: str, state: dict) -> dict:
        bundle_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        
        patient_id = "pat-" + session_id[:8]
        encounter_id = "enc-" + session_id[:8]

        entries = []

        # 1. Patient Resource
        entries.append({
            "fullUrl": f"urn:uuid:{patient_id}",
            "resource": {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"text": patient_name or "Anonymous Patient", "use": "official"}],
                "active": True
            }
        })

        # 2. Encounter Resource
        entries.append({
            "fullUrl": f"urn:uuid:{encounter_id}",
            "resource": {
                "resourceType": "Encounter",
                "id": encounter_id,
                "status": "finished",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory"
                },
                "subject": {"reference": f"urn:uuid:{patient_id}"},
                "period": {"start": now_str}
            }
        })

        # 3. Conditions (Symptoms)
        for symptom in state.get("symptoms", []):
            cond_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{cond_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": cond_id,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "text": symptom
                    },
                    "subject": {"reference": f"urn:uuid:{patient_id}"},
                    "encounter": {"reference": f"urn:uuid:{encounter_id}"}
                }
            })

        # 4. MedicationRequests
        meds = state.get("medications", {})
        for med_name, details in meds.items():
            med_id = str(uuid.uuid4())
            dosage_instruction = []
            dosage_text = f"{details.get('dosage', '')} {details.get('frequency', '')}".strip()
            if dosage_text:
                dosage_instruction.append({"text": dosage_text})

            entries.append({
                "fullUrl": f"urn:uuid:{med_id}",
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": med_id,
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "text": med_name.capitalize()
                    },
                    "subject": {"reference": f"urn:uuid:{patient_id}"},
                    "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                    "dosageInstruction": dosage_instruction
                }
            })

        # 5. AllergyIntolerances
        for allergy in state.get("allergies", []):
            alg_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{alg_id}",
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": alg_id,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
                    },
                    "type": "allergy",
                    "code": {
                        "text": allergy.capitalize()
                    },
                    "patient": {"reference": f"urn:uuid:{patient_id}"}
                }
            })

        # 6. Observations (Vitals)
        for vital in state.get("vitals", []):
            obs_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "category": [{
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]
                    }],
                    "code": {
                        "text": vital
                    },
                    "subject": {"reference": f"urn:uuid:{patient_id}"},
                    "encounter": {"reference": f"urn:uuid:{encounter_id}"},
                    "effectiveDateTime": now_str
                }
            })

        return {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "document",
            "timestamp": now_str,
            "entry": entries
        }

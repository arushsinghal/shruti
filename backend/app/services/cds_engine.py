_URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class CDSEngineService:
    def generate_cds(self, state: dict) -> list:
        suggestions = []
        
        medications = state.get("medications", {})
        allergies = [a.lower() for a in state.get("allergies", [])]
        symptoms_str = " ".join(state.get("symptoms", [])).lower()
        vitals_str = " ".join(state.get("vitals", [])).lower()
        
        # 1. Missing Dosage / Frequency Warnings & Allergy Checks
        for med_name, details in medications.items():
            # Missing dosage
            if not details.get("dosage"):
                suggestions.append({
                    "suggestion": f"Specify dosage for {med_name}",
                    "rationale": "Missing medication dosage can lead to dispensing errors.",
                    "urgency": "medium",
                    "safety_label": "doctor_review_required"
                })
                
            # Missing frequency
            if not details.get("frequency"):
                suggestions.append({
                    "suggestion": f"Specify frequency for {med_name}",
                    "rationale": "Missing administration frequency.",
                    "urgency": "medium",
                    "safety_label": "doctor_review_required"
                })

            # Basic Allergy check (simple substring match)
            for allergy in allergies:
                if allergy in med_name.lower():
                    suggestions.append({
                        "suggestion": f"High risk: Possible allergic reaction to {med_name}",
                        "rationale": f"Patient reported allergy to {allergy}.",
                        "urgency": "critical",
                        "safety_label": "doctor_review_required"
                    })

        # 2. Symptom-based Suggestions
        if "fever" in symptoms_str or "bukhar" in symptoms_str:
            suggestions.append({
                "suggestion": "Consider ordering CBC or Malaria/Dengue panel",
                "rationale": "Fever present; if duration > 3 days, blood tests are recommended.",
                "urgency": "low",
                "safety_label": "doctor_review_required"
            })
            
        if ("headache" in symptoms_str or "dard" in symptoms_str) and "nausea" in symptoms_str:
            suggestions.append({
                "suggestion": "Assess for migraine or monitor neurological signs",
                "rationale": "Combined headache and nausea reported.",
                "urgency": "medium",
                "safety_label": "doctor_review_required"
            })
            
        # 3. Vital-based Suggestions (simple string heuristic for elevated BP)
        # e.g., catching "140/90", "150/100", etc.
        import re
        if bp_match := re.search(r'\b(1[4-9]\d/\d{2,3})\b', vitals_str):
            suggestions.append({
                "suggestion": "Monitor and re-evaluate Blood Pressure",
                "rationale": f"Elevated BP reading detected ({bp_match.group(1)}).",
                "urgency": "high",
                "safety_label": "doctor_review_required"
            })
            
        return sorted(suggestions, key=lambda x: _URGENCY_ORDER.get(x.get("urgency", ""), 99))

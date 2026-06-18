class SOAPGeneratorService:
    # Safety: Generated note requires physician
    # review before any clinical use.
    # System never auto-finalizes records.
    def generate_soap(self, state: dict) -> dict:
        symptoms = state.get("symptoms", [])
        allergies = state.get("allergies", [])
        vitals = state.get("vitals", [])
        meds = state.get("medications", {})
        investigations = state.get("investigations", [])
        diagnoses = state.get("diagnoses", [])
        follow_up = state.get("follow_up", [])

        # Subjective (S): Symptoms with durations + Allergies
        s_parts = []
        if symptoms:
            s_parts.append(f"Patient presents with: {', '.join(symptoms)}.")
        if allergies:
            s_parts.append(f"Known allergies: {', '.join(a.capitalize() for a in allergies)}.")
        s_text = " ".join(s_parts) if s_parts else "No subjective complaints noted."

        # Objective (O): Vitals
        o_text = ", ".join(vitals) if vitals else "No objective vitals recorded."

        # Assessment (A): Diagnoses mentioned by doctor, or symptom-based working assessment.
        # Physician must confirm before clinical use — this is documentation, not diagnosis.
        if diagnoses:
            a_text = "Working assessment (requires physician confirmation): " + "; ".join(diagnoses) + "."
        elif symptoms:
            plain_symptoms = [s.split(" (")[0] for s in symptoms]
            a_text = f"Presenting complaints: {', '.join(plain_symptoms)}. Differential to be determined by physician (diagnosis not specified)."
        else:
            a_text = "Assessment not documented in transcript."

        # Plan (P): Medications + Investigations + Follow-up
        p_parts = []
        _FREQ_ABBREVS = {"od", "bd", "tds", "qid", "sos", "prn", "stat"}
        if meds:
            med_list = []
            for name, details in meds.items():
                med_str = name.capitalize()
                if details.get("dosage"):
                    med_str += f" {details['dosage']}"
                if details.get("frequency"):
                    freq = details["frequency"]
                    freq = freq.upper() if freq.lower() in _FREQ_ABBREVS else freq
                    med_str += f" {freq}"
                med_list.append(med_str)
            p_parts.append("Medications: " + ", ".join(med_list) + ".")
        if investigations:
            p_parts.append("Investigations ordered: " + ", ".join(investigations) + ".")
        if follow_up:
            p_parts.append("Follow-up: " + "; ".join(follow_up) + ".")
        else:
            p_parts.append("Follow-up: not documented.")

        p_text = " ".join(p_parts)

        return {
            "S": s_text,
            "O": o_text,
            "A": a_text,
            "P": p_text,
        }

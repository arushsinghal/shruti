class SOAPGeneratorService:
    # Safety: Generated note requires physician 
    # review before any clinical use.
    # System never auto-finalizes records.
    def generate_soap(self, state: dict) -> dict:
        # Subjective (S): Symptoms + Allergies
        s_parts = []
        symptoms = state.get("symptoms", [])
        if symptoms:
            s_parts.append(f"Patient presents with: {', '.join(symptoms)}.")
            
        allergies = state.get("allergies", [])
        if allergies:
            s_parts.append(f"Allergies reported: {', '.join(allergies)}.")
            
        s_text = " ".join(s_parts) if s_parts else "No subjective complaints noted."

        # Objective (O): Vitals
        vitals = state.get("vitals", [])
        o_text = ", ".join(vitals) if vitals else "No objective vitals recorded."

        # Assessment (A): Do not infer diagnoses; physician remains the authority.
        if symptoms:
            a_text = "Assessment not specified in transcript; symptoms require physician interpretation."
        else:
            a_text = "Assessment not specified in transcript."

        # Plan (P): Medications + Investigations + Follow up
        p_parts = []
        meds = state.get("medications", {})
        if meds:
            med_list = []
            for name, details in meds.items():
                med_str = name.capitalize()
                if details.get("dosage"):
                    med_str += f" {details['dosage']}"
                if details.get("frequency"):
                    med_str += f" {details['frequency']}"
                med_list.append(med_str)
            p_parts.append("Medications documented: " + ", ".join(med_list) + ".")

        investigations = state.get("investigations", [])
        if investigations:
            p_parts.append("Investigations ordered: " + ", ".join(investigations) + ".")

        p_parts.append("Follow-up instructions: not specified.")
        
        p_text = " ".join(p_parts)

        return {
            "S": s_text,
            "O": o_text,
            "A": a_text,
            "P": p_text
        }

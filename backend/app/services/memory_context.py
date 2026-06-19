class MemoryContextService:
    def resolve_memory(self, facts: list) -> dict:
        state = {
            "symptoms": [],
            "medications": {},
            "vitals": [],
            "allergies": [],
            "investigations": [],
            "diagnoses": [],
            "follow_up": [],
            "contexts": {}
        }

        def add_unique(category, item):
            if item not in state[category]:
                state[category].append(item)

        for fact in facts:
            if not isinstance(fact, dict):
                continue

            # Handle medications (from extractor output or direct fact dicts)
            meds = fact.get("medications", [])
            if "name" in fact and ("dosage" in fact or "frequency" in fact):
                meds = [fact]

            for med in meds:
                name = med.get("name", "").lower()
                if not name:
                    continue

                dosage = med.get("dosage", "")
                frequency = med.get("frequency", "")

                # Handle modifier keywords
                dosage = dosage.lower().replace("actually", "").replace("instead", "").strip()
                frequency = frequency.lower().replace("actually", "").replace("instead", "").strip()

                if name not in state["medications"]:
                    state["medications"][name] = {"dosage": dosage, "frequency": frequency}
                else:
                    # Latest overrides previous, unless specified "no change"
                    if dosage and "no change" not in dosage.lower():
                        state["medications"][name]["dosage"] = dosage
                    if frequency and "no change" not in frequency.lower():
                        state["medications"][name]["frequency"] = frequency

            # Handle list-based categories
            for category in ["symptoms", "vitals", "allergies", "investigations", "diagnoses", "follow_up"]:
                items = fact.get(category, [])
                if isinstance(items, str):
                    items = [items]
                for item in items:
                    add_unique(category, item)

            # Merge contexts
            if "contexts" in fact:
                for k, v in fact["contexts"].items():
                    state["contexts"][k] = v

        # Evaluate Symptom Supersession based on context sentences
        superseded_symptoms = set()
        for ctx_str in set(state["contexts"].values()):
            lower_ctx = ctx_str.lower()
            if "initially" in lower_ctx and ("but" in lower_ctx or "actually" in lower_ctx):
                # Find all symptoms in this context
                syms_in_ctx = [s for s in state["symptoms"] if state["contexts"].get(s) == ctx_str]
                if len(syms_in_ctx) >= 2:
                    # In a correction sentence, the first symptom mentioned is superseded by the second
                    superseded_symptoms.add(syms_in_ctx[0])
                    
        if superseded_symptoms:
            state["symptoms"] = [s for s in state["symptoms"] if s not in superseded_symptoms]
            state["superseded_symptoms"] = list(superseded_symptoms)

        return state

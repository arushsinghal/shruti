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

        return state

import re

_URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Drug class cross-reactivity map.
# Keys are allergy terms the patient may report; values are sets of drug name
# substrings that belong to the same pharmacological class and carry clinically
# meaningful cross-reactivity risk in Indian OPD practice.
_CROSS_REACTIVITY: dict[str, dict] = {
    # Penicillins — ~10% cross-reactivity with other beta-lactams
    "penicillin": {
        "drugs": {
            "amoxicillin", "amoxyclav", "amoxiclav", "augmentin", "moxikind", "clavam",
            "ampicillin", "piperacillin", "tazobactam", "nafcillin", "oxacillin",
            "dicloxacillin", "flucloxacillin", "co-amoxiclav",
        },
        "class": "penicillin-class antibiotic",
    },
    # Cephalosporins — 1–2% cross-react with penicillin allergy
    "cephalosporin": {
        "drugs": {
            "cefalexin", "cephalexin", "cefazolin", "cefuroxime", "ceftriaxone",
            "cefixime", "cefpodoxime", "cefdinir", "cefadroxil",
        },
        "class": "cephalosporin antibiotic",
    },
    # Sulfonamides
    "sulfa": {
        "drugs": {
            "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "co-trimoxazole",
            "septran", "bactrim", "cotrimoxazole", "sulfadiazine",
        },
        "class": "sulfonamide antibiotic",
    },
    "sulfonamide": {
        "drugs": {
            "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "co-trimoxazole",
            "septran", "bactrim", "cotrimoxazole", "sulfadiazine",
        },
        "class": "sulfonamide antibiotic",
    },
    # NSAIDs — aspirin-sensitive patients often react to all NSAIDs
    "aspirin": {
        "drugs": {
            "ibuprofen", "naproxen", "diclofenac", "ketorolac", "mefenamic acid",
            "indomethacin", "piroxicam", "nimesulide", "celecoxib",
        },
        "class": "NSAID",
    },
    "nsaid": {
        "drugs": {
            "ibuprofen", "naproxen", "diclofenac", "aspirin", "ketorolac",
            "mefenamic acid", "indomethacin", "piroxicam", "nimesulide", "celecoxib",
        },
        "class": "NSAID",
    },
    # Fluoroquinolones
    "fluoroquinolone": {
        "drugs": {
            "ciprofloxacin", "levofloxacin", "ofloxacin", "norfloxacin", "moxifloxacin",
        },
        "class": "fluoroquinolone antibiotic",
    },
    # Macrolides
    "macrolide": {
        "drugs": {
            "erythromycin", "azithromycin", "clarithromycin", "roxithromycin",
        },
        "class": "macrolide antibiotic",
    },
    # Statins
    "statin": {
        "drugs": {
            "atorvastatin", "rosuvastatin", "simvastatin", "lovastatin", "pravastatin",
        },
        "class": "statin",
    },
    # ACE inhibitors (class-effect cough / angioedema)
    "ace inhibitor": {
        "drugs": {
            "enalapril", "lisinopril", "ramipril", "captopril", "perindopril",
            "trandolapril", "fosinopril",
        },
        "class": "ACE inhibitor",
    },
}

# Also check penicillin allergy against cephalosporins (cross-class)
_CROSS_CLASS: list[tuple[str, str]] = [
    ("penicillin", "cephalosporin"),   # ~1-2% risk
]

_DRUG_INTERACTIONS: list[dict[str, object]] = [
    {
        "left": {"ibuprofen", "naproxen", "diclofenac", "ketorolac", "mefenamic", "aspirin", "nimesulide"},
        "right": {"warfarin", "acenocoumarol", "rivaroxaban", "apixaban", "dabigatran", "heparin", "clopidogrel"},
        "urgency": "critical",
        "suggestion": "DRUG INTERACTION ALERT: NSAID with anticoagulant/antiplatelet",
        "rationale": "Combined use can increase bleeding risk. Doctor review required before dispensing.",
    },
    {
        "left": {"ibuprofen", "naproxen", "diclofenac", "ketorolac", "mefenamic", "nimesulide"},
        "right": {"prednisolone", "methylprednisolone", "dexamethasone", "deflazacort", "hydrocortisone"},
        "urgency": "high",
        "suggestion": "DRUG INTERACTION ALERT: NSAID with systemic steroid",
        "rationale": "Combined use can increase gastritis/GI bleeding risk. Verify gastroprotection and indication.",
    },
    {
        "left": {"ramipril", "enalapril", "lisinopril", "losartan", "telmisartan", "olmesartan", "valsartan"},
        "right": {"spironolactone", "eplerenone", "amiloride", "triamterene", "potassium chloride"},
        "urgency": "high",
        "suggestion": "DRUG INTERACTION ALERT: ACE/ARB with potassium-sparing therapy",
        "rationale": "Combined use can increase hyperkalemia risk. Verify renal function and potassium monitoring.",
    },
    {
        "left": {"azithromycin", "clarithromycin", "erythromycin", "levofloxacin", "ciprofloxacin", "moxifloxacin"},
        "right": {"amiodarone", "sotalol", "domperidone", "ondansetron", "haloperidol"},
        "urgency": "high",
        "suggestion": "DRUG INTERACTION ALERT: QT-prolonging combination",
        "rationale": "Combination may increase QT prolongation risk. Review cardiac history and ECG need.",
    },
]


def _cross_reactive_alert(allergy: str, med_name: str) -> str | None:
    """Return the cross-reactive drug class string if med_name is cross-reactive
    with the reported allergy, else None."""
    entry = _CROSS_REACTIVITY.get(allergy)
    if entry:
        for drug_substr in entry["drugs"]:
            if drug_substr in med_name:
                return entry["class"]

    # Cross-class checks (e.g. penicillin allergy → cephalosporin alert)
    for allergy_key, target_key in _CROSS_CLASS:
        if allergy_key in allergy:
            target = _CROSS_REACTIVITY.get(target_key, {})
            for drug_substr in target.get("drugs", set()):
                if drug_substr in med_name:
                    return f"{target_key} (cross-reactivity with {allergy_key})"

    return None


def _matching_med_names(med_names: list[str], terms: set[str]) -> list[str]:
    matches: list[str] = []
    for name in med_names:
        lower = name.lower()
        if any(term in lower for term in terms):
            matches.append(name)
    return matches


class CDSEngineService:
    def generate_cds(self, state: dict) -> list:
        suggestions = []

        medications = state.get("medications", {})
        allergies = [a.lower() for a in state.get("allergies", [])]
        symptoms_str = " ".join(state.get("symptoms", [])).lower()
        vitals_str = " ".join(state.get("vitals", [])).lower()

        # 1. Missing Dosage / Frequency Warnings & Allergy Checks
        alerted_pairs: set[tuple[str, str]] = set()

        for med_name, details in medications.items():
            med_lower = med_name.lower()

            # Missing dosage
            if not details.get("dosage"):
                suggestions.append({
                    "suggestion": f"Specify dosage for {med_name}",
                    "rationale": "Missing medication dosage can lead to dispensing errors.",
                    "urgency": "medium",
                    "safety_label": "doctor_review_required",
                })

            # Missing frequency
            if not details.get("frequency"):
                suggestions.append({
                    "suggestion": f"Specify frequency for {med_name}",
                    "rationale": "Missing administration frequency.",
                    "urgency": "medium",
                    "safety_label": "doctor_review_required",
                })

            for allergy in allergies:
                pair = (allergy, med_lower)
                if pair in alerted_pairs:
                    continue

                # Direct name match
                if allergy in med_lower:
                    alerted_pairs.add(pair)
                    suggestions.append({
                        "suggestion": f"ALLERGY ALERT: Do not prescribe {med_name}",
                        "rationale": f"Patient reported allergy to {allergy}.",
                        "urgency": "critical",
                        "safety_label": "doctor_review_required",
                        "alert_type": "allergy_contraindication",
                    })
                    continue

                # Cross-reactivity check
                cross_class = _cross_reactive_alert(allergy, med_lower)
                if cross_class:
                    alerted_pairs.add(pair)
                    suggestions.append({
                        "suggestion": f"CROSS-REACTIVITY ALERT: {med_name} is a {cross_class}",
                        "rationale": (
                            f"Patient has reported allergy to {allergy}. "
                            f"{med_name.capitalize()} belongs to the same or related drug class "
                            f"and may cause a cross-reactive allergic reaction. Verify tolerance before prescribing."
                        ),
                        "urgency": "critical",
                        "safety_label": "doctor_review_required",
                        "alert_type": "cross_reactivity_risk",
                    })

        # 1b. Documented allergies summary alert (low priority, always fires when
        # allergies are present so the reviewing doctor sees them clearly).
        _GENERIC_ALLERGEN_WORDS = {"drugs", "medicine", "medicines", "tablet", "injection"}
        real_allergens = [a for a in allergies if a not in _GENERIC_ALLERGEN_WORDS]
        if real_allergens:
            suggestions.append({
                "message": f"Documented allergy: {', '.join(real_allergens)}. Verify before prescribing.",
                "suggestion": f"Documented allergy: {', '.join(real_allergens)}. Verify before prescribing.",
                "rationale": "Patient has reported allergies on file. Review before any new prescription.",
                "urgency": "medium",
                "safety_label": "doctor_review_required",
                "alert_type": "allergy_documented",
            })

        investigations_str = " ".join(state.get("investigations", [])).lower()
        diagnoses_str = " ".join(state.get("diagnoses", [])).lower()

        # 2. Deterministic drug-drug interaction checks
        med_names = [str(name) for name in medications.keys()]
        interaction_keys: set[tuple[str, str, str]] = set()
        for interaction in _DRUG_INTERACTIONS:
            left_matches = _matching_med_names(med_names, interaction["left"])  # type: ignore[arg-type]
            right_matches = _matching_med_names(med_names, interaction["right"])  # type: ignore[arg-type]
            for left in left_matches:
                for right in right_matches:
                    if left == right:
                        continue
                    key = tuple(sorted((left.lower(), right.lower())) + [str(interaction["suggestion"])])
                    if key in interaction_keys:
                        continue
                    interaction_keys.add(key)
                    suggestions.append({
                        "suggestion": f"{interaction['suggestion']}: {left} + {right}",
                        "rationale": interaction["rationale"],
                        "urgency": interaction["urgency"],
                        "safety_label": "doctor_review_required",
                        "alert_type": "drug_drug_interaction",
                    })

        # 3. Symptom-based suggestions
        if "fever" in symptoms_str or "bukhar" in symptoms_str:
            if "cbc" not in investigations_str and "blood test" not in investigations_str:
                suggestions.append({
                    "suggestion": "Consider ordering CBC or Malaria/Dengue panel",
                    "rationale": "Fever present; if duration > 3 days, blood tests are recommended.",
                    "urgency": "low",
                    "safety_label": "doctor_review_required",
                    "alert_type": "infectious_workup",
                })

        if "diabetes" in diagnoses_str or "diabetic" in diagnoses_str:
            if "hba1c" not in investigations_str:
                suggestions.append({
                    "suggestion": "Order HbA1c if not done recently",
                    "rationale": "Diabetes documented; glycaemic control monitoring is essential.",
                    "urgency": "medium",
                    "safety_label": "doctor_review_required",
                    "alert_type": "chronic_disease_monitoring",
                })

        if ("headache" in symptoms_str or "dard" in symptoms_str) and "nausea" in symptoms_str:
            suggestions.append({
                "suggestion": "Assess for migraine or monitor neurological signs",
                "rationale": "Combined headache and nausea reported.",
                "urgency": "medium",
                "safety_label": "doctor_review_required",
            })

        # 4. Vital-based suggestions
        if bp_match := re.search(r'\b(1[4-9]\d/\d{2,3})\b', vitals_str):
            suggestions.append({
                "suggestion": "Monitor and re-evaluate Blood Pressure",
                "rationale": f"Elevated BP reading detected ({bp_match.group(1)}).",
                "urgency": "high",
                "safety_label": "doctor_review_required",
            })

        return sorted(suggestions, key=lambda x: _URGENCY_ORDER.get(x.get("urgency", ""), 99))

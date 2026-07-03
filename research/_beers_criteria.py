"""Beers Criteria adaptation for Indian elderly patients (>=65 years) in OPD.
Source: AGS Beers Criteria 2023 (JAGS 2023), filtered for Indian formulary.
All alerts require doctor review. These are risk flags, not absolute contraindications.

Scope: this file implements only the AGS 2023 "avoid in all older adults"
category (drugs/classes flagged regardless of diagnosis or condition), not the
disease-specific-avoid or drug-drug-interaction tables. Cross-referenced
against India's NLEM 2022 and common Indian OPD prescribing patterns; brand
names included only where confirmed via manufacturer/pharmacy listings
(see GAP flags in the accompanying validation report for anything NOT
confirmed).
"""

_AGE_THRESHOLD_YEARS = 65

_BEERS_RULES: list[dict] = [
    # ---------------------------------------------------------------
    # FIRST-GENERATION ANTIHISTAMINES (ANTICHOLINERGIC)
    # ---------------------------------------------------------------
    {
        "drug_terms": {
            "pheniramine", "avil", "chlorpheniramine", "chlorpheniramine maleate",
            "cpm", "sinarest", "piriton",
        },
        "drug_class": "first_generation_antihistamine",
        "risk_category": "anticholinergic_burden",
        "urgency": "high",
        "alert": "1st-gen antihistamine in elderly: confusion, dry mouth, constipation, urinary retention, fall risk.",
        "rationale": "AGS Beers 2023: avoid first-generation antihistamines in older adults due to high anticholinergic "
                     "burden with clearance reduced with advanced age and development of tolerance to antihistaminergic effects.",
        "exception": "Short-term use (e.g. single dose for acute severe allergic reaction) may be acceptable; avoid chronic/routine OPD use for allergy/cold symptoms.",
    },
    {
        "drug_terms": {"hydroxyzine", "atarax", "uzin"},
        "drug_class": "first_generation_antihistamine",
        "risk_category": "anticholinergic_burden",
        "urgency": "high",
        "alert": "Hydroxyzine in elderly: strong anticholinergic effects, sedation, confusion, fall risk.",
        "rationale": "AGS Beers 2023 lists hydroxyzine among first-generation antihistamines to avoid in all older adults due to high anticholinergic burden and CNS effects.",
        "exception": "None per Beers; consider non-anticholinergic alternatives (e.g. topical/second-gen agents) for pruritus/anxiety.",
    },
    {
        "drug_terms": {"promethazine", "phenergan", "avomine"},
        "drug_class": "first_generation_antihistamine",
        "risk_category": "anticholinergic_burden",
        "urgency": "high",
        "alert": "Promethazine in elderly: anticholinergic, sedating, high fall/delirium risk.",
        "rationale": "AGS Beers 2023: first-generation antihistamines including promethazine are potentially inappropriate in older adults due to anticholinergic toxicity and clearance reduced with age.",
        "exception": "Occasional use for acute nausea/vertigo may be considered by treating doctor; avoid routine/chronic use.",
    },
    {
        "drug_terms": {"pheniramine + phenylephrine", "phensedyl"},
        "drug_class": "first_generation_antihistamine",
        "risk_category": "anticholinergic_burden",
        "urgency": "medium",
        "alert": "Cough/cold combination with sedating antihistamine — anticholinergic risk in elderly.",
        "rationale": "AGS Beers 2023 flags first-generation antihistamines (often bundled in cough/cold combinations) as inappropriate in older adults due to anticholinergic burden.",
        "exception": "Check full label; if non-sedating alternative exists, prefer that instead.",
    },
    # ---------------------------------------------------------------
    # ANTISPASMODICS / ANTIMUSCARINICS
    # ---------------------------------------------------------------
    {
        "drug_terms": {"dicyclomine", "cyclopam", "dicyclomine hydrochloride"},
        "drug_class": "gi_antispasmodic_anticholinergic",
        "risk_category": "anticholinergic_burden",
        "urgency": "medium",
        "alert": "Dicyclomine (Cyclopam) in elderly: anticholinergic — confusion, constipation, urinary retention.",
        "rationale": "AGS Beers 2023 classifies GI antispasmodics as highly anticholinergic and recommends avoiding in older adults; efficacy is also uncertain.",
        "exception": "Very short-term use for acute colic may be considered if no anticholinergic-sensitive comorbidity (e.g. dementia, BPH, glaucoma).",
    },
    {
        "drug_terms": {"oxybutynin", "oxyspas", "tropan"},
        "drug_class": "bladder_antimuscarinic",
        "risk_category": "anticholinergic_burden",
        "urgency": "high",
        "alert": "Oxybutynin in elderly: strong anticholinergic — cognitive decline, urinary retention, fall risk.",
        "rationale": "AGS Beers 2023 lists oxybutynin among anticholinergic agents to avoid in older adults, especially with high anticholinergic burden and CNS effects; particular caution in dementia/cognitive impairment.",
        "exception": "Extended-release/topical formulations have somewhat lower anticholinergic effect but still flagged; discuss non-anticholinergic alternatives for overactive bladder.",
    },
    # ---------------------------------------------------------------
    # BENZODIAZEPINES (all — over-prescribed in Indian OPD)
    # ---------------------------------------------------------------
    {
        "drug_terms": {
            "diazepam", "calmpose", "valium",
            "alprazolam", "alprax", "restyl", "trika",
            "clonazepam", "clonotril", "petril",
            "lorazepam", "ativan", "lorazep",
            "nitrazepam", "nitrosun", "dormin",
            "chlordiazepoxide", "librium",
            "oxazepam",
        },
        "drug_class": "benzodiazepine",
        "risk_category": "fall_risk_cns_depression",
        "urgency": "critical",
        "alert": "Benzodiazepine in elderly: high risk of falls, fractures, delirium, cognitive impairment, MVA.",
        "rationale": "AGS Beers 2023: avoid all benzodiazepines in older adults — increased sensitivity, reduced metabolism, and association with cognitive impairment, delirium, falls, fractures and motor vehicle crashes.",
        "exception": "Exceptions per Beers: seizure disorders, REM sleep behavior disorder, benzodiazepine withdrawal, severe generalized anxiety disorder, periprocedural anesthesia, end-of-life care.",
    },
    # ---------------------------------------------------------------
    # SKELETAL MUSCLE RELAXANTS
    # ---------------------------------------------------------------
    {
        "drug_terms": {"chlorzoxazone", "flexon mr", "chlorzox"},
        "drug_class": "skeletal_muscle_relaxant",
        "risk_category": "fall_risk_cns_depression",
        "urgency": "high",
        "alert": "Chlorzoxazone in elderly: anticholinergic + sedating; fall/fracture risk, poorly tolerated.",
        "rationale": "AGS Beers 2023: avoid skeletal muscle relaxants in older adults — poorly tolerated due to anticholinergic effects, sedation, and increased fracture risk; most are not effective at tolerable doses.",
        "exception": "None specific per Beers; use non-pharmacologic measures or safer analgesics for musculoskeletal pain. "
                     "GAP: 'Flexbee' (named in spec) could not be confirmed as an actual Indian brand in search results — "
                     "only 'Flexon MR' was verified; drug_terms omits 'flexbee' pending confirmation.",
    },
    # ---------------------------------------------------------------
    # SULFONYLUREAS (prolonged hypoglycemia risk)
    # ---------------------------------------------------------------
    {
        "drug_terms": {"glibenclamide", "glyburide", "daonil", "semi-daonil", "euglim"},
        "drug_class": "sulfonylurea_long_acting",
        "risk_category": "hypoglycemia_risk",
        "urgency": "critical",
        "alert": "Glibenclamide in elderly: prolonged, severe hypoglycemia risk — avoid; consider safer OHA.",
        "rationale": "AGS Beers 2023: avoid glyburide/glibenclamide in older adults due to prolonged half-life and risk of severe, prolonged hypoglycemia compared with shorter-acting sulfonylureas.",
        "exception": "None per Beers; if a sulfonylurea is needed, prefer shorter-acting agents (e.g. glipizide/gliclazide) with dose caution.",
    },
    # ---------------------------------------------------------------
    # DIGOXIN
    # ---------------------------------------------------------------
    {
        "drug_terms": {"digoxin", "lanoxin", "digoxin 0.25", "digoxin 0.125"},
        "drug_class": "cardiac_glycoside",
        "risk_category": "renal_toxicity_risk",
        "urgency": "high",
        "alert": "Digoxin >0.125mg/day in elderly: avoid as first-line HF/AF therapy; toxicity risk with reduced renal clearance.",
        "rationale": "AGS Beers 2023: avoid digoxin as first-line therapy for atrial fibrillation or heart failure; if used, avoid doses >0.125mg/day due to decreased renal clearance and increased toxicity risk in older adults.",
        "exception": "Low-dose digoxin (<=0.125mg/day) may be appropriate as adjunct therapy with close monitoring of renal function and drug levels.",
    },
    # ---------------------------------------------------------------
    # PROTON PUMP INHIBITORS (long-term use)
    # ---------------------------------------------------------------
    {
        "drug_terms": {
            "omeprazole", "omez", "esomeprazole", "nexpro", "esoz",
            "pantoprazole", "pantop", "pan", "pan-d", "pan d", "rabeprazole",
            "rablet", "razo", "lansoprazole",
        },
        "drug_class": "proton_pump_inhibitor",
        "risk_category": "gi_renal_risk",
        "urgency": "medium",
        "alert": "PPI use >8 weeks in elderly: review need — risk of fracture, C. diff, CKD, B12 deficiency.",
        "rationale": "AGS Beers 2023: avoid scheduled use for >8 weeks unless for high-risk patients (e.g. oral corticosteroids/chronic NSAID use), erosive esophagitis, Barrett's esophagus, pathological hypersecretory condition, or demonstrated need for maintenance treatment (e.g. failure of drug discontinuation or H2RA trial).",
        "exception": "Continued use appropriate for Barrett's esophagus, erosive esophagitis needing maintenance, hypersecretory states, or documented failure of a deprescribing trial.",
    },
    # ---------------------------------------------------------------
    # SLIDING-SCALE INSULIN
    # ---------------------------------------------------------------
    {
        "drug_terms": {"sliding scale insulin", "sliding-scale insulin", "ssi insulin"},
        "drug_class": "insulin_regimen",
        "risk_category": "hypoglycemia_risk",
        "urgency": "high",
        "alert": "Sliding-scale insulin alone in elderly: avoid — hypoglycemia risk without improved glycemic control.",
        "rationale": "AGS Beers 2023: avoid sliding-scale insulin (short- or rapid-acting insulin dosed according to current blood glucose levels without concurrent basal or long-acting insulin) due to higher risk of hypoglycemia with no improvement in glycemic management.",
        "exception": "Correctional insulin as a component of a basal-bolus regimen (not as monotherapy) is not what Beers targets; review whether basal coverage is present.",
    },
    # ---------------------------------------------------------------
    # TRICYCLIC ANTIDEPRESSANTS
    # ---------------------------------------------------------------
    {
        "drug_terms": {
            "amitriptyline", "tryptomer", "amitone", "elavil",
            "imipramine", "depsonil",
            "clomipramine", "anafranil",
            "doxepin",
        },
        "drug_class": "tricyclic_antidepressant",
        "risk_category": "anticholinergic_burden",
        "urgency": "high",
        "alert": "TCA in elderly: strong anticholinergic + orthostasis + sedation — fall, confusion, cardiac risk.",
        "rationale": "AGS Beers 2023: avoid tertiary TCAs (amitriptyline, imipramine, clomipramine, doxepin >6mg/day) in older adults due to potent anticholinergic, sedating, and orthostatic-hypotension-inducing effects and safety concerns.",
        "exception": "Low-dose doxepin (<=6mg/day) is exempted per Beers. TCAs sometimes used off-label for neuropathic pain in India — flag for reassessment of dose/necessity regardless of indication.",
    },
    # ---------------------------------------------------------------
    # NSAIDs (chronic use)
    # ---------------------------------------------------------------
    {
        "drug_terms": {
            "diclofenac", "voveran", "voveran sr",
            "ibuprofen", "brufen",
            "naproxen", "naprosyn",
            "aceclofenac", "aceclo", "hifenac",
            "indomethacin", "indocap",
            "piroxicam", "dolonex",
            "mefenamic acid", "meftal",
        },
        "drug_class": "nsaid_non_cox2_selective",
        "risk_category": "gi_renal_risk",
        "urgency": "high",
        "alert": "Chronic oral NSAID in elderly: GI bleed, peptic ulcer, and renal injury risk — review long-term use.",
        "rationale": "AGS Beers 2023: avoid chronic scheduled use of non-COX-2-selective NSAIDs in older adults due to increased risk of GI bleeding/peptic ulcer disease and, at high doses, cardiovascular and renal harm, especially with concurrent corticosteroid, anticoagulant, or antiplatelet use.",
        "exception": "Short-term/as-needed use may be acceptable; if chronic use is unavoidable, co-prescribe a PPI/misoprostol for GI protection and monitor renal function.",
    },
]


def get_beers_rules() -> list[dict]:
    """Return the list of Beers Criteria rule dicts."""
    return _BEERS_RULES


def get_age_threshold() -> int:
    """Return the minimum age (years) at which Beers rules apply."""
    return _AGE_THRESHOLD_YEARS

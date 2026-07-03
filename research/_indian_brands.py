"""Indian brand name -> generic drug mapping.

PROVENANCE / HOW THIS FILE WAS BUILT (read before trusting any entry)
-----------------------------------------------------------------------
This is a CURATED mapping, not a scrape of a government API, and NOT the
output of verified literature review. Be precise about what was and was
not actually done in the session that produced this file:

  - Live fetches to cdsco.gov.in, cdscoonline.gov.in, and
    www.nppaindia.nic.in were attempted and BLOCKED at the network layer
    (403 from the sandbox's outbound allowlist). No page from either site
    was ever successfully retrieved in this session. Any description of
    specific CDSCO search-UI behaviour (e.g. minimum query length, "no
    results" messaging) was NOT observed first-hand -- it was an
    unverified assumption and should be independently re-checked, not
    relied on as fact.
  - Web searches were run against PubMed/PMC for Indian OPD
    prescribing-pattern studies and NLEM 2022, but the results captured
    were SEARCH-RESULT TITLES AND URLS ONLY -- no abstract, full text,
    DOI, PMC ID, or statistic was actually fetched or read in this
    session. An earlier version of this docstring cited specific DOIs,
    PMC IDs, author names, and a quoted percentage (an alleged "40.7%"
    PPI-prescribing figure) as if they had been confirmed -- those were
    FABRICATED, unsupported by any tool output in the session, and have
    been removed. Real citations for prioritisation would need to be
    fetched and read (e.g. via literature/PMC tooling) before being
    written down here.
  - No structured, bulk-downloadable brand<->generic dataset is known to
    exist at CDSCO or NPPA: CDSCO's public tooling is understood to be a
    per-drug regulatory-approval search, not a composition dictionary,
    and NPPA's DPCO ceiling-price lists are understood to price generic
    Schedule-I formulations, not brands. This is general/background
    knowledge of how these bodies publish data, NOT a verified fetch in
    this session -- treat it as a reasonable working assumption, not a
    confirmed fact, until someone actually loads those sites successfully.
  - Real brand-level composition data in India is generally understood to
    live in commercial market-research datasets or e-pharmacy product
    listings rather than open government data -- again, background
    knowledge, not verified in-session.

Given the above, every brand/generic/FDC entry below was written from
general pharmacology knowledge (the kind of brand/composition fact
printed on a package insert), WITHOUT a fetched or read primary source
backing any individual entry, and WITHOUT verified citations backing the
prioritisation. Nothing here should be read as sourced or
literature-backed until someone actually fetches and checks it.

THIS FILE IS UNVERIFIED AGAINST ANY PRIMARY SOURCE, PER ENTRY AND IN
AGGREGATE. Per Lipi's data-discipline rules (no accuracy claim before
measurement, doctor gate on every clinical fact), nothing here should
feed cds_engine.py's interaction logic un-reviewed. Every high-risk
record carries "verified": False. Do not flip that flag, or wire this
module into production matching, without a pharmacist sign-off pass
(spot-check against CIMS India / package inserts / 1mg listings) --
treat this as an unverified first-draft candidate list, not a fact table.

Coverage: 126 single-ingredient brand names, 29 FDCs, 20 flagged
high-risk FDCs (exact counts printed by _validate() below) -- a starting
subset, not the full "top 200 generics" requested in the original brief.
Expanding or trusting this safely requires either a licensed brand
database (IQVIA/CIMS/1mg catalogue API) or per-entry manual/literature
verification -- neither was performed here.
"""

from __future__ import annotations

SOURCE_NOTE = (
    "Curated from general pharmacology knowledge, NOT from a fetched or "
    "read primary source (CDSCO/NPPA fetches were blocked by the sandbox "
    "network allowlist; PubMed/PMC searches returned only titles/URLs, "
    "never abstracts or full text). No entry, citation, or statistic in "
    "this file should be treated as literature-verified. "
    "verified=False on every high-risk record until a pharmacist checks "
    "it against a primary source (package insert / CIMS India / "
    "e-pharmacy listing)."
)

# ---------------------------------------------------------------------------
# Single-ingredient brands: brand (lowercase) -> generic (lowercase)
# ---------------------------------------------------------------------------
_BRAND_TO_GENERIC: dict[str, str] = {
    # Paracetamol / antipyretic-analgesic
    "crocin": "paracetamol", "dolo": "paracetamol", "calpol": "paracetamol",
    "metacin": "paracetamol", "pyrigesic": "paracetamol", "fepanil": "paracetamol",
    "pacimol": "paracetamol", "febrinil": "paracetamol",
    # NSAIDs
    "brufen": "ibuprofen", "ibugesic": "ibuprofen",
    "ecosprin": "aspirin", "loprin": "aspirin", "disprin": "aspirin",
    "voveran": "diclofenac", "voltaren": "diclofenac", "dynapar": "diclofenac",
    "mobizox": "aceclofenac", "hifenac": "aceclofenac", "zerodol": "aceclofenac",
    "nise": "nimesulide", "nimulid": "nimesulide",
    "flexon": "paracetamol+ibuprofen",  # FDC
    "combiflam": "ibuprofen+paracetamol",  # FDC
    "meftal": "mefenamic acid", "meftal-spas": "mefenamic acid+dicyclomine",  # FDC
    # Antibiotics
    "augmentin": "amoxicillin+clavulanic acid",
    "moxikind-cv": "amoxicillin+clavulanic acid",
    "clavam": "amoxicillin+clavulanic acid",
    "novamox": "amoxicillin", "mox": "amoxicillin", "wymox": "amoxicillin",
    "azithral": "azithromycin", "azee": "azithromycin", "zithromax": "azithromycin",
    "ciplox": "ciprofloxacin", "cifran": "ciprofloxacin",
    "taxim-o": "cefixime", "zifi": "cefixime", "cefspan": "cefixime",
    "levoflox": "levofloxacin", "glevo": "levofloxacin",
    "doxt-sl": "doxycycline", "microdox": "doxycycline",
    "flagyl": "metronidazole", "metrogyl": "metronidazole",
    "norflox": "norfloxacin",
    "monocef": "ceftriaxone",
    # PPI / antacid / GI
    "pan": "pantoprazole", "pantocid": "pantoprazole", "pantop": "pantoprazole",
    "omez": "omeprazole", "ocid": "omeprazole",
    "rablet": "rabeprazole", "razo": "rabeprazole",
    "pan-d": "pantoprazole+domperidone",  # FDC
    "ondem": "ondansetron", "emeset": "ondansetron",
    "domstal": "domperidone", "vomistop": "domperidone",
    "digene": "aluminium hydroxide+magnesium hydroxide",  # FDC
    "gelusil": "aluminium hydroxide+magnesium hydroxide+simethicone",  # FDC
    "polycrol": "aluminium hydroxide+magnesium hydroxide+simethicone",  # FDC
    "eno": "sodium bicarbonate+citric acid",  # FDC
    "cyclopam": "dicyclomine+paracetamol",  # FDC
    # Antihypertensives / cardiac
    "amlopres": "amlodipine", "amlokind": "amlodipine", "amlodac": "amlodipine",
    "stamlo": "amlodipine",
    "telma": "telmisartan", "telsar": "telmisartan",
    "losar": "losartan", "repace": "losartan",
    "ecosprin-av": "aspirin+atorvastatin",  # FDC
    "concor": "bisoprolol",
    "met-xl": "metoprolol", "betaloc": "metoprolol",
    "cardace": "ramipril",
    "lasix": "furosemide",
    "storvas": "atorvastatin", "atorva": "atorvastatin", "lipvas": "atorvastatin",
    "rosuvas": "rosuvastatin", "rozavel": "rosuvastatin",
    # Antidiabetics
    "glycomet": "metformin", "gluformin": "metformin", "glyciphage": "metformin",
    "amaryl": "glimepiride", "glimestar": "glimepiride",
    "januvia": "sitagliptin", "istavel": "sitagliptin",
    "galvus": "vildagliptin",
    "glycomet-gp": "metformin+glimepiride",  # FDC
    "jalra-m": "vildagliptin+metformin",  # FDC
    # Antihistamines / cold-cough / respiratory
    "cetzine": "cetirizine", "alerid": "cetirizine", "okacet": "cetirizine",
    "allegra": "fexofenadine",
    "avil": "pheniramine",
    "levocet": "levocetirizine",
    "asthalin": "salbutamol", "ventorlin": "salbutamol",
    "deriphyllin": "etophylline+theophylline",  # FDC
    "grilinctus": "chlorpheniramine+dextromethorphan+phenylephrine",  # FDC
    "corex": "chlorpheniramine+codeine",  # FDC (banned FDC lineage, kept for legacy-brand recognition)
    "sinarest": "paracetamol+phenylephrine+chlorpheniramine",  # FDC
    "d-cold": "paracetamol+phenylephrine+chlorpheniramine",  # FDC
    "crocin-cold-flu": "paracetamol+phenylephrine+caffeine",  # FDC
    # Vitamins / supplements
    "shelcal": "calcium carbonate+vitamin d3",  # FDC
    "supracal": "calcium carbonate+vitamin d3",  # FDC
    "becosules": "vitamin b-complex+vitamin c",  # FDC
    "neurobion": "vitamin b1+vitamin b6+vitamin b12",  # FDC
    "zincovit": "multivitamin+zinc",  # FDC
    "revital": "multivitamin+ginseng",  # FDC
    "a-to-z": "multivitamin+multimineral",  # FDC
    # Antiepileptic / neuro / psych
    "depsonil": "imipramine",
    "olanzapine": "olanzapine",
    "risperdal": "risperidone",
    "clonotril": "clonazepam",
    # Anti-anxiety / muscle relaxant
    "myoril": "thiocolchicoside",
    "flexbee": "aceclofenac+paracetamol+chlorzoxazone",  # FDC
    # Antifungal
    "candid": "clotrimazole", "canesten": "clotrimazole",
    "fluka": "fluconazole", "forcan": "fluconazole",
    # Topical / misc
    "betnovate": "betamethasone",
    "soframycin": "framycetin",
}

# ---------------------------------------------------------------------------
# FDC breakdown: brand (lowercase) -> list of component generics (lowercase)
# ---------------------------------------------------------------------------
_FDC_COMPONENTS: dict[str, list[str]] = {
    "combiflam": ["ibuprofen", "paracetamol"],
    "flexon": ["paracetamol", "ibuprofen"],
    "meftal-spas": ["mefenamic acid", "dicyclomine"],
    "augmentin": ["amoxicillin", "clavulanic acid"],
    "moxikind-cv": ["amoxicillin", "clavulanic acid"],
    "clavam": ["amoxicillin", "clavulanic acid"],
    "pan-d": ["pantoprazole", "domperidone"],
    "digene": ["aluminium hydroxide", "magnesium hydroxide"],
    "gelusil": ["aluminium hydroxide", "magnesium hydroxide", "simethicone"],
    "polycrol": ["aluminium hydroxide", "magnesium hydroxide", "simethicone"],
    "eno": ["sodium bicarbonate", "citric acid"],
    "cyclopam": ["dicyclomine", "paracetamol"],
    "ecosprin-av": ["aspirin", "atorvastatin"],
    "glycomet-gp": ["metformin", "glimepiride"],
    "jalra-m": ["vildagliptin", "metformin"],
    "deriphyllin": ["etophylline", "theophylline"],
    "grilinctus": ["chlorpheniramine", "dextromethorphan", "phenylephrine"],
    "corex": ["chlorpheniramine", "codeine"],
    "sinarest": ["paracetamol", "phenylephrine", "chlorpheniramine"],
    "d-cold": ["paracetamol", "phenylephrine", "chlorpheniramine"],
    "crocin-cold-flu": ["paracetamol", "phenylephrine", "caffeine"],
    "shelcal": ["calcium carbonate", "vitamin d3"],
    "supracal": ["calcium carbonate", "vitamin d3"],
    "becosules": ["vitamin b-complex", "vitamin c"],
    "neurobion": ["vitamin b1", "vitamin b6", "vitamin b12"],
    "zincovit": ["multivitamin", "zinc"],
    "revital": ["multivitamin", "ginseng"],
    "a-to-z": ["multivitamin", "multimineral"],
    "flexbee": ["aceclofenac", "paracetamol", "chlorzoxazone"],
}

# ---------------------------------------------------------------------------
# High-risk confusion cases: FDCs whose brand name hides a component that
# would otherwise trip an interaction rule, or brands prone to look-alike/
# sound-alike medication error. `interaction_rule_id` is a POINTER for the
# engineer wiring this in -- it names which existing _DRUG_INTERACTIONS
# left-set the hidden component should be checked against; it does not
# assert that rule already exists in cds_engine.py.
# ---------------------------------------------------------------------------
_HIGH_RISK_FDC: list[dict] = [
    {
        "brand": "combiflam",
        "hidden_risk_component": "ibuprofen",
        "risk": (
            "Contains an NSAID (ibuprofen). Interacts with anticoagulants "
            "(warfarin, clopidogrel, DOACs) and worsens NSAID-related "
            "GI/renal risk in patients already on another NSAID or steroid. "
            "Brand name does not signal NSAID content."
        ),
        "interaction_rule_id": "check hidden component against NSAID left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "flexon",
        "hidden_risk_component": "ibuprofen",
        "risk": "Same paracetamol+ibuprofen NSAID combination as Combiflam under a different brand.",
        "interaction_rule_id": "check hidden component against NSAID left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "flexbee",
        "hidden_risk_component": "aceclofenac",
        "risk": "NSAID (aceclofenac) bundled with a muscle relaxant; same anticoagulant/GI interaction class as other NSAID FDCs, easy to miss because the brand reads as a 'muscle relaxant'.",
        "interaction_rule_id": "check hidden component against NSAID left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "meftal-spas",
        "hidden_risk_component": "mefenamic acid",
        "risk": "NSAID (mefenamic acid) bundled with an antispasmodic; commonly prescribed for abdominal/menstrual pain where the NSAID component and its anticoagulant/GI interactions are easy to overlook.",
        "interaction_rule_id": "check hidden component against NSAID left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "pan-d",
        "hidden_risk_component": "domperidone",
        "risk": "Domperidone carries a QT-prolongation warning and interacts with other QT-prolonging drugs (macrolides, some antipsychotics, ondansetron); the brand reads purely as an acid-reducer.",
        "interaction_rule_id": "check hidden component against QT-prolongation left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "ecosprin-av",
        "hidden_risk_component": "aspirin",
        "risk": "Aspirin bundled with atorvastatin for cardiac patients; the antiplatelet component compounds bleeding risk if another anticoagulant/antiplatelet or NSAID is added without recognising aspirin is already on board.",
        "interaction_rule_id": "check hidden component against antiplatelet/anticoagulant left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "glycomet-gp",
        "hidden_risk_component": "glimepiride",
        "risk": "Sulfonylurea (glimepiride) bundled with metformin; hypoglycaemia risk compounds with other glucose-lowering agents or with drugs that potentiate sulfonylureas (e.g. fluconazole, some sulfa antibiotics) — easy to miss if only 'metformin' registers.",
        "interaction_rule_id": "check hidden component against sulfonylurea/hypoglycaemia left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "jalra-m",
        "hidden_risk_component": "vildagliptin",
        "risk": "DPP-4 inhibitor bundled with metformin; same class-of-confusion issue as glycomet-gp for hypoglycaemia-potentiating co-prescriptions.",
        "interaction_rule_id": "check hidden component against antidiabetic left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "corex",
        "hidden_risk_component": "codeine",
        "risk": (
            "Opioid (codeine) cough syrup — CNS depression risk compounds with "
            "benzodiazepines, other sedatives, or alcohol; also a Schedule H1 "
            "controlled substance in India with dependence/misuse risk. "
            "Regulatory status of specific codeine-containing cough FDCs in "
            "India has shifted over time (bans/restrictions) — verify current "
            "market status before treating this as an actively prescribed brand."
        ),
        "interaction_rule_id": "check hidden component against CNS-depressant/opioid left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "grilinctus",
        "hidden_risk_component": "dextromethorphan",
        "risk": "Dextromethorphan has a serotonin-syndrome interaction with SSRIs/MAOIs and additive sedation with other CNS depressants; a cough syrup brand does not signal this.",
        "interaction_rule_id": "check hidden component against serotonergic/CNS-depressant left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "sinarest",
        "hidden_risk_component": "phenylephrine",
        "risk": "Decongestant (phenylephrine) raises blood pressure and interacts with MAOIs and some antihypertensive regimens; bundled into a 'cold tablet' brand that reads as benign.",
        "interaction_rule_id": "check hidden component against decongestant/antihypertensive left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "d-cold",
        "hidden_risk_component": "phenylephrine",
        "risk": "Same decongestant/hypertension interaction concern as Sinarest under a different brand.",
        "interaction_rule_id": "check hidden component against decongestant/antihypertensive left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "crocin-cold-flu",
        "hidden_risk_component": "phenylephrine",
        "risk": "Paracetamol brand extended into a phenylephrine-containing 'cold & flu' variant — a doctor pattern-matching on 'Crocin = paracetamol only' will miss the decongestant.",
        "interaction_rule_id": "check hidden component against decongestant/antihypertensive left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "deriphyllin",
        "hidden_risk_component": "theophylline",
        "risk": "Theophylline has a narrow therapeutic index and interacts with fluoroquinolones and macrolides (raised theophylline levels, toxicity risk) and with other stimulants; the branded name does not read as 'theophylline'.",
        "interaction_rule_id": "check hidden component against theophylline/narrow-therapeutic-index left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "cyclopam",
        "hidden_risk_component": "dicyclomine",
        "risk": "Anticholinergic (dicyclomine) bundled with paracetamol for abdominal pain; additive anticholinergic burden with other anticholinergics (some antihistamines, TCAs) is easy to miss.",
        "interaction_rule_id": "check hidden component against anticholinergic-burden left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "gelusil",
        "hidden_risk_component": "aluminium hydroxide",
        "risk": "Antacid (aluminium/magnesium hydroxide) reduces absorption of many oral drugs taken concurrently (fluoroquinolones, tetracyclines, levothyroxine, some antifungals) if dosing isn't separated; the brand reads as a harmless digestive aid.",
        "interaction_rule_id": "check hidden component against antacid-absorption-interference left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "digene",
        "hidden_risk_component": "aluminium hydroxide",
        "risk": "Same antacid absorption-interference concern as Gelusil under a different brand.",
        "interaction_rule_id": "check hidden component against antacid-absorption-interference left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "polycrol",
        "hidden_risk_component": "aluminium hydroxide",
        "risk": "Same antacid absorption-interference concern as Gelusil/Digene under a different brand.",
        "interaction_rule_id": "check hidden component against antacid-absorption-interference left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
    {
        "brand": "amlopres",
        "hidden_risk_component": None,
        "risk": (
            "MEDICATION-ERROR risk, not an FDC: multiple unrelated brand "
            "families share the 'amlo-' prefix (amlopres = amlodipine) while "
            "sound-alike/look-alike brand stems across manufacturers can be "
            "confused at dispensing. Flagged here as a naming-collision "
            "risk to watch for, not a component-interaction case."
        ),
        "interaction_rule_id": "manual review — brand-prefix collision, not an interaction rule",
        "verified": False,
    },
    {
        "brand": "meftal",
        "is_fdc": False,  # single-ingredient NSAID, not itself an FDC
        "hidden_risk_component": "mefenamic acid",
        "risk": "Plain Meftal (no '-spas' suffix) is itself an NSAID; easily confused with Meftal-Spas (NSAID+antispasmodic) — same active ingredient, different combination, brand suffix is the only differentiator.",
        "interaction_rule_id": "check hidden component against NSAID left-set in _DRUG_INTERACTIONS",
        "verified": False,
    },
]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _validate() -> None:
    for brand, generic in _BRAND_TO_GENERIC.items():
        assert brand == brand.lower(), f"brand not lowercase: {brand}"
        assert generic == generic.lower(), f"generic not lowercase: {generic} ({brand})"

    for brand, components in _FDC_COMPONENTS.items():
        assert len(components) >= 2, f"FDC with <2 components: {brand} -> {components}"
        for c in components:
            assert c == c.lower(), f"FDC component not lowercase: {c} ({brand})"

    for entry in _HIGH_RISK_FDC:
        brand = entry["brand"]
        is_fdc = entry.get("is_fdc", True)  # default: entries are FDCs unless marked otherwise
        if is_fdc and entry.get("hidden_risk_component") is not None:
            assert brand in _FDC_COMPONENTS, (
                f"high-risk brand '{brand}' missing from _FDC_COMPONENTS"
            )


if __name__ == "__main__":
    _validate()
    print(f"total single brands: {len(_BRAND_TO_GENERIC)}")
    print(f"total FDCs: {len(_FDC_COMPONENTS)}")
    print(f"total high-risk FDCs flagged: {len(_HIGH_RISK_FDC)}")

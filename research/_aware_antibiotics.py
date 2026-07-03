"""WHO AWaRe antibiotic classification for Indian OPD prescribing.

Sources:
  - WHO AWaRe classification of antibiotics for evaluation and monitoring of use, 2023
    (WHO-MHP-HPS-EML-2023.04) -- the current WHO release; supersedes the 2019/2021
    iterations. WHO's 13th General Programme of Work country target: >=60% of national
    antibiotic consumption from the Access group by 2023 (raised to 70% by 2030 per the
    2024 UN political declaration on AMR).
  - WHO AWaRe (Access, Watch, Reserve) antibiotic book, 2022 -- syndrome-level empiric
    choice guidance for primary care and hospital settings (WHO, item 9789240062382).
  - India National List of Essential Medicines (NLEM) 2022 (CDSCO) -- cross-checked for
    which Access/Watch/Reserve antibiotics are on India's essential-medicines list. NOTE:
    NLEM 2022 does NOT itself categorise antibiotics by AWaRe group (Rao & Hotwani,
    IJPSR 2024; Lancet Reg Health SE Asia 2023, PMC10305940) -- AWaRe assignment here is
    taken directly from WHO, not NLEM.
  - India-specific outpatient prescribing literature (see per-drug citations below),
    e.g. a multicentre EMR study of 183,608 outpatient respiratory-infection
    prescriptions across 7 Indian metros (Jan 2021-Dec 2023) found 85% of antibiotics
    prescribed were WHO AWaRe "Watch" category, led by azithromycin (28.09%),
    cefpodoxime proxetil (19.07%) and cefixime (13.61%) (Journal of the Epidemiology
    Foundation of India, 2025, efi.org.in/journal/index.php/JEFI/article/view/129).

Category changes to note (verified via web search, 2026): WHO's global AWaRe
classification has long placed first-generation cephalosporins (e.g. cefalexin/
cephalexin, cefazolin) in Access -- this is NOT a new 2023 change. The move to Access
for first-generation cephalosporins was specific to the UK's own national adaptation
(2019 England-AWaRe had put ALL cephalosporins in Watch; the 2024 UK-AWaRe revision
brought first-generation cephalosporins in line with WHO's existing Access
classification). This file follows the WHO global classification throughout (cephalexin
= Access), not any single country's national adaptation. Second-, third- and
fourth-generation cephalosporins (cefixime, cefpodoxime, cefuroxime) remain Watch under
WHO. No other material reclassification affecting the drugs covered here was found
across the 2019/2021/2023 WHO revisions.

Scope and limits:
  - Reserve antibiotics: flag whenever prescribed in OPD at all -- these are hospital/
    ICU last-resort agents for confirmed or strongly suspected multidrug-resistant (MDR)
    infection, meant to be used under specialist/inpatient supervision.
  - Watch antibiotics: NOT blanket-flagged (many are legitimate first-line choices for
    specific syndromes, e.g. azithromycin for enteric fever). Instead, a subset prone to
    documented OPD over-prescription in India carries an `over_prescription_syndromes`
    list -- flag ONLY when the recorded diagnosis is one of those syndromes AND an
    Access-class antibiotic would ordinarily suffice.
  - This module is decision SUPPORT for a doctor at the point of care. It never
    auto-blocks, auto-changes, or auto-cancels a prescription -- every flag is surfaced
    for the prescribing doctor to review and confirm or override.
  - Brand names are India-market brands the author is reasonably confident about from
    general pharmaceutical knowledge; where confidence was insufficient the brand_names
    key is omitted rather than guessed (see GAPS notes in accompanying validation
    output / response, not fabricated here).
"""

from __future__ import annotations

_AWARE_CLASSIFICATION: dict[str, dict] = {

    # ---------------------------------------------------------------- ACCESS ----
    "amoxicillin": {
        "aware_category": "Access",
        "brand_names": {"Novamox", "Mox", "Amoxil"},
        "flag_in_opd": False,
    },
    "amoxicillin-clavulanate": {
        "aware_category": "Access",
        "brand_names": {"Augmentin", "Moxikind-CV", "Clavam"},
        "flag_in_opd": False,
    },
    "ampicillin": {
        "aware_category": "Access",
        "flag_in_opd": False,
        # brand_names omitted: no India-market brand name the author is confident of
        # (ampicillin is largely prescribed/dispensed generically or as inpatient
        # injectable in current Indian OPD practice) -- GAP, do not fabricate.
    },
    "cotrimoxazole": {
        "aware_category": "Access",
        "brand_names": {"Septran"},
        "flag_in_opd": False,
    },
    "doxycycline": {
        "aware_category": "Access",
        "brand_names": {"Doxt-SL", "Doxy-1"},
        "flag_in_opd": False,
    },
    "metronidazole": {
        "aware_category": "Access",
        "brand_names": {"Flagyl", "Metrogyl"},
        "flag_in_opd": False,
    },
    "nitrofurantoin": {
        "aware_category": "Access",
        "brand_names": {"Niftran"},
        "flag_in_opd": False,
    },
    "gentamicin": {
        "aware_category": "Access",
        "flag_in_opd": False,
        # brand_names omitted: gentamicin in Indian OPD is predominantly generic
        # injectable/topical; author not confident of a specific dominant retail
        # brand -- GAP, do not fabricate.
    },
    "cephalexin": {
        "aware_category": "Access",
        "brand_names": {"Sporidex"},
        "flag_in_opd": False,
        "alert": (
            "First-generation cephalosporin -- classified Access under WHO's global "
            "AWaRe list (this is a long-standing WHO classification, not a recent "
            "change; some national adaptations, e.g. the UK's pre-2024 list, had "
            "placed it in Watch). Reasonable Access-tier alternative to "
            "amoxicillin-clavulanate for mild skin/soft-tissue infection."
        ),
        "urgency": "medium",
    },

    # ---------------------------------------------------------------- WATCH -----
    "azithromycin": {
        "aware_category": "Watch",
        "brand_names": {"Azithral", "Azee", "Zithromax"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["URTI_viral", "CAP_mild"],
        "preferred_alternative_for_syndrome": {
            "URTI_viral": "none_indicated",
            "CAP_mild": "amoxicillin",
        },
        "alert": (
            "Azithromycin is a Watch antibiotic. It is the correct first-line choice "
            "for enteric fever in India (fluoroquinolone resistance) but is widely "
            "over-prescribed for viral URTI and mild CAP where an Access antibiotic "
            "(or no antibiotic at all) would suffice. A 7-metro Indian EMR study "
            "(2021-2023, n=183,608 outpatient respiratory prescriptions) found "
            "azithromycin was the single most-prescribed antibiotic (28.09% of "
            "antibiotic prescriptions; 85% of all antibiotics prescribed were Watch-"
            "category) -- Journal of the Epidemiology Foundation of India, 2025. "
            "Confirm bacterial etiology / syndrome before accepting this flag as a "
            "true over-prescription instance."
        ),
        "urgency": "medium",
    },
    "cefixime": {
        "aware_category": "Watch",
        "brand_names": {"Taxim-O", "Zifi", "Cefix"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["CAP_mild", "skin_soft_tissue_infection"],
        "preferred_alternative_for_syndrome": {
            "CAP_mild": "amoxicillin",
            "skin_soft_tissue_infection": "amoxicillin-clavulanate",
        },
        "alert": (
            "Third-generation oral cephalosporin (Watch). Frequently substituted for "
            "amoxicillin in Indian OPD without a documented indication requiring "
            "extended Gram-negative/beta-lactamase-stable cover. Same Indian EMR study "
            "found cefixime was 13.61% of outpatient respiratory antibiotic "
            "prescriptions (efi.org.in/journal/index.php/JEFI/article/view/129). "
            "Reserve for confirmed/suspected typhoid or documented cephalosporin-"
            "requiring infection."
        ),
        "urgency": "medium",
    },
    "cefpodoxime": {
        "aware_category": "Watch",
        "brand_names": {"Cepodem"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["CAP_mild", "skin_soft_tissue_infection"],
        "preferred_alternative_for_syndrome": {
            "CAP_mild": "amoxicillin",
            "skin_soft_tissue_infection": "amoxicillin-clavulanate",
        },
        "alert": (
            "Third-generation oral cephalosporin (Watch). Same Indian EMR study found "
            "cefpodoxime proxetil was the second most-prescribed antibiotic for "
            "outpatient respiratory infections (19.07%), behind only azithromycin "
            "(efi.org.in/journal/index.php/JEFI/article/view/129) -- a documented "
            "over-prescription pattern where Access-tier amoxicillin would usually "
            "suffice."
        ),
        "urgency": "medium",
    },
    "ciprofloxacin": {
        "aware_category": "Watch",
        "brand_names": {"Ciplox", "Cifran"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["simple_UTI"],
        "preferred_alternative_for_syndrome": {
            "simple_UTI": "nitrofurantoin",
        },
        "alert": (
            "Fluoroquinolone (Watch). Commonly over-used as empiric first-line therapy "
            "for uncomplicated/simple UTI in Indian OPD despite Access-tier "
            "alternatives (nitrofurantoin, cotrimoxazole where local resistance "
            "permits). Indian outpatient UTI resistance surveillance links "
            "fluoroquinolone/broad-spectrum overuse to rising resistance rates "
            "(PMC11993370, 2025). Confirm culture/sensitivity or documented "
            "complicated-UTI features before accepting fluoroquinolone use."
        ),
        "urgency": "medium",
    },
    "levofloxacin": {
        "aware_category": "Watch",
        "brand_names": {"Glevo"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["simple_UTI"],
        "preferred_alternative_for_syndrome": {
            "simple_UTI": "nitrofurantoin",
        },
        "alert": (
            "Respiratory fluoroquinolone (Watch). Same OPD over-use concern as "
            "ciprofloxacin for simple UTI; also frequently over-used for mild CAP "
            "where amoxicillin would suffice. See ciprofloxacin alert for the "
            "supporting Indian UTI resistance-surveillance citation (PMC11993370, "
            "2025)."
        ),
        "urgency": "medium",
    },
    "clarithromycin": {
        "aware_category": "Watch",
        "brand_names": {"Klaricid"},
        "flag_in_opd": False,
        # No India-specific OPD over-prescription audit for clarithromycin
        # specifically was found (distinct from azithromycin) -- GAP: flagging is
        # limited to the general Watch-category caution below, not a documented
        # India over-prescription pattern.
        "alert": (
            "Macrolide (Watch), pharmacologically similar to azithromycin. No "
            "India-specific OPD over-prescription audit for clarithromycin "
            "specifically was located (as distinct from azithromycin) -- flag "
            "conservatively as a general Watch-category caution rather than a "
            "confirmed over-prescription pattern."
        ),
        "urgency": "low",
    },
    "cefuroxime": {
        "aware_category": "Watch",
        "brand_names": {"Zinnat"},
        "flag_in_opd": False,
        "over_prescription_syndromes": ["CAP_mild"],
        "preferred_alternative_for_syndrome": {
            "CAP_mild": "amoxicillin",
        },
        "alert": (
            "Second-generation oral cephalosporin (Watch). Grouped with cefixime/"
            "cefpodoxime as a Watch-tier cephalosporin substituted for Access-tier "
            "amoxicillin in Indian outpatient respiratory prescribing; a dedicated "
            "India-specific prescribing audit for cefuroxime alone (vs. the pooled "
            "cephalosporin data for cefixime/cefpodoxime) was not located -- GAP."
        ),
        "urgency": "low",
    },

    # -------------------------------------------------------------- RESERVE -----
    "meropenem": {
        "aware_category": "Reserve",
        "brand_names": {"Meronem"},
        "flag_in_opd": True,
        "alert": (
            "Reserve-class carbapenem -- hospital/ICU last-resort agent for confirmed "
            "or strongly suspected multidrug-resistant (MDR) Gram-negative infection. "
            "Should not be initiated in outpatient primary care. If genuinely "
            "indicated, refer immediately to a hospital with infectious-disease/"
            "microbiology support rather than dispensing in OPD."
        ),
        "urgency": "critical",
    },
    "vancomycin": {
        "aware_category": "Reserve",
        "flag_in_opd": True,
        # brand_names omitted: predominantly generic/hospital-procured IV in India;
        # author not confident of a dominant India retail brand -- GAP.
        "alert": (
            "Reserve-class glycopeptide -- reserved for confirmed MRSA or other "
            "resistant Gram-positive infection, IV, hospital-monitored (requires "
            "level monitoring). Not an outpatient primary-care drug; refer to "
            "hospital care if suspected indication."
        ),
        "urgency": "critical",
    },
    "colistin": {
        "aware_category": "Reserve",
        "brand_names": {"Colicip"},
        "flag_in_opd": True,
        "alert": (
            "Reserve-class polymyxin -- true last-resort agent for extensively "
            "drug-resistant (XDR) Gram-negative infection, nephrotoxic, hospital/ICU "
            "use only. Presence in an OPD record should be treated as a critical "
            "data/safety flag requiring immediate doctor review, not routine "
            "dispensing."
        ),
        "urgency": "critical",
    },
    "linezolid": {
        "aware_category": "Reserve",
        "brand_names": {"Lizolid"},
        "flag_in_opd": True,
        "alert": (
            "Reserve-class oxazolidinone -- for confirmed resistant Gram-positive "
            "infection (e.g. MRSA, VRE) under specialist supervision. Not "
            "appropriate as an outpatient primary-care empiric choice; refer if "
            "genuinely indicated."
        ),
        "urgency": "critical",
    },
    "imipenem": {
        "aware_category": "Reserve",
        "brand_names": {"Zienam"},
        "flag_in_opd": True,
        "alert": (
            "Reserve-class carbapenem (imipenem-cilastatin) -- hospital/ICU last-"
            "resort agent for confirmed or strongly suspected MDR infection. Should "
            "not appear in outpatient primary-care prescribing; refer to hospital "
            "care immediately if this flag fires."
        ),
        "urgency": "critical",
    },
}

_RESERVE_ANTIBIOTICS: set[str] = {
    name for name, data in _AWARE_CLASSIFICATION.items()
    if data["aware_category"] == "Reserve"
}

_OPD_OVERUSE_WATCH: set[str] = {
    name for name, data in _AWARE_CLASSIFICATION.items()
    if data.get("flag_in_opd") is False and data.get("over_prescription_syndromes")
}

_SYNDROME_ANTIBIOTIC_GUIDANCE: dict[str, dict] = {
    "URTI_viral": {
        "category_preferred": None,
        "first_line": "No antibiotic indicated -- symptomatic/supportive care",
        "notes": (
            "Overwhelming majority of URTI in primary care is viral. Indian OPD data "
            "show azithromycin is nonetheless the most-prescribed antibiotic for "
            "respiratory-infection encounters (28.09% of antibiotic prescriptions "
            "across a 7-metro Indian EMR cohort, 2021-2023) -- Journal of the "
            "Epidemiology Foundation of India, 2025. Reserve antibiotics for "
            "documented bacterial superinfection (e.g. streptococcal pharyngitis, "
            "bacterial sinusitis, otitis media)."
        ),
    },
    "CAP_mild": {
        "category_preferred": "Access",
        "first_line": "amoxicillin",
        "notes": (
            "WHO AWaRe antibiotic book (2022): amoxicillin is first-line empiric "
            "therapy for non-severe community-acquired pneumonia. Escalate to a "
            "Watch antibiotic or hospital referral only for severity markers "
            "(hypoxia, altered mentation, high respiratory rate, comorbidity-driven "
            "risk) -- doctor judgement required, this file does not encode a "
            "severity score."
        ),
    },
    "simple_UTI": {
        "category_preferred": "Access",
        "first_line": "nitrofurantoin or cotrimoxazole (per local resistance)",
        "notes": (
            "WHO AWaRe antibiotic book (2022) lists nitrofurantoin/cotrimoxazole as "
            "first-line for uncomplicated cystitis. An Indian outpatient UTI cohort "
            "found E. coli resistance to trimethoprim-sulfamethoxazole at 30% and to "
            "fluoroquinolones at 22% (PMC11993370, 2025) -- interpret cotrimoxazole "
            "empiric use in light of local resistance; fluoroquinolones are Watch-"
            "tier and should not be first-line for simple/uncomplicated UTI."
        ),
    },
    "skin_soft_tissue_infection": {
        "category_preferred": "Access",
        "first_line": "amoxicillin-clavulanate",
        "notes": (
            "WHO AWaRe antibiotic book (2022): amoxicillin-clavulanate (or "
            "cephalexin, Access-tier since the 2023 WHO revision) covers common "
            "skin/soft-tissue pathogens empirically for mild-to-moderate "
            "presentations without systemic toxicity."
        ),
    },
    "enteric_fever_typhoid": {
        "category_preferred": "Watch",
        "first_line": "azithromycin",
        "notes": (
            "Fluoroquinolone resistance is widespread in Salmonella Typhi/Paratyphi "
            "across the Indian subcontinent, so ciprofloxacin/ofloxacin are no "
            "longer reliable empiric first-line agents. Azithromycin (Watch) is "
            "widely used as first-line oral therapy for uncomplicated enteric fever "
            "in India; ceftriaxone (Watch, injectable/inpatient) or referral is used "
            "for severe, MDR, or ceftriaxone-non-resistant complicated cases. This is "
            "a documented EXCEPTION where a Watch antibiotic, not Access, is the "
            "syndrome-appropriate first choice -- do not apply the generic Watch-"
            "overuse flag here."
        ),
    },
    "travellers_diarrhea": {
        "category_preferred": "Access",
        "first_line": "supportive care (ORS); antibiotic only if indicated",
        "notes": (
            "Most acute traveller's/OPD diarrhoea is self-limiting and viral or "
            "toxin-mediated; oral rehydration is first-line. Metronidazole (Access) "
            "is appropriate only if Giardia or amoebiasis is specifically suspected "
            "(cyst/trophozoite-positive stool, prolonged/relapsing course) -- not "
            "for routine acute watery diarrhoea."
        ),
    },
    "TB": {
        "category_preferred": None,
        "first_line": "OUT OF SCOPE -- dedicated multidrug regimen under national "
                       "TB programme guidance, not the AWaRe single-antibiotic "
                       "framework",
        "notes": (
            "Tuberculosis treatment uses a dedicated multidrug regimen (e.g. rifampicin/"
            "isoniazid/pyrazinamide/ethambutol combinations under India's National "
            "TB Elimination Programme) that falls outside the WHO AWaRe "
            "Access/Watch/Reserve single-antibiotic classification used in this "
            "module. This file deliberately does not encode TB treatment detail; "
            "route suspected TB cases to dedicated programme-guided care, not this "
            "engine."
        ),
    },
    "dengue_malaria": {
        "category_preferred": None,
        "first_line": "No antibiotic indicated -- not a bacterial infection",
        "notes": (
            "Dengue is viral and malaria is parasitic; neither is treated with "
            "antibiotics. An antibiotic prescription against either diagnosis code "
            "should be flagged as a probable diagnosis-treatment mismatch for doctor "
            "review, not auto-corrected."
        ),
    },
}

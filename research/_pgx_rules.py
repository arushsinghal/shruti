"""Indian OPD pharmacogenomics prescribing safety rules.

Sources:
  - IndiGen (Sahana et al. 2022, Clin Transl Sci) PMID:35338580
    NOTE: PMID 31626772 (cited in the original research brief as "IndiGen, Cell 2019")
    was checked and resolves to the Singapore SG10K whole-genome study, NOT IndiGen.
    The correct IndiGen PGx-focused publication located and used here is
    Sahana S et al., Clin Transl Sci 2022, PMID:35338580 (IndiGen, N=1,029 Indian genomes).
  - GenomeIndia: no "Science 2024" GenomeIndia PGx paper was found. The flagship
    GenomeIndia publication is Bhattacharyya et al., Nature Genetics 2025, PMID:40200122
    (paywalled, full text not retrievable in this pass). PGx frequency data used here
    instead comes from a related open dataset, 'An Atlas of Indian Genetic Diversity'
    (medRxiv 2026, DOI:10.64898/2026.03.20.26348801, N=9,768 genomes / 83 populations).
  - CPIC gene-drug pairs: pulled from api.cpicpgx.org (level 1A/1B only), cross-checked
    against CPIC guideline PMIDs.
  - Additional PMIDs cited per-rule below and in the companion evidence table
    (pgx_evidence_table.csv / pgx_indian_frequency_raw.json).

These are POPULATION-LEVEL flags based on published Indian (or, where explicitly
marked, proxy-population) allele/carrier frequency literature — NOT patient-specific
genomic diagnoses. Lipi has no genomic data pipeline. Every flag is a prompt for the
doctor to consider a population-level pharmacogenomic risk; it never triggers an
automated clinical action, and it must never be presented to the doctor as a
patient-specific genotype result.

Schema notes:
  - "data_quality" is one of: INDIAN_DATA | SOUTH_ASIAN_PROXY | GLOBAL_PROXY |
    NO_INDIAN_DATA (free-text suffix names the proxy source used).
  - "ships_now" = True means the rule can be deployed today as a population-level
    flag with no genomic input required. False means the rule is retained for
    documentation / future-readiness only and should NOT be surfaced to doctors yet
    (see _PGX_RULES_NEEDS_VOLUME below) — usually because observability is too weak
    (score < 2) and/or the clinical action requires patient-specific genomic input.
"""

from __future__ import annotations

CPIC_VERSION_NOTE = "CPIC gene-drug pairs pulled live from api.cpicpgx.org (level 1A/1B), 2026-07-02"

_PGX_RULES: list[dict] = [
    {
        "rule_id": 'PGX_001',
        "rule_name": 'G6PD deficiency - oxidant drug hemolysis risk',
        "genes": ['G6PD'],
        "trigger_drugs": {'co-trimoxazole', 'dapsone', 'nitrofurantoin', 'primaquine', 'rasburicase', 'sulfamethoxazole'},
        "trigger_drug_brand_names_india": {
        'co-trimoxazole': ['Septran', 'Bactrim', 'Ampilin-CO'],
        'dapsone': ['Dapsone (NLEP-supplied generic)', 'Avlosulfon'],
        'nitrofurantoin': ['Nitrofurantoin', 'Furadantin', 'Nitro-Wok'],
        'primaquine': ['Primaquine (NVBDCP-supplied generic)', 'Malirid'],
        'rasburicase': ['Fasturtec'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['24787449', '36049896'],
        "indian_frequency": '2-27.9% carrier prevalence depending on region/community (highest: Vataliya Prajapati Gujarat 27.9% males; tribal Odisha/Central India 6-8%; general population survey 1.9%; lowest in some North Indian cohorts <1%)',
        "indian_frequency_source": 'PMID:26139767 (7.7% national); PMID:33069889 (1.9%, N=20896); PMID:15226563; PMID:11345405 (27.9%); PMID:18568599; PMID:31833391; PMID:36384674; PMID:31061745; PMID:37674284 (Delhi newborn screening); PMID:29417859; PMID:39926832',
        "rank_score": 27,
        "observability_score": 2,
        "observability_note": 'Acute haemolysis (dark urine, jaundice, fatigue) days after starting primaquine/dapsone is a well-documented, recognizable clinical pattern; weaker for nitrofurantoin/co-trimoxazole (rare reports despite wide use per CPIC).',
        "opd_actionability_score": 3,
        "opd_actionability_note": 'Dispensed at PHC/OPD level (malaria elimination programme, NLEP, routine antibiotics); point-of-care G6PD test or referral before dosing is an OPD-level action.',
        "alert_template": 'G6PD risk: {drug} can trigger haemolytic anaemia in G6PD-deficient patients. Indian prevalence 2-27.9% depending on region/community. Consider point-of-care G6PD screening before prescribing, especially in patients from malaria-endemic, tribal, or high-prevalence-community backgrounds, or with a personal/family history of drug- or fava-bean-induced jaundice.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_002',
        "rule_name": 'CYP2C19 poor/intermediate metabolizer - clopidogrel non-response',
        "genes": ['CYP2C19'],
        "trigger_drugs": {'clopidogrel'},
        "trigger_drug_brand_names_india": {
        'clopidogrel': ['Deplatt', 'Clopilet', 'Ecosprin AV (combination)'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['36094131'],
        "indian_frequency": 'CYP2C19*2 allele frequency 0.34-0.36 (IndiGen national + South Indian CAD cohorts); GenomeIndia national poor-metabolizer phenotype ~15%',
        "indian_frequency_source": 'PMID:35338580 (IndiGen, *2 AF=0.36); PMID:41028360 (South Indian CAD/clopidogrel cohort, 34% PM/IM carriers); PMID:37985132 (South Indian ACS cohort); medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia, 15% PM phenotype)',
        "rank_score": 27,
        "observability_score": 3,
        "observability_note": 'Recurrent stent thrombosis, recurrent ACS, or stroke on clopidogrel despite adherence is a strong, well-recognized signal of poor-metabolizer status.',
        "opd_actionability_score": 3,
        "opd_actionability_note": 'Switching to prasugrel/ticagrelor or adding antiplatelet therapy is routine cardiology/OPD follow-up decision-making; genotyping increasingly available via referral.',
        "alert_template": 'CYP2C19 metabolizer risk: clopidogrel may be ineffective in ~34-36% of Indian patients carrying reduced-function CYP2C19 alleles (poor/intermediate metabolizers). Consider genotyping or empiric alternative antiplatelet (prasugrel/ticagrelor) in patients with recurrent ischemic events on clopidogrel.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_003',
        "rule_name": 'VKORC1/CYP2C9/CYP4F2 - warfarin dose sensitivity',
        "genes": ['VKORC1', 'CYP2C9', 'CYP4F2'],
        "trigger_drugs": {'acenocoumarol', 'warfarin'},
        "trigger_drug_brand_names_india": {
        'acenocoumarol': ['Acitrom', 'Sintrom'],
        'warfarin': ['Warf', 'Sofarin', 'Uniwarfin'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['28198005'],
        "indian_frequency": 'VKORC1 -1639G>A AF 0.14-0.72 depending on region (IGVdb range 6.5%->70% across 24 subpopulations); CYP2C9*3 AF 0.09-0.17 (higher in North Indian anticoagulant cohorts)',
        "indian_frequency_source": 'PMID:35338580 (IndiGen, VKORC1 AF=0.18); PMID:25155935 (IGVdb, 24 subpopulations, VKORC1 range 6.5-70%); PMID:23563037 (North vs South Indian pilot); PMID:26781925 (North Indian valve-replacement cohort on acenocoumarol)',
        "rank_score": 27,
        "observability_score": 3,
        "observability_note": 'Excessive INR/bleeding at low dose, or persistent sub-therapeutic INR at high dose, is a directly observable signal via routine INR monitoring already standard of care.',
        "opd_actionability_score": 3,
        "opd_actionability_note": 'Dose titration via INR monitoring is routine OPD/anticoagulation-clinic practice; no new infrastructure needed.',
        "alert_template": 'Anticoagulant sensitivity risk: VKORC1/CYP2C9/CYP4F2 variants are common in Indian populations and are associated with variable warfarin/acenocoumarol dose requirements (both hyper- and hypo-sensitivity reported). Start with close INR monitoring and consider a lower initial dose; adjust per response, not population average.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_004',
        "rule_name": 'NUDT15/TPMT - thiopurine-induced myelosuppression',
        "genes": ['NUDT15', 'TPMT'],
        "trigger_drugs": {'6-mercaptopurine', 'azathioprine', 'mercaptopurine'},
        "trigger_drug_brand_names_india": {
        'azathioprine': ['Imuran', 'Azoran'],
        'mercaptopurine': ['Puri-Nethol'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['30801620'],
        "indian_frequency": 'NUDT15*3 AF 0.068-0.107 in Indian thiopurine-treated cohorts (up to 20.8% in some Austro-Asiatic tribal groups); TPMT variants comparatively rare in India (*3C AF 0.02, *3A AF 0.003) -- NUDT15 is the dominant thiopurine-toxicity gene in South Asians, not TPMT',
        "indian_frequency_source": 'PMID:35338580 (IndiGen NUDT15*3=0.08, TPMT*3A/*3C); PMID:29470173 (Indian thiopurine cohort, NUDT15*3=0.107); PMID:32935219 (Indian GSA screening N=2000); medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia tribal groups)',
        "rank_score": 18,
        "observability_score": 2,
        "observability_note": 'Cytopenia (leukopenia) on routine follow-up CBC while on thiopurine therapy is a moderately specific signal, though confounded by disease activity and other marrow suppressants.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Dose reduction or alternative agent is an OPD-level decision once myelosuppression is flagged on routine CBC monitoring.',
        "alert_template": 'Thiopurine toxicity risk: NUDT15 (dominant in South Asians) and TPMT variants increase myelosuppression risk on azathioprine/mercaptopurine. Consider baseline CBC and closer monitoring in the first weeks of therapy; consider genotyping if available before starting.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_005',
        "rule_name": 'CYP2D6/CYP2C19 - tricyclic antidepressant metabolizer variability',
        "genes": ['CYP2D6', 'CYP2C19'],
        "trigger_drugs": {'amitriptyline', 'clomipramine', 'doxepin', 'imipramine', 'nortriptyline', 'trimipramine'},
        "trigger_drug_brand_names_india": {
        'amitriptyline': ['Tryptomer', 'Amitone', 'Sarotena'],
        'nortriptyline': ['Nortin'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['27997040'],
        "indian_frequency": 'CYP2D6 poor/intermediate-metabolizer alleles (*4, *10, *41) 6.6-32% depending on allele/region; CYP2C19*2 AF 0.36 nationally',
        "indian_frequency_source": 'PMID:35338580 (IndiGen); PMID:12942225 (South Indian Tamilian cohort); PMID:16880622 (South Indian states); PMID:31368850 (South Indian resequencing cohort)',
        "rank_score": 18,
        "observability_score": 2,
        "observability_note": 'Excess sedation/anticholinergic side effects (possible PM) vs. non-response at standard dose (possible UM) is a moderately usable signal on OPD follow-up, though confounded by other factors.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Dose titration for TCAs in OPD psychiatry/pain/neuropathy management is routine practice.',
        "alert_template": 'Antidepressant metabolizer variability: CYP2D6/CYP2C19 variants are common in Indian populations and affect amitriptyline/nortriptyline exposure. Start low, titrate slowly, and monitor for excess sedation/anticholinergic effects (possible poor metabolizer) or non-response at standard dose (possible ultrarapid metabolizer).',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_006',
        "rule_name": 'CYP2D6 - atomoxetine exposure variability',
        "genes": ['CYP2D6'],
        "trigger_drugs": {'atomoxetine'},
        "trigger_drug_brand_names_india": {
        'atomoxetine': ['Attentrol', 'Axepta'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['30801677'],
        "indian_frequency": 'Same CYP2D6 PM/IM allele burden as above (6.6-32%)',
        "indian_frequency_source": 'PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850',
        "rank_score": 18,
        "observability_score": 1,
        "observability_note": 'Side-effect profile is nonspecific; atomoxetine use in Indian OPD/psychiatry is moderate but growing, behind stimulants -- weaker standalone signal.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Dose adjustment is possible at OPD/psychiatry follow-up level.',
        "alert_template": 'CYP2D6 metabolizer variability may affect atomoxetine exposure and side-effect profile. Population-level flag only — clinical signal is nonspecific; consider genomic testing before acting.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_007',
        "rule_name": 'CYP2D6 - codeine analgesic failure/toxicity',
        "genes": ['CYP2D6'],
        "trigger_drugs": {'codeine'},
        "trigger_drug_brand_names_india": {
        'codeine': ['Codeine phosphate (cough/analgesic combinations, e.g. Corex, Phensedyl -- both under regulatory restriction in India)'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['33387367'],
        "indian_frequency": 'Same CYP2D6 PM/IM/UM allele burden as above',
        "indian_frequency_source": 'PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850',
        "rank_score": 18,
        "observability_score": 1,
        "observability_note": 'Poor analgesia (PM) or sedation/toxicity (UM) is observable but codeine use has declined in Indian OPD due to abuse-potential restrictions, reducing exposure and signal frequency.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Alternative analgesic can be chosen at OPD level.',
        "alert_template": 'CYP2D6 metabolizer variability may cause poor analgesia (poor metabolizers) or toxicity/sedation (ultrarapid metabolizers) with codeine. Population-level flag only — consider an alternative analgesic given regulatory restrictions on codeine-containing products in India.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_008',
        "rule_name": 'CYP2C19 - proton pump inhibitor metabolizer variability',
        "genes": ['CYP2C19'],
        "trigger_drugs": {'esomeprazole', 'lansoprazole', 'omeprazole', 'pantoprazole'},
        "trigger_drug_brand_names_india": {
        'omeprazole': ['Omez', 'Ocid'],
        'pantoprazole': ['Pantocid', 'Pan-D', 'Pantop'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['32770672'],
        "indian_frequency": 'CYP2C19*2 AF 0.36 nationally (IndiGen); PM phenotype ~15% (GenomeIndia)',
        "indian_frequency_source": 'PMID:35338580; medRxiv:10.64898/2026.03.20.26348801',
        "rank_score": 18,
        "observability_score": 1,
        "observability_note": 'Poor symptom control at standard PPI dose could reflect ultrarapid metabolizer status, but is heavily confounded by H. pylori status, adherence, and lifestyle -- weak standalone signal.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Dose/drug switch (e.g. to a non-CYP2C19-dependent option) is a routine OPD decision for reflux/PUD.',
        "alert_template": 'CYP2C19 metabolizer variability may affect PPI (omeprazole/pantoprazole) efficacy. Population-level flag only — symptom control at standard dose is a weak, confounded signal; consider genomic testing before acting on treatment failure.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_009',
        "rule_name": 'HLA-B*15:02 / HLA-A*31:01 - carbamazepine severe cutaneous reaction risk',
        "genes": ['HLA-B', 'HLA-A'],
        "trigger_drugs": {'carbamazepine', 'oxcarbazepine'},
        "trigger_drug_brand_names_india": {
        'carbamazepine': ['Tegretol', 'Mazetol'],
        'oxcarbazepine': ['Oxetol'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['23695185'],
        "indian_frequency": 'HLA-B*15:02 ~3% carrier prevalence (IndiGen); strong disease association in Indian case-control studies (OR up to 38.5); HLA-A*31:01 ~2% carrier prevalence (IndiGen)',
        "indian_frequency_source": 'PMID:35338580 (IndiGen); PMID:25266342 (meta-analysis, Malaysian-Indian + India-pooled, OR 38.54); PMID:25305458 (North Indian case-control); PMID:29076187 (Kerala case-control)',
        "rank_score": 12,
        "observability_score": 2,
        "observability_note": 'SJS/TEN is a severe, recognizable ADR, but by the time it is observed, harm has already occurred -- this is a pre-emptive flag, not a post-hoc one.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Pre-prescription HLA-B*15:02 screening exists but is not routinely ordered in Indian OPD; if unavailable, doctor can choose an alternative anticonvulsant empirically, especially with prior history.',
        "alert_template": 'Severe cutaneous adverse reaction risk: HLA-B*15:02/HLA-A*31:01 carriage is documented in Indian populations and is strongly associated with carbamazepine-induced SJS/TEN. Pre-prescription HLA-B*15:02 screening is recommended where available, especially before first exposure; consider an alternative anticonvulsant if screening is not feasible and risk factors are present.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_010',
        "rule_name": 'NAT2 slow acetylator - isoniazid hepatotoxicity risk',
        "genes": ['NAT2'],
        "trigger_drugs": {'isoniazid'},
        "trigger_drug_brand_names_india": {
        'isoniazid': ['Isoniazid (INH) -- part of NTEP fixed-dose combination ATT regimens, e.g. Akurit, Forecox'],
    },
        "cpic_level": '1B',
        "cpic_guideline_pmids": None,
        "indian_frequency": 'Slow-acetylator phenotype 44-74% depending on region (Mumbai 55%, North India 44-53%, South India 67-74%; Chennai TB cohort 58% slow)',
        "indian_frequency_source": "PMID:28862181 / PMC5460557 (IJMR, Chennai NAT2 genotyping); Dovepress review 'NAT2 Acetylation Phenotypes in India'",
        "rank_score": 12,
        "observability_score": 2,
        "observability_note": 'Hepatotoxicity (deranged LFTs) or peripheral neuropathy on isoniazid is a recognizable, commonly monitored OPD/NTEP signal.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Isoniazid dosing is standardized under NTEP weight-band protocols, but LFT monitoring and drug switch/interruption on hepatotoxicity is an OPD-level decision.',
        "alert_template": 'Isoniazid hepatotoxicity risk: NAT2 slow-acetylator phenotype affects 44-74% of Indians depending on region, increasing hepatotoxicity risk on standard-dose isoniazid. Monitor LFTs during the intensive phase of ATT, especially in patients with additional hepatotoxicity risk factors.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_011',
        "rule_name": 'CYP2D6 poor metabolizer - tamoxifen reduced efficacy',
        "genes": ['CYP2D6'],
        "trigger_drugs": {'tamoxifen'},
        "trigger_drug_brand_names_india": {
        'tamoxifen': ['Tamodex', 'Genox'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['30447069'],
        "indian_frequency": 'Same CYP2D6 PM/IM allele burden as above (6.6-32%)',
        "indian_frequency_source": 'PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850',
        "rank_score": 9,
        "observability_score": 1,
        "observability_note": 'Breast cancer recurrence on tamoxifen is a delayed, highly confounded signal, and management is oncology-led, not primary-care.',
        "opd_actionability_score": 1,
        "opd_actionability_note": 'Dosing/switch decisions are typically managed in oncology, not general OPD.',
        "alert_template": 'CYP2D6 poor-metabolizer status may reduce tamoxifen efficacy (impaired conversion to active endoxifen). Population-level flag for oncology referral — not an OPD-level action; consider genomic testing before altering oncology treatment plans.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_012',
        "rule_name": 'CYP2C19 poor metabolizer - voriconazole toxicity risk',
        "genes": ['CYP2C19'],
        "trigger_drugs": {'voriconazole'},
        "trigger_drug_brand_names_india": {
        'voriconazole': ['Vfend', 'Voritek'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['31544268'],
        "indian_frequency": 'CYP2C19*2 AF 0.36 nationally (IndiGen); PM phenotype ~15% (GenomeIndia)',
        "indian_frequency_source": 'PMID:35338580; medRxiv:10.64898/2026.03.20.26348801',
        "rank_score": 9,
        "observability_score": 1,
        "observability_note": 'Sub-therapeutic levels (PM) or visual/hepatic toxicity (UM) require drug-level monitoring rarely available in OPD; antifungal dosing for invasive infections is typically hospital/ID-specialist managed.',
        "opd_actionability_score": 1,
        "opd_actionability_note": 'Dosing decisions typically happen in hospital/ID-specialist setting, not general OPD.',
        "alert_template": 'CYP2C19 metabolizer variability may cause voriconazole under- or over-exposure. Population-level flag for specialist referral — drug-level monitoring (not available in OPD) is needed to act; consider genomic testing before altering antifungal dosing.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_013',
        "rule_name": 'CYP3A5 expresser status - tacrolimus dose requirement',
        "genes": ['CYP3A5'],
        "trigger_drugs": {'tacrolimus'},
        "trigger_drug_brand_names_india": {
        'tacrolimus': ['Panimun Bioral', 'Tacrograf'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['25801146'],
        "indian_frequency": 'GenomeIndia Tibeto-Burman group poor-metabolizer (non-expresser) phenotype 45%; broader pan-India CYP3A5*3 frequency not established in this search',
        "indian_frequency_source": 'medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia, Tibeto-Burman subgroup only)',
        "rank_score": 6,
        "observability_score": 1,
        "observability_note": 'Sub-therapeutic tacrolimus levels are only detectable via specialist drug-level monitoring, not general OPD observation.',
        "opd_actionability_score": 1,
        "opd_actionability_note": 'Transplant immunosuppression dosing is managed by transplant specialists, not general OPD.',
        "alert_template": 'CYP3A5 expresser status affects tacrolimus dose requirements. Population-level flag for transplant-specialist referral — Indian frequency data is limited to one tribal subgroup and not representative of pan-India frequency; do not act without genomic/therapeutic drug monitoring.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'NO_INDIAN_DATA — closest proxy: GenomeIndia Tibeto-Burman subgroup only, not representative of pan-India frequency',
    },
    {
        "rule_id": 'PGX_014',
        "rule_name": 'UGT1A1 reduced activity - atazanavir/irinotecan toxicity',
        "genes": ['UGT1A1'],
        "trigger_drugs": {'atazanavir', 'irinotecan'},
        "trigger_drug_brand_names_india": {
        'atazanavir': ['Atazor (NACO ART programme)'],
        'irinotecan': ['Camptocare'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['26417955', '24714115'],
        "indian_frequency": 'UGT1A1*28 allele frequency in Indians is comparable to other Asian populations and notably higher than East Asians at some related loci; Balram et al. 2002 (Singapore-based Indian ethnic cohort) found UGT1A1*28 to be a common allele in Indians. A separate South Indian healthy-cohort study (N=450-608) found UGT1A1 (TA)7 promoter allele frequency 39.8%.',
        "indian_frequency_source": 'PMID:11773869 (Balram et al. 2002, Pharmacogenetics -- Indian ethnic cohort, Singapore); South Indian healthy cohort TPMT/UGT1A1/MDR1 study (N=450-608, ResearchGate abstract, PMID not captured in this pass -- flagged for follow-up)',
        "rank_score": 3,
        "observability_score": 2,
        "observability_note": 'Jaundice/hyperbilirubinemia (atazanavir) or severe neutropenia/diarrhea (irinotecan) are fairly specific, specialist-monitored signals.',
        "opd_actionability_score": 1,
        "opd_actionability_note": 'ART regimen switch happens within NACO ART centres; chemotherapy dosing is oncology-managed -- not general OPD decisions, but flag is useful for referral communication.',
        "alert_template": 'UGT1A1 reduced-activity variants (UGT1A1*28) are common alleles in Indian populations and may increase atazanavir-associated hyperbilirubinemia or irinotecan-associated neutropenia/diarrhea risk. Consider monitoring bilirubin (atazanavir) or dose caution (irinotecan) per CPIC guidance; confirm with genomic testing before altering ART/chemotherapy regimens.',
        "needs_genomic_data": False,
        "ships_now": True,
        "data_quality": 'INDIAN_DATA',
    },
    {
        "rule_id": 'PGX_015',
        "rule_name": 'SLCO1B1/ABCG2 - statin-induced myopathy risk (DATA GAP)',
        "genes": ['SLCO1B1', 'ABCG2'],
        "trigger_drugs": {'atorvastatin', 'rosuvastatin', 'simvastatin'},
        "trigger_drug_brand_names_india": {
        'atorvastatin': ['Atorva', 'Storvas'],
        'rosuvastatin': ['Rosuvas', 'Rosufit'],
        'simvastatin': ['Simvotin'],
    },
        "cpic_level": '1A',
        "cpic_guideline_pmids": ['35152405'],
        "indian_frequency": 'NO INDIAN-SPECIFIC FREQUENCY FOUND in this search. Global/Asian proxy: SLCO1B1 rs4149056 minor-allele frequency ~14% in pooled Asian meta-analysis vs 15% Caucasian (not India-specific)',
        "indian_frequency_source": 'NO_INDIAN_DATA — closest proxy: pooled Asian meta-analysis (source not independently confirmed as covering India), South/West Asian gnomAD range 5-10% per CPIC guideline text',
        "rank_score": 0,
        "observability_score": 2,
        "observability_note": 'Statin-associated muscle symptoms on follow-up are moderately specific and commonly documented in OPD, but the underlying India-specific variant frequency is unverified — flagging risk without population evidence would violate the no-silent-substitution principle.',
        "opd_actionability_score": 2,
        "opd_actionability_note": 'Dose cap / switch to alternative statin is a routine OPD decision per CPIC once evidence permits a population claim.',
        "alert_template": 'Statin-associated myopathy may be influenced by SLCO1B1/ABCG2 variants, but NO Indian-specific allele frequency data was found in this search. This rule is retained as a documented gap, not an actionable flag — do not surface to doctors until Indian frequency data is obtained.',
        "needs_genomic_data": True,
        "ships_now": False,
        "data_quality": 'NO_INDIAN_DATA — closest proxy: pooled Asian/global meta-analyses, no India-specific study located',
    },
]

# Rules that should NOT ship to doctors until we have patient-specific outcome data
# or stronger Indian-specific evidence (observability_score < 2 and/or needs_genomic_data=True,
# and/or indian_frequency data is a proxy rather than India-specific).
_PGX_RULES_NEEDS_VOLUME: list[dict] = [r for r in _PGX_RULES if not r["ships_now"]]

# Convenience lookup: lowercase drug name -> list of rule_ids that trigger on it
_DRUG_TO_RULE_IDS: dict[str, list[str]] = {}
for _rule in _PGX_RULES:
    for _drug in _rule["trigger_drugs"]:
        _DRUG_TO_RULE_IDS.setdefault(_drug, []).append(_rule["rule_id"])


def get_rules_for_drug(drug_name: str, ships_now_only: bool = True) -> list[dict]:
    """Return PGx rules whose trigger_drugs include drug_name (case-insensitive).

    This is decision SUPPORT only: it surfaces a population-level pharmacogenomic
    risk flag for the doctor to review — it never returns a patient-specific result
    and must never be auto-actioned.
    """
    name = drug_name.strip().lower()
    ids = _DRUG_TO_RULE_IDS.get(name, [])
    rules = [r for r in _PGX_RULES if r["rule_id"] in ids]
    if ships_now_only:
        rules = [r for r in rules if r["ships_now"]]
    return rules
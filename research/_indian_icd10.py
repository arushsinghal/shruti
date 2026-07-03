"""Indian OPD diagnosis burden map with ICD-10 codes and Hinglish terms.

Sources (see accompanying sourcing/gap-flag report for full detail):
- India State-Level Disease Burden Initiative (ICMR/PHFI/IHME GBD 1990-2016), Lancet 2017;390:2437-2460,
  PMID 29150201; companion papers on CVD (PMID 30219317), diabetes (PMID 30219315),
  cancer (PMID 30219626), mental disorders (Lancet Psychiatry 2020, PMID 31879245).
- NFHS-5 (National Family Health Survey 2019-21), IIPS/MoHFW, plus secondary re-analyses
  (PMC10860231/PMID 38347505 anaemia; medRxiv 2025.09.17.25335963 hypertension;
  PMC10243276/PMID 37280601 ARI in children).
- Published Indian OPD morbidity-pattern studies: PMID 29302540, 38709793, 39736942, 30309742,
  32349770, 29302544, 31041230.
- Remaining ~100 diagnoses and ALL Hinglish terms are clinical-knowledge / vernacular-language
  placeholders (no India-specific literature citation located) -- each such entry is explicitly
  flagged via burden_source="clinical-knowledge placeholder..." and/or hinglish_source="inferred".
  A dedicated literature search for a published Hindi/Hinglish symptom-term lexicon (20+ PubMed
  queries) found NO citable source; see sourcing report for detail.

Generated: 2026-07-02
Methodology note: OPD_score deviates from a literal rank-multiplication (a raw DALY RANK of 1
would otherwise produce the SMALLEST, not largest, product). Instead: burden_score (0-100, higher
= more burden) x opd_manageability (0/0.5/1.0, clinical-judgment) x encounter_multiplier
(1.0 + literature encounter-frequency-fraction, or 1.0 neutral where no literature frequency was
found). Full derivation and every entry's exact source is in the accompanying gap report.

DISCLAIMER: This is a decision-support reference list for a doctor-gated clinical extractor, not
an autonomous diagnostic or coding tool. OPD_score ranks are a documented heuristic for triage of
which diagnoses a primary-care NLP pipeline should recognize first -- they are not a validated
epidemiological ranking and have not been benchmarked against ground truth Indian OPD registries.
"""

_INDIAN_OPD_DIAGNOSES: list[dict] = [
    {
        "rank": 1,
        "icd10_cm": 'D50.9',
        "icd10_who": 'D50.9',
        "canonical": 'Iron-deficiency anaemia',
        "common_names": ['anaemia', 'anemia', 'low haemoglobin', 'khoon ki kami'],
        "hinglish_names": ['khoon ki kami', 'kamzori', 'anaemia'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 78,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": "ICMR/PHFI/IHME 'India: Health of the Nation's States' Executive Summary, 2017 (top-10 nationally)",
        "encounter_freq": 0.571,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'NFHS-5 (2019-21), IIPS/MoHFW: 57.0% women 15-49y; adolescent girls 59.1%/boys 31.1% (NFHS-5 (2019-21), IIPS/MoHFW PIB Anaemia Mukt Bharat)',
        "opd_score": 122.538,
        "notes": None,
    },
    {
        "rank": 2,
        "icd10_cm": 'E11.9',
        "icd10_who": 'E11.9',
        "canonical": 'Diabetes mellitus (type 2)',
        "common_names": ['diabetes', 'sugar', 'T2DM'],
        "hinglish_names": ['sugar', 'madhumeh', 'sugar ki bimari'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 74,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'Tandon N et al., Lancet Glob Health 2018;6:e1352-e1362, PMID 30219315 (fastest-rising major NCD, +80% DALY-rate 1990-2016)',
        "encounter_freq": 0.452,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 31041230 (Bhubaneswar urban slum geriatric, 2019): 45.19% among urban geriatric population',
        "opd_score": 107.448,
        "notes": None,
    },
    {
        "rank": 3,
        "icd10_cm": 'M19.9',
        "icd10_who": 'M17.9',
        "canonical": 'Osteoarthritis',
        "common_names": ['osteoarthritis', 'OA', 'joint pain', 'knee pain'],
        "hinglish_names": ['ghutno mein dard', 'jodo ka dard', 'knee pain'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 65,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 39736942 (MMU camps Telangana, 2024): majority diagnosis among adult MMU camp patients; PMID 29302544 (Raichur Karnataka geriatric, 2017): orthopedic morbidities 50.5% (rural geriatric)',
        "encounter_freq": 0.505,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302544 (Raichur Karnataka geriatric, 2017)',
        "opd_score": 97.825,
        "notes": 'ICD-10-CM M19.9 = osteoarthritis unspecified site; ICD-10-WHO commonly indexes knee OA as M17.9',
    },
    {
        "rank": 4,
        "icd10_cm": 'A09',
        "icd10_who": 'A09',
        "canonical": 'Diarrhoeal disease (acute)',
        "common_names": ['diarrhoea', 'loose motions', 'gastroenteritis'],
        "hinglish_names": ['loose motion', 'dast', 'daast'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 90,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (rank 3)',
        "encounter_freq": 0.072,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'NFHS-5 (2019-21), IIPS/MoHFW: 7.2% under-5 2-week period prevalence',
        "opd_score": 96.48,
        "notes": None,
    },
    {
        "rank": 5,
        "icd10_cm": 'J44.9',
        "icd10_who": 'J44.9',
        "canonical": 'Chronic obstructive pulmonary disease',
        "common_names": ['COPD', 'chronic bronchitis', 'emphysema'],
        "hinglish_names": ['saans phoolna', 'purani khansi', 'dam ki bimari'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 95,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (rank 2)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 95.0,
        "notes": None,
    },
    {
        "rank": 6,
        "icd10_cm": 'O99.0',
        "icd10_who": 'O99.0',
        "canonical": 'Anaemia in pregnancy',
        "common_names": ['anaemia in pregnancy', 'pregnancy anemia'],
        "hinglish_names": ['pregnancy mein khoon ki kami', 'kamzori pregnancy mein'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 52,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": "NFHS-5 (2019-21), IIPS/MoHFW PIB 'Anaemia Mukt Bharat' release, 4 Feb 2022: 52.2% pregnant women 15-49y",
        "encounter_freq": 0.522,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'as above',
        "opd_score": 79.144,
        "notes": None,
    },
    {
        "rank": 7,
        "icd10_cm": 'A15.9',
        "icd10_who": 'A16.2',
        "canonical": 'Tuberculosis (pulmonary)',
        "common_names": ['TB', 'pulmonary TB', 'PTB'],
        "hinglish_names": ['TB', 'tapedik', 'kshay rog'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 75,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": "ICMR/PHFI/IHME 'India: Health of the Nation's States' Executive Summary, 2017 (top-10 nationally)",
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 75.0,
        "notes": 'ICD-10-CM A15.9 requires bacteriological/histological confirmation code; ICD-10-WHO A16.2 covers TB of lung, without mention of bacteriological/histological confirmation -- coding differs by confirmation status',
    },
    {
        "rank": 8,
        "icd10_cm": 'G43.9',
        "icd10_who": 'G43.9',
        "canonical": 'Migraine',
        "common_names": ['migraine', 'severe headache'],
        "hinglish_names": ['aadhe sir ka dard', 'migraine'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 70,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (top-10 DALY cause for women, India 2016)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 70.0,
        "notes": None,
    },
    {
        "rank": 9,
        "icd10_cm": 'M54.5',
        "icd10_who": 'M54.5',
        "canonical": 'Low back pain / neck pain',
        "common_names": ['back pain', 'LBP', 'neck pain', 'kamar dard'],
        "hinglish_names": ['kamar dard', 'gardan dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 70,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (top-10 DALY cause for women, India 2016)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 70.0,
        "notes": None,
    },
    {
        "rank": 10,
        "icd10_cm": 'F32.9',
        "icd10_who": 'F32.9',
        "canonical": 'Depressive disorder',
        "common_names": ['depression', 'low mood'],
        "hinglish_names": ['udaas rehna', 'man udaas', 'depression'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 65,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Mental Disorders Collaborators, Lancet Psychiatry 2020;7:148-161, PMID 31879245 (33.8% of mental-disorder DALYs, India 2017)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 65.0,
        "notes": None,
    },
    {
        "rank": 11,
        "icd10_cm": 'I10',
        "icd10_who": 'I10',
        "canonical": 'Essential hypertension',
        "common_names": ['hypertension', 'HTN', 'high BP', 'BP'],
        "hinglish_names": ['BP', 'BP high', 'blood pressure'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 62,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'NFHS-5 (2019-21), IIPS/MoHFW secondary re-analysis, medRxiv 2025.09.17.25335963 (JNC-7/ISH threshold: 21.78% men, 12.35% women); Factly Dec-2020 state-fact-sheet average ~24-25% men/22.5% women (NOT official national aggregate)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no single official NFHS-5 national headline figure located verbatim -- flagged as GAP; multiple proxy estimates given instead',
        "opd_score": 62.0,
        "notes": None,
    },
    {
        "rank": 12,
        "icd10_cm": 'A01.0',
        "icd10_who": 'A01.0',
        "canonical": 'Typhoid and paratyphoid fever',
        "common_names": ['typhoid', 'enteric fever', 'mottyjhar'],
        "hinglish_names": ['mottyjhar', 'typhoid', 'aanton ka bukhar'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 58,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (intestinal infectious diseases DALY-rate-ratio 61.75x expected; cause-group level, typhoid not separated)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 58.0,
        "notes": "GAP: GBD source reports only cause-GROUP ('intestinal infectious diseases, mainly typhoid/paratyphoid'); no pathogen-specific DALY rank found",
    },
    {
        "rank": 13,
        "icd10_cm": 'R50.9',
        "icd10_who": 'R50.9',
        "canonical": 'Fever of unknown/viral origin',
        "common_names": ['fever', 'bukhar', 'viral fever'],
        "hinglish_names": ['bukhar', 'tap', 'viral'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 50,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 29302540 (Odisha urban primary care, 2017): fever 11.4% (most common symptom, males); PMID 38709793 (ICPC-3 Odisha public facilities, 2024): most common reason for encounter across all facility tiers',
        "encounter_freq": 0.114,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302540 (Odisha urban primary care, 2017)',
        "opd_score": 55.7,
        "notes": None,
    },
    {
        "rank": 14,
        "icd10_cm": 'F41.9',
        "icd10_who": 'F41.9',
        "canonical": 'Anxiety disorder',
        "common_names": ['anxiety', 'generalised anxiety'],
        "hinglish_names": ['tension', 'ghabrahat', 'anxiety'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 55,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Mental Disorders Collaborators, Lancet Psychiatry 2020;7:148-161, PMID 31879245 (19.0% of mental-disorder DALYs, India 2017)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 55.0,
        "notes": None,
    },
    {
        "rank": 15,
        "icd10_cm": 'I25.9',
        "icd10_who": 'I25.9',
        "canonical": 'Ischaemic heart disease',
        "common_names": ['IHD', 'CAD', 'coronary artery disease'],
        "hinglish_names": ['dil ki bimari', 'heart problem', 'seene mein dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 100,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (rank 1)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 50.0,
        "notes": 'OPD role: symptom recognition, risk-factor management, referral for acute events',
    },
    {
        "rank": 16,
        "icd10_cm": 'K21.9',
        "icd10_who": 'K21.9',
        "canonical": 'Acid peptic disease / GERD',
        "common_names": ['acidity', 'gastritis', 'GERD', 'heartburn'],
        "hinglish_names": ['acidity', 'khatta dakaar', 'pet mein jalan'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 45,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 29302540 (Odisha urban primary care, 2017): heartburn 8.1% (males); PMID 31041230 (Bhubaneswar urban slum geriatric, 2019): acid peptic disease 37.78% (urban geriatric); PMID 32349770 (Odisha public/private primary care, 2020): leading diagnosis (public facility attendees)',
        "encounter_freq": 0.081,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302540 (Odisha urban primary care, 2017)',
        "opd_score": 48.645,
        "notes": None,
    },
    {
        "rank": 17,
        "icd10_cm": 'H25.9',
        "icd10_who": 'H25.9',
        "canonical": 'Cataract',
        "common_names": ['cataract', 'motiyabind'],
        "hinglish_names": ['motiyabind', 'aankh mein safedi'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 60,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 29302544 (Raichur Karnataka geriatric, 2017): cataract 50.4% (rural geriatric, Raichur Karnataka)',
        "encounter_freq": 0.504,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302544 (Raichur Karnataka geriatric, 2017)',
        "opd_score": 45.12,
        "notes": 'OPD role: screening and referral for surgery; not OPD-treatable itself, hence 0.5 manageability',
    },
    {
        "rank": 18,
        "icd10_cm": 'J18.9',
        "icd10_who": 'J18.9',
        "canonical": 'Lower respiratory infection / Pneumonia',
        "common_names": ['pneumonia', 'chest infection', 'LRI'],
        "hinglish_names": ['chest infection', 'seene mein infection', 'nimonia'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 85,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (rank 4)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 42.5,
        "notes": None,
    },
    {
        "rank": 19,
        "icd10_cm": 'M13.9',
        "icd10_who": 'M06.9',
        "canonical": 'Arthritis (unspecified/rheumatoid overlap)',
        "common_names": ['arthritis', 'joint pain', 'jodo mein dard'],
        "hinglish_names": ['jodo mein dard', 'gathiya'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 42,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 30309742 (Siddha OPD Tamil Nadu, 2018): arthritis 21% (Siddha OPD Tamil Nadu); PMID 38709793 (ICPC-3 Odisha public facilities, 2024): among top-9 reasons for encounter',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no single pooled % found',
        "opd_score": 42.0,
        "notes": None,
    },
    {
        "rank": 20,
        "icd10_cm": 'N39.0',
        "icd10_who": 'N39.0',
        "canonical": 'Urinary tract infection',
        "common_names": ['UTI', 'urine infection', 'peshab mein jalan'],
        "hinglish_names": ['peshab mein jalan', 'UTI', 'peshab ki takleef'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 21,
        "icd10_cm": 'R53.83',
        "icd10_who": 'R53',
        "canonical": 'Weakness / fatigue, unspecified',
        "common_names": ['weakness', 'kamzori', 'fatigue'],
        "hinglish_names": ['kamzori', 'thakaan'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 22,
        "icd10_cm": 'R10.9',
        "icd10_who": 'R10.4',
        "canonical": 'Abdominal pain, unspecified',
        "common_names": ['stomach pain', 'pet dard'],
        "hinglish_names": ['pet dard', 'pet mein dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 23,
        "icd10_cm": 'R05.9',
        "icd10_who": 'R05',
        "canonical": 'Cough, unspecified (chronic)',
        "common_names": ['chronic cough', 'purani khansi'],
        "hinglish_names": ['khansi', 'khasi', 'purani khansi'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 24,
        "icd10_cm": 'K30',
        "icd10_who": 'K30',
        "canonical": 'Dyspepsia (functional)',
        "common_names": ['indigestion', 'dyspepsia', 'badhazmi'],
        "hinglish_names": ['badhazmi', 'gas banna', 'indigestion'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 25,
        "icd10_cm": 'G44.209',
        "icd10_who": 'G44.2',
        "canonical": 'Tension-type headache',
        "common_names": ['tension headache', 'sir dard'],
        "hinglish_names": ['sir dard', 'sar dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 26,
        "icd10_cm": 'R50.9',
        "icd10_who": 'R50.9',
        "canonical": 'Fever in children (unspecified)',
        "common_names": ['bacha bukhar', 'child fever'],
        "hinglish_names": ['bachche ko bukhar', 'bachche ko tap'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": 'Distinct entry from adult fever for pediatric OPD coding pattern recognition',
    },
    {
        "rank": 27,
        "icd10_cm": 'K29.70',
        "icd10_who": 'K29.7',
        "canonical": 'Acute gastritis',
        "common_names": ['gastritis', 'acidity', 'pet mein jalan'],
        "hinglish_names": ['pet mein jalan', 'acidity', 'gastric problem'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 28,
        "icd10_cm": 'J02.9',
        "icd10_who": 'J02.9',
        "canonical": 'Pharyngitis / sore throat',
        "common_names": ['pharyngitis', 'sore throat', 'gale mein kharash'],
        "hinglish_names": ['gale mein kharash', 'gala kharab', 'gale mein dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 29,
        "icd10_cm": 'J20.9',
        "icd10_who": 'J20.9',
        "canonical": 'Acute bronchitis',
        "common_names": ['bronchitis', 'chest cold'],
        "hinglish_names": ['seene mein jamaav', 'chest cold'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 30,
        "icd10_cm": 'J45.909',
        "icd10_who": 'J45.9',
        "canonical": 'Bronchial asthma',
        "common_names": ['asthma', 'dama', 'wheezing'],
        "hinglish_names": ['dama', 'saans phoolna', 'asthma'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 31,
        "icd10_cm": 'Z34.90',
        "icd10_who": 'Z34.9',
        "canonical": 'Antenatal care / normal pregnancy supervision',
        "common_names": ['ANC visit', 'pregnancy checkup'],
        "hinglish_names": ['garbhavastha jaanch', 'pregnancy checkup'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 32,
        "icd10_cm": 'I63.9',
        "icd10_who": 'I64',
        "canonical": 'Cerebrovascular disease (stroke)',
        "common_names": ['stroke', 'CVA', 'brain attack'],
        "hinglish_names": ['lakwa', 'paksaghat', 'stroke'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 80,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (rank 5)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": 'ICD-10-WHO commonly codes unspecified stroke as I64; ICD-10-CM prefers I63.9 (cerebral infarction, unspecified) as default working code',
    },
    {
        "rank": 33,
        "icd10_cm": 'M54.9',
        "icd10_who": 'M54.5',
        "canonical": 'Chronic back pain (non-specific)',
        "common_names": ['chronic back pain', 'kamar dard'],
        "hinglish_names": ['kamar dard', 'purani kamar dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 32349770 (Odisha public/private primary care, 2020): chronic back pain among leading diagnoses, public facility attendees, Odisha',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 40.0,
        "notes": None,
    },
    {
        "rank": 34,
        "icd10_cm": 'R45.81',
        "icd10_who": 'X60-X84',
        "canonical": 'Self-harm / suicidal ideation',
        "common_names": ['self-harm', 'suicidal thoughts'],
        "hinglish_names": ['khudkushi ka khayal', 'marne ka man'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 68,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": "ICMR/PHFI/IHME 'India: Health of the Nation's States' Executive Summary, 2017 (top-10 DALY cause for men; DALY rate 1.8x global average)",
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 34.0,
        "notes": 'OPD role: screening and urgent psychiatric referral only, not autonomous management. ICD-10-CM uses R45.81 (symptom code) for OPD screening context; ICD-10-WHO classifies completed/attempted self-harm under X60-X84',
    },
    {
        "rank": 35,
        "icd10_cm": 'R42',
        "icd10_who": 'R42',
        "canonical": 'Vertigo / dizziness (BPPV and unspecified)',
        "common_names": ['vertigo', 'dizziness', 'giddiness'],
        "hinglish_names": ['chakkar aana', 'sar ghoomna'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 30,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 29302540 (Odisha urban primary care, 2017): vertigo/dizziness 3.6% (males)',
        "encounter_freq": 0.036,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302540 (Odisha urban primary care, 2017)',
        "opd_score": 31.08,
        "notes": None,
    },
    {
        "rank": 36,
        "icd10_cm": 'B20',
        "icd10_who": 'B20',
        "canonical": 'HIV/AIDS',
        "common_names": ['HIV', 'AIDS'],
        "hinglish_names": ['HIV', 'AIDS'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 60,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Initiative, Lancet 2017;390:2437-2460, PMID 29150201 (DALY rate ratio 3.61x expected)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 30.0,
        "notes": 'OPD role: screening, ART follow-up at ART centres; new diagnosis/complications refer to tertiary care',
    },
    {
        "rank": 37,
        "icd10_cm": 'J06.9',
        "icd10_who": 'J06.9',
        "canonical": 'Acute respiratory infection (upper, in children)',
        "common_names": ['ARI', 'URTI', 'cold', 'cough-cold'],
        "hinglish_names": ['sardi zukam', 'cold cough bachche mein'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 28,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'NFHS-5 (2019-21), IIPS/MoHFW: 2.8% under-5 2-week symptom prevalence (Varghese & Muhammad, BMC Pulm Med 2023, PMID 37280601)',
        "encounter_freq": 0.028,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'as above',
        "opd_score": 28.784,
        "notes": None,
    },
    {
        "rank": 38,
        "icd10_cm": 'G62.9',
        "icd10_who": 'G62.9',
        "canonical": 'Neuritis / peripheral neuropathy',
        "common_names": ['neuritis', 'nerve pain', 'neuropathy'],
        "hinglish_names": ['nason mein dard', 'sunn hona'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 30309742 (Siddha OPD Tamil Nadu, 2018): neuritis 10% (Siddha OPD Tamil Nadu)',
        "encounter_freq": 0.1,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 30309742 (Siddha OPD Tamil Nadu, 2018)',
        "opd_score": 27.5,
        "notes": None,
    },
    {
        "rank": 39,
        "icd10_cm": 'I09.9',
        "icd10_who": 'I09.9',
        "canonical": 'Rheumatic heart disease',
        "common_names": ['RHD', 'rheumatic valve disease'],
        "hinglish_names": ['dil ki bimari bachpan se', 'RHD'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 55,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'Prabhakaran D et al., Lancet Glob Health 2018;6:e1339-e1351, PMID 30219317 (DALY rate ratio 2.10-3.00x expected)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 27.5,
        "notes": None,
    },
    {
        "rank": 40,
        "icd10_cm": 'L08.9',
        "icd10_who": 'L08.9',
        "canonical": 'Bacterial skin infection (pyoderma)',
        "common_names": ['skin infection', 'pyoderma', 'boil', 'phoda'],
        "hinglish_names": ['phoda', 'skin mein infection', 'pus wali phunsi'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 41,
        "icd10_cm": 'L70.0',
        "icd10_who": 'L70.0',
        "canonical": 'Acne vulgaris',
        "common_names": ['acne', 'pimples', 'muhase'],
        "hinglish_names": ['muhase', 'pimples', 'chehre par daane'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 42,
        "icd10_cm": 'W54.0XXA',
        "icd10_who": 'W54',
        "canonical": 'Animal bite (dog/cat, for post-exposure prophylaxis)',
        "common_names": ['dog bite', 'animal bite'],
        "hinglish_names": ['kutte ne kaata', 'janwar ne kaata'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 43,
        "icd10_cm": 'M47.812',
        "icd10_who": 'M47.9',
        "canonical": 'Cervical spondylosis',
        "common_names": ['cervical spondylosis', 'neck stiffness', 'gardan dard'],
        "hinglish_names": ['gardan dard', 'gardan jam jaana'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 44,
        "icd10_cm": 'M79.7',
        "icd10_who": 'M79.1',
        "canonical": 'Fibromyalgia / generalised body ache',
        "common_names": ['body ache', 'fibromyalgia', 'badan dard'],
        "hinglish_names": ['badan dard', 'poore sharir mein dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 45,
        "icd10_cm": 'S00.90',
        "icd10_who": 'T14.0',
        "canonical": 'Contusion / soft tissue injury',
        "common_names": ['bruise', 'contusion'],
        "hinglish_names": ['chot lagna', 'neel padna'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 46,
        "icd10_cm": 'S93.409A',
        "icd10_who": 'T14.3',
        "canonical": 'Sprain/strain (ankle/knee, minor)',
        "common_names": ['sprain', 'strain', 'moch'],
        "hinglish_names": ['moch aana', 'pair mudna'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 47,
        "icd10_cm": 'L50.9',
        "icd10_who": 'L50.9',
        "canonical": 'Urticaria',
        "common_names": ['urticaria', 'hives', 'allergy rash'],
        "hinglish_names": ['allergy', 'khujli wale daane', 'sharir par chakatte'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 48,
        "icd10_cm": 'F17.200',
        "icd10_who": 'F17.2',
        "canonical": 'Tobacco use disorder',
        "common_names": ['tobacco use', 'smoking', 'gutkha/tambaku use'],
        "hinglish_names": ['tambaku ki lat', 'gutkha khana', 'smoking'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 49,
        "icd10_cm": 'M54.30',
        "icd10_who": 'M54.3',
        "canonical": 'Sciatica',
        "common_names": ['sciatica', 'leg pain radiating from back'],
        "hinglish_names": ['taang mein jhanjhanahat', 'sciatica dard'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 50,
        "icd10_cm": 'H52.10',
        "icd10_who": 'H52.1',
        "canonical": 'Refractive error (myopia/hyperopia)',
        "common_names": ['refractive error', 'weak eyesight', 'chashma'],
        "hinglish_names": ['chashme ka number', 'kam dikhna'],
        "hinglish_source": 'inferred',  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 51,
        "icd10_cm": 'S01.90',
        "icd10_who": 'T14.1',
        "canonical": 'Minor laceration / wound',
        "common_names": ['cut', 'wound', 'chot'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 52,
        "icd10_cm": 'B82.9',
        "icd10_who": 'B82.9',
        "canonical": 'Worm infestation (pediatric)',
        "common_names": ['worms (child)', 'pinworm'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 53,
        "icd10_cm": 'J03.90',
        "icd10_who": 'J03.9',
        "canonical": 'Acute tonsillopharyngitis (pediatric)',
        "common_names": ['throat infection (child)', 'pediatric tonsillopharyngitis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 54,
        "icd10_cm": 'R62.51',
        "icd10_who": 'E44.1',
        "canonical": 'Failure to thrive / malnutrition (child)',
        "common_names": ['malnutrition', 'failure to thrive', 'kamzori'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 55,
        "icd10_cm": 'F45.9',
        "icd10_who": 'F45.9',
        "canonical": 'Anxiety with somatic symptoms (somatoform)',
        "common_names": ['somatic symptoms', 'stress-related body pain'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 56,
        "icd10_cm": 'G47.00',
        "icd10_who": 'F51.0',
        "canonical": 'Insomnia',
        "common_names": ['insomnia', 'neend na aana', 'sleeplessness'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 57,
        "icd10_cm": 'N92.6',
        "icd10_who": 'N92.6',
        "canonical": 'Menstrual disorders (menorrhagia/oligomenorrhea)',
        "common_names": ['irregular periods', 'period problem', 'masik dharm samasya'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 58,
        "icd10_cm": 'N76.0',
        "icd10_who": 'N76.0',
        "canonical": 'Vaginal discharge / vaginitis',
        "common_names": ['white discharge', 'leucorrhoea', 'safed pani'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 59,
        "icd10_cm": 'E28.2',
        "icd10_who": 'E28.2',
        "canonical": 'Polycystic ovary syndrome (PCOS)',
        "common_names": ['PCOS', 'PCOD'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 60,
        "icd10_cm": 'N94.6',
        "icd10_who": 'N94.4',
        "canonical": 'Dysmenorrhea',
        "common_names": ['period pain', 'dysmenorrhea', 'masik dharm dard'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 61,
        "icd10_cm": 'L30.9',
        "icd10_who": 'L30.9',
        "canonical": 'Eczema / atopic dermatitis',
        "common_names": ['eczema', 'dermatitis', 'khujli wali skin'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 62,
        "icd10_cm": 'E66.9',
        "icd10_who": 'E66.9',
        "canonical": 'Obesity',
        "common_names": ['obesity', 'overweight', 'mota'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 63,
        "icd10_cm": 'L25.9',
        "icd10_who": 'L25.9',
        "canonical": 'Contact dermatitis',
        "common_names": ['contact dermatitis', 'allergy from contact'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 64,
        "icd10_cm": 'J01.90',
        "icd10_who": 'J01.9',
        "canonical": 'Sinusitis (acute)',
        "common_names": ['sinusitis', 'sinus infection'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 65,
        "icd10_cm": 'J11.1',
        "icd10_who": 'J11.1',
        "canonical": 'Influenza',
        "common_names": ['flu', 'influenza'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 66,
        "icd10_cm": 'H66.90',
        "icd10_who": 'H66.9',
        "canonical": 'Otitis media (acute)',
        "common_names": ['ear infection', 'otitis media', 'kaan dard'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 67,
        "icd10_cm": 'K58.9',
        "icd10_who": 'K58.9',
        "canonical": 'Irritable bowel syndrome',
        "common_names": ['IBS', 'spastic colon'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 68,
        "icd10_cm": 'K59.00',
        "icd10_who": 'K59.0',
        "canonical": 'Constipation',
        "common_names": ['constipation', 'kabj'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 69,
        "icd10_cm": 'B82.9',
        "icd10_who": 'B82.9',
        "canonical": 'Intestinal worm infestation',
        "common_names": ['worms', 'keede', 'helminthiasis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 70,
        "icd10_cm": 'J04.0',
        "icd10_who": 'J04.0',
        "canonical": 'Acute laryngitis',
        "common_names": ['laryngitis', 'hoarseness', 'awaaz baithna'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 71,
        "icd10_cm": 'J45.901',
        "icd10_who": 'J45.9',
        "canonical": 'Reactive airway disease (pediatric wheeze)',
        "common_names": ['wheezing child', 'bachche ko saans phoolna'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 72,
        "icd10_cm": 'E78.5',
        "icd10_who": 'E78.5',
        "canonical": 'Dyslipidemia',
        "common_names": ['high cholesterol', 'dyslipidemia'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 73,
        "icd10_cm": 'A08.4',
        "icd10_who": 'A08.4',
        "canonical": 'Gastroenteritis, viral',
        "common_names": ['stomach flu', 'viral gastroenteritis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 74,
        "icd10_cm": 'B86',
        "icd10_who": 'B86',
        "canonical": 'Scabies',
        "common_names": ['scabies', 'khujli'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 75,
        "icd10_cm": 'R00.2',
        "icd10_who": 'R00.2',
        "canonical": 'Generalized anxiety with palpitations',
        "common_names": ['palpitations', 'dil ki dhadkan'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 76,
        "icd10_cm": 'R63.0',
        "icd10_who": 'R63.0',
        "canonical": 'Loss of appetite',
        "common_names": ['loss of appetite', 'bhookh na lagna'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 77,
        "icd10_cm": 'J30.9',
        "icd10_who": 'J30.4',
        "canonical": 'Allergic rhinitis',
        "common_names": ['allergic rhinitis', 'nasal allergy', 'sardi jukam'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 78,
        "icd10_cm": 'H10.9',
        "icd10_who": 'H10.9',
        "canonical": 'Conjunctivitis (acute)',
        "common_names": ['conjunctivitis', 'eye infection', 'aankh aana'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 79,
        "icd10_cm": 'E03.9',
        "icd10_who": 'E03.9',
        "canonical": 'Hypothyroidism',
        "common_names": ['hypothyroidism', 'thyroid problem', 'low thyroid'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 80,
        "icd10_cm": 'R11.10',
        "icd10_who": 'R11',
        "canonical": 'Nausea and vomiting',
        "common_names": ['vomiting', 'ulti', 'nausea'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 81,
        "icd10_cm": 'J03.90',
        "icd10_who": 'J03.9',
        "canonical": 'Tonsillitis (acute)',
        "common_names": ['tonsillitis', 'throat gland infection'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 25.0,
        "notes": None,
    },
    {
        "rank": 82,
        "icd10_cm": 'B35.9',
        "icd10_who": 'B35.9',
        "canonical": 'Fungal skin infection (dermatophytosis)',
        "common_names": ['fungal infection', 'ringworm', 'dadd', 'tinea'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 22,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 30309742 (Siddha OPD Tamil Nadu, 2018): fungal diseases 7% (Siddha OPD Tamil Nadu)',
        "encounter_freq": 0.07,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 30309742 (Siddha OPD Tamil Nadu, 2018)',
        "opd_score": 23.54,
        "notes": None,
    },
    {
        "rank": 83,
        "icd10_cm": 'F20.9',
        "icd10_who": 'F20.9',
        "canonical": 'Schizophrenia',
        "common_names": ['schizophrenia', 'psychosis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 40,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Mental Disorders Collaborators, Lancet Psychiatry 2020;7:148-161, PMID 31879245 (9.8% of mental-disorder DALYs, India 2017)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 20.0,
        "notes": None,
    },
    {
        "rank": 84,
        "icd10_cm": 'F31.9',
        "icd10_who": 'F31.9',
        "canonical": 'Bipolar disorder',
        "common_names": ['bipolar disorder', 'manic depression'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 35,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'India State-Level Disease Burden Mental Disorders Collaborators, Lancet Psychiatry 2020;7:148-161, PMID 31879245 (6.9% of mental-disorder DALYs, India 2017)',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 17.5,
        "notes": None,
    },
    {
        "rank": 85,
        "icd10_cm": 'J06.9',
        "icd10_who": 'J06.9',
        "canonical": 'Acute pharyngotonsillitis with fever (viral)',
        "common_names": ['viral fever with sore throat', 'pharyngotonsillitis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": 'May overlap with URTI/fever entries; kept separate as doctors code distinctly',
    },
    {
        "rank": 86,
        "icd10_cm": 'J32.9',
        "icd10_who": 'J32.9',
        "canonical": 'Chronic sinusitis',
        "common_names": ['chronic sinusitis', 'long-standing sinus infection'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 87,
        "icd10_cm": 'T30.0',
        "icd10_who": 'T30.0',
        "canonical": 'Burns (minor, first/second degree)',
        "common_names": ['burn', 'jalna'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 88,
        "icd10_cm": 'N95.1',
        "icd10_who": 'N95.1',
        "canonical": 'Menopausal symptoms',
        "common_names": ['menopause', 'menopausal symptoms'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 89,
        "icd10_cm": 'H61.20',
        "icd10_who": 'H61.2',
        "canonical": 'Wax impaction (ear)',
        "common_names": ['ear wax', 'kaan mein mail'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 90,
        "icd10_cm": 'A06.9',
        "icd10_who": 'A06.9',
        "canonical": 'Amoebiasis',
        "common_names": ['amoebiasis', 'amoebic dysentery'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 91,
        "icd10_cm": 'M10.9',
        "icd10_who": 'M10.9',
        "canonical": 'Gout',
        "common_names": ['gout', 'uric acid'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 92,
        "icd10_cm": 'E55.9',
        "icd10_who": 'E55.9',
        "canonical": 'Vitamin D deficiency',
        "common_names": ['vitamin D deficiency', 'low vitamin D'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 93,
        "icd10_cm": 'E53.8',
        "icd10_who": 'E53.9',
        "canonical": 'Vitamin B12 deficiency',
        "common_names": ['B12 deficiency', 'low B12'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 94,
        "icd10_cm": 'B15.9',
        "icd10_who": 'B15.9',
        "canonical": 'Viral hepatitis A',
        "common_names": ['hepatitis A', 'jaundice', 'peeliya'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 95,
        "icd10_cm": 'A05.9',
        "icd10_who": 'A05.9',
        "canonical": 'Food poisoning',
        "common_names": ['food poisoning', 'foodborne illness'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 96,
        "icd10_cm": 'B01.9',
        "icd10_who": 'B01.9',
        "canonical": 'Chickenpox (varicella)',
        "common_names": ['chickenpox', 'mata', 'chicken pox'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 97,
        "icd10_cm": 'A92.0',
        "icd10_who": 'A92.0',
        "canonical": 'Chikungunya fever',
        "common_names": ['chikungunya', 'chikungunya fever'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 15.0,
        "notes": None,
    },
    {
        "rank": 98,
        "icd10_cm": 'K02.9',
        "icd10_who": 'K02.9',
        "canonical": 'Dental caries / dental problems',
        "common_names": ['dental caries', 'cavity', 'tooth decay'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 24,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'PMID 29302544 (Raichur Karnataka geriatric, 2017): dental problems 23.9% (rural geriatric, Raichur Karnataka)',
        "encounter_freq": 0.239,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'PMID 29302544 (Raichur Karnataka geriatric, 2017)',
        "opd_score": 14.868,
        "notes": None,
    },
    {
        "rank": 99,
        "icd10_cm": 'R17',
        "icd10_who": 'R17',
        "canonical": 'Jaundice, unspecified',
        "common_names": ['jaundice', 'peeliya'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": None,
    },
    {
        "rank": 100,
        "icd10_cm": 'N18.9',
        "icd10_who": 'N18.9',
        "canonical": 'Chronic kidney disease',
        "common_names": ['CKD', 'kidney disease', 'gurda kharab'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": None,
    },
    {
        "rank": 101,
        "icd10_cm": 'A97.0',
        "icd10_who": 'A90',
        "canonical": 'Dengue fever',
        "common_names": ['dengue', 'dengue bukhar'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": 'ICD-10-CM A97.0 = dengue without warning signs; ICD-10-WHO uses A90 for classic dengue fever',
    },
    {
        "rank": 102,
        "icd10_cm": 'N20.0',
        "icd10_who": 'N20.0',
        "canonical": 'Renal calculus (kidney stone)',
        "common_names": ['kidney stone', 'pathri'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": None,
    },
    {
        "rank": 103,
        "icd10_cm": 'K27.9',
        "icd10_who": 'K27.9',
        "canonical": 'Peptic ulcer disease',
        "common_names": ['peptic ulcer', 'stomach ulcer'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": None,
    },
    {
        "rank": 104,
        "icd10_cm": 'B54',
        "icd10_who": 'B54',
        "canonical": 'Malaria (P. vivax/falciparum, unspecified)',
        "common_names": ['malaria', 'malaria fever'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 25,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 12.5,
        "notes": None,
    },
    {
        "rank": 105,
        "icd10_cm": 'B07.9',
        "icd10_who": 'B07.9',
        "canonical": 'Warts (viral)',
        "common_names": ['warts', 'masse'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 106,
        "icd10_cm": 'H10.10',
        "icd10_who": 'H10.1',
        "canonical": 'Seasonal allergic conjunctivitis',
        "common_names": ['allergic conjunctivitis', 'seasonal eye allergy'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 107,
        "icd10_cm": 'L01.00',
        "icd10_who": 'L01.0',
        "canonical": 'Impetigo',
        "common_names": ['impetigo', 'school sores'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 108,
        "icd10_cm": 'B08.1',
        "icd10_who": 'B08.1',
        "canonical": 'Molluscum contagiosum',
        "common_names": ['molluscum', 'molluscum contagiosum'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 109,
        "icd10_cm": 'H60.90',
        "icd10_who": 'H60.9',
        "canonical": 'Acute otitis externa',
        "common_names": ['ear canal infection', 'otitis externa'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 110,
        "icd10_cm": 'B80',
        "icd10_who": 'B80',
        "canonical": 'Threadworm/pinworm (Enterobiasis)',
        "common_names": ['pinworm', 'threadworm'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 111,
        "icd10_cm": 'B36.9',
        "icd10_who": 'H62.2',
        "canonical": 'Otomycosis (fungal ear infection)',
        "common_names": ['fungal ear infection', 'otomycosis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 112,
        "icd10_cm": 'L22',
        "icd10_who": 'L22',
        "canonical": 'Diaper rash / napkin dermatitis',
        "common_names": ['diaper rash', 'napkin rash'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 113,
        "icd10_cm": 'H93.19',
        "icd10_who": 'H93.1',
        "canonical": 'Tinnitus',
        "common_names": ['ringing in ears', 'tinnitus'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 114,
        "icd10_cm": 'H00.19',
        "icd10_who": 'H00.1',
        "canonical": 'Chalazion / stye (hordeolum)',
        "common_names": ['stye', 'chalazion', 'aankh mein ganth'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 115,
        "icd10_cm": 'M72.2',
        "icd10_who": 'M77.3',
        "canonical": 'Plantar fasciitis / heel pain',
        "common_names": ['heel pain', 'plantar fasciitis', 'eddi mein dard'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 116,
        "icd10_cm": 'M75.00',
        "icd10_who": 'M75.0',
        "canonical": 'Frozen shoulder',
        "common_names": ['frozen shoulder', 'shoulder stiffness'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 117,
        "icd10_cm": 'L74.0',
        "icd10_who": 'L74.0',
        "canonical": 'Prickly heat / miliaria',
        "common_names": ['prickly heat', 'miliaria', 'gharmi daane'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 118,
        "icd10_cm": 'L73.9',
        "icd10_who": 'L73.9',
        "canonical": 'Folliculitis',
        "common_names": ['folliculitis', 'hair follicle infection'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 119,
        "icd10_cm": 'L84',
        "icd10_who": 'L84',
        "canonical": 'Corn/callus',
        "common_names": ['corn', 'callus'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 120,
        "icd10_cm": 'B26.9',
        "icd10_who": 'B26.9',
        "canonical": 'Mumps',
        "common_names": ['mumps', 'kanpedi'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 121,
        "icd10_cm": 'R04.0',
        "icd10_who": 'R04.0',
        "canonical": 'Epistaxis (nosebleed)',
        "common_names": ['nosebleed', 'naak se khoon'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 122,
        "icd10_cm": 'B85.2',
        "icd10_who": 'B85.2',
        "canonical": 'Pediculosis (lice infestation)',
        "common_names": ['lice', 'jooye'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 123,
        "icd10_cm": 'B02.9',
        "icd10_who": 'B02.9',
        "canonical": 'Herpes zoster',
        "common_names": ['shingles', 'herpes zoster'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 124,
        "icd10_cm": 'N52.9',
        "icd10_who": 'N52.9',
        "canonical": 'Erectile dysfunction',
        "common_names": ['erectile dysfunction', 'ED'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 1.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 8.0,
        "notes": None,
    },
    {
        "rank": 125,
        "icd10_cm": 'R55',
        "icd10_who": 'R55',
        "canonical": 'Syncope (fainting)',
        "common_names": ['fainting', 'behosh hona', 'syncope'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 126,
        "icd10_cm": 'F10.20',
        "icd10_who": 'F10.2',
        "canonical": 'Alcohol use disorder',
        "common_names": ['alcohol dependence', 'sharab ki lat'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 127,
        "icd10_cm": 'E05.90',
        "icd10_who": 'E05.9',
        "canonical": 'Hyperthyroidism',
        "common_names": ['hyperthyroidism', 'thyrotoxicosis'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 128,
        "icd10_cm": 'R63.4',
        "icd10_who": 'R63.4',
        "canonical": 'Weight loss, unspecified',
        "common_names": ['weight loss', 'unintentional weight loss'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 129,
        "icd10_cm": 'K64.9',
        "icd10_who": 'K64.9',
        "canonical": 'Hemorrhoids',
        "common_names": ['piles', 'hemorrhoids', 'bawaseer'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 130,
        "icd10_cm": 'L03.90',
        "icd10_who": 'L03.9',
        "canonical": 'Cellulitis',
        "common_names": ['cellulitis', 'skin infection with swelling'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 131,
        "icd10_cm": 'R60.9',
        "icd10_who": 'R60.9',
        "canonical": 'Edema, unspecified (pedal edema)',
        "common_names": ['swelling in legs', 'pair mein sujan'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 132,
        "icd10_cm": 'N40.0',
        "icd10_who": 'N40',
        "canonical": 'Benign prostatic hyperplasia',
        "common_names": ['BPH', 'enlarged prostate'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 133,
        "icd10_cm": 'H66.3X9',
        "icd10_who": 'H66.3',
        "canonical": 'Otitis media, chronic suppurative',
        "common_names": ['chronic ear discharge', 'kaan se pani'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 15,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 7.5,
        "notes": None,
    },
    {
        "rank": 134,
        "icd10_cm": 'B05.9',
        "icd10_who": 'B05.9',
        "canonical": 'Measles',
        "common_names": ['measles', 'khasra'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 135,
        "icd10_cm": 'D63.8',
        "icd10_who": 'D63.8',
        "canonical": 'Anemia of chronic disease',
        "common_names": ['anemia in chronic illness', 'chronic disease anaemia'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 136,
        "icd10_cm": 'I83.90',
        "icd10_who": 'I83.9',
        "canonical": 'Varicose veins',
        "common_names": ['varicose veins', 'swollen leg veins'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 137,
        "icd10_cm": 'A64',
        "icd10_who": 'A64',
        "canonical": 'Sexually transmitted infection, unspecified',
        "common_names": ['STI', 'STD'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 138,
        "icd10_cm": 'G56.00',
        "icd10_who": 'G56.0',
        "canonical": 'Carpal tunnel syndrome',
        "common_names": ['carpal tunnel', 'hand numbness'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 139,
        "icd10_cm": 'G45.9',
        "icd10_who": 'G45.9',
        "canonical": 'Ischemic stroke sequelae / TIA',
        "common_names": ['TIA', 'mini stroke'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 140,
        "icd10_cm": 'D17.9',
        "icd10_who": 'D17.9',
        "canonical": 'Lipoma',
        "common_names": ['lipoma', 'fatty lump'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 141,
        "icd10_cm": 'L72.3',
        "icd10_who": 'L72.3',
        "canonical": 'Sebaceous cyst',
        "common_names": ['sebaceous cyst', 'cyst'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 142,
        "icd10_cm": 'R62.50',
        "icd10_who": 'R62.9',
        "canonical": 'Growth/developmental concern (pediatric)',
        "common_names": ['delayed growth', 'developmental delay'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 143,
        "icd10_cm": 'I73.9',
        "icd10_who": 'I73.9',
        "canonical": 'Peripheral vascular disease / claudication',
        "common_names": ['poor circulation', 'claudication'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 144,
        "icd10_cm": 'L80',
        "icd10_who": 'L80',
        "canonical": 'Vitiligo',
        "common_names": ['vitiligo', 'safed daag', 'leucoderma'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 145,
        "icd10_cm": 'L40.9',
        "icd10_who": 'L40.9',
        "canonical": 'Psoriasis',
        "common_names": ['psoriasis', 'scaly skin patches'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 146,
        "icd10_cm": 'R00.1',
        "icd10_who": 'R00.0',
        "canonical": 'Sinus bradycardia/tachycardia (unspecified arrhythmia)',
        "common_names": ['irregular heartbeat', 'arrhythmia'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 147,
        "icd10_cm": 'K60.2',
        "icd10_who": 'K60.2',
        "canonical": 'Fissure in ano',
        "common_names": ['anal fissure', 'fissure'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 148,
        "icd10_cm": 'N72',
        "icd10_who": 'N72',
        "canonical": 'Cervicitis / pelvic inflammatory disease (mild, OPD-manageable)',
        "common_names": ['cervicitis', 'pelvic infection'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.5,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 4.0,
        "notes": None,
    },
    {
        "rank": 149,
        "icd10_cm": 'R04.2',
        "icd10_who": 'R04.2',
        "canonical": 'Hemoptysis',
        "common_names": ['coughing blood', 'khoon ki khansi'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 0.0,
        "notes": 'Hospital referral typically required; kept for completeness with manageability 0',
    },
    {
        "rank": 150,
        "icd10_cm": 'O20.0',
        "icd10_who": 'O20.0',
        "canonical": 'Threatened abortion / early pregnancy bleeding',
        "common_names": ['threatened miscarriage', 'pregnancy bleeding'],
        "hinglish_names": [],
        "hinglish_source": None,  # "published" | "inferred" | None (not yet annotated, rank>50)
        "opd_manageability": 0.0,  # 1.0=fully OPD, 0.5=mixed, 0=hospital-only (clinical-judgment)
        "burden_score": 8,  # 0-100, higher=more burden; see burden_source for provenance
        "burden_source": 'clinical-knowledge placeholder (no India-specific literature/registry citation found) -- NOT a sourced number',
        "encounter_freq": None,  # fraction [0,1] from literature, or None if not found
        "encounter_source": 'no literature encounter-frequency found',
        "opd_score": 0.0,
        "notes": 'Requires urgent referral; OPD role limited to recognition',
    },
]

# Fast lookup: any name (English common name or Hinglish term, lowercased) -> ICD-10-CM code.
# NOTE ON AMBIGUITY: some terms are used by patients/doctors for more than one distinct diagnosis
# (e.g. "kamzori" can mean anaemia, generalised fatigue, or child malnutrition; "acidity" can mean
# GERD or acute gastritis). Where ambiguous, this dict maps to the HIGHER OPD_score (more common)
# condition -- see _AMBIGUOUS_LOOKUP_TERMS below for the full set of alternate mappings a clinical
# extractor should disambiguate using context (age, associated symptoms, duration).
_DIAGNOSIS_LOOKUP: dict[str, str] = {
    'aadhe sir ka dard': 'G43.9',
    'aankh aana': 'H10.9',
    'aankh mein ganth': 'H00.19',
    'aankh mein safedi': 'H25.9',
    'aanton ka bukhar': 'A01.0',
    'acidity': 'K21.9',
    'acne': 'L70.0',
    'aids': 'B20',
    'alcohol dependence': 'F10.20',
    'allergic conjunctivitis': 'H10.10',
    'allergic rhinitis': 'J30.9',
    'allergy': 'L50.9',
    'allergy from contact': 'L25.9',
    'allergy rash': 'L50.9',
    'amoebiasis': 'A06.9',
    'amoebic dysentery': 'A06.9',
    'anaemia': 'D50.9',
    'anaemia in pregnancy': 'O99.0',
    'anal fissure': 'K60.2',
    'anc visit': 'Z34.90',
    'anemia': 'D50.9',
    'anemia in chronic illness': 'D63.8',
    'animal bite': 'W54.0XXA',
    'anxiety': 'F41.9',
    'ari': 'J06.9',
    'arrhythmia': 'R00.1',
    'arthritis': 'M13.9',
    'asthma': 'J45.909',
    'awaaz baithna': 'J04.0',
    'b12 deficiency': 'E53.8',
    'bacha bukhar': 'R50.9',
    'bachche ko bukhar': 'R50.9',
    'bachche ko saans phoolna': 'J45.901',
    'bachche ko tap': 'R50.9',
    'back pain': 'M54.5',
    'badan dard': 'M79.7',
    'badhazmi': 'K30',
    'bawaseer': 'K64.9',
    'behosh hona': 'R55',
    'bhookh na lagna': 'R63.0',
    'bipolar disorder': 'F31.9',
    'blood pressure': 'I10',
    'body ache': 'M79.7',
    'boil': 'L08.9',
    'bp': 'I10',
    'bp high': 'I10',
    'bph': 'N40.0',
    'brain attack': 'I63.9',
    'bronchitis': 'J20.9',
    'bruise': 'S00.90',
    'bukhar': 'R50.9',
    'burn': 'T30.0',
    'cad': 'I25.9',
    'callus': 'L84',
    'carpal tunnel': 'G56.00',
    'cataract': 'H25.9',
    'cavity': 'K02.9',
    'cellulitis': 'L03.90',
    'cervical spondylosis': 'M47.812',
    'cervicitis': 'N72',
    'chakkar aana': 'R42',
    'chalazion': 'H00.19',
    'chashma': 'H52.10',
    'chashme ka number': 'H52.10',
    'chehre par daane': 'L70.0',
    'chest cold': 'J20.9',
    'chest infection': 'J18.9',
    'chicken pox': 'B01.9',
    'chickenpox': 'B01.9',
    'chikungunya': 'A92.0',
    'chikungunya fever': 'A92.0',
    'child fever': 'R50.9',
    'chot': 'S01.90',
    'chot lagna': 'S00.90',
    'chronic back pain': 'M54.9',
    'chronic bronchitis': 'J44.9',
    'chronic cough': 'R05.9',
    'chronic disease anaemia': 'D63.8',
    'chronic ear discharge': 'H66.3X9',
    'chronic sinusitis': 'J32.9',
    'ckd': 'N18.9',
    'claudication': 'I73.9',
    'cold': 'J06.9',
    'cold cough bachche mein': 'J06.9',
    'conjunctivitis': 'H10.9',
    'constipation': 'K59.00',
    'contact dermatitis': 'L25.9',
    'contusion': 'S00.90',
    'copd': 'J44.9',
    'corn': 'L84',
    'coronary artery disease': 'I25.9',
    'cough-cold': 'J06.9',
    'coughing blood': 'R04.2',
    'cut': 'S01.90',
    'cva': 'I63.9',
    'cyst': 'L72.3',
    'daast': 'A09',
    'dadd': 'B35.9',
    'dam ki bimari': 'J44.9',
    'dama': 'J45.909',
    'dast': 'A09',
    'delayed growth': 'R62.50',
    'dengue': 'A97.0',
    'dengue bukhar': 'A97.0',
    'dental caries': 'K02.9',
    'depression': 'F32.9',
    'dermatitis': 'L30.9',
    'developmental delay': 'R62.50',
    'diabetes': 'E11.9',
    'diaper rash': 'L22',
    'diarrhoea': 'A09',
    'dil ki bimari': 'I25.9',
    'dil ki bimari bachpan se': 'I09.9',
    'dil ki dhadkan': 'R00.2',
    'dizziness': 'R42',
    'dog bite': 'W54.0XXA',
    'dyslipidemia': 'E78.5',
    'dysmenorrhea': 'N94.6',
    'dyspepsia': 'K30',
    'ear canal infection': 'H60.90',
    'ear infection': 'H66.90',
    'ear wax': 'H61.20',
    'eczema': 'L30.9',
    'ed': 'N52.9',
    'eddi mein dard': 'M72.2',
    'emphysema': 'J44.9',
    'enlarged prostate': 'N40.0',
    'enteric fever': 'A01.0',
    'erectile dysfunction': 'N52.9',
    'eye infection': 'H10.9',
    'failure to thrive': 'R62.51',
    'fainting': 'R55',
    'fatigue': 'R53.83',
    'fatty lump': 'D17.9',
    'fever': 'R50.9',
    'fibromyalgia': 'M79.7',
    'fissure': 'K60.2',
    'flu': 'J11.1',
    'folliculitis': 'L73.9',
    'food poisoning': 'A05.9',
    'foodborne illness': 'A05.9',
    'frozen shoulder': 'M75.00',
    'fungal ear infection': 'B36.9',
    'fungal infection': 'B35.9',
    'gala kharab': 'J02.9',
    'gale mein dard': 'J02.9',
    'gale mein kharash': 'J02.9',
    'garbhavastha jaanch': 'Z34.90',
    'gardan dard': 'M54.5',
    'gardan jam jaana': 'M47.812',
    'gas banna': 'K30',
    'gastric problem': 'K29.70',
    'gastritis': 'K21.9',
    'gastroenteritis': 'A09',
    'gathiya': 'M13.9',
    'generalised anxiety': 'F41.9',
    'gerd': 'K21.9',
    'ghabrahat': 'F41.9',
    'gharmi daane': 'L74.0',
    'ghutno mein dard': 'M19.9',
    'giddiness': 'R42',
    'gout': 'M10.9',
    'gurda kharab': 'N18.9',
    'gutkha khana': 'F17.200',
    'gutkha/tambaku use': 'F17.200',
    'hair follicle infection': 'L73.9',
    'hand numbness': 'G56.00',
    'heart problem': 'I25.9',
    'heartburn': 'K21.9',
    'heel pain': 'M72.2',
    'helminthiasis': 'B82.9',
    'hemorrhoids': 'K64.9',
    'hepatitis a': 'B15.9',
    'herpes zoster': 'B02.9',
    'high bp': 'I10',
    'high cholesterol': 'E78.5',
    'hiv': 'B20',
    'hives': 'L50.9',
    'hoarseness': 'J04.0',
    'htn': 'I10',
    'hypertension': 'I10',
    'hyperthyroidism': 'E05.90',
    'hypothyroidism': 'E03.9',
    'ibs': 'K58.9',
    'ihd': 'I25.9',
    'impetigo': 'L01.00',
    'indigestion': 'K30',
    'influenza': 'J11.1',
    'insomnia': 'G47.00',
    'irregular heartbeat': 'R00.1',
    'irregular periods': 'N92.6',
    'jalna': 'T30.0',
    'janwar ne kaata': 'W54.0XXA',
    'jaundice': 'B15.9',
    'jodo ka dard': 'M19.9',
    'jodo mein dard': 'M13.9',
    'joint pain': 'M19.9',
    'jooye': 'B85.2',
    'kaan dard': 'H66.90',
    'kaan mein mail': 'H61.20',
    'kaan se pani': 'H66.3X9',
    'kabj': 'K59.00',
    'kam dikhna': 'H52.10',
    'kamar dard': 'M54.5',
    'kamzori': 'D50.9',
    'kamzori pregnancy mein': 'O99.0',
    'kanpedi': 'B26.9',
    'keede': 'B82.9',
    'khansi': 'R05.9',
    'khasi': 'R05.9',
    'khasra': 'B05.9',
    'khatta dakaar': 'K21.9',
    'khoon ki kami': 'D50.9',
    'khoon ki khansi': 'R04.2',
    'khudkushi ka khayal': 'R45.81',
    'khujli': 'B86',
    'khujli wale daane': 'L50.9',
    'khujli wali skin': 'L30.9',
    'kidney disease': 'N18.9',
    'kidney stone': 'N20.0',
    'knee pain': 'M19.9',
    'kshay rog': 'A15.9',
    'kutte ne kaata': 'W54.0XXA',
    'lakwa': 'I63.9',
    'laryngitis': 'J04.0',
    'lbp': 'M54.5',
    'leg pain radiating from back': 'M54.30',
    'leucoderma': 'L80',
    'leucorrhoea': 'N76.0',
    'lice': 'B85.2',
    'lipoma': 'D17.9',
    'long-standing sinus infection': 'J32.9',
    'loose motion': 'A09',
    'loose motions': 'A09',
    'loss of appetite': 'R63.0',
    'low b12': 'E53.8',
    'low haemoglobin': 'D50.9',
    'low mood': 'F32.9',
    'low thyroid': 'E03.9',
    'low vitamin d': 'E55.9',
    'lri': 'J18.9',
    'madhumeh': 'E11.9',
    'malaria': 'B54',
    'malaria fever': 'B54',
    'malnutrition': 'R62.51',
    'man udaas': 'F32.9',
    'manic depression': 'F31.9',
    'marne ka man': 'R45.81',
    'masik dharm dard': 'N94.6',
    'masik dharm samasya': 'N92.6',
    'masse': 'B07.9',
    'mata': 'B01.9',
    'measles': 'B05.9',
    'menopausal symptoms': 'N95.1',
    'menopause': 'N95.1',
    'migraine': 'G43.9',
    'miliaria': 'L74.0',
    'mini stroke': 'G45.9',
    'moch': 'S93.409A',
    'moch aana': 'S93.409A',
    'molluscum': 'B08.1',
    'molluscum contagiosum': 'B08.1',
    'mota': 'E66.9',
    'motiyabind': 'H25.9',
    'mottyjhar': 'A01.0',
    'muhase': 'L70.0',
    'mumps': 'B26.9',
    'naak se khoon': 'R04.0',
    'napkin rash': 'L22',
    'nasal allergy': 'J30.9',
    'nason mein dard': 'G62.9',
    'nausea': 'R11.10',
    'neck pain': 'M54.5',
    'neck stiffness': 'M47.812',
    'neel padna': 'S00.90',
    'neend na aana': 'G47.00',
    'nerve pain': 'G62.9',
    'neuritis': 'G62.9',
    'neuropathy': 'G62.9',
    'nimonia': 'J18.9',
    'nosebleed': 'R04.0',
    'oa': 'M19.9',
    'obesity': 'E66.9',
    'osteoarthritis': 'M19.9',
    'otitis externa': 'H60.90',
    'otitis media': 'H66.90',
    'otomycosis': 'B36.9',
    'overweight': 'E66.9',
    'pair mein sujan': 'R60.9',
    'pair mudna': 'S93.409A',
    'paksaghat': 'I63.9',
    'palpitations': 'R00.2',
    'pathri': 'N20.0',
    'pcod': 'E28.2',
    'pcos': 'E28.2',
    'pediatric tonsillopharyngitis': 'J03.90',
    'peeliya': 'B15.9',
    'pelvic infection': 'N72',
    'peptic ulcer': 'K27.9',
    'period pain': 'N94.6',
    'period problem': 'N92.6',
    'peshab ki takleef': 'N39.0',
    'peshab mein jalan': 'N39.0',
    'pet dard': 'R10.9',
    'pet mein dard': 'R10.9',
    'pet mein jalan': 'K21.9',
    'pharyngitis': 'J02.9',
    'pharyngotonsillitis': 'J06.9',
    'phoda': 'L08.9',
    'piles': 'K64.9',
    'pimples': 'L70.0',
    'pinworm': 'B82.9',
    'plantar fasciitis': 'M72.2',
    'pneumonia': 'J18.9',
    'poor circulation': 'I73.9',
    'poore sharir mein dard': 'M79.7',
    'pregnancy anemia': 'O99.0',
    'pregnancy bleeding': 'O20.0',
    'pregnancy checkup': 'Z34.90',
    'pregnancy mein khoon ki kami': 'O99.0',
    'prickly heat': 'L74.0',
    'psoriasis': 'L40.9',
    'psychosis': 'F20.9',
    'ptb': 'A15.9',
    'pulmonary tb': 'A15.9',
    'purani kamar dard': 'M54.9',
    'purani khansi': 'J44.9',
    'pus wali phunsi': 'L08.9',
    'pyoderma': 'L08.9',
    'refractive error': 'H52.10',
    'rhd': 'I09.9',
    'rheumatic valve disease': 'I09.9',
    'ringing in ears': 'H93.19',
    'ringworm': 'B35.9',
    'saans phoolna': 'J44.9',
    'safed daag': 'L80',
    'safed pani': 'N76.0',
    'sar dard': 'G44.209',
    'sar ghoomna': 'R42',
    'sardi jukam': 'J30.9',
    'sardi zukam': 'J06.9',
    'scabies': 'B86',
    'scaly skin patches': 'L40.9',
    'schizophrenia': 'F20.9',
    'school sores': 'L01.00',
    'sciatica': 'M54.30',
    'sciatica dard': 'M54.30',
    'seasonal eye allergy': 'H10.10',
    'sebaceous cyst': 'L72.3',
    'seene mein dard': 'I25.9',
    'seene mein infection': 'J18.9',
    'seene mein jamaav': 'J20.9',
    'self-harm': 'R45.81',
    'severe headache': 'G43.9',
    'sharab ki lat': 'F10.20',
    'sharir par chakatte': 'L50.9',
    'shingles': 'B02.9',
    'shoulder stiffness': 'M75.00',
    'sinus infection': 'J01.90',
    'sinusitis': 'J01.90',
    'sir dard': 'G44.209',
    'skin infection': 'L08.9',
    'skin infection with swelling': 'L03.90',
    'skin mein infection': 'L08.9',
    'sleeplessness': 'G47.00',
    'smoking': 'F17.200',
    'somatic symptoms': 'F45.9',
    'sore throat': 'J02.9',
    'spastic colon': 'K58.9',
    'sprain': 'S93.409A',
    'std': 'A64',
    'sti': 'A64',
    'stomach flu': 'A08.4',
    'stomach pain': 'R10.9',
    'stomach ulcer': 'K27.9',
    'strain': 'S93.409A',
    'stress-related body pain': 'F45.9',
    'stroke': 'I63.9',
    'stye': 'H00.19',
    'sugar': 'E11.9',
    'sugar ki bimari': 'E11.9',
    'suicidal thoughts': 'R45.81',
    'sunn hona': 'G62.9',
    'swelling in legs': 'R60.9',
    'swollen leg veins': 'I83.90',
    'syncope': 'R55',
    't2dm': 'E11.9',
    'taang mein jhanjhanahat': 'M54.30',
    'tambaku ki lat': 'F17.200',
    'tap': 'R50.9',
    'tapedik': 'A15.9',
    'tb': 'A15.9',
    'tension': 'F41.9',
    'tension headache': 'G44.209',
    'thakaan': 'R53.83',
    'threadworm': 'B80',
    'threatened miscarriage': 'O20.0',
    'throat gland infection': 'J03.90',
    'throat infection (child)': 'J03.90',
    'thyroid problem': 'E03.9',
    'thyrotoxicosis': 'E05.90',
    'tia': 'G45.9',
    'tinea': 'B35.9',
    'tinnitus': 'H93.19',
    'tobacco use': 'F17.200',
    'tonsillitis': 'J03.90',
    'tooth decay': 'K02.9',
    'typhoid': 'A01.0',
    'udaas rehna': 'F32.9',
    'ulti': 'R11.10',
    'unintentional weight loss': 'R63.4',
    'uric acid': 'M10.9',
    'urine infection': 'N39.0',
    'urti': 'J06.9',
    'urticaria': 'L50.9',
    'uti': 'N39.0',
    'varicose veins': 'I83.90',
    'vertigo': 'R42',
    'viral': 'R50.9',
    'viral fever': 'R50.9',
    'viral fever with sore throat': 'J06.9',
    'viral gastroenteritis': 'A08.4',
    'vitamin d deficiency': 'E55.9',
    'vitiligo': 'L80',
    'vomiting': 'R11.10',
    'warts': 'B07.9',
    'weak eyesight': 'H52.10',
    'weakness': 'R53.83',
    'weight loss': 'R63.4',
    'wheezing': 'J45.909',
    'wheezing child': 'J45.901',
    'white discharge': 'N76.0',
    'worms': 'B82.9',
    'worms (child)': 'B82.9',
    'wound': 'S01.90',
}

# Terms whose ICD-10 mapping in _DIAGNOSIS_LOOKUP above is context-dependent -- lists ALL candidate
# (canonical diagnosis, icd10_cm) pairs a term could refer to, ordered by OPD_score (most common first).
_AMBIGUOUS_LOOKUP_TERMS: dict[str, list[tuple]] = {
    'kamzori': [('Iron-deficiency anaemia', 'D50.9'), ('Weakness / fatigue, unspecified', 'R53.83'), ('Failure to thrive / malnutrition (child)', 'R62.51')],
    'joint pain': [('Osteoarthritis', 'M19.9'), ('Arthritis (unspecified/rheumatoid overlap)', 'M13.9')],
    'saans phoolna': [('Chronic obstructive pulmonary disease', 'J44.9'), ('Bronchial asthma', 'J45.909')],
    'purani khansi': [('Chronic obstructive pulmonary disease', 'J44.9'), ('Cough, unspecified (chronic)', 'R05.9')],
    'kamar dard': [('Low back pain / neck pain', 'M54.5'), ('Chronic back pain (non-specific)', 'M54.9')],
    'gardan dard': [('Low back pain / neck pain', 'M54.5'), ('Cervical spondylosis', 'M47.812')],
    'acidity': [('Acid peptic disease / GERD', 'K21.9'), ('Acute gastritis', 'K29.70')],
    'gastritis': [('Acid peptic disease / GERD', 'K21.9'), ('Acute gastritis', 'K29.70')],
    'pet mein jalan': [('Acid peptic disease / GERD', 'K21.9'), ('Acute gastritis', 'K29.70')],
    'pinworm': [('Worm infestation (pediatric)', 'B82.9'), ('Threadworm/pinworm (Enterobiasis)', 'B80')],
    'jaundice': [('Viral hepatitis A', 'B15.9'), ('Jaundice, unspecified', 'R17')],
    'peeliya': [('Viral hepatitis A', 'B15.9'), ('Jaundice, unspecified', 'R17')],
}


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------
def _validate() -> dict:
    """Run integrity checks on _INDIAN_OPD_DIAGNOSES / _DIAGNOSIS_LOOKUP and return a summary dict."""
    failures = []

    # 1. Duplicate ICD-10-CM codes across DIFFERENT canonical diagnoses (flag, don't fail --
    #    some conditions legitimately share an unspecified-site code, e.g. multiple "unspecified"
    #    symptom codes; each such case is flagged for manual review).
    code_to_canons = {}
    for e in _INDIAN_OPD_DIAGNOSES:
        code_to_canons.setdefault(e["icd10_cm"], []).append(e["canonical"])
    duplicate_codes = {code: canons for code, canons in code_to_canons.items() if len(set(canons)) > 1}

    # 2. Every entry has at least 2 common_names
    entries_with_lt2_common_names = [
        e["canonical"] for e in _INDIAN_OPD_DIAGNOSES if len(e["common_names"]) < 2
    ]
    if entries_with_lt2_common_names:
        failures.append(f"{len(entries_with_lt2_common_names)} entries have <2 common_names: {entries_with_lt2_common_names}")

    # 3. Entry count
    if len(_INDIAN_OPD_DIAGNOSES) != 150:
        failures.append(f"Expected 150 entries, found {len(_INDIAN_OPD_DIAGNOSES)}")

    # 4. All ranks unique and 1..N
    ranks = sorted(e["rank"] for e in _INDIAN_OPD_DIAGNOSES)
    if ranks != list(range(1, len(_INDIAN_OPD_DIAGNOSES) + 1)):
        failures.append("Ranks are not a contiguous 1..N sequence")

    # 5. Top-50 entries (by rank) must have non-empty hinglish_names
    top50_missing_hinglish = [
        e["canonical"] for e in _INDIAN_OPD_DIAGNOSES
        if e["rank"] <= 50 and not e["hinglish_names"]
    ]
    if top50_missing_hinglish:
        failures.append(f"{len(top50_missing_hinglish)} top-50 entries missing hinglish_names: {top50_missing_hinglish}")

    # 6. Lookup dict coverage: every common_name/hinglish_name from every entry should resolve
    #    in _DIAGNOSIS_LOOKUP (allowing for the documented ambiguous-term override -- lookup may
    #    point to a DIFFERENT but still-valid diagnosis's code for an ambiguous shared term).
    all_names = set()
    for e in _INDIAN_OPD_DIAGNOSES:
        all_names.update(n.strip().lower() for n in e["common_names"] + e["hinglish_names"])
    missing_from_lookup = [n for n in all_names if n not in _DIAGNOSIS_LOOKUP]
    if missing_from_lookup:
        failures.append(f"{len(missing_from_lookup)} names missing from _DIAGNOSIS_LOOKUP: {missing_from_lookup}")

    summary = {
        "total_entries": len(_INDIAN_OPD_DIAGNOSES),
        "total_lookup_terms": len(_DIAGNOSIS_LOOKUP),
        "total_ambiguous_terms": len(_AMBIGUOUS_LOOKUP_TERMS),
        "duplicate_icd10_cm_codes": duplicate_codes,
        "validation_failures": failures,
    }
    return summary


if __name__ == "__main__":
    result = _validate()
    print(f"Total entries: {result['total_entries']}")
    print(f"Total lookup terms: {result['total_lookup_terms']}")
    print(f"Total ambiguous terms flagged: {result['total_ambiguous_terms']}")
    print(f"Duplicate ICD-10-CM codes shared by >1 diagnosis: {len(result['duplicate_icd10_cm_codes'])}")
    for code, canons in result["duplicate_icd10_cm_codes"].items():
        print(f"  {code}: {sorted(set(canons))}")
    if result["validation_failures"]:
        print(f"VALIDATION FAILURES ({len(result['validation_failures'])}):")
        for f in result["validation_failures"]:
            print(f"  - {f}")
    else:
        print("All validation checks passed.")

# Indian OPD PGx Rules — Scoring Rationale

## Methodology

Every CPIC level 1A/1B gene-drug pair (109 pairs pulled live from `api.cpicpgx.org` on 2026-07-02)
was scored on three axes, each with a written rationale citing a source:

1. **Indian frequency score (0-3)** — a per-gene judgment of how strong and how large the
   Indian-population allele/carrier-frequency evidence is, built from IndiGen (PMID:35338580),
   the GenomeIndia-adjacent "Atlas of Indian Genetic Diversity" dataset (medRxiv
   10.64898/2026.03.20.26348801), and supplementary PubMed literature. 0 = no Indian data found
   in this search pass; 3 = large, well-replicated Indian frequency, often higher than global
   reference populations.
2. **OPD prescribing frequency** (informational, not part of the rank formula below, but used to
   sanity-check the actionability score) — how often the trigger drug is actually prescribed in
   Indian primary care, from WHO NLEM India (NLEM 2022) listing status and PubMed-indexed Indian
   prescribing-pattern studies.
3. **OPD actionability (0-3)** — whether the CPIC-recommended action (dose change, drug switch,
   pre-screen) is something a primary-care doctor can act on directly, versus something that only
   happens in a hospital/specialist setting (oncology, transplant medicine, ART centres).
4. **Observability (0-3)** — per the rubric specified in the brief: can a doctor, working from a
   patient's own visit history and without a genome, infer likely poor-metabolizer/risk-carrier
   status? 0 = not observable; 3 = a clear ADR or treatment failure pattern maps to the variant.

**Rank score = (CPIC level weight: 1A=3, 1B=2) × Indian frequency score × OPD actionability.**
Observability is reported alongside every rule but is NOT part of the rank formula (as specified) —
it instead governs the `ships_now` / `needs_genomic_data` classification: rules with observability
< 2 are held back from doctor-facing deployment even if their rank score is high, because a
population-level flag with no observable clinical signal risks generating alert fatigue rather
than useful decision support.

## Corrections made to the source citations given in the original brief

- **PMID 31626772** (given in the brief as "IndiGen, Cell 2019") resolves to the Singapore SG10K
  whole-genome study, not IndiGen. The correct IndiGen pharmacogenomics publication located and
  used throughout this rules file is **Sahana et al. 2022, Clinical and Translational Science,
  PMID:35338580** (IndiGen, N=1,029 Indian genomes).
- **"GenomeIndia Consortium (Science 2024)"** — no such paper was found. The GenomeIndia
  Consortium's flagship publication is Bhattacharyya et al., *Nature Genetics* 2025
  (PMID:40200122), which is paywalled and could not be retrieved as full text in this pass. In its
  place, a related open-access dataset — "An Atlas of Indian Genetic Diversity" (medRxiv 2026,
  DOI:10.64898/2026.03.20.26348801, N=9,768 genomes across 83 populations) — was used for
  supplementary PGx frequency data, and is cited explicitly wherever used.

## Full ranked list (all scored CPIC 1A/1B pairs considered)

| Rank | Rule | Gene(s) | Drug(s) | CPIC Level | Indian Freq Score | OPD Actionability | Observability | Rank Score | Ships Now? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PGX_001 | G6PD | co-trimoxazole, dapsone, nitrofurantoin... | 1A | 3 | 3 | 2 | 27 | ✅ |
| 2 | PGX_002 | CYP2C19 | clopidogrel | 1A | 3 | 3 | 3 | 27 | ✅ |
| 3 | PGX_003 | VKORC1, CYP2C9, CYP4F2 | acenocoumarol, warfarin | 1A | 3 | 3 | 3 | 27 | ✅ |
| 4 | PGX_004 | NUDT15, TPMT | 6-mercaptopurine, azathioprine, mercaptopurine | 1A | 3 | 2 | 2 | 18 | ✅ |
| 5 | PGX_005 | CYP2D6, CYP2C19 | amitriptyline, clomipramine, doxepin... | 1A | 3 | 2 | 2 | 18 | ✅ |
| 6 | PGX_006 | CYP2D6 | atomoxetine | 1A | 3 | 2 | 1 | 18 | ⏸️ (needs data/observability) |
| 7 | PGX_007 | CYP2D6 | codeine | 1A | 3 | 2 | 1 | 18 | ⏸️ (needs data/observability) |
| 8 | PGX_008 | CYP2C19 | esomeprazole, lansoprazole, omeprazole... | 1A | 3 | 2 | 1 | 18 | ⏸️ (needs data/observability) |
| 9 | PGX_009 | HLA-B, HLA-A | carbamazepine, oxcarbazepine | 1A | 2 | 2 | 2 | 12 | ✅ |
| 10 | PGX_010 | NAT2 | isoniazid | 1B | 3 | 2 | 2 | 12 | ✅ |
| 11 | PGX_011 | CYP2D6 | tamoxifen | 1A | 3 | 1 | 1 | 9 | ⏸️ (needs data/observability) |
| 12 | PGX_012 | CYP2C19 | voriconazole | 1A | 3 | 1 | 1 | 9 | ⏸️ (needs data/observability) |
| 13 | PGX_013 | CYP3A5 | tacrolimus | 1A | 2 | 1 | 1 | 6 | ⏸️ (needs data/observability) |
| 14 | PGX_014 | UGT1A1 | atazanavir, irinotecan | 1A | 2 | 1 | 2 | 3 | ✅ |
| 15 | PGX_015 | SLCO1B1, ABCG2 | atorvastatin, rosuvastatin, simvastatin | 1A | 0 | 2 | 2 | 0 | ⏸️ (needs data/observability) |

## Per-rule rationale

### PGX_001: G6PD deficiency - oxidant drug hemolysis risk

- **Genes / Drugs:** G6PD → co-trimoxazole, dapsone, nitrofurantoin, primaquine, rasburicase, sulfamethoxazole
- **CPIC level:** 1A (guideline PMIDs: 24787449, 36049896)
- **Indian frequency:** 2-27.9% carrier prevalence depending on region/community (highest: Vataliya Prajapati Gujarat 27.9% males; tribal Odisha/Central India 6-8%; general population survey 1.9%; lowest in some North Indian cohorts <1%)
  - *Source:* PMID:26139767 (7.7% national); PMID:33069889 (1.9%, N=20896); PMID:15226563; PMID:11345405 (27.9%); PMID:18568599; PMID:31833391; PMID:36384674; PMID:31061745; PMID:37674284 (Delhi newborn screening); PMID:29417859; PMID:39926832
- **OPD actionability (3/3):** Dispensed at PHC/OPD level (malaria elimination programme, NLEP, routine antibiotics); point-of-care G6PD test or referral before dosing is an OPD-level action.
- **Observability (2/3):** Acute haemolysis (dark urine, jaundice, fatigue) days after starting primaquine/dapsone is a well-documented, recognizable clinical pattern; weaker for nitrofurantoin/co-trimoxazole (rare reports despite wide use per CPIC).
- **Rank score:** 27
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_002: CYP2C19 poor/intermediate metabolizer - clopidogrel non-response

- **Genes / Drugs:** CYP2C19 → clopidogrel
- **CPIC level:** 1A (guideline PMIDs: 36094131)
- **Indian frequency:** CYP2C19*2 allele frequency 0.34-0.36 (IndiGen national + South Indian CAD cohorts); GenomeIndia national poor-metabolizer phenotype ~15%
  - *Source:* PMID:35338580 (IndiGen, *2 AF=0.36); PMID:41028360 (South Indian CAD/clopidogrel cohort, 34% PM/IM carriers); PMID:37985132 (South Indian ACS cohort); medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia, 15% PM phenotype)
- **OPD actionability (3/3):** Switching to prasugrel/ticagrelor or adding antiplatelet therapy is routine cardiology/OPD follow-up decision-making; genotyping increasingly available via referral.
- **Observability (3/3):** Recurrent stent thrombosis, recurrent ACS, or stroke on clopidogrel despite adherence is a strong, well-recognized signal of poor-metabolizer status.
- **Rank score:** 27
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_003: VKORC1/CYP2C9/CYP4F2 - warfarin dose sensitivity

- **Genes / Drugs:** VKORC1, CYP2C9, CYP4F2 → acenocoumarol, warfarin
- **CPIC level:** 1A (guideline PMIDs: 28198005)
- **Indian frequency:** VKORC1 -1639G>A AF 0.14-0.72 depending on region (IGVdb range 6.5%->70% across 24 subpopulations); CYP2C9*3 AF 0.09-0.17 (higher in North Indian anticoagulant cohorts)
  - *Source:* PMID:35338580 (IndiGen, VKORC1 AF=0.18); PMID:25155935 (IGVdb, 24 subpopulations, VKORC1 range 6.5-70%); PMID:23563037 (North vs South Indian pilot); PMID:26781925 (North Indian valve-replacement cohort on acenocoumarol)
- **OPD actionability (3/3):** Dose titration via INR monitoring is routine OPD/anticoagulation-clinic practice; no new infrastructure needed.
- **Observability (3/3):** Excessive INR/bleeding at low dose, or persistent sub-therapeutic INR at high dose, is a directly observable signal via routine INR monitoring already standard of care.
- **Rank score:** 27
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_004: NUDT15/TPMT - thiopurine-induced myelosuppression

- **Genes / Drugs:** NUDT15, TPMT → 6-mercaptopurine, azathioprine, mercaptopurine
- **CPIC level:** 1A (guideline PMIDs: 30801620)
- **Indian frequency:** NUDT15*3 AF 0.068-0.107 in Indian thiopurine-treated cohorts (up to 20.8% in some Austro-Asiatic tribal groups); TPMT variants comparatively rare in India (*3C AF 0.02, *3A AF 0.003) -- NUDT15 is the dominant thiopurine-toxicity gene in South Asians, not TPMT
  - *Source:* PMID:35338580 (IndiGen NUDT15*3=0.08, TPMT*3A/*3C); PMID:29470173 (Indian thiopurine cohort, NUDT15*3=0.107); PMID:32935219 (Indian GSA screening N=2000); medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia tribal groups)
- **OPD actionability (2/3):** Dose reduction or alternative agent is an OPD-level decision once myelosuppression is flagged on routine CBC monitoring.
- **Observability (2/3):** Cytopenia (leukopenia) on routine follow-up CBC while on thiopurine therapy is a moderately specific signal, though confounded by disease activity and other marrow suppressants.
- **Rank score:** 18
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_005: CYP2D6/CYP2C19 - tricyclic antidepressant metabolizer variability

- **Genes / Drugs:** CYP2D6, CYP2C19 → amitriptyline, clomipramine, doxepin, imipramine, nortriptyline, trimipramine
- **CPIC level:** 1A (guideline PMIDs: 27997040)
- **Indian frequency:** CYP2D6 poor/intermediate-metabolizer alleles (*4, *10, *41) 6.6-32% depending on allele/region; CYP2C19*2 AF 0.36 nationally
  - *Source:* PMID:35338580 (IndiGen); PMID:12942225 (South Indian Tamilian cohort); PMID:16880622 (South Indian states); PMID:31368850 (South Indian resequencing cohort)
- **OPD actionability (2/3):** Dose titration for TCAs in OPD psychiatry/pain/neuropathy management is routine practice.
- **Observability (2/3):** Excess sedation/anticholinergic side effects (possible PM) vs. non-response at standard dose (possible UM) is a moderately usable signal on OPD follow-up, though confounded by other factors.
- **Rank score:** 18
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_006: CYP2D6 - atomoxetine exposure variability

- **Genes / Drugs:** CYP2D6 → atomoxetine
- **CPIC level:** 1A (guideline PMIDs: 30801677)
- **Indian frequency:** Same CYP2D6 PM/IM allele burden as above (6.6-32%)
  - *Source:* PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850
- **OPD actionability (2/3):** Dose adjustment is possible at OPD/psychiatry follow-up level.
- **Observability (1/3):** Side-effect profile is nonspecific; atomoxetine use in Indian OPD/psychiatry is moderate but growing, behind stimulants -- weaker standalone signal.
- **Rank score:** 18
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** INDIAN_DATA

### PGX_007: CYP2D6 - codeine analgesic failure/toxicity

- **Genes / Drugs:** CYP2D6 → codeine
- **CPIC level:** 1A (guideline PMIDs: 33387367)
- **Indian frequency:** Same CYP2D6 PM/IM/UM allele burden as above
  - *Source:* PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850
- **OPD actionability (2/3):** Alternative analgesic can be chosen at OPD level.
- **Observability (1/3):** Poor analgesia (PM) or sedation/toxicity (UM) is observable but codeine use has declined in Indian OPD due to abuse-potential restrictions, reducing exposure and signal frequency.
- **Rank score:** 18
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** INDIAN_DATA

### PGX_008: CYP2C19 - proton pump inhibitor metabolizer variability

- **Genes / Drugs:** CYP2C19 → esomeprazole, lansoprazole, omeprazole, pantoprazole
- **CPIC level:** 1A (guideline PMIDs: 32770672)
- **Indian frequency:** CYP2C19*2 AF 0.36 nationally (IndiGen); PM phenotype ~15% (GenomeIndia)
  - *Source:* PMID:35338580; medRxiv:10.64898/2026.03.20.26348801
- **OPD actionability (2/3):** Dose/drug switch (e.g. to a non-CYP2C19-dependent option) is a routine OPD decision for reflux/PUD.
- **Observability (1/3):** Poor symptom control at standard PPI dose could reflect ultrarapid metabolizer status, but is heavily confounded by H. pylori status, adherence, and lifestyle -- weak standalone signal.
- **Rank score:** 18
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** INDIAN_DATA

### PGX_009: HLA-B*15:02 / HLA-A*31:01 - carbamazepine severe cutaneous reaction risk

- **Genes / Drugs:** HLA-B, HLA-A → carbamazepine, oxcarbazepine
- **CPIC level:** 1A (guideline PMIDs: 23695185)
- **Indian frequency:** HLA-B*15:02 ~3% carrier prevalence (IndiGen); strong disease association in Indian case-control studies (OR up to 38.5); HLA-A*31:01 ~2% carrier prevalence (IndiGen)
  - *Source:* PMID:35338580 (IndiGen); PMID:25266342 (meta-analysis, Malaysian-Indian + India-pooled, OR 38.54); PMID:25305458 (North Indian case-control); PMID:29076187 (Kerala case-control)
- **OPD actionability (2/3):** Pre-prescription HLA-B*15:02 screening exists but is not routinely ordered in Indian OPD; if unavailable, doctor can choose an alternative anticonvulsant empirically, especially with prior history.
- **Observability (2/3):** SJS/TEN is a severe, recognizable ADR, but by the time it is observed, harm has already occurred -- this is a pre-emptive flag, not a post-hoc one.
- **Rank score:** 12
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_010: NAT2 slow acetylator - isoniazid hepatotoxicity risk

- **Genes / Drugs:** NAT2 → isoniazid
- **CPIC level:** 1B (guideline PMIDs: N/A)
- **Indian frequency:** Slow-acetylator phenotype 44-74% depending on region (Mumbai 55%, North India 44-53%, South India 67-74%; Chennai TB cohort 58% slow)
  - *Source:* PMID:28862181 / PMC5460557 (IJMR, Chennai NAT2 genotyping); Dovepress review 'NAT2 Acetylation Phenotypes in India'
- **OPD actionability (2/3):** Isoniazid dosing is standardized under NTEP weight-band protocols, but LFT monitoring and drug switch/interruption on hepatotoxicity is an OPD-level decision.
- **Observability (2/3):** Hepatotoxicity (deranged LFTs) or peripheral neuropathy on isoniazid is a recognizable, commonly monitored OPD/NTEP signal.
- **Rank score:** 12
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_011: CYP2D6 poor metabolizer - tamoxifen reduced efficacy

- **Genes / Drugs:** CYP2D6 → tamoxifen
- **CPIC level:** 1A (guideline PMIDs: 30447069)
- **Indian frequency:** Same CYP2D6 PM/IM allele burden as above (6.6-32%)
  - *Source:* PMID:35338580; PMID:12942225; PMID:16880622; PMID:31368850
- **OPD actionability (1/3):** Dosing/switch decisions are typically managed in oncology, not general OPD.
- **Observability (1/3):** Breast cancer recurrence on tamoxifen is a delayed, highly confounded signal, and management is oncology-led, not primary-care.
- **Rank score:** 9
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** INDIAN_DATA

### PGX_012: CYP2C19 poor metabolizer - voriconazole toxicity risk

- **Genes / Drugs:** CYP2C19 → voriconazole
- **CPIC level:** 1A (guideline PMIDs: 31544268)
- **Indian frequency:** CYP2C19*2 AF 0.36 nationally (IndiGen); PM phenotype ~15% (GenomeIndia)
  - *Source:* PMID:35338580; medRxiv:10.64898/2026.03.20.26348801
- **OPD actionability (1/3):** Dosing decisions typically happen in hospital/ID-specialist setting, not general OPD.
- **Observability (1/3):** Sub-therapeutic levels (PM) or visual/hepatic toxicity (UM) require drug-level monitoring rarely available in OPD; antifungal dosing for invasive infections is typically hospital/ID-specialist managed.
- **Rank score:** 9
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** INDIAN_DATA

### PGX_013: CYP3A5 expresser status - tacrolimus dose requirement

- **Genes / Drugs:** CYP3A5 → tacrolimus
- **CPIC level:** 1A (guideline PMIDs: 25801146)
- **Indian frequency:** GenomeIndia Tibeto-Burman group poor-metabolizer (non-expresser) phenotype 45%; broader pan-India CYP3A5*3 frequency not established in this search
  - *Source:* medRxiv:10.64898/2026.03.20.26348801 (GenomeIndia, Tibeto-Burman subgroup only)
- **OPD actionability (1/3):** Transplant immunosuppression dosing is managed by transplant specialists, not general OPD.
- **Observability (1/3):** Sub-therapeutic tacrolimus levels are only detectable via specialist drug-level monitoring, not general OPD observation.
- **Rank score:** 6
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** NO_INDIAN_DATA — closest proxy: GenomeIndia Tibeto-Burman subgroup only, not representative of pan-India frequency

### PGX_014: UGT1A1 reduced activity - atazanavir/irinotecan toxicity

- **Genes / Drugs:** UGT1A1 → atazanavir, irinotecan
- **CPIC level:** 1A (guideline PMIDs: 26417955, 24714115)
- **Indian frequency:** UGT1A1*28 allele frequency in Indians is comparable to other Asian populations and notably higher than East Asians at some related loci; Balram et al. 2002 (Singapore-based Indian ethnic cohort) found UGT1A1*28 to be a common allele in Indians. A separate South Indian healthy-cohort study (N=450-608) found UGT1A1 (TA)7 promoter allele frequency 39.8%.
  - *Source:* PMID:11773869 (Balram et al. 2002, Pharmacogenetics -- Indian ethnic cohort, Singapore); South Indian healthy cohort TPMT/UGT1A1/MDR1 study (N=450-608, ResearchGate abstract, PMID not captured in this pass -- flagged for follow-up)
- **OPD actionability (1/3):** ART regimen switch happens within NACO ART centres; chemotherapy dosing is oncology-managed -- not general OPD decisions, but flag is useful for referral communication.
- **Observability (2/3):** Jaundice/hyperbilirubinemia (atazanavir) or severe neutropenia/diarrhea (irinotecan) are fairly specific, specialist-monitored signals.
- **Rank score:** 3
- **Ships now:** True | **Needs genomic data:** False | **Data quality:** INDIAN_DATA

### PGX_015: SLCO1B1/ABCG2 - statin-induced myopathy risk (DATA GAP)

- **Genes / Drugs:** SLCO1B1, ABCG2 → atorvastatin, rosuvastatin, simvastatin
- **CPIC level:** 1A (guideline PMIDs: 35152405)
- **Indian frequency:** NO INDIAN-SPECIFIC FREQUENCY FOUND in this search. Global/Asian proxy: SLCO1B1 rs4149056 minor-allele frequency ~14% in pooled Asian meta-analysis vs 15% Caucasian (not India-specific)
  - *Source:* NO_INDIAN_DATA — closest proxy: pooled Asian meta-analysis (source not independently confirmed as covering India), South/West Asian gnomAD range 5-10% per CPIC guideline text
- **OPD actionability (2/3):** Dose cap / switch to alternative statin is a routine OPD decision per CPIC once evidence permits a population claim.
- **Observability (2/3):** Statin-associated muscle symptoms on follow-up are moderately specific and commonly documented in OPD, but the underlying India-specific variant frequency is unverified — flagging risk without population evidence would violate the no-silent-substitution principle.
- **Rank score:** 0
- **Ships now:** False | **Needs genomic data:** True | **Data quality:** NO_INDIAN_DATA — closest proxy: pooled Asian/global meta-analyses, no India-specific study located

## Key limitations and gaps

- **No India-specific data found in this search pass** for: SLCO1B1/ABCG2 (statins), DPYD
  (fluoropyrimidines), MT-RNR1 (aminoglycoside ototoxicity), CACNA1S/RYR1 (malignant
  hyperthermia — inherently rare everywhere), IFNL3/IFNL4 (declining clinical relevance),
  CFTR (cystic fibrosis is rare in Indian populations). These are flagged `NO_INDIAN_DATA`
  in the rules file and excluded from, or ranked at the bottom of, the top-15 list rather than
  silently assigned a plausible-looking frequency.
- **CYP4F2 and CYP3A5** have only partial or subgroup-limited Indian data (CYP3A5 frequency
  is only established for one GenomeIndia tribal subgroup, not pan-India).
- **Scoring is expert judgment informed by literature, not a validated predictive model.** The
  OPD actionability and observability scores were assigned per-pair using clinical reasoning
  about India's care-delivery context (NTEP, NACO ART centres, oncology referral pathways,
  routine INR/CBC/LFT monitoring) — they are not derived from measured outcomes on Lipi's own
  patient data, and should be revisited once real prescribing/outcome data exists.
- **All frequency numbers derive from published studies with varying sample sizes** (from N=53
  regional cohorts to N=9,768 national genomes) and should be treated as approximate,
  population-level estimates, not diagnostic thresholds.

# Indian OPD Drug-Drug Interaction Database — Sourcing & Methodology Report

Generated: 2026-07-02 | Module: `_indian_ddi.py` | Total pairs: 80

## 1. Data sources actually used


| Purpose | Source | What was pulled | Substitution flag |
|---|---|---|---|
| DDI evidence base | openFDA structured product labels (`drug_interactions` SPL section), via `mcp-drug-regulatory` | 950 candidate pair mentions from 139 unique SPL `set_id` label records across 31 OPD drugs | **Substitutes for DrugBank** — DrugBank's full DDI export is license-gated (not in the free Open Data / CC0 release), so it was excluded entirely per project rules. openFDA labels are US-approved-product labels; no public bulk Indian-government DDI-labeled-text source exists. |
| Indian-context DDI/ADR literature | PubMed (`mcp-pubmed`), 2015–2024, 6 queries incl. "drug interaction India outpatient" | 46 drug-pair mentions from 7 of 25 relevant Indian-context articles (abstracts only, not full text) | None — used as specified. |
| Primary formulary filter | National List of Essential Medicines (NLEM) India 2022, official MoHFW/CDSCO PDF | 387 unique generic names | None — official government source, retrieved directly. |
| Backup formulary filter | NPPA ceiling-price list (DPCO 2013, as on 01-08-2025) | 976 generic name strings (noisier, used only as fallback) | Fetched via a Kerala state-government mirror (dc.kerala.gov.in) since nppa.gov.in itself was not directly network-accessible this session — document is NPPA's own official list, only the hosting URL differs. |
| Indian brand names | `junioralive/Indian-Medicine-Dataset` GitHub repo (`DATA/indian_medicine_data.csv`), main branch | ~150k Indian retail product names, inverted to generic→brand mapping | **Substitutes for CDSCO** — CDSCO has no public bulk brand-name-mapping API. This is an unofficial, community-maintained dataset of Indian pharmacy retail listings, not a government dataset. Not regulator-verified. |

## 2. Pipeline / methodology summary


1. Raw candidate DDI pairs (996 rows) were expanded from drug-class mentions (e.g. "ACE inhibitors", "NSAIDs") into concrete generic-drug pairs using a hand-built class→representative-generic mapping.
2. Pairs were filtered to require **both** drugs to appear in the NLEM India 2022 list (primary) or the NPPA scheduled list (backup, half-weighted in scoring).
3. **Every one of the 182 formulary-filtered candidate pairs was passed through an LLM clinical-pharmacology verification step** that read the raw evidence snippet and explicitly checked for a known failure mode of openFDA extraction: fixed-dose-combination product labels (e.g. "Amlodipine and Olmesartan Medoxomil") whose warning text is actually about the *other* active ingredient in the combination, not the drug it was naively attributed to. **33 of 182 pairs (18%) were rejected at this step** as misattributed or as PubMed co-prescription-frequency mentions with no actual pharmacological evidence (see Section 4).
4. The 149 verified pairs were scored: `severity_score (major=3, moderate=2) × formulary_coverage (1.0 if both NLEM, 0.5 if NPPA-only) × class_frequency_weight × source_diversity_bonus`. The top 80 by score were selected (major/moderate only — the 17 "unclear"-severity pairs were excluded outright).
5. Indian brand names were pulled from the open Indian-Medicine-Dataset, restricted to standalone (non-combination) product listings where possible to keep the generic→brand mapping unambiguous. Widely-recognized brand names (e.g. voveran, brufen) were manually cross-checked against the dataset before inclusion.
6. Urgency was classified `critical` (major severity + life-threatening mechanism keywords: bleeding/INR, hyperkalemia/renal failure, cardiac depression/bradycardia, etc.), `high` (major severity, no acute life-threat keyword; or moderate + life-threat keyword), `medium` (moderate, monitoring-level).

## 3. All 80 pairs with exact source citations

| # | Left (generic) | Right (generic) | Urgency | Severity | Source citation | Mechanism |
|---|---|---|---|---|---|---|
| 1 | amlodipine | atenolol | critical | major | PMID:29430412 | additive cardiac depressant effect (calcium channel blockade |
| 2 | enalapril | telmisartan | critical | major | SPL 074fe718, 0a12343f, 0ad4bfb4 | dual RAAS blockade (ACE inhibitor + ARB) |
| 3 | ramipril | telmisartan | critical | major | SPL 0c1bd0f4, 15b438b4, 1b303136 | dual RAAS blockade |
| 4 | diclofenac | warfarin | critical | major | SPL 02e90e33, 0379c918, 0416ce03 | additive/synergistic bleeding risk via NSAID-induced GI muco |
| 5 | metronidazole | warfarin | critical | major | SPL 02046a22, 05707735, 06bd4afb | CYP2C9 inhibition by metronidazole reducing warfarin clearan |
| 6 | amoxicillin | warfarin | critical | major | SPL 00fbd46e, 0173e9de | amoxicillin alters gut flora affecting vitamin K synthesis/w |
| 7 | clopidogrel | diclofenac | critical | major | SPL 02e90e33, 0379c918, 0416ce03 | additive bleeding risk from antiplatelet effect plus NSAID-i |
| 8 | ibuprofen | warfarin | critical | major | SPL 0170876a, 0550fa2f | NSAID-induced GI mucosal injury plus antiplatelet effect com |
| 9 | clopidogrel | warfarin | critical | major | SPL 0078fb3d, 02f0eaf8, 03bec9ad | additive bleeding risk from independent antiplatelet and ant |
| 10 | amiodarone | atenolol | critical | major | SPL 09b21985, 0ad0c7dd, 0f744371 | additive negative chronotropic/AV nodal suppression |
| 11 | enalapril | spironolactone | critical | major | SPL 074fe718, 0a12343f, 0ad4bfb4 | additive hyperkalemia from ACE inhibition plus potassium-spa |
| 12 | atorvastatin | clarithromycin | high | major | SPL 01eadde8 | CYP3A4 inhibition by clarithromycin increases atorvastatin e |
| 13 | clopidogrel | omeprazole | high | major | SPL 0078fb3d, 02f0eaf8, 03ac077f | CYP2C19 inhibition by omeprazole reduces clopidogrel active  |
| 14 | pantoprazole | warfarin | critical | major | SPL 014f9762, 02ee7ed6, 03dea010 | PPI-induced potentiation of warfarin anticoagulant effect |
| 15 | omeprazole | warfarin | critical | major | SPL 03ac077f, 064b1418, 0b1ec3e1 | CYP2C19 inhibition by omeprazole reducing warfarin metabolis |
| 16 | lithium | telmisartan | critical | major | SPL 09d31eee | reduced renal lithium clearance via ARB effect on sodium/lit |
| 17 | enalapril | lithium | critical | major | SPL 074fe718, 0a12343f, 0ad4bfb4 | ACE inhibitor-induced sodium/lithium clearance reduction lea |
| 18 | lithium | metronidazole | critical | major | SPL 02046a22, 06bd4afb, 08abacec | reduced renal lithium clearance leading to elevated serum li |
| 19 | diclofenac | lithium | high | major | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced reduction in renal lithium clearance |
| 20 | ibuprofen | lithium | critical | major | SPL 0170876a, 0550fa2f | NSAID-induced reduction in renal lithium clearance |
| 21 | fluoxetine | warfarin | critical | major | SPL 02283de9, 0259db51, 06394c4b | CYP2C9 inhibition by fluoxetine potentiating warfarin antico |
| 22 | ciprofloxacin | zolpidem | high | major | SPL 0ce2221d, 0fac4466 | CYP3A4 inhibition by ciprofloxacin increasing zolpidem level |
| 23 | diclofenac | methotrexate | critical | major | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced reduction in renal methotrexate clearance |
| 24 | cyclosporine | diclofenac | critical | major | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced reduction in renal prostaglandins potentiating |
| 25 | acetazolamide | metformin | high | major | SPL 0178b9dd | carbonic anhydrase inhibition/renal effects compounding meta |
| 26 | fluoxetine | phenytoin | critical | major | SPL 02283de9, 06394c4b | CYP2C9/CYP2C19 inhibition by fluoxetine reducing phenytoin m |
| 27 | carbamazepine | fluoxetine | critical | major | SPL 02283de9, 06394c4b | CYP2D6/3A4 inhibition by fluoxetine reducing carbamazepine c |
| 28 | dolutegravir | metformin | high | major | SPL 0178b9dd | OCT2/MATE transporter inhibition by dolutegravir increasing  |
| 29 | atorvastatin | itraconazole | high | major | SPL 01eadde8 | CYP3A4 inhibition by itraconazole increases atorvastatin exp |
| 30 | methotrexate | pantoprazole | high | major | SPL 014f9762, 02ee7ed6, 03dea010 | PPI-mediated inhibition of methotrexate renal elimination |
| 31 | methotrexate | omeprazole | high | major | SPL 03ac077f, 064b1418, 0b1ec3e1 | PPI inhibition of renal transporters reducing methotrexate e |
| 32 | atorvastatin | cyclosporine | high | major | SPL 01eadde8 | OATP1B1/CYP3A4-mediated increased atorvastatin exposure by c |
| 33 | atorvastatin | ritonavir | high | major | SPL 01eadde8 | CYP3A4 inhibition by ritonavir increasing atorvastatin expos |
| 34 | atorvastatin | darunavir | high | major | SPL 01eadde8 | CYP3A4 inhibition by darunavir increases atorvastatin exposu |
| 35 | atorvastatin | colchicine | critical | major | SPL 01eadde8 | CYP3A4/P-gp interaction increasing colchicine and/or statin  |
| 36 | atorvastatin | sofosbuvir | critical | major | SPL 01eadde8 | ledipasvir-mediated inhibition of OATP1B1/BCRP increasing at |
| 37 | diclofenac | enalapril | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced prostaglandin inhibition blunting ACE inhibito |
| 38 | diclofenac | ramipril | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced prostaglandin inhibition reduces ACE inhibitor |
| 39 | diclofenac | telmisartan | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced prostaglandin inhibition reducing ARB antihype |
| 40 | atenolol | diclofenac | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced prostaglandin inhibition reducing antihyperten |
| 41 | diclofenac | metoprolol | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced prostaglandin inhibition reducing beta-blocker |
| 42 | enalapril | ibuprofen | medium | moderate | SPL 0170876a, 0550fa2f | NSAID-induced prostaglandin inhibition reducing ACE-inhibito |
| 43 | ibuprofen | ramipril | medium | moderate | SPL 0170876a, 0550fa2f | NSAID-induced prostaglandin inhibition reducing ACE-inhibito |
| 44 | isoniazid | metformin | medium | moderate | SPL 0178b9dd | isoniazid-induced hyperglycemia reducing glycemic control |
| 45 | ciprofloxacin | warfarin | high | moderate | SPL 05b2836d, 09ca5374, 0ce2221d | CYP1A2 inhibition potentiating warfarin anticoagulant effect |
| 46 | azithromycin | warfarin | high | moderate | SPL 003307c5, 01649d79, 0c926669 | potentiation of anticoagulant effect |
| 47 | doxycycline | warfarin | high | moderate | SPL 00b2aa98, 0106a3d3, 02f87c60 | tetracycline-induced depression of plasma prothrombin activi |
| 48 | digoxin | telmisartan | medium | moderate | SPL 09d31eee | telmisartan increases digoxin plasma concentration (likely P |
| 49 | diclofenac | digoxin | medium | moderate | SPL 02e90e33, 0379c918, 0416ce03 | NSAID-induced reduction in renal clearance of digoxin |
| 50 | furosemide | ibuprofen | medium | moderate | SPL 0170876a, 0550fa2f | NSAID inhibition of renal prostaglandin synthesis blunting l |
| 51 | atorvastatin | erythromycin | medium | moderate | SPL 01eadde8 | CYP3A4 inhibition increasing atorvastatin exposure |
| 52 | clopidogrel | pantoprazole | medium | moderate | SPL 0078fb3d, 03bec9ad | CYP2C19 inhibition reducing clopidogrel active metabolite fo |
| 53 | digoxin | omeprazole | high | moderate | SPL 03ac077f, 064b1418, 0b1ec3e1 | PPI-induced increase in gastric pH altering digoxin absorpti |
| 54 | atorvastatin | digoxin | medium | moderate | SPL 01eadde8 | P-glycoprotein inhibition by atorvastatin increasing digoxin |
| 55 | carbamazepine | doxycycline | medium | moderate | SPL 00b2aa98, 0106a3d3, 02f87c60 | hepatic enzyme induction (CYP3A4) accelerating doxycycline m |
| 56 | doxycycline | phenytoin | medium | moderate | SPL 00b2aa98, 0106a3d3, 02f87c60 | hepatic enzyme induction (CYP450) increasing doxycycline cle |
| 57 | metronidazole | phenytoin | medium | moderate | SPL 02046a22, 06bd4afb, 0949690c | CYP450 enzyme induction |
| 58 | ciprofloxacin | phenytoin | medium | moderate | SPL 0ce2221d, 0fac4466 | altered hepatic metabolism of phenytoin by ciprofloxacin |
| 59 | metformin | phenytoin | medium | moderate | SPL 0178b9dd | phenytoin-induced hyperglycemia reducing glycemic control |
| 60 | meropenem | valproate | medium | moderate | SPL 8d5fc1c1 | carbapenem-induced reduction in valproic acid serum concentr |
| 61 | valproate | warfarin | medium | moderate | SPL 8d5fc1c1 | protein binding displacement / hepatic metabolism inhibition |
| 62 | omeprazole | phenytoin | medium | moderate | SPL 03ac077f, 064b1418, 0b1ec3e1 | CYP2C19 inhibition by omeprazole reducing phenytoin metaboli |
| 63 | enalapril | losartan | critical | major | SPL 021cd76a, 04c4ba11, 05818573 | dual RAS blockade (ACE inhibitor + ARB) |
| 64 | aspirin | diclofenac | critical | major | SPL 02e90e33, 0379c918, 0416ce03 | additive antiplatelet/GI bleeding risk from combined NSAID a |
| 65 | aspirin | naproxen | critical | major | SPL 000155a8, 0041b483, 004bb832 | additive antiplatelet/GI bleeding risk from combined NSAID a |
| 66 | allopurinol | amoxicillin | medium | moderate | SPL 00fbd46e, 0173e9de | increased incidence of skin rash |
| 67 | amoxicillin | ethinylestradiol | medium | moderate | SPL 00fbd46e, 0173e9de | antibiotic alteration of gut flora reducing enterohepatic re |
| 68 | losartan | ramipril | critical | major | SPL 021cd76a, 04c4ba11, 05818573 | dual RAS blockade (ARB + ACE inhibitor) |
| 69 | amitriptyline | fluoxetine | medium | moderate | SPL 0067b698, 00d11130, 04e1c5f8 | CYP2D6 inhibition by fluoxetine increasing TCA levels |
| 70 | caffeine | ciprofloxacin | medium | moderate | SPL 05b2836d, 09ca5374, 0ce2221d | CYP1A2 inhibition by ciprofloxacin reduces caffeine metaboli |
| 71 | ciprofloxacin | cyclosporine | high | moderate | SPL 05b2836d, 09ca5374, 0ce2221d | additive nephrotoxicity/reduced cyclosporine clearance |
| 72 | amlodipine | cyclosporine | medium | moderate | SPL 003dd1ec, 00a037f6, 01139e81 | amlodipine inhibits CYP3A4/P-gp-mediated cyclosporine metabo |
| 73 | amlodipine | tacrolimus | medium | moderate | SPL 003dd1ec, 00a037f6, 01139e81 | CYP3A4/P-gp inhibition by amlodipine increasing tacrolimus e |
| 74 | diazepam | omeprazole | medium | moderate | SPL 03ac077f, 064b1418, 0b1ec3e1 | CYP2C19 inhibition by omeprazole reducing diazepam clearance |
| 75 | doxycycline | ethinylestradiol | medium | moderate | SPL 00b2aa98, 0106a3d3, 02f87c60 | tetracycline-class antibiotics reducing oral contraceptive e |
| 76 | aspirin | ibuprofen | high | major | SPL 00872852, 0170876a, 0550fa2f | NSAID interference with aspirin's antiplatelet effect / cros |
| 77 | ciprofloxacin | methotrexate | medium | moderate | SPL 0ce2221d, 0fac4466 | inhibition of renal tubular secretion of methotrexate |
| 78 | ciprofloxacin | clozapine | medium | moderate | SPL 0ce2221d, 0fac4466 | CYP1A2 inhibition by ciprofloxacin increasing clozapine leve |
| 79 | ibuprofen | methotrexate | high | moderate | SPL 0170876a, 0550fa2f | NSAID inhibition of renal tubular secretion/methotrexate cle |
| 80 | ethinylestradiol | metformin | medium | moderate | SPL 0178b9dd | estrogen-induced insulin resistance/hyperglycemia |

## 4. Explicit gaps — pairs rejected during LLM verification (misattribution / no real evidence)

These 33 candidate pairs (of 182 formulary-filtered candidates) were excluded because the LLM verification pass found the evidence snippet was misattributed (usually a fixed-dose-combination-product label warning about the *other* co-formulated ingredient) or was a mere co-prescription-frequency observation with no documented pharmacological mechanism:

| Drug 1 | Drug 2 | Reason for exclusion |
|---|---|---|
| amlodipine | lithium | Both snippets describe lithium toxicity risk attributable to the ACE inhibitor (benazepril) or ARB (olmesartan) co-formulated with amlodipin |
| amlodipine | losartan | The evidence snippet is from an amlodipine/benazepril combination label warning about dual blockade risk with ARBs, which pertains to benaze |
| amlodipine | telmisartan | The dual-blockade hyperkalemia/renal failure warning pertains to the benazepril component of the combination product, not to amlodipine, whi |
| amlodipine | enalapril | The snippet warns about combining RAS-blocking agents like ACE inhibitors and ARBs with each other, and comes from an amlodipine/olmesartan  |
| amlodipine | ramipril | The evidence describes dual renin-angiotensin system blockade risk involving olmesartan (an ARB) co-formulated with amlodipine, not a docume |
| losartan | metformin | The warning about needing antidiabetic dosage adjustment is a well-known thiazide diuretic effect on glucose tolerance, attributable to hydr |
| metformin | telmisartan | The evidence describes hydrochlorothiazide's effect on antidiabetic drug dosing from a telmisartan/HCTZ combo label, not an interaction betw |
| glimepiride | telmisartan | The evidence attributes the antidiabetic interaction to hydrochlorothiazide, the co-formulated ingredient in the combination product, not to |
| cyclosporine | telmisartan | The evidence describes amlodipine increasing cyclosporine exposure, not telmisartan, and is misattributed from a telmisartan-amlodipine comb |
| tacrolimus | telmisartan | The evidence describes an interaction between tacrolimus and amlodipine, the co-formulated partner in the telmisartan/amlodipine combination |
| atenolol | lithium | The evidence describes lithium toxicity risk from diuretics (chlorthalidone), the co-formulated ingredient, not from atenolol itself, and be |
| amlodipine | metformin | The snippet is a generic class-effect warning about drugs that cause hyperglycemia and does not specifically name or pharmacologically link  |
| adenosine | aspirin | The evidence describes dipyridamole, the co-formulated ingredient, increasing adenosine levels/effects, not aspirin, so it is misattributed  |
| aspirin | donepezil | The evidence describes dipyridamole, not aspirin, counteracting cholinesterase inhibitors like donepezil, so it is misattributed from the co |
| aspirin | fluconazole | Both evidence snippets describe an interaction between a CYP inhibitor and codeine causing respiratory depression, which is attributable to  |
| aspirin | itraconazole | Both snippets describe an interaction between itraconazole (a CYP inhibitor) and codeine, a co-formulated ingredient in the combination prod |
| aspirin | carbamazepine | The evidence describes a respiratory depression/CYP3A4 induction interaction involving codeine (and carbamazepine as the inducer) from a com |
| aspirin | paroxetine | The evidence concerns codeine's respiratory depression risk when combined with CYP2D6 inhibitors like paroxetine, not an interaction involvi |
| aspirin | diazepam | The warning concerns codeine (an opioid) combined with benzodiazepines causing respiratory depression, not aspirin, which is merely a co-for |
| ciprofloxacin | meropenem | The evidence discusses combinatorial antibiotic testing against resistant Pseudomonas but identifies colistin+ciprofloxacin as effective, no |
| capecitabine | diclofenac | This snippet describes a clinical trial testing topical diclofenac as a treatment/prevention for capecitabine-induced hand-foot syndrome, no |
| aspirin | telmisartan | The evidence is merely a prescription-frequency survey noting both drugs were commonly prescribed, with no pharmacological or clinical inter |
| atorvastatin | telmisartan | The evidence is a prescription-frequency survey noting co-occurrence of telmisartan and statins in cardiovascular prescriptions, not any pha |
| rosuvastatin | telmisartan | The evidence is a prescription-frequency survey noting telmisartan and statins as commonly co-prescribed cardiovascular drugs, but it provid |
| aspirin | atorvastatin | The evidence is a prescription-frequency survey noting aspirin and statins were commonly co-prescribed, not a pharmacological or clinical de |
| aspirin | rosuvastatin | The evidence is merely a prescription-frequency survey noting aspirin and statins are commonly co-prescribed, with no pharmacological or cli |
| domperidone | rabeprazole | The snippet is a prescribing-pattern/guideline-adherence audit noting co-prescription of rabeprazole+domperidone, not evidence of an actual  |
| capecitabine | ondansetron | The evidence describes ondansetron and other QT-prolonging drugs used in cancer patients broadly but does not specifically document a pharma |
| capecitabine | pantoprazole | The evidence is a pharmacoepidemiology study listing pantoprazole among commonly co-prescribed QT-prolonging drugs in cancer patients genera |
| oxaliplatin | pantoprazole | The evidence documents QT-prolonging risk associated with pantoprazole in cancer patients generally but does not establish a specific pharma |
| bortezomib | pantoprazole | The evidence describes pantoprazole and various antineoplastics as independently prevalent QT-prolonging drugs in cancer patients rather tha |
| domperidone | oxaliplatin | The evidence describes co-prevalence of QT-prolonging drug use in a cancer population rather than a documented pharmacokinetic or pharmacody |
| glimepiride | losartan | Warning originates from losartan/HCTZ combo label and describes thiazide-induced hyperglycemia, not a losartan-glimepiride interaction. |

## 5. Coverage / Indian-specificity gap flags


- **No Indian-specific DDI-labeled-text source exists publicly.** All openFDA-derived severity signals are from US-approved product labels. Indian-market-specific formulations/combinations not sold in the US (or with different excipients/dosing conventions) have not been independently re-verified against an Indian regulatory source — **a doctor should review before this list drives autonomous alerts.**
- **PubMed evidence is thin for India-specific pair-level data**: only 7 of 64 unique Indian-context PMIDs found in this search named specific drug pairs in their *abstracts*; full-text mining (out of scope here) would likely surface more India-specific pairs, especially from case reports. Only 1 of the final 80 pairs (amlodipine + atenolol) is PubMed-sourced from an Indian clinical study; the remaining 79 rely on openFDA (US-label) evidence.
- **Brand-name mapping is unofficial**: the Indian-Medicine-Dataset used is community-maintained pharmacy retail data, not CDSCO-verified. Brand names were selected by standalone-product frequency in that dataset and manually spot-checked for two entries (voveran, brufen) against common clinical knowledge; the remainder were not manually cross-verified one-by-one.
- **NPPA list is noisy**: used only as a fallback formulary filter (0.5 weight) since it contains unmerged spelling variants and verbose combination-drug descriptions; NLEM 2022 (387 drugs) was the primary, cleaner filter.
- **No accuracy/precision measurement has been performed** on this list against a clinical ground truth — per project rules, this is unverified candidate content for doctor review, not a validated clinical accuracy claim.
- **DrugBank excluded entirely** — its curated, much larger DDI database (paywalled) was not used; this list is necessarily less exhaustive than a DrugBank-filtered approach would have been.


## 6. Final summary

- **Total pairs delivered**: 80

- **By urgency**: critical=28, high=19, medium=33

- **By underlying severity signal**: major=41, moderate=39

- **Pairs rejected during LLM clinical verification**: 33 of 182 formulary-filtered candidates (18%)

- **Verification suite results**: 0 duplicate pairs, 0 empty sets, 0 non-lowercase strings, 0 rationale ≥200 chars, 0 invalid urgency values, 0 left/right set overlaps, 0 cross-generic brand-name collisions.

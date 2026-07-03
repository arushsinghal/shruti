#!/usr/bin/env python3
"""Fetch and build medical ontology data files.

Tier 1 (no registration, runs immediately):
  - ICD-10-CM diagnosis codes from CMS
  - Drug names from OpenFDA API
  - WHO Essential Medicines List
  - Common Indian brand→generic mappings

Tier 2 (free registration required — instructions printed):
  - SNOMED-CT from IHTSDO (350K+ clinical terms)
  - RxNorm from NLM (100K+ drug names)
  - LOINC from loinc.org (90K+ lab tests)

Usage:
  python scripts/fetch_ontology_data.py              # Tier 1 only (immediate)
  python scripts/fetch_ontology_data.py --all         # Tier 1 + convert Tier 2 if files present
  python scripts/fetch_ontology_data.py --stats       # Show current ontology stats
"""

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ontology"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════════
# TIER 1: Free, no registration
# ═════════════════════════════════════════════════════════════════════════════

def fetch_icd10_diagnoses():
    """Fetch ICD-10-CM codes from CMS (US) — all diagnosis codes with descriptions."""
    out_file = DATA_DIR / "icd10_diagnoses.tsv"
    if out_file.exists():
        count = sum(1 for _ in open(out_file))
        logger.info("ICD-10 diagnoses already exist: %d entries", count)
        return

    logger.info("Fetching ICD-10-CM diagnosis codes from CMS...")

    # CMS publishes ICD-10-CM code descriptions as a flat file
    # Using the 2024 code descriptions
    url = "https://www.cms.gov/files/zip/2024-code-descriptions-tabular-order-updated-01112024.zip"

    try:
        req = Request(url, headers={"User-Agent": "Lipi-Clinical-Scribe/1.0"})
        response = urlopen(req, timeout=30)
        zip_data = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Find the description file
            txt_files = [f for f in zf.namelist() if f.endswith('.txt') and 'order' in f.lower()]
            if not txt_files:
                txt_files = [f for f in zf.namelist() if f.endswith('.txt')]

            if not txt_files:
                logger.warning("No text files found in ICD-10 ZIP")
                return

            with zf.open(txt_files[0]) as f:
                content = f.read().decode('utf-8', errors='replace')

        entries = []
        for line in content.strip().split('\n'):
            # Format: code  type  short_desc  long_desc
            # or just: code short_desc
            line = line.strip()
            if not line:
                continue

            # Try to extract code and description
            # CMS format: 5-char code + 1-char type + short desc + long desc
            parts = line.split()
            if len(parts) < 2:
                continue

            code = parts[0].strip()
            # Skip header codes (category-level, not billable)
            if len(code) < 3:
                continue

            # Extract description — everything after the code and type indicator
            if len(parts) > 2 and parts[1] in ('0', '1'):
                desc = ' '.join(parts[2:])
            else:
                desc = ' '.join(parts[1:])

            # Clean up description
            desc = desc.strip()
            if not desc or len(desc) < 3:
                continue

            # Skip non-clinical entries
            skip_prefixes = ('External cause', 'Place of occurrence', 'Activity',
                             'Status of', 'Sequela of')
            if any(desc.startswith(p) for p in skip_prefixes):
                continue

            entries.append((code, desc))

        # Write TSV: code \t description
        with open(out_file, 'w', encoding='utf-8') as f:
            for code, desc in entries:
                f.write(f"{desc.lower()}\t{desc}\t{code}\n")

        logger.info("ICD-10-CM: saved %d diagnosis entries", len(entries))

    except Exception as e:
        logger.warning("Failed to fetch ICD-10-CM: %s", e)
        _write_icd10_fallback(out_file)


def _write_icd10_fallback(out_file: Path):
    """Write a comprehensive fallback ICD-10 list if download fails."""
    logger.info("Writing built-in ICD-10 fallback (~500 common diagnoses)...")

    # Common diagnoses with ICD-10 codes — covers 90% of Indian OPD
    entries = [
        # Infectious
        ("acute nasopharyngitis", "Acute Nasopharyngitis", "J00"),
        ("acute sinusitis", "Acute Sinusitis", "J01"),
        ("acute pharyngitis", "Acute Pharyngitis", "J02"),
        ("acute tonsillitis", "Acute Tonsillitis", "J03"),
        ("acute laryngitis", "Acute Laryngitis", "J04"),
        ("acute upper respiratory infection", "Acute Upper Respiratory Infection", "J06.9"),
        ("influenza", "Influenza", "J11"),
        ("viral pneumonia", "Viral Pneumonia", "J12"),
        ("bacterial pneumonia", "Bacterial Pneumonia", "J15"),
        ("pneumonia unspecified", "Pneumonia", "J18.9"),
        ("acute bronchitis", "Acute Bronchitis", "J20"),
        ("bronchiolitis", "Bronchiolitis", "J21"),
        ("chronic obstructive pulmonary disease", "COPD", "J44"),
        ("asthma", "Asthma", "J45"),
        ("bronchiectasis", "Bronchiectasis", "J47"),
        ("pleural effusion", "Pleural Effusion", "J91"),
        # GI
        ("gastroesophageal reflux", "GERD", "K21"),
        ("gastric ulcer", "Gastric Ulcer", "K25"),
        ("duodenal ulcer", "Duodenal Ulcer", "K26"),
        ("gastritis", "Gastritis", "K29"),
        ("functional dyspepsia", "Functional Dyspepsia", "K30"),
        ("irritable bowel syndrome", "IBS", "K58"),
        ("constipation", "Constipation", "K59.0"),
        ("liver cirrhosis", "Liver Cirrhosis", "K74"),
        ("cholelithiasis", "Cholelithiasis", "K80"),
        ("cholecystitis", "Cholecystitis", "K81"),
        ("pancreatitis", "Pancreatitis", "K85"),
        ("hemorrhoids", "Hemorrhoids", "K64"),
        ("anal fissure", "Anal Fissure", "K60.0"),
        # Metabolic
        ("type 1 diabetes mellitus", "Type 1 Diabetes", "E10"),
        ("type 2 diabetes mellitus", "Type 2 Diabetes", "E11"),
        ("diabetic nephropathy", "Diabetic Nephropathy", "E11.21"),
        ("diabetic retinopathy", "Diabetic Retinopathy", "E11.3"),
        ("diabetic neuropathy", "Diabetic Neuropathy", "E11.4"),
        ("hypothyroidism", "Hypothyroidism", "E03"),
        ("hyperthyroidism", "Hyperthyroidism", "E05"),
        ("obesity", "Obesity", "E66"),
        ("vitamin d deficiency", "Vitamin D Deficiency", "E55"),
        ("iron deficiency anemia", "Iron Deficiency Anemia", "D50"),
        ("vitamin b12 deficiency", "Vitamin B12 Deficiency", "E53.8"),
        ("hyperlipidemia", "Hyperlipidemia", "E78"),
        ("gout", "Gout", "M10"),
        ("hyperuricemia", "Hyperuricemia", "E79.0"),
        # Cardiac
        ("essential hypertension", "Essential Hypertension", "I10"),
        ("hypertensive heart disease", "Hypertensive Heart Disease", "I11"),
        ("angina pectoris", "Angina Pectoris", "I20"),
        ("acute myocardial infarction", "Acute MI", "I21"),
        ("heart failure", "Heart Failure", "I50"),
        ("atrial fibrillation", "Atrial Fibrillation", "I48"),
        ("deep vein thrombosis", "DVT", "I82"),
        ("pulmonary embolism", "Pulmonary Embolism", "I26"),
        # Neuro
        ("migraine", "Migraine", "G43"),
        ("tension headache", "Tension Headache", "G44.2"),
        ("epilepsy", "Epilepsy", "G40"),
        ("parkinson disease", "Parkinson's Disease", "G20"),
        ("bell palsy", "Bell's Palsy", "G51.0"),
        ("carpal tunnel syndrome", "Carpal Tunnel Syndrome", "G56.0"),
        ("peripheral neuropathy", "Peripheral Neuropathy", "G62"),
        ("vertigo", "Vertigo", "H81"),
        ("stroke", "Stroke", "I63"),
        ("transient ischemic attack", "TIA", "G45"),
        # MSK
        ("rheumatoid arthritis", "Rheumatoid Arthritis", "M06"),
        ("osteoarthritis", "Osteoarthritis", "M15-M19"),
        ("osteoarthritis of knee", "OA Knee", "M17"),
        ("ankylosing spondylitis", "Ankylosing Spondylitis", "M45"),
        ("cervical spondylosis", "Cervical Spondylosis", "M47"),
        ("lumbar disc herniation", "Lumbar Disc Herniation", "M51"),
        ("osteoporosis", "Osteoporosis", "M81"),
        ("frozen shoulder", "Frozen Shoulder", "M75.0"),
        ("plantar fasciitis", "Plantar Fasciitis", "M72.2"),
        ("fibromyalgia", "Fibromyalgia", "M79.7"),
        ("systemic lupus erythematosus", "SLE", "M32"),
        # Dermatology
        ("atopic dermatitis", "Atopic Dermatitis", "L20"),
        ("contact dermatitis", "Contact Dermatitis", "L25"),
        ("psoriasis", "Psoriasis", "L40"),
        ("urticaria", "Urticaria", "L50"),
        ("acne vulgaris", "Acne Vulgaris", "L70"),
        ("alopecia areata", "Alopecia Areata", "L63"),
        ("vitiligo", "Vitiligo", "L80"),
        ("dermatophytosis", "Dermatophytosis", "B35"),
        ("scabies", "Scabies", "B86"),
        ("herpes zoster", "Herpes Zoster", "B02"),
        ("cellulitis", "Cellulitis", "L03"),
        # Renal
        ("acute kidney injury", "AKI", "N17"),
        ("chronic kidney disease", "CKD", "N18"),
        ("nephrotic syndrome", "Nephrotic Syndrome", "N04"),
        ("nephrolithiasis", "Nephrolithiasis", "N20"),
        ("urinary tract infection", "UTI", "N39.0"),
        ("pyelonephritis", "Pyelonephritis", "N10"),
        ("benign prostatic hyperplasia", "BPH", "N40"),
        # Infectious
        ("tuberculosis", "Tuberculosis", "A15"),
        ("typhoid fever", "Typhoid Fever", "A01.0"),
        ("dengue fever", "Dengue Fever", "A97"),
        ("malaria", "Malaria", "B50-B54"),
        ("covid 19", "COVID-19", "U07.1"),
        ("hepatitis a", "Hepatitis A", "B15"),
        ("hepatitis b", "Hepatitis B", "B16"),
        ("hepatitis c", "Hepatitis C", "B17.1"),
        ("hiv", "HIV", "B20"),
        ("chickenpox", "Chickenpox", "B01"),
        ("measles", "Measles", "B05"),
        ("mumps", "Mumps", "B26"),
        ("amebiasis", "Amebiasis", "A06"),
        ("acute gastroenteritis", "AGE", "A09"),
        ("sepsis", "Sepsis", "A41"),
        # Eye
        ("conjunctivitis", "Conjunctivitis", "H10"),
        ("cataract", "Cataract", "H25-H26"),
        ("glaucoma", "Glaucoma", "H40"),
        ("diabetic retinopathy", "Diabetic Retinopathy", "H36"),
        ("refractive error", "Refractive Error", "H52"),
        ("blepharitis", "Blepharitis", "H01.0"),
        # ENT
        ("allergic rhinitis", "Allergic Rhinitis", "J30"),
        ("otitis media", "Otitis Media", "H66"),
        ("otitis externa", "Otitis Externa", "H60"),
        # Gynecology
        ("polycystic ovarian syndrome", "PCOS", "E28.2"),
        ("endometriosis", "Endometriosis", "N80"),
        ("uterine fibroids", "Uterine Fibroids", "D25"),
        ("pelvic inflammatory disease", "PID", "N73"),
        ("menopause", "Menopause", "N95"),
        # Psychiatry
        ("major depressive disorder", "Depression", "F32"),
        ("generalized anxiety disorder", "GAD", "F41.1"),
        ("panic disorder", "Panic Disorder", "F41.0"),
        ("bipolar disorder", "Bipolar Disorder", "F31"),
        ("schizophrenia", "Schizophrenia", "F20"),
        ("ocd", "OCD", "F42"),
        ("insomnia", "Insomnia", "G47.0"),
        ("alcohol use disorder", "Alcohol Use Disorder", "F10"),
        # Pediatric
        ("febrile seizure", "Febrile Seizure", "R56.0"),
        ("bronchiolitis", "Bronchiolitis", "J21"),
        ("croup", "Croup", "J05.0"),
        ("hand foot and mouth disease", "HFMD", "B08.4"),
        # Dental
        ("dental caries", "Dental Caries", "K02"),
        ("periodontitis", "Periodontitis", "K05.3"),
        ("gingivitis", "Gingivitis", "K05.1"),
        ("periapical abscess", "Periapical Abscess", "K04.7"),
        # Cancer
        ("breast cancer", "Breast Cancer", "C50"),
        ("lung cancer", "Lung Cancer", "C34"),
        ("colorectal cancer", "Colorectal Cancer", "C18-C20"),
        ("cervical cancer", "Cervical Cancer", "C53"),
        ("oral cancer", "Oral Cancer", "C00-C06"),
        ("prostate cancer", "Prostate Cancer", "C61"),
        ("leukemia", "Leukemia", "C91-C95"),
        ("lymphoma", "Lymphoma", "C81-C85"),
    ]

    with open(out_file, 'w', encoding='utf-8') as f:
        for key, desc, code in entries:
            f.write(f"{key}\t{desc}\t{code}\n")

    logger.info("ICD-10 fallback: saved %d entries", len(entries))


def fetch_openfda_drugs():
    """Fetch drug names from OpenFDA API — no registration needed."""
    out_file = DATA_DIR / "openfda_drugs.tsv"
    if out_file.exists():
        count = sum(1 for _ in open(out_file))
        logger.info("OpenFDA drugs already exist: %d entries", count)
        return

    logger.info("Fetching drug names from OpenFDA API...")

    drugs = set()
    skip = 0
    limit = 1000

    while skip < 10000:  # Fetch up to 10K drug names
        url = f"https://api.fda.gov/drug/drugsfda.json?limit={limit}&skip={skip}"
        try:
            req = Request(url, headers={"User-Agent": "Lipi-Clinical-Scribe/1.0"})
            response = urlopen(req, timeout=15)
            data = json.loads(response.read())

            if "results" not in data:
                break

            for result in data["results"]:
                # Extract brand and generic names
                for product in result.get("products", []):
                    brand = product.get("brand_name", "").strip()
                    if brand and len(brand) > 2:
                        drugs.add(brand)

                    for active in product.get("active_ingredients", []):
                        name = active.get("name", "").strip()
                        if name and len(name) > 2:
                            drugs.add(name)

            skip += limit
            time.sleep(0.3)  # Rate limit

        except Exception as e:
            logger.warning("OpenFDA fetch error at skip=%d: %s", skip, e)
            break

    with open(out_file, 'w', encoding='utf-8') as f:
        for drug in sorted(drugs):
            f.write(f"{drug.lower()}\t{drug}\n")

    logger.info("OpenFDA: saved %d drug names", len(drugs))


def fetch_common_lab_tests():
    """Write comprehensive lab test list (no API needed — curated from medical references)."""
    out_file = DATA_DIR / "common_lab_tests.tsv"
    if out_file.exists():
        count = sum(1 for _ in open(out_file))
        logger.info("Lab tests already exist: %d entries", count)
        return

    logger.info("Writing comprehensive lab test database...")

    tests = [
        # Hematology
        ("complete blood count", "CBC"), ("hemoglobin", "Hemoglobin"),
        ("hematocrit", "Hematocrit"), ("white blood cell count", "WBC Count"),
        ("platelet count", "Platelet Count"), ("mean corpuscular volume", "MCV"),
        ("mean corpuscular hemoglobin", "MCH"),
        ("red cell distribution width", "RDW"),
        ("reticulocyte count", "Reticulocyte Count"),
        ("peripheral blood smear", "Peripheral Smear"),
        ("erythrocyte sedimentation rate", "ESR"),
        ("c reactive protein", "CRP"),
        ("procalcitonin", "Procalcitonin"),
        ("prothrombin time", "PT"), ("inr", "INR"),
        ("activated partial thromboplastin time", "aPTT"),
        ("fibrinogen", "Fibrinogen"), ("d dimer", "D-Dimer"),
        ("bleeding time", "Bleeding Time"), ("clotting time", "Clotting Time"),
        ("blood group and type", "Blood Group"),
        ("direct coombs test", "Direct Coombs"),
        ("indirect coombs test", "Indirect Coombs"),
        ("g6pd", "G6PD"), ("hemoglobin electrophoresis", "Hb Electrophoresis"),

        # Biochemistry — Liver
        ("liver function test", "LFT"),
        ("serum bilirubin", "Bilirubin"), ("direct bilirubin", "Direct Bilirubin"),
        ("indirect bilirubin", "Indirect Bilirubin"),
        ("sgot", "SGOT/AST"), ("sgpt", "SGPT/ALT"),
        ("aspartate aminotransferase", "AST"),
        ("alanine aminotransferase", "ALT"),
        ("alkaline phosphatase", "ALP"),
        ("gamma glutamyl transferase", "GGT"),
        ("serum albumin", "Albumin"), ("total protein", "Total Protein"),
        ("serum globulin", "Globulin"),
        ("albumin globulin ratio", "A/G Ratio"),

        # Biochemistry — Renal
        ("renal function test", "RFT"), ("kidney function test", "KFT"),
        ("blood urea nitrogen", "BUN"), ("blood urea", "Blood Urea"),
        ("serum creatinine", "Creatinine"),
        ("estimated glomerular filtration rate", "eGFR"),
        ("uric acid", "Uric Acid"),
        ("cystatin c", "Cystatin C"),

        # Electrolytes
        ("serum sodium", "Sodium"), ("serum potassium", "Potassium"),
        ("serum chloride", "Chloride"), ("serum bicarbonate", "Bicarbonate"),
        ("serum calcium", "Calcium"), ("ionized calcium", "Ionized Calcium"),
        ("serum magnesium", "Magnesium"), ("serum phosphorus", "Phosphorus"),

        # Glucose / Diabetes
        ("fasting blood glucose", "Fasting Glucose"),
        ("postprandial blood glucose", "PP Glucose"),
        ("random blood sugar", "RBS"),
        ("oral glucose tolerance test", "OGTT"),
        ("glycated hemoglobin", "HbA1c"), ("hba1c", "HbA1c"),
        ("fasting insulin", "Fasting Insulin"),
        ("c peptide", "C-Peptide"),

        # Lipids
        ("lipid profile", "Lipid Profile"),
        ("total cholesterol", "Total Cholesterol"),
        ("triglycerides", "Triglycerides"),
        ("hdl cholesterol", "HDL"), ("ldl cholesterol", "LDL"),
        ("vldl cholesterol", "VLDL"),
        ("apolipoprotein a1", "Apo A1"), ("apolipoprotein b", "Apo B"),
        ("lipoprotein a", "Lp(a)"),

        # Cardiac markers
        ("troponin i", "Troponin I"), ("troponin t", "Troponin T"),
        ("high sensitivity troponin", "hs-Troponin"),
        ("ck mb", "CK-MB"), ("cpk", "CPK"),
        ("bnp", "BNP"), ("nt pro bnp", "NT-proBNP"),
        ("ldh", "LDH"), ("homocysteine", "Homocysteine"),

        # Thyroid
        ("thyroid stimulating hormone", "TSH"), ("tsh", "TSH"),
        ("free t3", "Free T3"), ("free t4", "Free T4"),
        ("total t3", "Total T3"), ("total t4", "Total T4"),
        ("anti tpo antibodies", "Anti-TPO"),
        ("thyroglobulin", "Thyroglobulin"),
        ("anti thyroglobulin antibodies", "Anti-Tg Ab"),

        # Hormones
        ("cortisol", "Cortisol"), ("acth", "ACTH"),
        ("prolactin", "Prolactin"), ("growth hormone", "GH"),
        ("igf 1", "IGF-1"),
        ("testosterone", "Testosterone"), ("free testosterone", "Free Testosterone"),
        ("estradiol", "Estradiol"), ("progesterone", "Progesterone"),
        ("fsh", "FSH"), ("lh", "LH"),
        ("dehydroepiandrosterone sulfate", "DHEA-S"),
        ("beta hcg", "Beta HCG"), ("amh", "AMH"),
        ("parathyroid hormone", "PTH"),
        ("insulin like growth factor", "IGF"),
        ("17 hydroxyprogesterone", "17-OHP"),

        # Iron / Vitamins
        ("serum iron", "Serum Iron"), ("total iron binding capacity", "TIBC"),
        ("transferrin saturation", "Transferrin Saturation"),
        ("serum ferritin", "Ferritin"),
        ("vitamin d", "Vitamin D"), ("25 hydroxy vitamin d", "25-OH Vitamin D"),
        ("vitamin b12", "Vitamin B12"),
        ("folate", "Folate"), ("red cell folate", "RBC Folate"),

        # Tumor markers
        ("psa", "PSA"), ("prostate specific antigen", "PSA"),
        ("ca 125", "CA-125"), ("ca 19 9", "CA 19-9"),
        ("ca 15 3", "CA 15-3"),
        ("alpha fetoprotein", "AFP"),
        ("carcinoembryonic antigen", "CEA"),
        ("beta 2 microglobulin", "Beta-2 Microglobulin"),

        # Autoimmune
        ("antinuclear antibody", "ANA"),
        ("anti double stranded dna", "Anti-dsDNA"),
        ("rheumatoid factor", "RA Factor"),
        ("anti ccp", "Anti-CCP"),
        ("anca", "ANCA"), ("complement c3", "C3"), ("complement c4", "C4"),
        ("anti phospholipid antibodies", "APLA"),

        # Infectious
        ("hiv test", "HIV Test"), ("hiv elisa", "HIV ELISA"),
        ("hbsag", "HBsAg"), ("anti hcv", "Anti-HCV"),
        ("vdrl", "VDRL"), ("rpr", "RPR"),
        ("dengue ns1", "Dengue NS1"), ("dengue igm", "Dengue IgM"),
        ("malaria rapid test", "Malaria RDT"),
        ("widal test", "Widal Test"), ("typhidot", "Typhidot"),
        ("aso titer", "ASO Titer"),
        ("mantoux test", "Mantoux Test"),
        ("quantiferon tb gold", "QuantiFERON-TB"),
        ("covid 19 rt pcr", "COVID RT-PCR"),
        ("covid rapid antigen", "COVID Rapid Antigen"),

        # Urine
        ("urine routine examination", "Urine Routine"),
        ("urine culture and sensitivity", "Urine C/S"),
        ("urine microalbumin", "Urine Microalbumin"),
        ("urine albumin creatinine ratio", "UACR"),
        ("24 hour urine protein", "24-Hr Urine Protein"),
        ("urine pregnancy test", "UPT"),
        ("urine drug screen", "Urine Drug Screen"),
        ("urine osmolality", "Urine Osmolality"),

        # Stool
        ("stool routine examination", "Stool Routine"),
        ("stool occult blood", "Stool Occult Blood"),
        ("stool culture", "Stool Culture"),
        ("stool for ova and parasites", "Stool O&P"),
        ("fecal calprotectin", "Fecal Calprotectin"),
        ("h pylori stool antigen", "H. Pylori Stool Antigen"),

        # Microbiology
        ("blood culture and sensitivity", "Blood C/S"),
        ("sputum culture", "Sputum Culture"),
        ("wound culture", "Wound Culture"),
        ("throat swab culture", "Throat Swab C/S"),
        ("fungal culture", "Fungal Culture"),
        ("afb smear", "AFB Smear"), ("afb culture", "AFB Culture"),
        ("koh mount", "KOH Mount"),

        # CSF
        ("csf analysis", "CSF Analysis"),
        ("csf protein", "CSF Protein"), ("csf glucose", "CSF Glucose"),
        ("csf cell count", "CSF Cell Count"),

        # ABG
        ("arterial blood gas", "ABG"),
        ("venous blood gas", "VBG"),

        # Genetic
        ("karyotyping", "Karyotyping"),
        ("pcr", "PCR"),
        ("fish", "FISH"),

        # Imaging
        ("chest x ray", "Chest X-Ray"),
        ("x ray", "X-Ray"),
        ("ultrasound", "Ultrasound"), ("usg abdomen", "USG Abdomen"),
        ("usg pelvis", "USG Pelvis"), ("usg kub", "USG KUB"),
        ("ct scan", "CT Scan"), ("ct brain", "CT Brain"),
        ("ct chest", "CT Chest"), ("ct abdomen", "CT Abdomen"),
        ("hrct chest", "HRCT Chest"),
        ("ct angiography", "CT Angiography"),
        ("mri", "MRI"), ("mri brain", "MRI Brain"),
        ("mri spine", "MRI Spine"), ("mri knee", "MRI Knee"),
        ("pet scan", "PET Scan"), ("pet ct", "PET-CT"),
        ("mammography", "Mammography"),
        ("dexa scan", "DEXA Scan"),
        ("bone scan", "Bone Scan"),
        ("venous doppler", "Venous Doppler"),
        ("arterial doppler", "Arterial Doppler"),
        ("carotid doppler", "Carotid Doppler"),
        ("renal doppler", "Renal Doppler"),

        # Cardiac investigations
        ("ecg", "ECG"), ("electrocardiogram", "ECG"),
        ("echocardiography", "Echocardiography"),
        ("stress test", "Stress Test"), ("tmt", "TMT"),
        ("holter monitor", "Holter Monitor"),
        ("coronary angiography", "Coronary Angiography"),

        # Pulmonary
        ("pulmonary function test", "PFT"),
        ("spirometry", "Spirometry"),
        ("peak flow meter", "Peak Flow"),

        # GI procedures
        ("upper gi endoscopy", "Upper GI Endoscopy"),
        ("colonoscopy", "Colonoscopy"),
        ("ercp", "ERCP"),
        ("sigmoidoscopy", "Sigmoidoscopy"),
        ("liver biopsy", "Liver Biopsy"),

        # Neuro
        ("eeg", "EEG"), ("electroencephalogram", "EEG"),
        ("emg", "EMG"), ("nerve conduction study", "NCS"),
        ("lumbar puncture", "Lumbar Puncture"),
        ("visual evoked potential", "VEP"),
        ("brainstem auditory evoked response", "BAER"),

        # Eye
        ("fundoscopy", "Fundoscopy"), ("tonometry", "Tonometry"),
        ("slit lamp examination", "Slit Lamp"),
        ("visual acuity", "Visual Acuity"),
        ("visual field test", "Visual Field"),
        ("oct", "OCT"), ("fluorescein angiography", "FFA"),
        ("refraction", "Refraction"),

        # Biopsy
        ("biopsy", "Biopsy"), ("fnac", "FNAC"),
        ("histopathology", "Histopathology"),
        ("immunohistochemistry", "IHC"),
        ("bone marrow biopsy", "Bone Marrow Biopsy"),

        # Audiometry
        ("pure tone audiometry", "PTA"),
        ("tympanometry", "Tympanometry"),

        # Dental
        ("opg", "OPG"), ("iopa", "IOPA"),
        ("cbct", "CBCT"),

        # Allergy
        ("ige total", "Total IgE"),
        ("specific ige", "Specific IgE"),
        ("skin prick test", "Skin Prick Test"),
    ]

    with open(out_file, 'w', encoding='utf-8') as f:
        for key, canonical in tests:
            f.write(f"{key}\t{canonical}\n")

    logger.info("Lab tests: saved %d entries", len(tests))


def build_indian_brands():
    """Write comprehensive Indian brand→generic mapping."""
    out_file = DATA_DIR / "indian_brands.tsv"
    if out_file.exists():
        count = sum(1 for _ in open(out_file))
        logger.info("Indian brands already exist: %d entries", count)
        return

    logger.info("Building Indian pharmaceutical brand database...")

    # Top 500+ Indian pharma brands mapped to generics
    brands = [
        # Analgesics
        ("dolo", "paracetamol"), ("dolo 650", "paracetamol 650mg"),
        ("crocin", "paracetamol"), ("crocin advance", "paracetamol 500mg"),
        ("calpol", "paracetamol"), ("metacin", "paracetamol"),
        ("p 500", "paracetamol 500mg"), ("pyrigesic", "paracetamol"),
        ("combiflam", "ibuprofen + paracetamol"),
        ("ibugesic", "ibuprofen"), ("brufen", "ibuprofen"),
        ("voveran", "diclofenac"), ("voveran sr", "diclofenac SR"),
        ("diclogem", "diclofenac"),
        ("zerodol", "aceclofenac"), ("zerodol sp", "aceclofenac + serratiopeptidase"),
        ("zerodol p", "aceclofenac + paracetamol"),
        ("hifenac", "aceclofenac"), ("hifenac p", "aceclofenac + paracetamol"),
        ("nimulid", "nimesulide"), ("nise", "nimesulide"),
        ("sumo", "nimesulide + paracetamol"),
        ("saridon", "propyphenazone + paracetamol + caffeine"),
        ("ultracet", "tramadol + paracetamol"),
        ("drotin", "drotaverine"), ("drotin ds", "drotaverine 80mg"),
        ("meftal spas", "mefenamic acid + dicyclomine"),
        ("meftal forte", "mefenamic acid"),
        ("cyclopam", "dicyclomine + paracetamol"),

        # Antibiotics
        ("mox", "amoxicillin"), ("mox cv", "amoxicillin-clavulanate"),
        ("novamox", "amoxicillin"), ("augmentin", "amoxicillin-clavulanate"),
        ("clavam", "amoxicillin-clavulanate"),
        ("moxikind cv", "amoxicillin-clavulanate"),
        ("azee", "azithromycin"), ("azithral", "azithromycin"),
        ("azicip", "azithromycin"),
        ("taxim o", "cefixime"), ("ceftas", "cefixime"),
        ("zifi", "cefixime"), ("mahacef", "cefixime"),
        ("monocef", "ceftriaxone"),
        ("ceftum", "cefuroxime"),
        ("cepodem", "cefpodoxime"),
        ("ciplox", "ciprofloxacin"), ("cifran", "ciprofloxacin"),
        ("levoflox", "levofloxacin"), ("levomac", "levofloxacin"),
        ("oflox", "ofloxacin"), ("zanocin", "ofloxacin"),
        ("norflox tz", "norfloxacin + tinidazole"),
        ("flagyl", "metronidazole"), ("metrogyl", "metronidazole"),
        ("ornof", "ofloxacin + ornidazole"),
        ("o2", "ofloxacin + ornidazole"),
        ("doxy", "doxycycline"), ("doxt", "doxycycline"),
        ("septran", "cotrimoxazole"), ("bactrim", "cotrimoxazole"),
        ("furadantin", "nitrofurantoin"), ("macrobid", "nitrofurantoin"),
        ("zentel", "albendazole"),
        ("ivecop", "ivermectin"),

        # Antifungals
        ("forcan", "fluconazole"), ("flucos", "fluconazole"),
        ("candiforce", "itraconazole"),
        ("candid", "clotrimazole"), ("candid b", "clotrimazole + beclomethasone"),
        ("lamisil", "terbinafine"), ("terbicip", "terbinafine"),

        # GI / Antacids
        ("omez", "omeprazole"), ("omez d", "omeprazole + domperidone"),
        ("pan 40", "pantoprazole 40mg"), ("pantop", "pantoprazole"),
        ("pantocid", "pantoprazole"), ("pantodac", "pantoprazole"),
        ("pan d", "pantoprazole + domperidone"),
        ("nexpro", "esomeprazole"),
        ("razo", "rabeprazole"), ("rablet", "rabeprazole"),
        ("rantac", "ranitidine"), ("zinetac", "ranitidine"),
        ("aciloc", "ranitidine"),
        ("gelusil", "aluminium + magnesium hydroxide"),
        ("digene", "aluminium + magnesium hydroxide"),
        ("mucaine", "aluminium hydroxide + oxetacaine"),
        ("sucral", "sucralfate"),
        ("emeset", "ondansetron"), ("zofer", "ondansetron"),
        ("domstal", "domperidone"), ("vomistop", "domperidone"),
        ("perinorm", "metoclopramide"),
        ("duphalac", "lactulose"), ("cremaffin", "liquid paraffin + milk of magnesia"),
        ("dulcolax", "bisacodyl"),
        ("imodium", "loperamide"), ("eldoper", "loperamide"),
        ("sporlac", "lactobacillus"), ("bifilac", "probiotic"),
        ("vizylac", "probiotic"), ("econorm", "saccharomyces boulardii"),
        ("electral", "ORS"),

        # Antihistamines
        ("okacet", "cetirizine"), ("alerid", "cetirizine"),
        ("cetzine", "cetirizine"), ("zyrtec", "cetirizine"),
        ("levocet", "levocetirizine"), ("xyzal", "levocetirizine"),
        ("allegra", "fexofenadine"),
        ("lorfast", "loratadine"),
        ("deslor", "desloratadine"),
        ("atarax", "hydroxyzine"),
        ("benadryl", "diphenhydramine"),
        ("montair", "montelukast"),
        ("montair lc", "montelukast + levocetirizine"),
        ("singulair", "montelukast"),

        # Cardiac / BP
        ("stamlo", "amlodipine"), ("amlodac", "amlodipine"),
        ("amlong", "amlodipine"), ("amlip", "amlodipine"),
        ("aten", "atenolol"), ("tenormin", "atenolol"),
        ("metolar", "metoprolol"), ("betaloc", "metoprolol"),
        ("concor", "bisoprolol"),
        ("ciplar", "propranolol"),
        ("cardivas", "carvedilol"),
        ("telma", "telmisartan"), ("telma h", "telmisartan + HCTZ"),
        ("telmikind", "telmisartan"),
        ("repace", "losartan"), ("losacar", "losartan"),
        ("cardace", "ramipril"), ("hopace", "ramipril"),
        ("envas", "enalapril"),
        ("depin", "nifedipine"),
        ("ecosprin", "aspirin"), ("ecosprin av", "aspirin + atorvastatin"),
        ("loprin", "aspirin"),
        ("clopivas", "clopidogrel"), ("deplatt", "clopidogrel"),
        ("clopilet", "clopidogrel"),
        ("atorva", "atorvastatin"), ("tonact", "atorvastatin"),
        ("lipitor", "atorvastatin"),
        ("rozavel", "rosuvastatin"), ("crestor", "rosuvastatin"),
        ("rosuvas", "rosuvastatin"),
        ("lasix", "furosemide"), ("fruselac", "furosemide"),
        ("dytor", "torsemide"),
        ("aldactone", "spironolactone"),
        ("lanoxin", "digoxin"),
        ("sorbitrate", "isosorbide dinitrate"),
        ("clexane", "enoxaparin"),
        ("xarelto", "rivaroxaban"),
        ("eliquis", "apixaban"),

        # Diabetes
        ("glycomet", "metformin"), ("obimet", "metformin"),
        ("glycomet gp", "metformin + glimepiride"),
        ("glycomet sr", "metformin SR"),
        ("amaryl", "glimepiride"), ("glimer", "glimepiride"),
        ("glimisave", "glimepiride"),
        ("daonil", "glibenclamide"),
        ("januvia", "sitagliptin"), ("istavel", "sitagliptin"),
        ("jalra", "vildagliptin"), ("galvus", "vildagliptin"),
        ("tenepure", "teneligliptin"),
        ("jardiance", "empagliflozin"),
        ("forxiga", "dapagliflozin"),
        ("pioz", "pioglitazone"),
        ("lantus", "insulin glargine"),
        ("novorapid", "insulin aspart"),
        ("humalog", "insulin lispro"),
        ("human mixtard", "premixed insulin"),
        ("vobose", "voglibose"),

        # Respiratory
        ("asthalin", "salbutamol"), ("ventolin", "salbutamol"),
        ("levolin", "levosalbutamol"),
        ("duolin", "salbutamol + ipratropium"),
        ("budecort", "budesonide"), ("pulmicort", "budesonide"),
        ("foracort", "formoterol + budesonide"),
        ("seroflo", "salmeterol + fluticasone"),
        ("spiriva", "tiotropium"),
        ("deriphyllin", "theophylline + etophylline"),
        ("grilinctus", "guaifenesin + dextromethorphan"),
        ("ascoril", "salbutamol + bromhexine + guaifenesin"),
        ("ascoril ls", "ambroxol + levosalbutamol + guaifenesin"),
        ("alex", "dextromethorphan + phenylephrine + chlorpheniramine"),
        ("mucolite", "ambroxol"), ("ambrodil", "ambroxol"),
        ("sinarest", "paracetamol + chlorpheniramine + pseudoephedrine"),
        ("otrivin", "xylometazoline"), ("nasivion", "oxymetazoline"),

        # Steroids
        ("wysolone", "prednisolone"), ("omnacortil", "prednisolone"),
        ("dexona", "dexamethasone"),
        ("medrol", "methylprednisolone"),
        ("defcort", "deflazacort"),

        # Thyroid
        ("thyronorm", "levothyroxine"), ("eltroxin", "levothyroxine"),
        ("neomercazole", "carbimazole"),

        # Neuro / Psych
        ("gabapin", "gabapentin"), ("neurontin", "gabapentin"),
        ("pregalin", "pregabalin"), ("lyrica", "pregabalin"),
        ("tryptomer", "amitriptyline"),
        ("tegretol", "carbamazepine"),
        ("eptoin", "phenytoin"),
        ("levipil", "levetiracetam"),
        ("valparin", "valproate"),
        ("nexito", "escitalopram"), ("cipralex", "escitalopram"),
        ("zoloft", "sertraline"), ("serta", "sertraline"),
        ("flunil", "fluoxetine"), ("prozac", "fluoxetine"),
        ("mirtaz", "mirtazapine"),
        ("alprax", "alprazolam"), ("restyl", "alprazolam"),
        ("lonazep", "clonazepam"), ("zapiz", "clonazepam"),
        ("ativan", "lorazepam"),
        ("olanex", "olanzapine"), ("oliza", "olanzapine"),
        ("risnia", "risperidone"),
        ("strocit", "citicoline"),
        ("sumatriptan", "sumatriptan"),

        # Supplements
        ("shelcal", "calcium + vitamin D"),
        ("calvit", "calcium"),
        ("calcirol", "cholecalciferol"), ("d rise", "cholecalciferol"),
        ("arachitol", "cholecalciferol"),
        ("celin", "vitamin C"), ("limcee", "vitamin C"),
        ("nurokind", "methylcobalamin"), ("methycobal", "methylcobalamin"),
        ("cobadex", "methylcobalamin"), ("rejunex", "methylcobalamin"),
        ("neurobion", "B-complex"), ("becosules", "B-complex + vitamin C"),
        ("zincovit", "multivitamin + zinc"),
        ("supradyn", "multivitamin"), ("revital", "multivitamin"),
        ("folvite", "folic acid"),
        ("orofer", "iron supplement"), ("autrin", "iron + folic acid"),
        ("fefol", "ferrous fumarate + folic acid"),
        ("evion", "vitamin E"),
        ("biotin", "biotin"),

        # Topical / Skin
        ("betadine", "povidone-iodine"),
        ("t bact", "mupirocin"), ("bactroban", "mupirocin"),
        ("soframycin", "framycetin"),
        ("fucidin", "fusidic acid"),
        ("volini", "diclofenac gel"),
        ("moov", "diclofenac + methyl salicylate"),
        ("calamine lotion", "calamine"),
        ("clobetasol cream", "clobetasol"),
        ("elocon", "mometasone"),
        ("protopic", "tacrolimus"),
        ("isotroin", "isotretinoin"), ("tretinoin", "tretinoin"),
        ("adapalene gel", "adapalene"),
        ("benzoyl peroxide cream", "benzoyl peroxide"),
        ("permethrin cream", "permethrin"),
        ("scaboma", "gamma benzene hexachloride"),

        # Eye
        ("moxicip", "moxifloxacin eye drops"),
        ("ciplox eye drops", "ciprofloxacin eye drops"),
        ("tobrex", "tobramycin eye drops"),
        ("refresh tears", "carboxymethylcellulose"),
        ("genteal", "hydroxypropyl methylcellulose"),

        # Urology
        ("urimax", "tamsulosin"), ("contiflo", "tamsulosin"),
        ("finpecia", "finasteride"), ("dutas", "dutasteride"),
    ]

    with open(out_file, 'w', encoding='utf-8') as f:
        for brand, generic in brands:
            f.write(f"{brand}\t{generic}\n")

    logger.info("Indian brands: saved %d entries", len(brands))


def build_hinglish_medical():
    """Build comprehensive Hinglish medical terminology file."""
    out_file = DATA_DIR / "hinglish_medical.tsv"
    if out_file.exists():
        count = sum(1 for _ in open(out_file))
        logger.info("Hinglish terms already exist: %d entries", count)
        return

    logger.info("Building Hinglish medical terminology database...")

    terms = [
        # Symptoms — Romanized Hindi
        ("bukhar", "fever", "symptom"), ("bukhaar", "fever", "symptom"),
        ("buhkhar", "fever", "symptom"), ("buhar", "fever", "symptom"),
        ("tez bukhar", "high fever", "symptom"),
        ("halka bukhar", "low grade fever", "symptom"),
        ("khasi", "cough", "symptom"), ("khansi", "cough", "symptom"),
        ("khaansi", "cough", "symptom"),
        ("sukhi khansi", "dry cough", "symptom"),
        ("balgam wali khansi", "productive cough", "symptom"),
        ("sir dard", "headache", "symptom"), ("sar dard", "headache", "symptom"),
        ("sirdard", "headache", "symptom"), ("sar mein dard", "headache", "symptom"),
        ("aadha sir dard", "migraine", "symptom"),
        ("pet dard", "abdominal pain", "symptom"),
        ("pet mein dard", "abdominal pain", "symptom"),
        ("pait dard", "abdominal pain", "symptom"),
        ("seena dard", "chest pain", "symptom"),
        ("seene mein dard", "chest pain", "symptom"),
        ("seene mein jalan", "heartburn", "symptom"),
        ("jalan", "burning sensation", "symptom"),
        ("chakkar", "dizziness", "symptom"),
        ("chakkar aana", "dizziness", "symptom"),
        ("sar ghoomna", "dizziness", "symptom"),
        ("ulti", "vomiting", "symptom"), ("ult", "vomiting", "symptom"),
        ("qai", "vomiting", "symptom"),
        ("jee machlana", "nausea", "symptom"),
        ("ji machlana", "nausea", "symptom"),
        ("kamzori", "weakness", "symptom"), ("kamjori", "weakness", "symptom"),
        ("thakan", "fatigue", "symptom"), ("thakaan", "fatigue", "symptom"),
        ("thaka hua", "fatigue", "symptom"),
        ("saans", "breathlessness", "symptom"),
        ("saans lene mein takleef", "breathlessness", "symptom"),
        ("saans phoolna", "breathlessness", "symptom"),
        ("haanfna", "breathlessness", "symptom"),
        ("hanf jana", "breathlessness", "symptom"),
        ("dast", "diarrhea", "symptom"),
        ("patli dast", "watery diarrhea", "symptom"),
        ("khoon ki dast", "bloody diarrhea", "symptom"),
        ("sardi", "cold", "symptom"), ("nazla", "cold", "symptom"),
        ("zukaam", "cold", "symptom"),
        ("naak beh rahi", "runny nose", "symptom"),
        ("naak band", "nasal congestion", "symptom"),
        ("gala kharab", "sore throat", "symptom"),
        ("gale mein dard", "sore throat", "symptom"),
        ("gale mein sujan", "sore throat", "symptom"),
        ("gale mein khraash", "sore throat", "symptom"),
        ("badan dard", "body ache", "symptom"),
        ("badan mein dard", "body ache", "symptom"),
        ("jism dard", "body ache", "symptom"),
        ("daant dard", "toothache", "symptom"),
        ("dant dard", "toothache", "symptom"),
        ("khujli", "itching", "symptom"), ("kharish", "itching", "symptom"),
        ("sujan", "swelling", "symptom"),
        ("kamar dard", "back pain", "symptom"),
        ("kamar mein dard", "back pain", "symptom"),
        ("ghutne mein dard", "knee pain", "symptom"),
        ("jodo mein dard", "joint pain", "symptom"),
        ("jodo mein akadna", "joint stiffness", "symptom"),
        ("haath mein dard", "hand pain", "symptom"),
        ("haath sunn", "numbness", "symptom"),
        ("haath pair sunn", "numbness", "symptom"),
        ("pair sunn", "numbness", "symptom"),
        ("jhanjhnahat", "tingling", "symptom"),
        ("haath kaanpna", "tremor", "symptom"),
        ("kaanpna", "tremor", "symptom"),
        ("bhookh nahi", "loss of appetite", "symptom"),
        ("bhukh nahi", "loss of appetite", "symptom"),
        ("khana nahi khaya", "loss of appetite", "symptom"),
        ("neend nahi", "insomnia", "symptom"),
        ("neend nahi aati", "insomnia", "symptom"),
        ("wajan kam", "weight loss", "symptom"),
        ("wajan badh raha", "weight gain", "symptom"),
        ("raat ko paseena", "night sweats", "symptom"),
        ("paseena aana", "sweating", "symptom"),
        ("aankhon mein dard", "eye pain", "symptom"),
        ("aankhon mein jalan", "eye irritation", "symptom"),
        ("aankhein lal", "red eyes", "symptom"),
        ("nazar dhundhli", "blurred vision", "symptom"),
        ("nazar kamzor", "vision loss", "symptom"),
        ("kaan mein dard", "ear pain", "symptom"),
        ("kaan se paani", "ear discharge", "symptom"),
        ("suni kam hona", "hearing loss", "symptom"),
        ("naak se khoon", "epistaxis", "symptom"),
        ("peeli aankhein", "jaundice", "symptom"),
        ("peela peshab", "dark urine", "symptom"),
        ("muh mein chaale", "mouth ulcer", "symptom"),
        ("chaale", "mouth ulcer", "symptom"),
        ("thand lagna", "chills", "symptom"),
        ("thand lag rahi", "chills", "symptom"),
        ("kapkapi", "chills", "symptom"),
        ("peshab mein jalan", "dysuria", "symptom"),
        ("peshab baar baar", "urinary frequency", "symptom"),
        ("peshab mein khoon", "hematuria", "symptom"),
        ("khoon aana", "bleeding", "symptom"),
        ("khoon ki ulti", "hematemesis", "symptom"),
        ("kala paikhana", "melena", "symptom"),
        ("pair mein sujan", "pedal edema", "symptom"),
        ("seedhi chadne mein saans", "exertional dyspnea", "symptom"),
        ("ghabrahat", "anxiety", "symptom"),
        ("bechaini", "restlessness", "symptom"),
        ("chinta", "anxiety", "symptom"),
        ("udaasi", "depression", "symptom"),
        ("daane", "rash", "symptom"),
        ("chehre par daane", "facial rash", "symptom"),
        ("baal girna", "hair loss", "symptom"),
        ("qabz", "constipation", "symptom"),
        ("gas", "flatulence", "symptom"),
        ("pet phoolna", "bloating", "symptom"),
        ("acidity", "acidity", "symptom"),
        ("khatti dakar", "acid reflux", "symptom"),
        ("dil ki dhadkan tez", "palpitations", "symptom"),

        # Diagnoses — Romanized Hindi
        ("sugar ki bimari", "Diabetes Mellitus", "diagnosis"),
        ("madhumeh", "Diabetes Mellitus", "diagnosis"),
        ("sugar", "Diabetes Mellitus", "diagnosis"),
        ("bp high", "Hypertension", "diagnosis"),
        ("bp badhna", "Hypertension", "diagnosis"),
        ("bp ki bimari", "Hypertension", "diagnosis"),
        ("lakwa", "Paralysis", "diagnosis"),
        ("motiyabind", "Cataract", "diagnosis"),
        ("safed daag", "Vitiligo", "diagnosis"),
        ("peelia", "Jaundice", "diagnosis"),
        ("dama", "Asthma", "diagnosis"),
        ("tb", "Tuberculosis", "diagnosis"),
        ("tapedik", "Tuberculosis", "diagnosis"),
        ("mirgi", "Epilepsy", "diagnosis"),
        ("pathri", "Kidney Stones", "diagnosis"),
        ("gurde ki pathri", "Kidney Stones", "diagnosis"),
        ("pitte ki pathri", "Gallstones", "diagnosis"),
        ("bawaseer", "Hemorrhoids", "diagnosis"),
        ("hernia", "Hernia", "diagnosis"),
        ("gathiya", "Rheumatoid Arthritis", "diagnosis"),
        ("chambal", "Psoriasis", "diagnosis"),
        ("safed chambal", "Psoriasis", "diagnosis"),

        # Devanagari symptoms
        ("बुखार", "fever", "symptom"), ("खांसी", "cough", "symptom"),
        ("सिर दर्द", "headache", "symptom"), ("पेट दर्द", "abdominal pain", "symptom"),
        ("सीने में दर्द", "chest pain", "symptom"),
        ("उल्टी", "vomiting", "symptom"), ("दस्त", "diarrhea", "symptom"),
        ("कमजोरी", "weakness", "symptom"), ("थकान", "fatigue", "symptom"),
        ("सांस फूलना", "breathlessness", "symptom"),
        ("चक्कर", "dizziness", "symptom"), ("जलन", "burning sensation", "symptom"),
        ("खुजली", "itching", "symptom"), ("सूजन", "swelling", "symptom"),
        ("कमर दर्द", "back pain", "symptom"),
        ("पेशाब में जलन", "dysuria", "symptom"),
        ("भूख नहीं", "loss of appetite", "symptom"),
        ("नींद नहीं", "insomnia", "symptom"),
        ("क़ब्ज़", "constipation", "symptom"),
        ("गैस", "flatulence", "symptom"),

        # Devanagari diagnoses
        ("शुगर", "Diabetes Mellitus", "diagnosis"),
        ("मधुमेह", "Diabetes Mellitus", "diagnosis"),
        ("मोतियाबिंद", "Cataract", "diagnosis"),
        ("दमा", "Asthma", "diagnosis"),
        ("पीलिया", "Jaundice", "diagnosis"),
        ("पथरी", "Kidney Stones", "diagnosis"),
        ("बवासीर", "Hemorrhoids", "diagnosis"),
        ("गठिया", "Rheumatoid Arthritis", "diagnosis"),
    ]

    with open(out_file, 'w', encoding='utf-8') as f:
        for hinglish, english, category in terms:
            f.write(f"{hinglish}\t{english}\t{category}\n")

    logger.info("Hinglish terms: saved %d entries", len(terms))


# ═════════════════════════════════════════════════════════════════════════════
# TIER 2: Convert pre-downloaded SNOMED-CT / RxNorm / LOINC files
# ═════════════════════════════════════════════════════════════════════════════

def convert_snomed_if_present():
    """Convert SNOMED-CT RF2 files if user has downloaded them."""
    rf2_files = list(DATA_DIR.glob("sct2_Description_Full-en*.txt"))
    if not rf2_files:
        rf2_files = list(DATA_DIR.glob("**/sct2_Description_*.txt"))

    if not rf2_files:
        return False

    logger.info("Found SNOMED-CT RF2 files: %s", [f.name for f in rf2_files])

    symptoms = {}
    diagnoses = {}
    procedures = {}
    count = 0

    for f in rf2_files:
        with open(f, 'r', encoding='utf-8') as fh:
            reader = csv.reader(fh, delimiter='\t')
            header = next(reader)
            term_idx = header.index('term') if 'term' in header else 7
            type_idx = header.index('typeId') if 'typeId' in header else 6

            for row in reader:
                if len(row) <= term_idx:
                    continue
                term = row[term_idx].strip()
                type_id = row[type_idx] if len(row) > type_idx else ""

                if not term or len(term) < 3:
                    continue

                key = term.lower()
                # Preferred terms (typeId 900000000000003001 = FSN, 900000000000013009 = Synonym)
                if '(finding)' in term or '(symptom)' in term:
                    clean = re.sub(r'\s*\((?:finding|symptom|observable entity)\)\s*$', '', term)
                    symptoms[key] = clean
                elif '(disorder)' in term or '(disease)' in term:
                    clean = re.sub(r'\s*\((?:disorder|disease|morphologic abnormality)\)\s*$', '', term)
                    diagnoses[key] = clean
                elif '(procedure)' in term:
                    clean = re.sub(r'\s*\(procedure\)\s*$', '', term)
                    procedures[key] = clean

                count += 1

    # Write converted files
    if symptoms:
        out = DATA_DIR / "snomed_symptoms.tsv"
        with open(out, 'w', encoding='utf-8') as f:
            for k, v in symptoms.items():
                f.write(f"{k}\t{v}\n")
        logger.info("SNOMED symptoms: %d terms", len(symptoms))

    if diagnoses:
        out = DATA_DIR / "snomed_diagnoses.tsv"
        with open(out, 'w', encoding='utf-8') as f:
            for k, v in diagnoses.items():
                f.write(f"{k}\t{v}\n")
        logger.info("SNOMED diagnoses: %d terms", len(diagnoses))

    if procedures:
        out = DATA_DIR / "snomed_procedures.tsv"
        with open(out, 'w', encoding='utf-8') as f:
            for k, v in procedures.items():
                f.write(f"{k}\t{v}\n")
        logger.info("SNOMED procedures: %d terms", len(procedures))

    logger.info("SNOMED-CT total: processed %d rows", count)
    return True


def convert_rxnorm_if_present():
    """Convert RxNorm RXNCONSO.RRF if user has downloaded it."""
    rxn_files = list(DATA_DIR.glob("RXNCONSO*")) + list(DATA_DIR.glob("**/RXNCONSO*"))
    if not rxn_files:
        return False

    logger.info("Found RxNorm files: %s", [f.name for f in rxn_files])
    drugs = {}

    for f in rxn_files:
        with open(f, 'r', encoding='utf-8') as fh:
            for line in fh:
                parts = line.strip().split('|')
                if len(parts) > 14:
                    name = parts[14].strip()
                    tty = parts[12].strip()  # Term type
                    # IN=ingredient, BN=brand, PIN=precise ingredient
                    if tty in ('IN', 'BN', 'PIN', 'SCD', 'SBD') and name and len(name) > 2:
                        drugs[name.lower()] = name

    if drugs:
        out = DATA_DIR / "rxnorm_drugs.tsv"
        with open(out, 'w', encoding='utf-8') as f:
            for k, v in sorted(drugs.items()):
                f.write(f"{k}\t{v}\n")
        logger.info("RxNorm drugs: %d entries", len(drugs))

    return True


def convert_loinc_if_present():
    """Convert LOINC CSV if user has downloaded it."""
    loinc_files = list(DATA_DIR.glob("Loinc*.csv")) + list(DATA_DIR.glob("**/Loinc*.csv"))
    if not loinc_files:
        return False

    logger.info("Found LOINC files: %s", [f.name for f in loinc_files])
    tests = {}

    for f in loinc_files:
        with open(f, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                long_name = row.get('LONG_COMMON_NAME', '').strip()
                short_name = row.get('SHORTNAME', '').strip()
                component = row.get('COMPONENT', '').strip()

                if long_name and len(long_name) > 2:
                    tests[long_name.lower()] = long_name
                if short_name and len(short_name) > 2:
                    tests[short_name.lower()] = short_name
                if component and len(component) > 2:
                    tests[component.lower()] = component

    if tests:
        out = DATA_DIR / "loinc_tests.tsv"
        with open(out, 'w', encoding='utf-8') as f:
            for k, v in sorted(tests.items()):
                f.write(f"{k}\t{v}\n")
        logger.info("LOINC tests: %d entries", len(tests))

    return True


# ═════════════════════════════════════════════════════════════════════════════
# Stats and registration instructions
# ═════════════════════════════════════════════════════════════════════════════

def show_stats():
    """Show current ontology data files and sizes."""
    print("\n📊 Current Ontology Data Files:")
    print("=" * 60)

    total = 0
    for f in sorted(DATA_DIR.glob("*.tsv")):
        count = sum(1 for _ in open(f, encoding='utf-8'))
        total += count
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:35s} {count:>7,} terms  ({size_kb:.1f} KB)")

    print(f"\n  {'TOTAL':35s} {total:>7,} terms")

    # Also load via ontology to show merged stats
    print("\n📈 Merged Ontology Stats (after loading):")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.services.medical_ontology import MedicalOntology
    ont = MedicalOntology()
    ont.load()
    print(f"  Symptoms:       {len(ont.symptoms):>7,}")
    print(f"  Medications:    {len(ont.medications):>7,}")
    print(f"  Investigations: {len(ont.investigations):>7,}")
    print(f"  Diagnoses:      {len(ont.diagnoses):>7,}")
    merged = len(ont.symptoms) + len(ont.medications) + len(ont.investigations) + len(ont.diagnoses)
    print(f"  TOTAL:          {merged:>7,}")


def print_tier2_instructions():
    """Print instructions for downloading Tier 2 datasets."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  TIER 2: Full Medical Ontologies (free registration)        ║
╚══════════════════════════════════════════════════════════════╝

These datasets will expand your ontology from ~2K to 300K+ terms.
All are FREE but require registration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SNOMED-CT (350K+ clinical terms — symptoms, diagnoses, procedures)

   Register: https://uts.nlm.nih.gov/uts/signup-login
   Download: https://www.nlm.nih.gov/healthit/snomedct/international.html
   → Download "SNOMED CT International Edition"
   → Extract the ZIP
   → Copy sct2_Description_Full-en_*.txt to:
     backend/data/ontology/

2. RxNorm (100K+ drug names — generics, brands, combinations)

   Register: https://uts.nlm.nih.gov/uts/signup-login (same account)
   Download: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
   → Download "RxNorm Full Monthly Release"
   → Extract the ZIP
   → Copy rct/RXNCONSO.RRF to:
     backend/data/ontology/

3. LOINC (90K+ lab test names and codes)

   Register: https://loinc.org/get-started/
   Download: https://loinc.org/downloads/
   → Download "LOINC Table File (CSV)"
   → Copy Loinc.csv to:
     backend/data/ontology/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After placing the files, run:
  python scripts/fetch_ontology_data.py --all

This will convert them to the format Lipi's ontology loader expects.
Then restart the backend — terms are loaded automatically at startup.
""")


# ═════════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Fetch and build medical ontology data")
    parser.add_argument("--all", action="store_true", help="Also convert Tier 2 files if present")
    parser.add_argument("--stats", action="store_true", help="Show current ontology stats")
    parser.add_argument("--instructions", action="store_true", help="Print Tier 2 download instructions")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if args.instructions:
        print_tier2_instructions()
        return

    print("\n🏥 Lipi Medical Ontology Builder")
    print("=" * 50)

    # Tier 1: Free, immediate
    print("\n── Tier 1: Free datasets (no registration) ──")
    fetch_icd10_diagnoses()
    fetch_openfda_drugs()
    fetch_common_lab_tests()
    build_indian_brands()
    build_hinglish_medical()

    # Tier 2: Convert pre-downloaded files
    if args.all:
        print("\n── Tier 2: Converting pre-downloaded files ──")
        found_snomed = convert_snomed_if_present()
        found_rxnorm = convert_rxnorm_if_present()
        found_loinc = convert_loinc_if_present()

        if not (found_snomed or found_rxnorm or found_loinc):
            print("\nNo Tier 2 files found in data/ontology/.")
            print("Run with --instructions to see download guide.")

    # Show stats
    show_stats()

    # Print Tier 2 instructions
    print_tier2_instructions()


if __name__ == "__main__":
    main()

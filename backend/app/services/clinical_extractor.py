"""Deterministic clinical fact extraction from multilingual transcripts.

Extraction layers (applied in order, results merged):
  1. Keyword maps   — English + transliterated Hinglish + Devanagari Hindi
  2. Fuzzy matching — catches ASR spelling errors via rapidfuzz (optional dep)
  3. Regex rules    — vitals, allergies, medications, follow-up
  4. Negation guard — pre-negation (English) + post-negation (Hindi "nahi")

spaCy is used only for sentence segmentation.
"""

import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")


# ──────────────────────────────────────────────────────────────────────────────
# Pre-processing: Devanagari detection + transliteration
# ──────────────────────────────────────────────────────────────────────────────

_DEVANAGARI_RE = re.compile(r'[ऀ-ॿ]')


def _maybe_transliterate(text: str) -> str:
    """If Devanagari script detected, try indic_transliteration → ITRANS Roman.
    Falls back to original text if library not installed."""
    if not _DEVANAGARI_RE.search(text):
        return text
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
    except Exception:
        return text  # library not installed — Devanagari keywords in maps still fire


# ──────────────────────────────────────────────────────────────────────────────
# Keyword maps  (canonical English ← Hindi / Hinglish / Devanagari)
# ──────────────────────────────────────────────────────────────────────────────

_SYMPTOM_MAP: dict[str, str] = {
    # ── Core English symptoms ─────────────────────────────────────────────
    "fever": "fever",
    # Common ASR mis-spellings (Sarvam STT errors on English words)
    "fevre": "fever", "fver": "fever", "fevr": "fever",
    "headach": "headache", "hedache": "headache",
    "vomitin": "vomiting", "vomitting": "vomiting",
    "diarrhoea": "diarrhea", "diarreia": "diarrhea", "diarea": "diarrhea",
    "sweling": "swelling", "swollne": "swelling",
    "high fever": "fever",
    "high grade fever": "fever",
    "low grade fever": "low grade fever",
    "intermittent fever": "intermittent fever",
    "continuous fever": "fever",
    "persistent fever": "fever",
    "cough": "cough",
    "dry cough": "dry cough",
    "wet cough": "productive cough",
    "productive cough": "productive cough",
    "headache": "headache",
    "chest pain": "chest pain",
    "chest tightness": "chest tightness",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "dizziness": "dizziness",
    "vertigo": "dizziness",
    "weakness": "weakness",
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "lethargy": "fatigue",
    "breathlessness": "breathlessness",
    "shortness of breath": "breathlessness",
    "difficulty breathing": "breathlessness",
    "sob": "breathlessness",
    "dyspnea": "breathlessness",
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "loose motions": "diarrhea",
    "loose motion": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "frequent stools": "diarrhea",
    "cold": "cold",
    "common cold": "cold",
    "runny nose": "runny nose",
    "nasal discharge": "runny nose",
    "nasal drip": "runny nose",
    "blocked nose": "blocked nose",
    "nasal congestion": "blocked nose",
    "stuffy nose": "blocked nose",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "throat irritation": "sore throat",
    "throat infection": "sore throat",
    "body ache": "body ache",
    "muscle ache": "body ache",
    "muscle pain": "body ache",
    "myalgia": "body ache",
    "abdominal pain": "abdominal pain",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "belly ache": "abdominal pain",
    "lower abdominal pain": "lower abdominal pain",
    "upper abdominal pain": "upper abdominal pain",
    "epigastric pain": "epigastric pain",
    "back pain": "back pain",
    "lower back pain": "lower back pain",
    "backache": "back pain",
    "rash": "rash",
    "skin rash": "rash",
    "hives": "rash",
    "urticaria": "rash",
    "itching": "itching",
    "itchy": "itching",
    "pruritus": "itching",
    "burning": "burning sensation",
    "burning sensation": "burning sensation",
    "burning micturition": "burning micturition",
    "burning urination": "burning micturition",
    "dysuria": "burning micturition",
    "painful urination": "burning micturition",
    "swelling": "swelling",
    "edema": "edema",
    "pitting edema": "edema",
    "ankle swelling": "ankle swelling",
    "leg swelling": "ankle swelling",
    "facial swelling": "facial swelling",
    "palpitations": "palpitations",
    "heart racing": "palpitations",
    "rapid heartbeat": "palpitations",
    "wheezing": "wheezing",
    "constipation": "constipation",
    "bloating": "bloating",
    "gas": "bloating",
    "flatulence": "bloating",
    "acidity": "acidity",
    "heartburn": "acidity",
    "acid reflux": "acidity",
    "regurgitation": "acidity",
    "indigestion": "indigestion",
    "dyspepsia": "indigestion",
    "toothache": "toothache",
    "tooth ache": "toothache",
    "tooth pain": "toothache",
    "teeth pain": "toothache",
    "dental pain": "toothache",
    "eye pain": "eye pain",
    "eye irritation": "eye irritation",
    "red eyes": "eye irritation",
    "watery eyes": "watery eyes",
    "blurred vision": "blurred vision",
    "double vision": "blurred vision",
    "vision problems": "blurred vision",
    "vision loss": "vision loss",
    "ear pain": "ear pain",
    "earache": "ear pain",
    "hearing loss": "hearing loss",
    "insomnia": "insomnia",
    "sleep problems": "insomnia",
    "difficulty sleeping": "insomnia",
    "anxiety": "anxiety",
    "tremors": "tremors",
    "shaking": "tremors",
    "numbness": "numbness",
    "tingling": "numbness",
    "joint pain": "joint pain",
    "knee pain": "knee pain",
    "shoulder pain": "shoulder pain",
    "neck pain": "neck pain",
    "hip pain": "hip pain",
    "loss of appetite": "loss of appetite",
    "poor appetite": "loss of appetite",
    "weight loss": "weight loss",
    "chills": "chills",
    "rigors": "chills",
    "night sweats": "night sweats",
    "sweating": "sweating",
    "excessive sweating": "sweating",
    "mouth ulcer": "mouth ulcer",
    "oral ulcer": "mouth ulcer",
    "nosebleed": "nosebleed",
    "epistaxis": "nosebleed",
    "bleeding": "bleeding",
    "blood in urine": "hematuria",
    "hematuria": "hematuria",
    "blood in stool": "rectal bleeding",
    "pale": "pallor",
    "pallor": "pallor",
    "jaundice": "jaundice",
    "yellow eyes": "jaundice",
    "yellowish eyes": "jaundice",
    "dark urine": "dark urine",
    "yellowish urine": "dark urine",
    "hair loss": "hair loss",
    "alopecia": "hair loss",
    "cavity": "cavity",
    # ── Hinglish transliterations ─────────────────────────────────────────
    # Note: bare "dard" and "pain" intentionally excluded — too generic.
    # Specific combos (gale mein dard, sar dard, etc.) already cover them.
    "bukhar": "fever",
    "bukhaar": "fever",
    "buhkhar": "fever",
    "buhar": "fever",
    "tez bukhar": "fever",
    "khasi": "cough",
    "khansi": "cough",
    "khaansi": "cough",
    "sukhi khansi": "dry cough",
    "sir dard": "headache",
    "sar dard": "headache",
    "sirdard": "headache",
    "sar mein dard": "headache",
    "pet dard": "abdominal pain",
    "pet mein dard": "abdominal pain",
    "pait dard": "abdominal pain",
    "pait mein dard": "abdominal pain",
    "seena dard": "chest pain",
    "seene mein dard": "chest pain",
    "seene mein jalan": "acidity",
    "jalan": "burning sensation",
    "chakkar": "dizziness",
    "chakkar aana": "dizziness",
    "sar ghoomna": "dizziness",
    "ulti": "vomiting",
    "ult": "vomiting",
    "jee machlana": "nausea",
    "ji machlana": "nausea",
    "jee machlaana": "nausea",
    "kamzori": "weakness",
    "kamjori": "weakness",
    "thakan": "fatigue",
    "thakaan": "fatigue",
    "thaka hua": "fatigue",
    "saans": "breathlessness",
    "saans lene mein takleef": "breathlessness",
    "saans phoolna": "breathlessness",
    "haanfna": "breathlessness",
    "hanf jana": "breathlessness",
    "dast": "diarrhea",
    "sardi": "cold",
    "nazla": "cold",
    "naak beh rahi": "runny nose",
    "naak beh raha": "runny nose",
    "naak band": "blocked nose",
    "gala kharab": "sore throat",
    "gale mein dard": "sore throat",
    "gale mein sujan": "sore throat",
    "badan dard": "body ache",
    "badan mein dard": "body ache",
    "daant dard": "toothache",
    "dant dard": "toothache",
    "khujli": "itching",
    "kharish": "itching",
    "sujan": "swelling",
    "kamar dard": "back pain",
    "kamar mein dard": "back pain",
    "ghutne mein dard": "knee pain",
    "jodo mein dard": "joint pain",
    "haath mein dard": "hand pain",
    "haath sunn": "numbness",
    "haath pair sunn": "numbness",
    "pair sunn": "numbness",
    "jhanjhnahat": "numbness",
    "haath kaanpna": "tremors",
    "haath kaanpe": "tremors",
    "kaanpna": "tremors",
    "bhookh nahi": "loss of appetite",
    "bhukh nahi": "loss of appetite",
    "khana nahi khaya": "loss of appetite",
    "neend nahi": "insomnia",
    "neend aati nahi": "insomnia",
    "wajan kam": "weight loss",
    "vajan ghat raha": "weight loss",
    "raat ko paseena": "night sweats",
    "aankhon mein dard": "eye pain",
    "aankhon mein jalan": "eye irritation",
    "aankhein lal": "eye irritation",
    "nazar dhundhli": "blurred vision",
    "dhundhla dikhna": "blurred vision",
    "naak se khoon": "nosebleed",
    "peeli aankhein": "jaundice",
    "aankhein peeli": "jaundice",
    "peeli skin": "jaundice",
    "muh mein chaale": "mouth ulcer",
    "chaale": "mouth ulcer",
    "kaan mein dard": "ear pain",
    # ── Devanagari Hindi (direct Unicode matching) ─────────────────────────
    "बुखार": "fever",
    "बुखाऱ": "fever",
    "खांसी": "cough",
    "खाँसी": "cough",
    "खासी": "cough",
    "सिर दर्द": "headache",
    "सर दर्द": "headache",
    # Note: bare "दर्द" intentionally excluded — too generic, causes false positives.
    "सीने में दर्द": "chest pain",
    "सीने में जलन": "acidity",
    "जलन": "burning sensation",
    "जी मिचलाना": "nausea",
    "उल्टी": "vomiting",
    "चक्कर": "dizziness",
    "कमजोरी": "weakness",
    "थकान": "fatigue",
    "सांस फूलना": "breathlessness",
    "सांस लेने में तकलीफ": "breathlessness",
    "दस्त": "diarrhea",
    "सर्दी": "cold",
    "नाक बहना": "runny nose",
    "नाक बंद": "blocked nose",
    "गले में दर्द": "sore throat",
    "गले में खराश": "sore throat",
    "बदन दर्द": "body ache",
    "पेट दर्द": "abdominal pain",
    "पेट में दर्द": "abdominal pain",
    "खुजली": "itching",
    "सूजन": "swelling",
    "कमर दर्द": "back pain",
    "भूख नहीं": "loss of appetite",
    "नींद नहीं": "insomnia",
    "वजन कम": "weight loss",
    "हाथ-पैर सुन्न": "numbness",
    "हाथ कांपना": "tremors",
    "पीली आंखें": "jaundice",
    "आंखों में दर्द": "eye pain",
    "घुटने में दर्द": "knee pain",
    "जोड़ों में दर्द": "joint pain",
}

_INVESTIGATION_MAP: dict[str, str] = {
    "x-ray": "X-Ray",
    "x ray": "X-Ray",
    "xray": "X-Ray",
    "chest x-ray": "Chest X-Ray",
    "chest xray": "Chest X-Ray",
    "blood test": "Blood Test",
    "blood work": "Blood Test",
    "khoon ki jaanch": "Blood Test",
    "खून की जांच": "Blood Test",
    "cbc": "CBC",
    "complete blood count": "CBC",
    "hemogram": "CBC",
    "crp": "CRP",
    "esr": "ESR",
    "mri": "MRI",
    "ultrasound": "Ultrasound",
    "usg": "Ultrasound",
    "sonography": "Ultrasound",
    "ct scan": "CT Scan",
    "ctscan": "CT Scan",
    "ecg": "ECG",
    "ekg": "ECG",
    "electrocardiogram": "ECG",
    "echo": "Echocardiography",
    "echocardiogram": "Echocardiography",
    "2d echo": "Echocardiography",
    "urine test": "Urine Test",
    "urine routine": "Urine Routine",
    "urine re": "Urine Routine",
    "urine r/e": "Urine Routine",
    "urine culture": "Urine Culture",
    "thyroid test": "Thyroid Panel",
    "thyroid function": "Thyroid Panel",
    "tsh": "Thyroid Panel",
    "t3 t4": "Thyroid Panel",
    "t3": "Thyroid Panel",
    "t4": "Thyroid Panel",
    "hba1c": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    "glycosylated hemoglobin": "HbA1c",
    "lft": "Liver Function Test",
    "liver function": "Liver Function Test",
    "liver function test": "Liver Function Test",
    "rft": "Renal Function Test",
    "kidney function": "Renal Function Test",
    "renal function": "Renal Function Test",
    "creatinine": "Renal Function Test",
    "bun": "Renal Function Test",
    "lipid profile": "Lipid Profile",
    "cholesterol": "Lipid Profile",
    "triglycerides": "Lipid Profile",
    "electrolytes": "Electrolytes",
    "sodium potassium": "Electrolytes",
    "serum electrolytes": "Electrolytes",
    "blood culture": "Blood Culture",
    "culture sensitivity": "Culture & Sensitivity",
    "throat swab": "Throat Swab Culture",
    "throat culture": "Throat Swab Culture",
    "sputum": "Sputum Culture",
    "sputum culture": "Sputum Culture",
    "dengue test": "Dengue NS1/IgM",
    "dengue ns1": "Dengue NS1/IgM",
    "dengue": "Dengue NS1/IgM",
    "malaria test": "Malaria RDT",
    "malaria rdt": "Malaria RDT",
    "widal": "Widal Test",
    "typhidot": "Typhidot",
    "covid test": "COVID Antigen",
    "covid rtpcr": "COVID RT-PCR",
    "rapid antigen": "Rapid Antigen Test",
    "stool test": "Stool Examination",
    "stool routine": "Stool Examination",
    "stool culture": "Stool Culture",
    "blood sugar": "Blood Glucose",
    "fasting sugar": "Fasting Blood Glucose",
    "pp sugar": "Post-Prandial Glucose",
    "rbs": "Random Blood Sugar",
    "fbs": "Fasting Blood Sugar",
    "bone density": "DEXA Scan",
    "dexa": "DEXA Scan",
    "pft": "Pulmonary Function Test",
    "pulmonary function": "Pulmonary Function Test",
    "spirometry": "Spirometry",
    "tmt": "TMT (Stress Test)",
    "stress test": "TMT (Stress Test)",
    "holter": "Holter Monitor",
    "root canal": "Root Canal Treatment",
    "root canal treatment": "Root Canal Treatment",
    "rct": "Root Canal Treatment",
    "filling": "Cavity Filling",
    "cavity filling": "Cavity Filling",
    "extraction": "Tooth Extraction",
    "scaling": "Dental Scaling",
    "examination": "Clinical Examination",
}

_ALLERGY_PATTERNS = [
    r'(?:allergic\s+to|allergy\s+to)\s+([a-zA-Z]+)',
    r'([a-zA-Z]{4,})\s+(?:se\s+allergy|ko\s+allergy)',
    r'(?:known\s+allergy|allergy)\s*:\s*([a-zA-Z]+)',
    r'([a-zA-Z]{4,})\s+allergy\b',
    r'(?:reaction\s+to|had\s+reaction\s+with)\s+([a-zA-Z]+)',
    r'([a-zA-Z]{4,})\s+se\s+(?:rash|reaction|problem)\s+(?:hua|hai|hoti)',
    r'([a-zA-Z]{4,})\s+(?:nahi\s+leni|band\s+kar)',  # "penicillin nahi leni"
]

_POST_NEGATION_RE = re.compile(r'\b(nahi|nahin|mat|na|nhi)\b', re.IGNORECASE)

_DIAGNOSIS_MAP: dict[str, str] = {
    # ── Infections ────────────────────────────────────────────────────────
    "viral fever": "Viral Fever",
    "viral infection": "Viral Infection",
    "viral illness": "Viral Illness",
    "dengue": "Dengue Fever",
    "dengue fever": "Dengue Fever",
    "typhoid": "Typhoid Fever",
    "malaria": "Malaria",
    "covid": "COVID-19",
    "corona": "COVID-19",
    "influenza": "Influenza",
    "flu": "Influenza",
    "chickenpox": "Varicella",
    "varicella": "Varicella",
    "mumps": "Mumps",
    "measles": "Measles",
    "tuberculosis": "Tuberculosis",
    "tb": "Tuberculosis",
    "scabies": "Scabies",
    "fungal infection": "Fungal Infection",
    "ringworm": "Fungal Infection",
    "tinea": "Fungal Infection",
    "cellulitis": "Cellulitis",
    "hepatitis": "Hepatitis",
    "hepatitis a": "Hepatitis A",
    "hepatitis b": "Hepatitis B",
    "hepatitis c": "Hepatitis C",
    # ── Respiratory ───────────────────────────────────────────────────────
    "urti": "URTI",
    "upper respiratory tract infection": "URTI",
    "upper respiratory infection": "URTI",
    "uri": "URTI",
    "lrti": "LRTI",
    "lower respiratory tract infection": "LRTI",
    "pneumonia": "Pneumonia",
    "bronchitis": "Bronchitis",
    "bronchopneumonia": "Bronchopneumonia",
    "asthma": "Asthma",
    "copd": "COPD",
    "pleural effusion": "Pleural Effusion",
    "pharyngitis": "Pharyngitis",
    "tonsillitis": "Tonsillitis",
    "laryngitis": "Laryngitis",
    "sinusitis": "Sinusitis",
    "otitis": "Otitis Media",
    "otitis media": "Otitis Media",
    "conjunctivitis": "Conjunctivitis",
    "pink eye": "Conjunctivitis",
    # ── Cardiac ───────────────────────────────────────────────────────────
    "hypertension": "Hypertension",
    "hypertensive": "Hypertension",
    "bp high": "Hypertension",
    "high bp": "Hypertension",
    "high blood pressure": "Hypertension",
    "bp badhna": "Hypertension",
    "heart attack": "Myocardial Infarction",
    "mi": "Myocardial Infarction",
    "myocardial infarction": "Myocardial Infarction",
    "angina": "Angina",
    "arrhythmia": "Arrhythmia",
    "atrial fibrillation": "Atrial Fibrillation",
    "heart failure": "Heart Failure",
    # ── Metabolic ─────────────────────────────────────────────────────────
    "diabetes": "Diabetes Mellitus",
    "diabetic": "Diabetes Mellitus",
    "sugar": "Diabetes Mellitus",
    "sugar ki bimari": "Diabetes Mellitus",
    "madhumeh": "Diabetes Mellitus",
    "शुगर": "Diabetes Mellitus",
    "मधुमेह": "Diabetes Mellitus",
    "hypothyroid": "Hypothyroidism",
    "hypothyroidism": "Hypothyroidism",
    "hyperthyroid": "Hyperthyroidism",
    "hyperthyroidism": "Hyperthyroidism",
    "thyroid": "Thyroid Disorder",
    "anemia": "Anemia",
    "anaemia": "Anemia",
    "खून की कमी": "Anemia",
    "khoon ki kami": "Anemia",
    "gout": "Gout",
    "uric acid": "Gout",
    # ── GI ───────────────────────────────────────────────────────────────
    "gastritis": "Gastritis",
    "acute gastritis": "Acute Gastritis",
    "gastroenteritis": "Acute Gastroenteritis",
    "acute gastroenteritis": "Acute Gastroenteritis",
    "food poisoning": "Food Poisoning",
    "gerd": "GERD",
    "acid reflux": "GERD",
    "irritable bowel": "IBS",
    "ibs": "IBS",
    "appendicitis": "Appendicitis",
    "jaundice": "Jaundice",
    "cirrhosis": "Liver Cirrhosis",
    "liver failure": "Liver Failure",
    "peptic ulcer": "Peptic Ulcer",
    "gallstones": "Gallstones",
    "gall stones": "Gallstones",
    "kidney stones": "Kidney Stones",
    "renal stones": "Kidney Stones",
    "kidney failure": "Renal Failure",
    "renal failure": "Renal Failure",
    "uti": "UTI",
    "urinary tract infection": "UTI",
    # ── Neuro / Musculo ───────────────────────────────────────────────────
    "migraine": "Migraine",
    "stroke": "Stroke",
    "paralysis": "Paralysis",
    "lakwa": "Paralysis",
    "seizure": "Seizure",
    "fits": "Seizure",
    "mircchi": "Seizure",
    "epilepsy": "Epilepsy",
    "vertigo": "Vertigo",
    "neuropathy": "Neuropathy",
    "arthritis": "Arthritis",
    "rheumatoid": "Rheumatoid Arthritis",
    "rheumatoid arthritis": "Rheumatoid Arthritis",
    "osteoarthritis": "Osteoarthritis",
    "spondylitis": "Spondylitis",
    "slip disc": "Disc Prolapse",
    "slipped disc": "Disc Prolapse",
    "disc prolapse": "Disc Prolapse",
    "frozen shoulder": "Frozen Shoulder",
    "sciatica": "Sciatica",
    "fracture": "Fracture",
    # ── Eye / Skin / Mental ───────────────────────────────────────────────
    "cataract": "Cataract",
    "motiyabind": "Cataract",
    "मोतियाबिंद": "Cataract",
    "glaucoma": "Glaucoma",
    "psoriasis": "Psoriasis",
    "eczema": "Eczema",
    "vitiligo": "Vitiligo",
    "safed daag": "Vitiligo",
    "anxiety": "Anxiety Disorder",
    "depression": "Depression",
    "insomnia disorder": "Insomnia",
    "pcos": "PCOS",
    "polycystic": "PCOS",
    # ── Dental ───────────────────────────────────────────────────────────
    "dental caries": "Dental Caries",
    "periodontitis": "Periodontitis",
    "gingivitis": "Gingivitis",
}

_DURATION_RE = re.compile(
    r'\b(\d+(?:\.\d+)?\s*(?:din|day|days|week|weeks|month|months|hour|hours|hr|hrs))\s*'
    r'(?:se|since|for|pehle|ago)?\b'
    r'|(?:since|for)\s+(yesterday|morning|evening|last\s+\w+|\d+\s+\w+)',
    re.IGNORECASE,
)

_FOLLOWUP_PATTERNS = [
    re.compile(r'follow[\s-]?up\s+(?:(?:in|after|within)\s+)?([^\.\n;]+)', re.IGNORECASE),
    re.compile(r'come\s+back\s+(?:(?:after|in)\s+)?([^\.\n;,]+)', re.IGNORECASE),
    re.compile(r'review\s+(?:(?:in|after)\s+)?([^\.\n;,]+)', re.IGNORECASE),
    re.compile(r'milne\s+aana\s+(?:in\s+)?([^\.\n;]+)', re.IGNORECASE),
    re.compile(r'(?:wapas|aana|milna)\s+(?:teen|do|ek|char|paanch)\s+din\s+(?:baad|mein)', re.IGNORECASE),
    re.compile(r'\b(\d+)\s*(?:din|day|days)\s*(?:baad|mein|ke\s+baad)\s*(?:aana|wapas|milna|review)', re.IGNORECASE),
]

_DIAGNOSIS_LABEL_RE = re.compile(
    r'(?:diagnosis|impression|assessment|dx|impression|provisional\s+diagnosis)[\s:]+([^.\n;]+)',
    re.IGNORECASE,
)

_KNOWN_MEDICATIONS = {
    # ── Analgesics / Antipyretics ─────────────────────────────────────────
    "painkiller", "painkillers", "pain killer", "pain killers",
    "paracetamol", "dolo", "crocin", "calpol", "fevago",
    "aspirin", "ibuprofen", "naproxen", "diclofenac", "aceclofenac",
    "ketorolac", "tramadol", "codeine", "morphine",
    # ── Antibiotics ───────────────────────────────────────────────────────
    "antibiotic", "antibiotics",
    "amoxicillin", "amoxyclav", "amoxiclav", "augmentin",
    "azithromycin", "azee", "azithral", "zithromax",
    "clarithromycin", "erythromycin",
    "ciprofloxacin", "norflox", "norfloxacin", "ofloxacin", "levofloxacin",
    "doxycycline", "tetracycline",
    "metronidazole", "flagyl", "tinidazole", "secnidazole",
    "cefixime", "cefpodoxime", "ceftriaxone", "cephalexin", "cefuroxime",
    "cotrimoxazole", "trimethoprim",
    "rifampicin", "ethambutol", "isoniazid", "pyrazinamide",
    "vancomycin", "meropenem", "piperacillin",
    "acyclovir", "oseltamivir", "tamiflu",
    "albendazole", "ivermectin", "hydroxychloroquine", "artemether",
    # ── Antihistamines ────────────────────────────────────────────────────
    "cetirizine", "levocetirizine", "fexofenadine", "loratadine",
    "chlorpheniramine", "diphenhydramine",
    "montelukast",
    # ── Diabetes ─────────────────────────────────────────────────────────
    "insulin", "metformin", "glycomet", "glimepiride", "glipizide",
    "sitagliptin", "empagliflozin", "dapagliflozin", "vildagliptin",
    # ── Cardiac / BP ──────────────────────────────────────────────────────
    "amlodipine", "atenolol", "telmisartan", "ramipril", "enalapril",
    "losartan", "lisinopril", "nifedipine", "verapamil", "diltiazem",
    "metoprolol", "carvedilol", "bisoprolol",
    "warfarin", "heparin", "enoxaparin", "clopidogrel", "aspirin",
    "atorvastatin", "rosuvastatin", "simvastatin",
    # ── GI ───────────────────────────────────────────────────────────────
    "omeprazole", "pantoprazole", "rabeprazole", "esomeprazole",
    "pantop", "pan d", "gelusil", "digene", "ranitidine", "sucralfate",
    "domperidone", "ondansetron", "metoclopramide",
    "lactulose", "bisacodyl", "loperamide", "imodium",
    "oral rehydration", "ors",
    # ── Respiratory ───────────────────────────────────────────────────────
    "salbutamol", "budesonide", "tiotropium", "ipratropium",
    "prednisolone", "prednisone", "dexamethasone", "betamethasone",
    "methylprednisolone", "hydrocortisone",
    # ── Thyroid / Hormones ────────────────────────────────────────────────
    "levothyroxine", "thyroxine",
    # ── Vitamins / Supplements ────────────────────────────────────────────
    "pcm", "antacid", "antacids",
    "calcium", "vitamin", "zinc", "iron", "ferrous",
    "folic acid", "vitamin d", "vitamin c", "vitamin b12",
    "multivitamin", "b complex", "biotin",
    # ── Psych ────────────────────────────────────────────────────────────
    "diazepam", "alprazolam", "clonazepam",
    "sertraline", "fluoxetine", "escitalopram", "amitriptyline",
    # ── Skin / Topical ────────────────────────────────────────────────────
    "betadine", "mupirocin", "clotrimazole", "fluconazole",
    "tacrolimus", "cyclosporine",
    # ── Gout ──────────────────────────────────────────────────────────────
    "colchicine", "allopurinol",
    # ── Urology ───────────────────────────────────────────────────────────
    "tamsulosin", "finasteride", "dutasteride",
    # ── Eye drops ─────────────────────────────────────────────────────────
    "timolol", "latanoprost", "pilocarpine",
    "tobramycin", "gentamicin",
}

_UNCERTAINTY_WORDS = re.compile(
    r'\b(maybe|possible|possibly|probably|might|suspected?|shayad|ho\s+sakta)\b',
    re.IGNORECASE,
)

_NEGATION_RE = re.compile(
    r'\b(no|not|denies?|denied|without|never|nor|nahi|nahin|absent)\b',
    re.IGNORECASE,
)
_CLAUSE_RESET_RE = re.compile(
    r'\b(but|however|and|also|though|although|yet|still|except)\b|,',
    re.IGNORECASE,
)
_CORRECTION_RE = re.compile(
    r'(?:no\s+make\s+it|actually|wait)[,\s]+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))',
    re.IGNORECASE,
)

# Fuzzy matching: common non-medical words to skip
_FUZZY_SKIP_WORDS = {
    "patient", "doctor", "please", "since", "start", "about", "after",
    "their", "there", "where", "which", "while", "would", "could", "should",
    "today", "yesterday", "morning", "evening", "taking", "having", "feeling",
    "going", "coming", "getting", "doing", "being", "saying", "years", "months",
    "weeks", "report", "present", "noted", "given", "complain", "history",
    "review", "follow", "clinic", "hospital", "discharge", "admission",
    "treatment", "advice", "tablet", "capsule", "syrup", "injection",
}


def _is_negated(text: str, match_start: int, match_end: int = -1, window: int = 40) -> bool:
    preceding = text[max(0, match_start - window): match_start]
    neg_match = None
    for m in _NEGATION_RE.finditer(preceding):
        neg_match = m
    if neg_match is not None:
        reset = _CLAUSE_RESET_RE.search(preceding, neg_match.end())
        if reset is None:
            return True

    if match_end < 0:
        match_end = match_start
    following = text[match_end: min(len(text), match_end + 25)]
    post_neg = _POST_NEGATION_RE.search(following)
    if post_neg:
        boundary = _CLAUSE_RESET_RE.search(following)
        if boundary is None or boundary.start() > post_neg.start():
            return True

    return False


# ──────────────────────────────────────────────────────────────────────────────
# Fuzzy matching helpers (rapidfuzz optional)
# ──────────────────────────────────────────────────────────────────────────────

def _fuzzy_extract_symptoms(sent_text: str, result: dict) -> None:
    """Fuzzy-match words ≥5 chars against symptom map to catch ASR errors."""
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        return

    lower = sent_text.lower()
    words = re.findall(r'\b[a-zA-Z]{5,}\b', lower)
    if not words:
        return

    symptom_keys = list(_SYMPTOM_MAP.keys())

    for word in words:
        if word in _SYMPTOM_MAP or word in _FUZZY_SKIP_WORDS:
            continue
        match = process.extractOne(word, symptom_keys, scorer=fuzz.ratio)
        if match and match[1] >= 88:
            canonical = _SYMPTOM_MAP[match[0]]
            m = re.search(rf'\b{re.escape(word)}\b', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                if canonical not in result["symptoms"]:
                    result["symptoms"].append(canonical)
                    result["contexts"].setdefault(canonical, sent_text)


def _fuzzy_extract_medications(sent_text: str, result: dict) -> None:
    """Fuzzy-match words ≥6 chars against known medication list."""
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        return

    lower = sent_text.lower()
    words = re.findall(r'\b[a-zA-Z]{6,}\b', lower)
    if not words:
        return

    med_list = list(_KNOWN_MEDICATIONS)

    for word in words:
        if word in _KNOWN_MEDICATIONS or word in _FUZZY_SKIP_WORDS:
            continue
        match = process.extractOne(word, med_list, scorer=fuzz.ratio)
        if match and match[1] >= 90:  # higher threshold for meds
            matched_med = match[0]
            # Check not already present — also fuzzy-check existing names
            already_present = any(
                matched_med in m["name"]
                or m["name"] in matched_med
                or fuzz.ratio(matched_med, m["name"]) >= 85
                for m in result["medications"]
            )
            if not already_present:
                result["medications"].append({
                    "name": matched_med,
                    "dosage": "",
                    "frequency": "",
                })
                result["contexts"].setdefault(matched_med, sent_text)


def _fuzzy_extract_diagnoses(sent_text: str, result: dict) -> None:
    """Fuzzy-match diagnosis keywords for ASR errors."""
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        return

    lower = sent_text.lower()
    words = re.findall(r'\b[a-zA-Z]{6,}\b', lower)
    if not words:
        return

    dx_keys = [k for k in _DIAGNOSIS_MAP.keys() if len(k) >= 6 and ' ' not in k]

    for word in words:
        if word in _DIAGNOSIS_MAP or word in _FUZZY_SKIP_WORDS:
            continue
        match = process.extractOne(word, dx_keys, scorer=fuzz.ratio)
        if match and match[1] >= 88:
            canonical = _DIAGNOSIS_MAP[match[0]]
            m = re.search(rf'\b{re.escape(word)}\b', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                if canonical not in result["diagnoses"]:
                    result["diagnoses"].append(canonical)
                    result["contexts"].setdefault(f"dx:{canonical}", sent_text)


# ──────────────────────────────────────────────────────────────────────────────
# Main extractor service
# ──────────────────────────────────────────────────────────────────────────────

class ClinicalExtractorService:

    def extract(self, transcript: str) -> dict:
        result: dict = {
            "symptoms": [],
            "medications": [],
            "vitals": [],
            "allergies": [],
            "investigations": [],
            "diagnoses": [],
            "follow_up": [],
            "contexts": {},
        }

        if not transcript or not transcript.strip():
            return result

        # Pre-process: transliterate Devanagari to Roman if present
        processed = _maybe_transliterate(transcript)

        doc = nlp(processed)

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            # Skip uncertain sentences
            if _UNCERTAINTY_WORDS.search(sent_text):
                continue

            # Layer 1: exact keyword extraction
            self._extract_symptoms(sent_text, result)
            self._extract_vitals(sent_text, result)
            self._extract_allergies(sent_text, result)
            self._extract_investigations(sent_text, result)
            self._extract_medications(sent_text, result)
            self._extract_diagnoses(sent_text, result)
            self._extract_followup(sent_text, result)

            # Layer 2: fuzzy extraction as fallback for ASR spelling errors
            _fuzzy_extract_symptoms(sent_text, result)
            _fuzzy_extract_medications(sent_text, result)
            _fuzzy_extract_diagnoses(sent_text, result)

        # Also run on the original (non-transliterated) transcript for Devanagari maps
        if processed != transcript:
            orig_doc = nlp(transcript)
            for sent in orig_doc.sents:
                sent_text = sent.text.strip()
                if sent_text:
                    self._extract_symptoms(sent_text, result)
                    self._extract_diagnoses(sent_text, result)

        self._enrich_symptom_durations(processed, result)

        return result

    # ──────────────────────────────────────────────────────────────────────
    # Private extraction helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_symptoms(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        for keyword, canonical in _SYMPTOM_MAP.items():
            m = re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                original_word = m.group(0).strip()
                if original_word != canonical and original_word not in canonical:
                    display_sym = f"{canonical} ('{original_word}')"
                else:
                    display_sym = canonical
                    
                if display_sym not in result["symptoms"]:
                    # Remove plain canonical if it was added, to upgrade it
                    if canonical in result["symptoms"]:
                        result["symptoms"].remove(canonical)
                    result["symptoms"].append(display_sym)
                    result["contexts"][display_sym] = sent_text

    @staticmethod
    def _extract_vitals(sent_text: str, result: dict) -> None:
        # Blood Pressure — "150/90" or "150 over 90" or "BP 150/90"
        bp_match = re.search(r'\b(\d{2,3})\s*(?:/|over)\s*(\d{2,3})\b', sent_text, re.IGNORECASE)
        if bp_match:
            bp_value = f"{bp_match.group(1)}/{bp_match.group(2)}"
            vital = f"BP {bp_value}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Temperature — "38.5C", "38.5 degree C", "38.5 degree Celsius", "101 F"
        temp_match = re.search(
            r'\b(\d{2,3}(?:\.\d{1,2})?)\s*(?:degree\s*)?(?:°\s*)?(F|C|fahrenheit|celsius)\b',
            sent_text, re.IGNORECASE,
        )
        if temp_match:
            unit = temp_match.group(2)[0].upper()
            vital = f"Temp {temp_match.group(1)} {unit}"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # SpO2
        spo2_match = re.search(
            r'\b(?:spo2|o2\s*sat(?:uration)?|oxygen\s+sat(?:uration)?|oxygen)\s*(?:is\s*)?(\d{2,3})\s*%?',
            sent_text, re.IGNORECASE,
        )
        if spo2_match:
            vital = f"SpO2 {spo2_match.group(1)}%"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Pulse / Heart rate
        hr_match = re.search(
            r'\b(?:pulse|hr|heart\s+rate|nadi)\s*(?:is\s*)?(\d{2,3})\s*(?:bpm|/min)?\b',
            sent_text, re.IGNORECASE,
        )
        if hr_match:
            vital = f"Pulse {hr_match.group(1)} bpm"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Respiratory rate
        rr_match = re.search(
            r'\b(?:rr|respiratory\s+rate)\s*(?:is\s*)?(\d{1,2})\b',
            sent_text, re.IGNORECASE,
        )
        if rr_match:
            vital = f"RR {rr_match.group(1)}/min"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Weight
        wt_match = re.search(
            r'\b(?:weight|wt|wajan|vajan)\s*(?:is\s*)?(\d{2,3}(?:\.\d)?)\s*kg\b',
            sent_text, re.IGNORECASE,
        )
        if wt_match:
            vital = f"Weight {wt_match.group(1)} kg"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

        # Blood glucose
        glucose_match = re.search(
            r'\b(?:sugar|rbs|fbs|ppbs|fasting\s+sugar|blood\s+sugar|blood\s+glucose|glucose)\s*(?:is\s*)?(\d{2,3})\s*(?:mg/dl|mg)?\b',
            sent_text, re.IGNORECASE,
        )
        if glucose_match:
            vital = f"Blood Glucose {glucose_match.group(1)} mg/dL"
            if vital not in result["vitals"]:
                result["vitals"].append(vital)
                result["contexts"][vital] = sent_text

    @staticmethod
    def _extract_allergies(sent_text: str, result: dict) -> None:
        for pattern in _ALLERGY_PATTERNS:
            match = re.search(pattern, sent_text, re.IGNORECASE)
            if match:
                allergen = match.group(1).lower().strip()
                if allergen and allergen not in result["allergies"]:
                    result["allergies"].append(allergen)
                    result["contexts"][allergen] = sent_text

    @staticmethod
    def _extract_investigations(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()
        for keyword, canonical in _INVESTIGATION_MAP.items():
            if re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower):
                if canonical not in result["investigations"]:
                    result["investigations"].append(canonical)
                    result["contexts"][canonical] = sent_text

    @staticmethod
    def _extract_medications(sent_text: str, result: dict) -> None:
        freq_pattern = re.compile(
            r'\b(BD|OD|TDS|QID|SOS|PRN|STAT|twice\s+daily|once\s+(?:a\s+)?day|'
            r'thrice\s+daily|three\s+times\s+(?:a\s+)?day|'
            r'din\s+mein\s+do\s+baar|din\s+mein\s+teen\s+baar)\b',
            re.IGNORECASE,
        )
        med_matches = re.finditer(
            r'\b([A-Za-z]{3,})\s+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g)\b)',
            sent_text, re.IGNORECASE,
        )

        for match in med_matches:
            name = match.group(1).lower()
            dosage = match.group(2).strip()

            skip_words = {
                "the", "and", "for", "with", "this", "that", "from",
                "has", "was", "are", "his", "her", "she", "him",
                "not", "also", "but", "start", "give", "take",
                "patient", "doctor", "daily", "twice", "once",
            }
            if name in skip_words:
                continue

            freq = ""
            freq_match = freq_pattern.search(sent_text, match.end())
            if freq_match:
                freq = freq_match.group(1).strip()

            existing = [m for m in result["medications"] if m["name"] == name]
            if existing:
                if not existing[0]["dosage"]:
                    existing[0]["dosage"] = dosage
                if not existing[0]["frequency"] and freq:
                    existing[0]["frequency"] = freq
            else:
                result["medications"].append({"name": name, "dosage": dosage, "frequency": freq})
                result["contexts"][name] = sent_text

        lower_sent = sent_text.lower()
        for med_name in _KNOWN_MEDICATIONS:
            pattern = rf'\b{re.escape(med_name)}\b'
            m = re.search(pattern, lower_sent)
            if m:
                already_matched = any(
                    existing["name"] == med_name
                    or med_name in existing["name"]
                    or existing["name"] in med_name
                    for existing in result["medications"]
                )
                if not already_matched:
                    freq = ""
                    freq_match = freq_pattern.search(lower_sent, m.end())
                    if freq_match:
                        freq = freq_match.group(1).strip()
                    result["medications"].append({"name": med_name, "dosage": "", "frequency": freq})
                    result["contexts"][med_name] = sent_text

        correction = _CORRECTION_RE.search(sent_text)
        if correction and result["medications"]:
            new_dosage = correction.group(1).strip()
            freq_match = freq_pattern.search(sent_text, correction.end())
            last_med = result["medications"][-1]
            last_med["dosage"] = new_dosage
            if freq_match:
                last_med["frequency"] = freq_match.group(1).strip()

    @staticmethod
    def _extract_diagnoses(sent_text: str, result: dict) -> None:
        lower = sent_text.lower()

        for keyword, canonical in _DIAGNOSIS_MAP.items():
            m = re.search(rf'(?:^|\b){re.escape(keyword)}(?:\b|$)', lower)
            if m and not _is_negated(lower, m.start(), m.end()):
                if canonical not in result["diagnoses"]:
                    result["diagnoses"].append(canonical)
                    result["contexts"][f"dx:{canonical}"] = sent_text

        label_match = _DIAGNOSIS_LABEL_RE.search(sent_text)
        if label_match:
            raw_full = label_match.group(1).strip().rstrip('.')
            # Split comma/semicolon-separated diagnoses ("URTI, pharyngitis likely")
            for raw_part in re.split(r'[,;]', raw_full):
                raw = raw_part.strip().rstrip('.')
                if not raw or len(raw) < 2:
                    continue
                # Strip trailing qualifiers ("likely", "possible", etc.)
                raw = re.sub(r'\s+(?:likely|possible|probable|suspected)$', '', raw, flags=re.IGNORECASE).strip()
                normalised = _DIAGNOSIS_MAP.get(raw.lower())
                canonical = normalised if normalised else raw.title()
                if canonical and canonical not in result["diagnoses"]:
                    result["diagnoses"].append(canonical)
                    result["contexts"][f"dx:{canonical}"] = sent_text

    @staticmethod
    def _extract_followup(sent_text: str, result: dict) -> None:
        for pattern in _FOLLOWUP_PATTERNS:
            m = pattern.search(sent_text)
            if m:
                text = (m.group(1) if m.lastindex and m.group(1) else m.group(0)).strip(" .")
                if text and text not in result["follow_up"]:
                    result["follow_up"].append(text)
                break

    @staticmethod
    def _enrich_symptom_durations(transcript: str, result: dict) -> None:
        doc = nlp(transcript)
        enriched = []
        for symptom in result["symptoms"]:
            plain = symptom.split(" (")[0]
            duration_found = None
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                for kw, canonical in _SYMPTOM_MAP.items():
                    if canonical == plain and re.search(rf'\b{re.escape(kw)}\b', sent_lower):
                        dm = _DURATION_RE.search(sent_lower)
                        if dm:
                            duration_found = (dm.group(1) or dm.group(2) or "").strip()
                        break
            enriched.append(f"{plain} ({duration_found})" if duration_found else plain)
        result["symptoms"] = enriched

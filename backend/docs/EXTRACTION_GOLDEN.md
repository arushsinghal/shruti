# Lipi Golden Test Set (20) — transcripts + expected JSON

Companion to `EXTRACTION_AUDIT.md`. Field-level ground truth = what the eval
harness consumes. `negation_checks` = explicit regression assertions.
G03 and G10 also shown in full per-fact rich schema as contract exemplars.

Languages: G01–G07 Hindi-heavy · G08–G14 Hinglish · G15–G20 English-heavy Indian OPD.

---

## Hindi-heavy

### G01
> "Do din se tej bukhar hai aur sar mein dard ho raha hai. Ulti nahi hui hai. Paracetamol 650 din mein teen baar de raha hun. Teen din baad dikhana."
```json
{
  "symptoms": ["fever", "headache"],
  "negated_findings": ["vomiting"],
  "medications": [{"name": "paracetamol", "dosage": "650mg", "frequency": "TDS", "status": "new"}],
  "vitals": [], "allergies": [], "investigations": [],
  "diagnoses": [],
  "follow_up": ["after 3 days"],
  "negation_checks": {"vomiting": "negated"}
}
```

### G02
> "Mareez ko khansi hai ek hafte se, balgam ke saath. Saans lene mein dikkat ho rahi hai. Chest pain nahi hai. X-ray chest karwa lo."
```json
{
  "symptoms": ["cough", "breathlessness"],
  "negated_findings": ["chest pain"],
  "medications": [],
  "vitals": [], "allergies": [],
  "investigations": ["chest x-ray"],
  "diagnoses": [],
  "follow_up": [],
  "red_flags": ["breathlessness"],
  "negation_checks": {"chest pain": "negated"}
}
```

### G03  (rich-schema exemplar)
> "Pet mein dard hai do din se, aur dast lag gaye hain. Bukhar nahi hai. ORS aur Ofloxacin 200 do baar lena. Agar dast continue rahe toh stool test karana."
```json
{
  "facts": [
    {"original_text": "Pet mein dard", "normalized_value": "abdominal pain", "category": "symptom", "language": "hindi", "source_sentence": "Pet mein dard hai do din se, aur dast lag gaye hain.", "evidence_span": [0, 13], "confidence": 0.95, "negated": false, "temporality": "current", "section_hint": "S", "safety_flags": []},
    {"original_text": "dast", "normalized_value": "diarrhea", "category": "symptom", "language": "hindi", "source_sentence": "Pet mein dard hai do din se, aur dast lag gaye hain.", "evidence_span": [33, 37], "confidence": 0.93, "negated": false, "temporality": "current", "section_hint": "S", "safety_flags": []},
    {"original_text": "Bukhar", "normalized_value": "fever", "category": "symptom", "language": "hindi", "source_sentence": "Bukhar nahi hai.", "evidence_span": [0, 6], "confidence": 0.97, "negated": true, "temporality": "current", "section_hint": "S", "safety_flags": []},
    {"original_text": "Ofloxacin 200", "normalized_value": "ofloxacin", "category": "medication", "language": "english", "source_sentence": "ORS aur Ofloxacin 200 do baar lena.", "evidence_span": [8, 21], "confidence": 0.9, "negated": false, "temporality": "current", "section_hint": "P", "safety_flags": []},
    {"original_text": "agar dast continue rahe toh stool test karana", "normalized_value": "stool test if diarrhea continues", "category": "follow_up", "language": "hinglish", "source_sentence": "Agar dast continue rahe toh stool test karana.", "evidence_span": [0, 45], "confidence": 0.85, "negated": false, "temporality": "conditional", "section_hint": "P", "safety_flags": []}
  ],
  "views": {
    "symptoms": ["abdominal pain", "diarrhea"],
    "negated_findings": ["fever"],
    "medications": [{"name": "ofloxacin", "dosage": "200mg", "frequency": "BD", "status": "new"}, {"name": "ors", "status": "new"}],
    "investigations": [],
    "diagnoses": [],
    "follow_up": ["stool test if diarrhea continues (conditional)"]
  },
  "negation_checks": {"fever": "negated"}
}
```

### G04
> "Gale mein kharash hai aur nigalne mein dard. Halka bukhar bhi hai. Azithromycin 500 ek baar paanch din. Aaram karo."
```json
{
  "symptoms": ["sore throat", "painful swallowing", "fever"],
  "negated_findings": [],
  "medications": [{"name": "azithromycin", "dosage": "500mg", "frequency": "OD", "duration": "5 days", "status": "new"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "negation_checks": {}
}
```

### G05  (explicit diagnosis present)
> "Jodon mein dard aur sujan hai. Subah akadan rehti hai. Mujhe lagta hai yeh rheumatoid arthritis ka case hai. RA factor test karwao."
```json
{
  "symptoms": ["joint pain", "joint swelling", "morning stiffness"],
  "negated_findings": [],
  "medications": [],
  "investigations": ["ra factor"],
  "diagnoses": ["rheumatoid arthritis"],
  "follow_up": [],
  "negation_checks": {},
  "diagnosis_check": "explicit — clinician said 'lagta hai yeh rheumatoid arthritis ka case hai'"
}
```

### G06
> "Chakkar aa rahe hain aur kamzori hai. BP 100 by 70 hai. Pehle bhi BP low rehta tha. Iron ki goli aur khana theek se khao."
```json
{
  "symptoms": ["dizziness", "weakness"],
  "negated_findings": [],
  "vitals": ["BP 100/70"],
  "medications": [{"name": "iron", "status": "new"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "temporality_checks": {"BP low (pehle)": "historical — not an active finding"}
}
```

### G07
> "Peshab mein jalan ho rahi hai aur baar baar peshab aata hai. Bukhar bhi halka hai. Urine routine karwao. Nitrofurantoin 100 do baar saat din."
```json
{
  "symptoms": ["burning micturition", "increased urinary frequency", "fever"],
  "negated_findings": [],
  "medications": [{"name": "nitrofurantoin", "dosage": "100mg", "frequency": "BD", "duration": "7 days", "status": "new"}],
  "investigations": ["urine routine"],
  "diagnoses": [], "follow_up": [],
  "negation_checks": {}
}
```

---

## Hinglish / code-mixed

### G08
> "Patient ko 3 din se fever hai, body ache bhi hai. Throat normal hai, no congestion. Dolo 650 SOS le sakte hain. Hydration maintain karo."
```json
{
  "symptoms": ["fever", "body ache"],
  "negated_findings": ["congestion"],
  "medications": [{"name": "dolo", "dosage": "650mg", "frequency": "SOS", "status": "advised"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "negation_checks": {"congestion": "negated"}
}
```

### G09  (RT1, RT2, RT6 — the core failure cases)
> "Mera gala kharab hai, naak band hai aur pairon mein dard hai. Aur kuch nahi."
```json
{
  "symptoms": ["sore throat", "blocked nose", "leg pain"],
  "negated_findings": [],
  "medications": [], "vitals": [], "investigations": [],
  "diagnoses": [],
  "follow_up": [],
  "negation_checks": {},
  "must_not_contain": {"diagnoses": ["gallbladder", "gallstones", "appendicitis"], "symptoms": ["ear pain"]}
}
```

### G10  (rich-schema exemplar)
> "BP high chal raha hai, 150 over 95. Sir bhari rehta hai. Amlodipine 5 once daily start kar rahe hain. Salt kam karo. 2 hafte baad follow up."
```json
{
  "facts": [
    {"original_text": "150 over 95", "normalized_value": "BP 150/95", "category": "vital", "language": "english", "source_sentence": "BP high chal raha hai, 150 over 95.", "evidence_span": [23, 34], "confidence": 0.98, "negated": false, "temporality": "current", "section_hint": "O", "safety_flags": ["value_out_of_range"]},
    {"original_text": "Sir bhari", "normalized_value": "head heaviness", "category": "symptom", "language": "hinglish", "source_sentence": "Sir bhari rehta hai.", "evidence_span": [0, 9], "confidence": 0.8, "negated": false, "temporality": "current", "section_hint": "S", "safety_flags": []},
    {"original_text": "Amlodipine 5", "normalized_value": "amlodipine", "category": "medication", "language": "english", "source_sentence": "Amlodipine 5 once daily start kar rahe hain.", "evidence_span": [0, 12], "confidence": 0.95, "negated": false, "temporality": "current", "section_hint": "P", "safety_flags": []},
    {"original_text": "2 hafte baad follow up", "normalized_value": "after 2 weeks", "category": "follow_up", "language": "hinglish", "source_sentence": "2 hafte baad follow up.", "evidence_span": [0, 22], "confidence": 0.9, "negated": false, "temporality": "current", "section_hint": "P", "safety_flags": []}
  ],
  "views": {
    "symptoms": ["head heaviness"],
    "vitals": ["BP 150/95"],
    "medications": [{"name": "amlodipine", "dosage": "5mg", "frequency": "OD", "status": "new"}],
    "diagnoses": [],
    "follow_up": ["after 2 weeks"]
  },
  "negation_checks": {}
}
```

### G11  (RT4)
> "Loose motions ho rahe hain subah se. Vomiting nahi hai. Pet mein halka dard. ORS lo, Zinc tablet do."
```json
{
  "symptoms": ["diarrhea", "abdominal pain"],
  "negated_findings": ["vomiting"],
  "medications": [{"name": "ors", "status": "new"}, {"name": "zinc", "status": "new"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "negation_checks": {"vomiting": "negated"}
}
```

### G12  (RT8 — conditional follow-up)
> "Viral fever lag raha hai. Paracetamol le rahe ho continue karo. Agar fever continue kare toh CBC kara lena."
```json
{
  "symptoms": [],
  "negated_findings": [],
  "medications": [{"name": "paracetamol", "status": "current"}],
  "investigations": [],
  "diagnoses": ["viral fever"],
  "follow_up": ["CBC if fever continues (conditional)"],
  "negation_checks": {},
  "conditional_check": "CBC must NOT appear as an active investigation",
  "diagnosis_check": "explicit — 'viral fever lag raha hai'"
}
```

### G13
> "Skin pe rash aur khujli hai do din se. Penicillin se allergy hai, woh mat dena. Cetirizine 10 raat ko."
```json
{
  "symptoms": ["skin rash", "itching"],
  "negated_findings": [],
  "allergies": ["penicillin"],
  "medications": [{"name": "cetirizine", "dosage": "10mg", "frequency": "HS", "status": "new"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "safety_checks": {"penicillin": "allergy, not a medication"}
}
```

### G14  (RT9 — medication stop)
> "Sugar control mein hai ab. Metformin band kar do, Glimepiride 1 morning start karo. HbA1c 3 mahine baad."
```json
{
  "symptoms": [],
  "negated_findings": [],
  "medications": [
    {"name": "metformin", "status": "stopped"},
    {"name": "glimepiride", "dosage": "1mg", "frequency": "morning", "status": "new"}
  ],
  "investigations": ["hba1c"],
  "diagnoses": [],
  "follow_up": ["after 3 months"],
  "status_checks": {"metformin": "stopped", "glimepiride": "new"}
}
```

---

## English-heavy Indian OPD

### G15  (RT — allergy not a med)
> "Patient complains of fever and dry cough for two days. Known allergy to sulfa drugs. Prescribed azithromycin 500 once daily for three days. Review if no improvement."
```json
{
  "symptoms": ["fever", "dry cough"],
  "negated_findings": [],
  "allergies": ["sulfa drugs"],
  "medications": [{"name": "azithromycin", "dosage": "500mg", "frequency": "OD", "duration": "3 days", "status": "new"}],
  "diagnoses": [], "investigations": [],
  "follow_up": ["review if no improvement (conditional)"],
  "safety_checks": {"sulfa drugs": "allergy, not a medication"}
}
```

### G16  (RT3)
> "Complains of epigastric burning after meals. No chest pain, no breathlessness. Start pantoprazole 40 before breakfast. Avoid spicy food."
```json
{
  "symptoms": ["epigastric burning"],
  "negated_findings": ["chest pain", "breathlessness"],
  "medications": [{"name": "pantoprazole", "dosage": "40mg", "frequency": "before breakfast", "status": "new"}],
  "diagnoses": [], "investigations": [], "follow_up": [],
  "negation_checks": {"chest pain": "negated", "breathlessness": "negated"}
}
```

### G17
> "Three-day history of high-grade fever with chills. Temp 102 F, pulse 98. Advise CBC, dengue NS1, and malaria smear. Paracetamol 650 QID. Follow up after 2 days with reports."
```json
{
  "symptoms": ["fever", "chills"],
  "negated_findings": [],
  "vitals": ["Temp 102 F", "Pulse 98 bpm"],
  "medications": [{"name": "paracetamol", "dosage": "650mg", "frequency": "QID", "status": "new"}],
  "investigations": ["cbc", "dengue ns1", "malaria smear"],
  "diagnoses": [],
  "follow_up": ["after 2 days"],
  "negation_checks": {}
}
```

### G18  (RT10 — fasting sugar value)
> "Diabetic on follow-up. Fasting sugar 160, post-prandial 240. BP 130 over 85. Increase metformin to 1000 twice daily. Repeat fasting sugar in 2 weeks."
```json
{
  "symptoms": [],
  "negated_findings": [],
  "vitals": ["BP 130/85"],
  "labs": ["fasting sugar 160", "post-prandial 240"],
  "medications": [{"name": "metformin", "dosage": "1000mg", "frequency": "BD", "status": "current"}],
  "investigations": ["fasting sugar"],
  "diagnoses": [],
  "follow_up": ["after 2 weeks"],
  "value_checks": {"fasting sugar": "160 preserved exactly", "post-prandial": "240 preserved exactly"}
}
```

### G19
> "Known hypertensive presents with occipital headache and giddiness. BP 170 over 100. No visual disturbance, no vomiting. Add telmisartan 40 once daily. Urgent follow up tomorrow."
```json
{
  "symptoms": ["headache", "giddiness"],
  "negated_findings": ["visual disturbance", "vomiting"],
  "vitals": ["BP 170/100"],
  "medications": [{"name": "telmisartan", "dosage": "40mg", "frequency": "OD", "status": "new"}],
  "diagnoses": [],
  "investigations": [],
  "follow_up": ["tomorrow"],
  "red_flags": ["BP 170/100"],
  "negation_checks": {"visual disturbance": "negated", "vomiting": "negated"}
}
```

### G20  (RT5, RT6 — no diagnosis inference)
> "Patient reports sore throat, mild fever, and runny nose for two days. Throat mildly congested on exam. Symptomatic treatment with paracetamol and steam inhalation. Review in 3 days if not better."
```json
{
  "symptoms": ["sore throat", "fever", "runny nose"],
  "negated_findings": [],
  "medications": [{"name": "paracetamol", "status": "new"}],
  "diagnoses": [],
  "investigations": [],
  "follow_up": ["review in 3 days if not better (conditional)"],
  "must_not_contain": {"diagnoses": ["URTI", "viral URTI", "pharyngitis", "appendicitis"]},
  "diagnosis_check": "no explicit diagnosis stated — diagnoses MUST be empty"
}
```

---

## Notes for the harness
- `negated_findings` must NOT appear in `symptoms`.
- `must_not_contain` blocks are hard assertions (RT1, RT5, RT6).
- `diagnosis_check` cases distinguish explicit (G05, G12) from absent (G09, G20).
- `labs` is a real field (G18) — fix the phantom-field issue (R9) so labs/advice/red_flags are produced, not just scored.

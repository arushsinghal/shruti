-- ============================================================
-- Lipi Demo Data Seed — run once in Supabase SQL Editor
-- Idempotent: uses ON CONFLICT DO NOTHING
-- ============================================================

DO $$
DECLARE
    demo_uid TEXT;
    p1 TEXT := 'pat-demo-ramesh-001';
    p2 TEXT := 'pat-demo-priya-001';
    p3 TEXT := 'pat-demo-suresh-001';
BEGIN
    SELECT id::TEXT INTO demo_uid FROM users WHERE username = 'demo';
    IF demo_uid IS NULL THEN
        RAISE EXCEPTION 'Demo user not found — run the app first so it seeds the demo account';
    END IF;

    -- ── Patients ───────────────────────────────────────────────
    INSERT INTO patients (id, phone_number, name, age, sex, created_at, updated_at) VALUES
        (p1, '+919876500001', 'Ramesh Kumar',  '45', 'M', '2026-05-20T09:00:00', '2026-07-01T09:30:00'),
        (p2, '+919876500002', 'Priya Sharma',  '28', 'F', '2026-07-02T11:00:00', '2026-07-02T11:30:00'),
        (p3, '+919876500003', 'Suresh Patel',  '62', 'M', '2026-06-05T08:00:00', '2026-06-20T09:00:00')
    ON CONFLICT (phone_number) DO NOTHING;

    -- ══════════════════════════════════════════════════════════
    -- RAMESH KUMAR — 3 visits (HTN + T2DM follow-up arc)
    -- ══════════════════════════════════════════════════════════

    -- Visit 1 — Initial diagnosis
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-r1',
        'Ramesh Kumar', 'Dr. Demo', '2026-05-20T09:15:00',
        'complete', 'health', demo_uid, p1, '45', 'M',
        $TR$Doctor: Good morning Ramesh. What brings you in today?
Patient: Doctor, main bahut thaka hua rehta hoon. Sar mein dard bhi rehta hai kaafi din se.
Doctor: How long has this been going on?
Patient: Around 2-3 months. My neighbour said my face looks red, so I got worried.
Doctor: Let me check your blood pressure. [measures BP] 158/96. That is quite high. Any family history of BP or diabetes?
Patient: Haan, mere papa ko bhi BP tha. Aur sugar bhi hai unhe.
Doctor: Do you have any chest pain or breathlessness on climbing stairs?
Patient: Kabhi kabhi seedhi chadne mein thodi taklif hoti hai. Chest pain nahi.
Doctor: Your random blood sugar is 240, which is elevated. I am starting you on Amlodipine 5mg once daily for BP, and Metformin 500mg twice daily with meals for sugar. Get fasting sugar, HbA1c, lipid profile, kidney function test, and an ECG done this week. Come back in 2 weeks with reports.$TR$,
        $CF$[
{"id":"cf-r1-1","category":"vital","value":"BP 158/96 mmHg","status":"active","confidence":0.97,"source_text":"158/96","timestamp_order":1},
{"id":"cf-r1-2","category":"vital","value":"Random blood sugar 240 mg/dL","status":"active","confidence":0.97,"source_text":"random blood sugar is 240","timestamp_order":2},
{"id":"cf-r1-3","category":"symptom","value":"Fatigue (2-3 months)","status":"active","confidence":0.92,"source_text":"thaka hua rehta hoon","timestamp_order":3},
{"id":"cf-r1-4","category":"symptom","value":"Headache (chronic)","status":"active","confidence":0.92,"source_text":"sar mein dard bhi rehta hai","timestamp_order":4},
{"id":"cf-r1-5","category":"symptom","value":"Exertional dyspnoea (on climbing stairs)","status":"active","confidence":0.88,"source_text":"seedhi chadne mein thodi taklif","timestamp_order":5},
{"id":"cf-r1-6","category":"family_history","value":"Father: hypertension, type 2 diabetes","status":"active","confidence":0.96,"source_text":"mere papa ko bhi BP tha. Aur sugar bhi","timestamp_order":6},
{"id":"cf-r1-7","category":"medication","value":"Amlodipine 5mg OD","status":"active","confidence":0.99,"source_text":"Amlodipine 5mg once daily","timestamp_order":7},
{"id":"cf-r1-8","category":"medication","value":"Metformin 500mg BD with meals","status":"active","confidence":0.99,"source_text":"Metformin 500mg twice daily with meals","timestamp_order":8}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Fatigue and headache for 2-3 months","hpi":"45-year-old male presenting with fatigue, chronic headache, and facial flushing for 2-3 months. Exertional dyspnoea on climbing stairs. No chest pain at rest.","symptoms":["Fatigue","Headache","Exertional dyspnoea"],"allergies":["not specified"],"current_medications":[]},
"objective":{"vitals":{"bp":"158/96 mmHg","rbs":"240 mg/dL"},"exam":"not specified","labs":"RBS 240 mg/dL","imaging":"not specified"},
"assessment":{"diagnosis":"1. Hypertension (newly diagnosed)  2. Probable Type 2 Diabetes Mellitus","differentials":["Essential hypertension","Secondary hypertension","Metabolic syndrome"],"impression":"Newly diagnosed hypertension with elevated random blood sugar. Strong family history of both conditions. Exertional dyspnoea warrants cardiac evaluation.","severity":"moderate"},
"plan":{"medications":["Amlodipine 5mg once daily","Metformin 500mg twice daily with meals"],"investigations":["Fasting blood sugar","HbA1c","Lipid profile","Kidney function test (urea, creatinine)","ECG"],"lifestyle":["Low-sodium diet (< 2g/day)","Reduce refined carbohydrates and sugar","30 minutes brisk walking daily","Avoid smoking and alcohol"],"follow_up":"2 weeks with lab reports","red_flags":["BP > 180/110 mmHg","Chest pain","Sudden severe headache","Blurred vision","Blood sugar > 300 mg/dL"],"referrals":[]}}
}$SOAP$,
        $CDS$[
{"suggestion":"Order HbA1c and fasting glucose urgently to confirm T2DM","rationale":"RBS of 240 mg/dL with symptoms warrants formal diagnosis — HbA1c ≥ 6.5% confirms T2DM per ADA criteria","urgency":"high","evidence_from_transcript":["random blood sugar is 240"],"safety_label":"doctor_review_required"},
{"suggestion":"ECG to screen for hypertensive cardiac involvement","rationale":"Patient has exertional dyspnoea with new-onset hypertension — rule out LVH and ischaemia","urgency":"high","evidence_from_transcript":["158/96","seedhi chadne mein thodi taklif"],"safety_label":"doctor_review_required"},
{"suggestion":"Consider statin therapy at next visit — high cardiovascular risk","rationale":"Hypertension + probable T2DM + family history elevates 10-year CV risk significantly","urgency":"medium","evidence_from_transcript":["158/96","mere papa ko bhi BP tha"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    -- Visit 2 — 2-week follow-up: BP partially controlled, HbA1c ordered
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-r2',
        'Ramesh Kumar', 'Dr. Demo', '2026-06-03T10:00:00',
        'complete', 'health', demo_uid, p1, '45', 'M',
        $TR$Doctor: Hello Ramesh, how are the readings now?
Patient: Doctor thoda better hoon lekin BP abhi bhi thoda high hai. Ghar pe check kiya tha 148/92.
Doctor: Okay, the Amlodipine is helping but not enough. Let me add Losartan 50mg once daily. How is the sugar?
Patient: Khana khane ke baad 180-190 aa raha hai. Fasting nahi liya abhi tak.
Doctor: Please get fasting and HbA1c this week. Also get serum creatinine before we continue Losartan. Take Metformin morning and evening with food. Come back in 3 weeks with all reports.$TR$,
        $CF$[
{"id":"cf-r2-1","category":"vital","value":"BP 148/92 mmHg (home)","status":"active","confidence":0.93,"source_text":"148/92","timestamp_order":1},
{"id":"cf-r2-2","category":"vital","value":"Post-prandial blood sugar 180-190 mg/dL","status":"active","confidence":0.93,"source_text":"Khana khane ke baad 180-190","timestamp_order":2},
{"id":"cf-r2-3","category":"medication","value":"Amlodipine 5mg OD (continued)","status":"active","confidence":0.98,"source_text":"continued","timestamp_order":3},
{"id":"cf-r2-4","category":"medication","value":"Losartan 50mg OD","status":"active","confidence":0.99,"source_text":"Losartan 50mg once daily","timestamp_order":4},
{"id":"cf-r2-5","category":"medication","value":"Metformin 500mg BD (continued)","status":"active","confidence":0.99,"source_text":"Metformin morning and evening","timestamp_order":5}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Follow-up hypertension and blood sugar — partial improvement","hpi":"Home BP 148/92. Post-prandial sugars 180-190 mg/dL. Fasting glucose not yet checked. General wellbeing slightly improved.","symptoms":["Mild improvement in fatigue"],"allergies":["not specified"],"current_medications":["Amlodipine 5mg OD","Metformin 500mg BD"]},
"objective":{"vitals":{"bp_home":"148/92 mmHg","ppbs":"180-190 mg/dL"},"exam":"not specified","labs":"PPBS 180-190 mg/dL","imaging":"not specified"},
"assessment":{"diagnosis":"1. Hypertension — partially controlled  2. T2DM — suboptimal glycaemic control","differentials":[],"impression":"BP partially responding to Amlodipine monotherapy. ARB added for synergistic antihypertensive effect and renal protection. Awaiting fasting glucose and HbA1c for diabetes titration.","severity":"moderate"},
"plan":{"medications":["Amlodipine 5mg OD (continue)","Losartan 50mg OD (add)","Metformin 500mg BD (continue)"],"investigations":["Fasting blood sugar (urgent)","HbA1c","Serum creatinine and potassium (baseline before Losartan)","Lipid profile"],"lifestyle":["Low-sodium diet reinforced","Monitor home BP twice daily and log","30-minute walk daily"],"follow_up":"3 weeks with lab reports","red_flags":["BP > 180/110","Chest pain","Sudden severe headache"],"referrals":[]}}
}$SOAP$,
        $CDS$[
{"suggestion":"Check serum creatinine and potassium before continuing Losartan","rationale":"ARBs can worsen renal function and cause hyperkalaemia — baseline essential before prescribing","urgency":"high","evidence_from_transcript":["Losartan 50mg once daily"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    -- Visit 3 — 4-week follow-up: Controlled, Metformin uptitrated
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-r3',
        'Ramesh Kumar', 'Dr. Demo', '2026-07-01T09:30:00',
        'complete', 'health', demo_uid, p1, '45', 'M',
        $TR$Doctor: Ramesh, you look much better today! What are the home readings?
Patient: Doctor BP bohot better ho gaya. 126/82 consistently aa raha hai. Reports bhi laya hoon.
Doctor: Excellent. HbA1c 7.2% — that is very good for a newly diagnosed patient. Fasting sugar 116. Creatinine 0.9, normal. Lipid profile — LDL 148, I will start a statin.
Patient: Weight bhi 3 kilo kam hua hai doctor. Khana aur exercise control kar raha hoon.
Doctor: Fantastic. Increase Metformin to 1000mg twice daily. Start Atorvastatin 20mg at night. Continue all other medications. Repeat HbA1c in 3 months. Refer to ophthalmology for annual diabetic eye check.$TR$,
        $CF$[
{"id":"cf-r3-1","category":"vital","value":"BP 126/82 mmHg (well controlled)","status":"active","confidence":0.98,"source_text":"126/82 consistently","timestamp_order":1},
{"id":"cf-r3-2","category":"lab","value":"HbA1c 7.2%","status":"active","confidence":0.99,"source_text":"HbA1c 7.2%","timestamp_order":2},
{"id":"cf-r3-3","category":"lab","value":"Fasting blood sugar 116 mg/dL","status":"active","confidence":0.99,"source_text":"Fasting sugar 116","timestamp_order":3},
{"id":"cf-r3-4","category":"lab","value":"Serum creatinine 0.9 mg/dL (normal)","status":"active","confidence":0.99,"source_text":"Creatinine 0.9, normal","timestamp_order":4},
{"id":"cf-r3-5","category":"lab","value":"LDL cholesterol 148 mg/dL","status":"active","confidence":0.99,"source_text":"LDL 148","timestamp_order":5},
{"id":"cf-r3-6","category":"other","value":"Weight loss 3 kg (lifestyle change)","status":"active","confidence":0.96,"source_text":"Weight bhi 3 kilo kam hua hai","timestamp_order":6},
{"id":"cf-r3-7","category":"medication","value":"Metformin 1000mg BD (uptitrated from 500mg)","status":"active","confidence":0.99,"source_text":"Increase Metformin to 1000mg twice daily","timestamp_order":7},
{"id":"cf-r3-8","category":"medication","value":"Atorvastatin 20mg OD at night (new)","status":"active","confidence":0.99,"source_text":"Start Atorvastatin 20mg at night","timestamp_order":8}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Follow-up — hypertension and T2DM — excellent response","hpi":"Home BP consistently 126/82. Lab reports reviewed: HbA1c 7.2%, fasting glucose 116, creatinine 0.9 (normal on Losartan), LDL 148. Weight loss of 3 kg with diet and exercise.","symptoms":["Significant improvement in fatigue","3 kg weight loss"],"allergies":["not specified"],"current_medications":["Amlodipine 5mg OD","Losartan 50mg OD","Metformin 500mg BD"]},
"objective":{"vitals":{"bp":"126/82 mmHg"},"exam":"not specified","labs":"HbA1c 7.2% | FBS 116 mg/dL | Creatinine 0.9 mg/dL | LDL 148 mg/dL","imaging":"not specified"},
"assessment":{"diagnosis":"1. Hypertension — well controlled  2. T2DM — improving (HbA1c 7.2%)  3. Dyslipidaemia","differentials":[],"impression":"Excellent response to treatment and lifestyle changes. BP controlled on dual antihypertensive. HbA1c acceptable for newly diagnosed T2DM. LDL elevated — statin indicated. Metformin uptitrated.","severity":"mild"},
"plan":{"medications":["Amlodipine 5mg OD (continue)","Losartan 50mg OD (continue)","Metformin 1000mg BD (uptitrated)","Atorvastatin 20mg at night (new)"],"investigations":["HbA1c repeat in 3 months","Annual urine microalbumin (diabetic nephropathy screen)","LFT baseline before statin"],"lifestyle":["Maintain dietary changes","Continue 30-minute daily walk","Target further 5 kg weight loss","Monitor home BP log"],"follow_up":"3 months or sooner if readings worsen","red_flags":["BP > 160/100","FBS > 200 mg/dL","Chest pain","Foot numbness or sores","Muscle pain on statin"],"referrals":["Ophthalmology — annual diabetic retinopathy screening"]}}
}$SOAP$,
        $CDS$[
{"suggestion":"Annual ophthalmology referral due — first diabetic retinopathy screen at diagnosis","rationale":"T2DM diagnosed 6 weeks ago; ADA guidelines recommend first eye exam at diagnosis and then annually","urgency":"medium","evidence_from_transcript":["HbA1c 7.2%"],"safety_label":"doctor_review_required"},
{"suggestion":"Check LFT baseline before starting Atorvastatin","rationale":"Statins can rarely cause hepatotoxicity; baseline LFT recommended before initiation","urgency":"medium","evidence_from_transcript":["Start Atorvastatin 20mg"],"safety_label":"doctor_review_required"},
{"suggestion":"Annual urine microalbumin to screen for early diabetic nephropathy","rationale":"Patient on Losartan (nephroprotective) but baseline microalbumin not yet established","urgency":"medium","evidence_from_transcript":["Creatinine 0.9, normal"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    -- ══════════════════════════════════════════════════════════
    -- PRIYA SHARMA — Acute fever and URTI
    -- ══════════════════════════════════════════════════════════
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-p1',
        'Priya Sharma', 'Dr. Demo', '2026-07-02T11:30:00',
        'complete', 'health', demo_uid, p2, '28', 'F',
        $TR$Doctor: Hello Priya, what happened?
Patient: Doctor kal se bukhaar hai, 102 degree. Gala bhi bahut dard kar raha hai. Peena mushkil ho gaya hai.
Doctor: Any cough? Runny nose?
Patient: Thodi khaansi hai. Naak bhi beh rahi hai 2 din se.
Doctor: Any drug allergies?
Patient: Nahi doctor, koi allergy nahi hai.
Doctor: Let me check your throat. Very red and inflamed, but no pus. Likely viral pharyngitis with a risk of secondary bacterial infection. I will give you Azithromycin 500mg once daily for 3 days, Paracetamol 650mg every 6 hours for fever, and Cetirizine 10mg at night for the runny nose. Plenty of warm fluids, rest. Come back if fever goes above 103 or does not settle in 3 days.$TR$,
        $CF$[
{"id":"cf-p1-1","category":"vital","value":"Fever 102°F (since yesterday)","status":"active","confidence":0.99,"source_text":"bukhaar hai, 102 degree","timestamp_order":1},
{"id":"cf-p1-2","category":"symptom","value":"Sore throat with odynophagia","status":"active","confidence":0.97,"source_text":"Gala bahut dard kar raha hai. Peena mushkil","timestamp_order":2},
{"id":"cf-p1-3","category":"symptom","value":"Mild cough","status":"active","confidence":0.93,"source_text":"Thodi khaansi hai","timestamp_order":3},
{"id":"cf-p1-4","category":"symptom","value":"Rhinorrhoea (2 days)","status":"active","confidence":0.95,"source_text":"Naak bhi beh rahi hai 2 din se","timestamp_order":4},
{"id":"cf-p1-5","category":"exam","value":"Throat: erythematous and inflamed, no tonsillar exudate","status":"active","confidence":0.97,"source_text":"Very red and inflamed, but no pus","timestamp_order":5},
{"id":"cf-p1-6","category":"allergy","value":"No known drug allergies","status":"active","confidence":0.99,"source_text":"Nahi doctor, koi allergy nahi hai","timestamp_order":6},
{"id":"cf-p1-7","category":"medication","value":"Azithromycin 500mg OD x 3 days","status":"active","confidence":0.99,"source_text":"Azithromycin 500mg once daily for 3 days","timestamp_order":7},
{"id":"cf-p1-8","category":"medication","value":"Paracetamol 650mg Q6H PRN","status":"active","confidence":0.99,"source_text":"Paracetamol 650mg every 6 hours for fever","timestamp_order":8},
{"id":"cf-p1-9","category":"medication","value":"Cetirizine 10mg OD at night","status":"active","confidence":0.99,"source_text":"Cetirizine 10mg at night","timestamp_order":9}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Fever and sore throat since yesterday","hpi":"28-year-old female presenting with fever 102°F since yesterday, severe sore throat with difficulty swallowing, mild cough, and rhinorrhoea for 2 days. No prior similar episodes.","symptoms":["Fever 102°F","Sore throat","Odynophagia","Mild cough","Rhinorrhoea"],"allergies":["No known drug allergies"],"current_medications":[]},
"objective":{"vitals":{"temperature":"102°F (38.9°C)"},"exam":"Throat: erythematous inflamed mucosa, no tonsillar exudate or peritonsillar swelling","labs":"not specified","imaging":"not specified"},
"assessment":{"diagnosis":"Acute viral pharyngitis with upper respiratory tract infection","differentials":["Streptococcal pharyngitis","Infectious mononucleosis"],"impression":"Viral URTI with pharyngitis most likely. No tonsillar exudate to suggest bacterial tonsillitis. Azithromycin added prophylactically given symptom severity and fever.","severity":"mild"},
"plan":{"medications":["Azithromycin 500mg once daily x 3 days","Paracetamol 650mg every 6 hours as needed for fever","Cetirizine 10mg once daily at night"],"investigations":["Throat swab culture if no improvement in 3 days"],"lifestyle":["2-3 litres warm fluids daily","Complete rest","Warm saline gargles 4-5 times daily","Avoid cold foods and drinks"],"follow_up":"Return if fever > 103°F or no improvement in 3 days","red_flags":["Fever > 103°F","Difficulty breathing","Neck stiffness","Inability to swallow even saliva","Rash"],"referrals":[]}}
}$SOAP$,
        $CDS$[
{"suggestion":"Consider rapid strep test to guide antibiotic use","rationale":"No tonsillar exudate suggests viral aetiology — rapid antigen detection test would confirm or rule out Group A Strep and avoid unnecessary antibiotic prescribing","urgency":"low","evidence_from_transcript":["Very red and inflamed, but no pus"],"safety_label":"doctor_review_required"},
{"suggestion":"Monospot test if no improvement — rule out infectious mononucleosis","rationale":"Young female with pharyngitis and fever — EBV mononucleosis can mimic viral URTI and is common in this age group; avoid Amoxicillin if mono suspected (risk of rash)","urgency":"low","evidence_from_transcript":["102 degree","Gala bahut dard"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    -- ══════════════════════════════════════════════════════════
    -- SURESH PATEL — COPD exacerbation + follow-up arc
    -- ══════════════════════════════════════════════════════════

    -- Visit 1: Acute COPD exacerbation
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-s1',
        'Suresh Patel', 'Dr. Demo', '2026-06-05T08:30:00',
        'complete', 'health', demo_uid, p3, '62', 'M',
        $TR$Doctor: Suresh bhai, kya ho gaya? You look very short of breath.
Patient: Doctor 3 din se bahut takleef hai. Saas nahi aati. Raat ko so bhi nahi paa raha.
Doctor: Do you smoke?
Patient: Haan doctor, 30 saal se pee raha hoon. Abhi 5-6 cigarette roz.
Doctor: Any cough with sputum?
Patient: Haan yellow-green colour ka. Thoda blood bhi tha kal.
Doctor: I am checking your oxygen now. SpO2 is 91%. That is quite low. You have COPD and this is an acute exacerbation. I am giving you Salbutamol nebulisation right now. Then Prednisolone 40mg once daily for 5 days, Amoxicillin-Clavulanate 625mg twice daily for 7 days. Urgent chest X-ray. If you do not improve in 24 hours you will need hospital admission.$TR$,
        $CF$[
{"id":"cf-s1-1","category":"vital","value":"SpO2 91% on room air","status":"active","confidence":0.99,"source_text":"SpO2 is 91%. That is quite low","timestamp_order":1},
{"id":"cf-s1-2","category":"symptom","value":"Acute dyspnoea (3 days)","status":"active","confidence":0.99,"source_text":"3 din se bahut takleef hai. Saas nahi aati","timestamp_order":2},
{"id":"cf-s1-3","category":"symptom","value":"Orthopnoea (unable to sleep)","status":"active","confidence":0.91,"source_text":"Raat ko so bhi nahi paa raha","timestamp_order":3},
{"id":"cf-s1-4","category":"symptom","value":"Purulent sputum (yellow-green)","status":"active","confidence":0.99,"source_text":"yellow-green colour ka","timestamp_order":4},
{"id":"cf-s1-5","category":"symptom","value":"Haemoptysis (1 episode yesterday)","status":"active","confidence":0.97,"source_text":"Thoda blood bhi tha kal","timestamp_order":5},
{"id":"cf-s1-6","category":"social_history","value":"Smoking 5-6 cigarettes/day for 30 years (~30 pack-years)","status":"active","confidence":0.98,"source_text":"30 saal se pee raha hoon. Abhi 5-6 cigarette","timestamp_order":6},
{"id":"cf-s1-7","category":"diagnosis","value":"COPD — acute exacerbation (AECOPD)","status":"active","confidence":0.97,"source_text":"You have COPD and this is an acute exacerbation","timestamp_order":7},
{"id":"cf-s1-8","category":"medication","value":"Salbutamol nebulisation (stat)","status":"active","confidence":0.99,"source_text":"Salbutamol nebulisation right now","timestamp_order":8},
{"id":"cf-s1-9","category":"medication","value":"Prednisolone 40mg OD x 5 days","status":"active","confidence":0.99,"source_text":"Prednisolone 40mg once daily for 5 days","timestamp_order":9},
{"id":"cf-s1-10","category":"medication","value":"Amoxicillin-Clavulanate 625mg BD x 7 days","status":"active","confidence":0.99,"source_text":"Amoxicillin-Clavulanate 625mg twice daily for 7 days","timestamp_order":10}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Acute breathlessness, productive cough, and haemoptysis for 3 days","hpi":"62-year-old male with heavy smoking history (30 pack-years, currently 5-6/day) presenting with acute dyspnoea for 3 days, orthopnoea, yellow-green productive cough, and single episode of haemoptysis yesterday. No prior COPD diagnosis on record.","symptoms":["Acute dyspnoea","Orthopnoea","Purulent sputum","Haemoptysis"],"allergies":["not specified"],"current_medications":[]},
"objective":{"vitals":{"spo2":"91% on room air"},"exam":"Clinically in respiratory distress","labs":"not specified","imaging":"Chest X-ray ordered (urgent)"},
"assessment":{"diagnosis":"Acute exacerbation of COPD (AECOPD)","differentials":["Community-acquired pneumonia","Pulmonary embolism","Decompensated cardiac failure"],"impression":"AECOPD with significant hypoxaemia. Haemoptysis in a heavy smoker is a red flag — malignancy must be excluded. Admission threshold low given SpO2 91%.","severity":"severe"},
"plan":{"medications":["Salbutamol nebulisation stat and 4-hourly","Prednisolone 40mg OD x 5 days","Amoxicillin-Clavulanate 625mg BD x 7 days"],"investigations":["Chest X-ray urgent","CBC and CRP","Sputum culture and sensitivity","ABG if SpO2 does not improve with nebulisation"],"lifestyle":["Smoking cessation — mandatory and urgent","Refer to pulmonologist urgently"],"follow_up":"24 hours — admit if no improvement","red_flags":["SpO2 < 88%","Worsening breathlessness","Cyanosis","Altered consciousness","Increased haemoptysis"],"referrals":["Pulmonology — urgent"]}}
}$SOAP$,
        $CDS$[
{"suggestion":"SpO2 91% — initiate controlled oxygen therapy; target SpO2 88-92% in COPD","rationale":"Hypoxaemia in COPD requires controlled O2 to avoid hypercapnic drive suppression; supplemental oxygen indicated","urgency":"critical","evidence_from_transcript":["SpO2 is 91%. That is quite low"],"safety_label":"doctor_review_required"},
{"suggestion":"Haemoptysis + 30 pack-years = urgent CT chest to exclude lung malignancy","rationale":"CXR alone has limited sensitivity for early bronchogenic carcinoma; CT is mandatory workup for haemoptysis in high-risk smokers","urgency":"high","evidence_from_transcript":["Thoda blood bhi tha kal","30 saal se pee raha hoon"],"safety_label":"doctor_review_required"},
{"suggestion":"Offer Varenicline or NRT for smoking cessation at this visit","rationale":"Hospital or acute illness episodes are high-motivation windows for cessation; pharmacotherapy doubles quit rates","urgency":"medium","evidence_from_transcript":["Abhi 5-6 cigarette roz"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    -- Visit 2: 2-week follow-up — improved, COPD confirmed, maintenance inhaler started
    INSERT INTO sessions (
        id, patient_name, doctor_name, created_at, status, mode,
        user_id, patient_id, patient_age, patient_sex,
        transcript, clinical_facts, soap_note, cds_suggestions
    ) VALUES (
        'sess-demo-s2',
        'Suresh Patel', 'Dr. Demo', '2026-06-20T09:00:00',
        'complete', 'health', demo_uid, p3, '62', 'M',
        $TR$Doctor: Suresh bhai, you look much better today!
Patient: Haan doctor, medicine se bahut farak pada. Saas ab theek se aati hai. Raat ko bhi so pa raha hoon. Cigarette bhi 3 kar li hai — koshish kar raha hoon.
Doctor: Excellent. Oxygen is 96% now. Your chest X-ray shows hyperinflation, no consolidation, no mass lesion.
Patient: Relief hua doctor. Cancer ka darr bahut tha.
Doctor: Good news — no cancer on X-ray. But COPD is confirmed. You need long-term inhalers now. Starting Tiotropium 18 mcg once daily as the main inhaler, and Salbutamol as rescue only. Stop smoking completely — I strongly recommend Varenicline to help. Pulmonologist appointment next week for spirometry and formal COPD grading.$TR$,
        $CF$[
{"id":"cf-s2-1","category":"vital","value":"SpO2 96% (improved from 91%)","status":"active","confidence":0.99,"source_text":"Oxygen is 96% now","timestamp_order":1},
{"id":"cf-s2-2","category":"imaging","value":"CXR: hyperinflation (COPD pattern), no consolidation, no mass","status":"active","confidence":0.99,"source_text":"hyperinflation, no consolidation, no mass lesion","timestamp_order":2},
{"id":"cf-s2-3","category":"diagnosis","value":"COPD confirmed on imaging","status":"active","confidence":0.98,"source_text":"COPD is confirmed","timestamp_order":3},
{"id":"cf-s2-4","category":"social_history","value":"Smoking reduced to 3 cigarettes/day (from 5-6)","status":"active","confidence":0.97,"source_text":"Cigarette bhi 3 kar li hai","timestamp_order":4},
{"id":"cf-s2-5","category":"medication","value":"Tiotropium 18mcg inhaler OD (LAMA — new)","status":"active","confidence":0.99,"source_text":"Tiotropium 18 mcg once daily","timestamp_order":5},
{"id":"cf-s2-6","category":"medication","value":"Salbutamol inhaler PRN (rescue)","status":"active","confidence":0.99,"source_text":"Salbutamol as rescue only","timestamp_order":6}
]$CF$,
        $SOAP${
"subjective":{"chief_complaint":"Follow-up AECOPD — significant improvement","hpi":"Patient reports complete resolution of dyspnoea. Sleeping well at night. Smoking reduced from 5-6 to 3 cigarettes/day. No further haemoptysis since last visit.","symptoms":["Dyspnoea resolved","Sleep normalised","No further haemoptysis"],"allergies":["not specified"],"current_medications":["Prednisolone (course completed)","Amoxicillin-Clavulanate (course completed)","Salbutamol nebulisation"]},
"objective":{"vitals":{"spo2":"96% on room air"},"exam":"Clinically improved, no respiratory distress","labs":"not specified","imaging":"CXR: hyperinflation consistent with COPD, no consolidation, no mass lesion"},
"assessment":{"diagnosis":"COPD — stable post-exacerbation. No malignancy on CXR.","differentials":[],"impression":"Excellent clinical recovery. COPD confirmed radiologically. CXR reassuringly clear — no mass. CT chest still advisable given haemoptysis history. Initiate maintenance bronchodilator therapy. Cessation counselling ongoing.","severity":"mild (post-exacerbation, stable)"},
"plan":{"medications":["Tiotropium 18mcg inhaler once daily (new — long-acting bronchodilator)","Salbutamol 100mcg inhaler 2 puffs as needed (rescue only)"],"investigations":["Spirometry / PFTs at pulmonologist for GOLD grading","CT chest — recommended to fully exclude malignancy given haemoptysis history","Echocardiogram to rule out cor pulmonale"],"lifestyle":["Complete smoking cessation — target 0 cigarettes (offer Varenicline)","Influenza vaccination annually","Pneumococcal vaccination","Pulmonary rehabilitation referral"],"follow_up":"Pulmonologist next week","red_flags":["SpO2 < 90%","Haemoptysis recurrence","Chest pain","Unintentional weight loss"],"referrals":["Pulmonology — confirmed appointment for spirometry and COPD management plan"]}}
}$SOAP$,
        $CDS$[
{"suggestion":"CT chest still recommended despite clear CXR — haemoptysis workup in a heavy smoker requires CT-level exclusion","rationale":"CXR sensitivity for early lung cancer is < 50%; CT chest is standard of care for haemoptysis in high-risk smokers per BTS/ATS guidelines","urgency":"high","evidence_from_transcript":["no mass lesion","Thoda blood bhi tha kal","30 saal se pee raha hoon"],"safety_label":"doctor_review_required"},
{"suggestion":"Prescribe Varenicline — patient is motivated and in a receptive window","rationale":"Patient has already halved smoking; pharmacotherapy with Varenicline achieves 2-3x higher quit rates vs willpower alone","urgency":"medium","evidence_from_transcript":["Cigarette bhi 3 kar li hai — koshish kar raha hoon"],"safety_label":"doctor_review_required"}
]$CDS$
    ) ON CONFLICT (id) DO NOTHING;

    RAISE NOTICE 'Demo data seeded successfully for user_id = %', demo_uid;
END $$;

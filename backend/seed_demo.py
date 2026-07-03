"""
Seed script — creates demo patient "Priya Sharma" with 4 realistic sessions
showing a longitudinal care timeline (hypertension + T2DM management).

Run from backend/:
    python3 seed_demo.py

Safe to run multiple times — checks for existing demo sessions first.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta

DB_PATH = "lipi.db"
ARUSH_USER_ID = "1"
ARUSH_CLINIC_ID = "a41b1557-4b22-4c61-a9ee-66993d4195c5"
DOCTOR_NAME = "Dr. Arush Singhal"
PATIENT_NAME = "Priya Sharma"
PATIENT_PHONE = "+91 98765 43210"
PATIENT_AGE = "42"
PATIENT_SEX = "F"

SESSIONS = [
    # ── Visit 1: Initial presentation 6 months ago ─────────────────────────
    {
        "offset_days": -180,
        "transcript": (
            "[Professional] Priya ji, aapko kya takleef hai aaj? "
            "[Client] Doctor sahab, kaafi dino se sar dard ho raha hai, aur kabhi kabhi aankhon ke aage andhera sa ho jaata hai. "
            "[Professional] Kitne din se ye symptoms hain? "
            "[Client] Kareeb ek mahine se. Ghar mein tension bhi bahut hai. "
            "[Professional] BP check karte hain. 158 over 96. Ye thoda high hai. "
            "[Professional] Koi family history hai hypertension ki? "
            "[Client] Haan, meri maa ko bhi tha. "
            "[Professional] Theek hai. Amlodipine 5mg shuru karte hain. Ek mahine baad check-up karna."
        ),
        "soap_note": {
            "S": "42F presenting with persistent headaches and intermittent visual blurring for ~1 month. Family history of hypertension (mother). Increased home stress reported.",
            "O": "BP 158/96 mmHg. HR 82 bpm. No papilloedema on fundoscopy. BMI 26.4.",
            "A": "Stage 1 Hypertension (HTN), likely essential. Visual symptoms secondary to elevated BP.",
            "P": "Start Amlodipine 5 mg OD. Low-salt diet counselling. Avoid caffeine. Review in 4 weeks with BP log. Urgent review if vision worsens or headache becomes severe.",
        },
        "extracted_facts": [
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Persistent headache × 1 month", "review_status": "confirmed", "source_sentence": "kaafi dino se sar dard ho raha hai"},
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Intermittent visual blurring", "review_status": "confirmed", "source_sentence": "aankhon ke aage andhera sa ho jaata hai"},
            {"id": str(uuid.uuid4()), "category": "vital", "normalized_value": "BP 158/96 mmHg", "review_status": "confirmed", "source_sentence": "158 over 96. Ye thoda high hai"},
            {"id": str(uuid.uuid4()), "category": "diagnosis", "normalized_value": "Stage 1 Hypertension (essential)", "review_status": "confirmed", "source_sentence": "Stage 1 Hypertension"},
            {"id": str(uuid.uuid4()), "category": "medication", "normalized_value": "Amlodipine 5 mg OD — started", "review_status": "confirmed", "source_sentence": "Amlodipine 5mg shuru karte hain"},
            {"id": str(uuid.uuid4()), "category": "follow_up", "normalized_value": "Review in 4 weeks with BP log", "review_status": "confirmed", "source_sentence": "ek mahine baad check-up karna"},
        ],
    },

    # ── Visit 2: 3 months ago — HTN review + T2DM new diagnosis ───────────
    {
        "offset_days": -90,
        "transcript": (
            "[Professional] Priya ji, BP kaisa raha ghar pe? "
            "[Client] Thoda better hai, zyaadatar 140 ke aas paas. "
            "[Professional] Acha. Aur koi nayi takleef? "
            "[Client] Haan doctor, bahut pyaas lagti hai aur baar baar bathroom jaana pad raha hai. Thakan bhi bahut hai. "
            "[Professional] Kitne din se? "
            "[Client] Shayad do teen mahine se. Weight bhi thoda bada hai. "
            "[Professional] Fasting glucose 214 mg/dL, HbA1c 8.2%. "
            "[Professional] Priya ji aapko diabetes bhi hai. Metformin shuru karni padegi. "
            "[Client] Main ghabra gayi doctor. "
            "[Professional] Ghabrao mat. Dono conditions manage ho jaati hain. Diet pe dhyan do."
        ),
        "soap_note": {
            "S": "Follow-up for HTN. BP improved to ~140/88 on Amlodipine 5mg. New complaints: polyuria, polydipsia, fatigue × 2–3 months. Weight gain ~4 kg over 3 months.",
            "O": "BP 142/88 mmHg. HR 78 bpm. FBG 214 mg/dL. HbA1c 8.2%. BMI 27.8. No signs of peripheral neuropathy.",
            "A": "1. Hypertension — partially controlled on Amlodipine 5mg.\n2. New diagnosis: Type 2 Diabetes Mellitus (T2DM), HbA1c 8.2%.",
            "P": "Continue Amlodipine 5mg. Add Metformin 500mg BD with meals, uptitrate to 1g BD in 2 weeks if tolerated. HbA1c recheck in 3 months. Dietary counselling (low GI, reduce refined carbs). Daily step target ≥7000. Ophthalmology referral for baseline diabetic eye screen.",
        },
        "extracted_facts": [
            {"id": str(uuid.uuid4()), "category": "vital", "normalized_value": "BP 142/88 mmHg (improved)", "review_status": "confirmed", "source_sentence": "Thoda better hai, zyaadatar 140 ke aas paas"},
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Polyuria and polydipsia × 2–3 months", "review_status": "confirmed", "source_sentence": "bahut pyaas lagti hai aur baar baar bathroom jaana"},
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Fatigue and weight gain 4 kg", "review_status": "confirmed", "source_sentence": "Thakan bhi bahut hai. Weight bhi thoda bada hai"},
            {"id": str(uuid.uuid4()), "category": "investigation", "normalized_value": "FBG 214 mg/dL", "review_status": "confirmed", "source_sentence": "Fasting glucose 214 mg/dL"},
            {"id": str(uuid.uuid4()), "category": "investigation", "normalized_value": "HbA1c 8.2%", "review_status": "confirmed", "source_sentence": "HbA1c 8.2%"},
            {"id": str(uuid.uuid4()), "category": "diagnosis", "normalized_value": "Type 2 Diabetes Mellitus — new diagnosis", "review_status": "confirmed", "source_sentence": "diabetes bhi hai"},
            {"id": str(uuid.uuid4()), "category": "medication", "normalized_value": "Metformin 500mg BD → uptitrate to 1g BD", "review_status": "confirmed", "source_sentence": "Metformin 500mg BD with meals"},
            {"id": str(uuid.uuid4()), "category": "follow_up", "normalized_value": "HbA1c recheck in 3 months. Ophthalmology referral.", "review_status": "confirmed", "source_sentence": "HbA1c recheck in 3 months. Ophthalmology referral"},
        ],
    },

    # ── Visit 3: 1 month ago — chest pain workup ───────────────────────────
    {
        "offset_days": -28,
        "transcript": (
            "[Professional] Priya ji kya hua aaj? Aap worried lag rahi hain. "
            "[Client] Doctor, kal raat ko seene mein bahut dard hua. Saans bhi thodi takleef se aaya. Main bahut darr gayi thi. "
            "[Professional] Dard kaisa tha, kahan tha exactly? "
            "[Client] Seedha seene ke beech mein, dabane wala dard tha. Do teen minute raha phir apne aap theek ho gaya. "
            "[Professional] ECG normal hai. Troponin negative. BP aaj 148/90. "
            "[Professional] Lagta hai musculoskeletal ya acidity ka issue hai but rule out karna padega. "
            "[Client] Kya mujhe hospital jaana chahiye? "
            "[Professional] Abhi urgent nahi hai but stress test karwao kal subah. Acidity ke liye pantoprazole shuru karo. "
            "[Professional] Amlodipine 5 se 10mg karte hain BP ke liye. Aur Metformin continue karo."
        ),
        "soap_note": {
            "S": "Acute chest pain episode last night — central, pressure-like, 2–3 min, self-resolving. Associated mild dyspnoea. Patient was alarmed. No radiation to arm/jaw. No diaphoresis. Background: HTN + T2DM.",
            "O": "BP 148/90 mmHg. HR 86 bpm. ECG: NSR, no ST changes. Troponin I: negative. Chest clear on auscultation. Epigastric tenderness on palpation.",
            "A": "1. Atypical chest pain — likely musculoskeletal vs. GERD. ACS ruled out (negative troponin, normal ECG). Exercise stress test ordered to exclude silent ischaemia.\n2. HTN — suboptimal control, uptitrating Amlodipine.\n3. T2DM — stable.",
            "P": "Uptitrate Amlodipine to 10 mg OD. Add Pantoprazole 40 mg OD (before breakfast) for 4 weeks. Treadmill stress test tomorrow morning (fasting). Return immediately if chest pain recurs or if dyspnoea worsens. Continue Metformin 1g BD.",
        },
        "extracted_facts": [
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Central chest pain — pressure-like, 2–3 min, self-resolving", "review_status": "confirmed", "source_sentence": "seene mein bahut dard hua. Seedha seene ke beech mein"},
            {"id": str(uuid.uuid4()), "category": "symptom", "normalized_value": "Mild dyspnoea associated", "review_status": "confirmed", "source_sentence": "Saans bhi thodi takleef se aaya"},
            {"id": str(uuid.uuid4()), "category": "investigation", "normalized_value": "ECG: normal sinus rhythm, no ST changes", "review_status": "confirmed", "source_sentence": "ECG normal hai"},
            {"id": str(uuid.uuid4()), "category": "investigation", "normalized_value": "Troponin I: negative", "review_status": "confirmed", "source_sentence": "Troponin negative"},
            {"id": str(uuid.uuid4()), "category": "vital", "normalized_value": "BP 148/90 mmHg", "review_status": "confirmed", "source_sentence": "BP aaj 148/90"},
            {"id": str(uuid.uuid4()), "category": "diagnosis", "normalized_value": "Atypical chest pain — GERD/MSK likely; ACS excluded", "review_status": "confirmed", "source_sentence": "musculoskeletal ya acidity ka issue hai but rule out karna padega"},
            {"id": str(uuid.uuid4()), "category": "medication", "normalized_value": "Amlodipine uptitrated to 10 mg OD", "review_status": "confirmed", "source_sentence": "Amlodipine 5 se 10mg karte hain"},
            {"id": str(uuid.uuid4()), "category": "medication", "normalized_value": "Pantoprazole 40 mg OD added", "review_status": "confirmed", "source_sentence": "Acidity ke liye pantoprazole shuru karo"},
            {"id": str(uuid.uuid4()), "category": "follow_up", "normalized_value": "Treadmill stress test next morning (fasting)", "review_status": "confirmed", "source_sentence": "stress test karwao kal subah"},
        ],
    },

    # ── Visit 4: Today — registered by assistant Meena, in Waiting Room ────
    {
        "offset_days": 0,
        "is_intake": True,
        "transcript": "[Chief complaint: Pet mein dard aur nausea, subah se]",
        "soap_note": None,
        "extracted_facts": [],
    },
]


def seed():
    con = sqlite3.connect(DB_PATH)

    existing = con.execute(
        "SELECT COUNT(*) FROM sessions WHERE patient_name = ? AND user_id = ?",
        (PATIENT_NAME, ARUSH_USER_ID),
    ).fetchone()[0]

    if existing >= 3:
        print(f"Demo data already exists ({existing} sessions for {PATIENT_NAME}). Skipping.")
        con.close()
        return

    now = datetime.now()
    inserted = 0

    for s in SESSIONS:
        session_id = str(uuid.uuid4())
        created_at = (now + timedelta(days=s["offset_days"])).strftime("%Y-%m-%dT%H:%M:%S")
        is_intake = s.get("is_intake", False)

        soap_json = json.dumps(s["soap_note"]) if s["soap_note"] else None
        facts_json = json.dumps(s["extracted_facts"])

        # Build memory_state the way the app does
        memory_state = json.dumps({
            "_extracted_facts": s["extracted_facts"],
            "_version": "1.0",
        })

        status = "created" if is_intake else "complete"
        initiated_by = "assistant" if is_intake else "doctor"

        con.execute(
            """
            INSERT INTO sessions (
                id, patient_name, doctor_name, created_at, status, mode,
                transcript, soap_note, extracted_facts, memory_state,
                cloud_ai_consent, user_id, clinic_id,
                patient_phone, patient_age, patient_sex, initiated_by,
                patient_consent_given, memory_enabled
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                session_id, PATIENT_NAME, DOCTOR_NAME, created_at, status, "health",
                s["transcript"], soap_json, facts_json, memory_state,
                1, ARUSH_USER_ID, ARUSH_CLINIC_ID,
                PATIENT_PHONE, PATIENT_AGE, PATIENT_SEX, initiated_by,
                1 if not is_intake else 0, 1,
            ),
        )
        label = "Intake (Waiting Room)" if is_intake else f"Visit {inserted + 1} ({created_at[:10]})"
        print(f"  ✓ {label} — {s.get('soap_note', {}).get('A', '[pending]')[:60] if s['soap_note'] else '[no SOAP yet]'}")
        inserted += 1

    con.commit()
    con.close()
    print(f"\nSeeded {inserted} sessions for {PATIENT_NAME}.")
    print("→ Log in as arush to see all 4 visits on Dashboard + patient timeline")
    print("→ The intake session appears in the Waiting Room (initiated_by=assistant)")


if __name__ == "__main__":
    seed()

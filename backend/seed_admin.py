"""
Admin + Cardiology Demo Seed Script
====================================
Creates two accounts:
  1. arush / admin123  — your personal admin account, no trial limits, paid forever
  2. lipi_demo / demo1234 — cardiology demo account for AIIMS visit, pre-loaded with
     3 realistic PAH/RHD/HF sessions so Dr. Narang sees longitudinal history

Run from backend/:
    uv run python3 seed_admin.py

Safe to re-run — skips if accounts already exist.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
import bcrypt

DB_PATH = "lipi.db"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


CARDIOLOGY_SESSIONS = [
    {
        "offset_days": -45,
        "patient_name": "Sunita Devi",
        "patient_phone": "+91 98110 23456",
        "patient_age": "38",
        "patient_sex": "F",
        "transcript": (
            "Patient Sunita Devi, 38 year old female. "
            "Known case of rheumatic heart disease with severe mitral stenosis. "
            "Presenting with NYHA class III dyspnoea and orthopnea for last 2 months. "
            "Bilateral ankle swelling present. Dhadkan tez ho jaati hai kabhi kabhi. "
            "Echo shows tight MS, MVA 0.9 cm squared, LVEF 65 percent, PASP 55 mmHg, moderate TR. "
            "She is in atrial fibrillation with rapid ventricular rate. "
            "On warfarin with INR 2.5. "
            "Plan: BMV scheduled next week. Continue warfarin. "
            "Add furosemide 40 mg once daily, spironolactone 25 mg once daily. "
            "Rate control with digoxin. Follow up in 1 week."
        ),
    },
    {
        "offset_days": -20,
        "patient_name": "Rakesh Mehra",
        "patient_phone": "+91 99100 34567",
        "patient_age": "52",
        "patient_sex": "M",
        "transcript": (
            "Patient Rakesh Mehra, 52 year old male. "
            "Known case of PAH — pulmonary arterial hypertension — on bosentan and sildenafil. "
            "Six minute walk test today: 260 metres, down from 310 last month. "
            "PASP on echo 72 mmHg. NYHA class III. "
            "Dyspnoea on exertion worsening. No syncope. No haemoptysis. "
            "RHC done 6 months ago showing mPAP 48 mmHg, PVR 8 wood units. "
            "Plan: Escalate to triple therapy. Add macitentan in place of bosentan. "
            "Continue sildenafil 20 mg three times daily. "
            "Start rivaroxaban 20 mg once daily for anticoagulation. "
            "Refer to lung transplant team for evaluation. Follow up in 4 weeks."
        ),
    },
    {
        "offset_days": -5,
        "patient_name": "Vijay Kumar",
        "patient_phone": "+91 97300 45678",
        "patient_age": "61",
        "patient_sex": "M",
        "transcript": (
            "Patient Vijay Kumar, 61 year old male. "
            "Known case of CAD — triple vessel disease — post CABG 3 years ago. "
            "Now presenting with NYHA class III effort intolerance and bilateral leg swelling. "
            "LVEF on echo 28 percent — severely reduced. "
            "Old anterior wall MI with RWMA anterior wall. "
            "Troponin I elevated at 0.8. BNP 890. "
            "Diagnosis: HFrEF, ischaemic cardiomyopathy. "
            "Plan: Start sacubitril-valsartan 24 by 26 mg twice daily. "
            "Add ivabradine 5 mg twice daily — heart rate 82 per minute. "
            "Dapagliflozin 10 mg once daily. "
            "Continue aspirin, ticagrelor, rosuvastatin. "
            "Refer for ICD evaluation given LVEF 28 percent. "
            "ECG and repeat echo in 3 months. Follow up in 2 weeks."
        ),
    },
]


async def run():
    import aiosqlite

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # ── 1. Arush admin account ────────────────────────────────────────────
        cur = await db.execute("SELECT id FROM users WHERE username=?", ("arush",))
        arush_row = await cur.fetchone()
        if arush_row:
            arush_id = arush_row["id"]
            print(f"[skip] arush account already exists (id={arush_id})")
        else:
            cur = await db.execute(
                "INSERT INTO users (username, email, hashed_password, full_name, role, "
                "plan, paid_until, nmc_number, specialization) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "arush",
                    "arush@lipi.health",
                    _hash("admin123"),
                    "Dr. Arush Singhal",
                    "doctor",
                    "paid",
                    "2099-12-31",
                    "MCI-2024-001",
                    "Internal Medicine",
                ),
            )
            await db.commit()
            arush_id = cur.lastrowid
            print(f"[created] arush (id={arush_id})  password=admin123")

        # ── 2. Lipi demo / cardiology demo account ────────────────────────────
        cur = await db.execute("SELECT id FROM users WHERE username=?", ("lipi_demo",))
        demo_row = await cur.fetchone()
        if demo_row:
            demo_id = demo_row["id"]
            print(f"[skip] lipi_demo account already exists (id={demo_id})")
        else:
            cur = await db.execute(
                "INSERT INTO users (username, email, hashed_password, full_name, role, "
                "plan, paid_until, nmc_number, specialization) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "lipi_demo",
                    "demo@lipi.health",
                    _hash("demo1234"),
                    "Dr. Arush Singhal",
                    "doctor",
                    "paid",
                    "2099-12-31",
                    "MCI-2024-042",
                    "Cardiology",
                ),
            )
            await db.commit()
            demo_id = cur.lastrowid
            print(f"[created] lipi_demo (id={demo_id})  password=demo1234")

        # ── 3. Seed 3 cardiology sessions on lipi_demo ───────────────────────
        cur = await db.execute(
            "SELECT COUNT(*) as n FROM sessions WHERE user_id=?", (str(demo_id),)
        )
        row = await cur.fetchone()
        if row["n"] >= len(CARDIOLOGY_SESSIONS):
            print(f"[skip] cardiology sessions already seeded ({row['n']} found)")
            return

        from app.services.clinical_extractor import ClinicalExtractorService
        from app.services.memory_context import MemoryContextService
        from app.services.soap_generator import SOAPGeneratorService

        extractor = ClinicalExtractorService()
        memory = MemoryContextService()
        soap_gen = SOAPGeneratorService()

        clinic_id = str(uuid.uuid4())

        for s in CARDIOLOGY_SESSIONS:
            session_id = str(uuid.uuid4())
            created = (datetime.now() + timedelta(days=s["offset_days"])).isoformat()

            facts = extractor.extract(s["transcript"])
            state = memory.resolve_memory([facts])
            soap = soap_gen.generate_soap(state)

            await db.execute(
                """INSERT INTO sessions
                   (id, user_id, clinic_id, patient_name, patient_phone,
                    patient_age, patient_sex, transcript, clinical_facts,
                    soap_note, status, mode, cloud_ai_consent, doctor_name, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    session_id,
                    str(demo_id),
                    clinic_id,
                    s["patient_name"],
                    s["patient_phone"],
                    s["patient_age"],
                    s["patient_sex"],
                    s["transcript"],
                    json.dumps(facts),
                    json.dumps(soap),
                    "complete",
                    "health",
                    1,
                    "Dr. Arush Singhal",
                    created,
                ),
            )
            print(f"  [seeded] {s['patient_name']} — {s['offset_days']}d ago")

        await db.commit()
        print("\nDone. Login credentials:")
        print("  Personal  →  username: arush       password: admin123")
        print("  Demo      →  username: lipi_demo   password: demo1234")
        print("\nDemo account: Cardiology specialty, paid plan, 3 pre-loaded cardiology patients.")


asyncio.run(run())

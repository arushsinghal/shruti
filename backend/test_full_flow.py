#!/usr/bin/env python3
"""
Full integration test — every major flow.
Run from: clinical-decision-support-system/backend/
Usage:    .venv/bin/python test_full_flow.py
"""

import asyncio, json, sys, uuid
import httpx

BASE = "http://localhost:8000"
OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
HEAD = "\033[1;94m"
RST  = "\033[0m"

pass_count = 0
fail_count = 0

def check(label, condition, detail=""):
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"  {OK}  {label}")
    else:
        fail_count += 1
        print(f"  {FAIL}  {label}", f"  → {detail}" if detail else "")

def section(title):
    print(f"\n{HEAD}{'━'*55}{RST}")
    print(f"{HEAD} {title}{RST}")
    print(f"{HEAD}{'━'*55}{RST}")

async def main():
    user = f"testuser_{uuid.uuid4().hex[:6]}"
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as c:

        # ── 1. AUTH ──────────────────────────────────────────────
        section("1. Auth — register + login")
        r = await c.post("/api/auth/register", json={
            "username": user, "password": "pass123",
            "full_name": "Dr. Test", "email": f"{user}@gmail.com"
        })
        check("Register", r.status_code == 201, r.text[:80])

        r = await c.post("/api/auth/token", data={"username": user, "password": "pass123"})
        check("Login", r.status_code == 200, r.text[:80])
        token = r.json().get("access_token", "")
        H = {"Authorization": f"Bearer {token}"}
        check("Got token", len(token) > 20)

        # ── 2. DOCTOR PROFILE ────────────────────────────────────
        section("2. Doctor profile")
        r = await c.put("/api/auth/doctor-profile", json={
            "name": "Dr. Test", "mci_number": "MH-12345",
            "specialization": "General Physician / Family Medicine",
            "clinic_name": "Test Clinic", "clinic_address": "Mumbai",
            "clinic_phone": "+919876543210", "whatsapp_phone": "+919876543210",
        }, headers=H)
        check("Save profile", r.status_code == 200, r.text[:80])

        r = await c.get("/api/auth/doctor-profile", headers=H)
        check("Fetch profile", r.status_code == 200)
        check("Profile has name", r.json().get("name") == "Dr. Test")

        # ── 3. CLINIC CODE ───────────────────────────────────────
        section("3. Clinic invite code")
        r = await c.get("/api/auth/clinic-invite-code", headers=H)
        check("Get clinic code", r.status_code == 200, r.text[:80])
        clinic_code = r.json().get("code", "")
        check("Code is non-empty", bool(clinic_code), f"got: {clinic_code}")

        # ── 4. PROCESS CLINICAL ──────────────────────────────────
        section("4. Clinical pipeline — transcript → facts → SOAP")
        transcript = (
            "Patient has fever for 3 days. No vomiting. Possible dengue. Any cough? Yes. "
            "BP 150/90. Paracetamol 500mg twice daily. CBC karwao. Follow up in 3 days."
        )

        r = await c.post("/api/sessions", json={"mode": "health", "cloud_ai_consent": True}, headers=H)
        check("Create session", r.status_code == 201, r.text[:80])
        sid = r.json()["id"]

        r = await c.post(f"/api/sessions/{sid}/transcript",
                         json={"transcript": transcript}, headers=H)
        check("Submit transcript", r.status_code == 200)

        r = await c.post(f"/api/sessions/{sid}/process-clinical", headers=H)
        check("Process clinical", r.status_code == 200, r.text[:120])
        body = r.json()

        facts = body.get("extracted_facts", [])
        soap  = body.get("soap", {})
        soap_text = " ".join(soap.values()).lower()

        check("Facts extracted",          len(facts) > 0,          f"got {len(facts)}")
        check("All facts are candidates", all(f["review_status"] == "candidate" for f in facts),
              str({f["review_status"] for f in facts}))
        check("Fever is a candidate",     any("fever" in f["normalized_value"].lower() for f in facts))
        check("SOAP gated — no fever",    "fever" not in soap_text, f"S: {soap.get('S','')[:60]}")
        check("SOAP gated — no cough",    "cough" not in soap_text)

        # ── 5. FHIR GATE ─────────────────────────────────────────
        section("5. FHIR export gate")
        r = await c.get(f"/api/sessions/{sid}/fhir", headers=H)
        check("FHIR blocked before confirm (409)", r.status_code == 409, f"got {r.status_code}")

        r = await c.get(f"/api/sessions/{sid}/investigation-order", headers=H)
        check("Investigation order blocked (409)", r.status_code == 409, f"got {r.status_code}")

        # ── 6. FACT REVIEW ───────────────────────────────────────
        section("6. Fact review — accept one, reject one")
        fever_fact = next((f for f in facts if "fever" in f["normalized_value"].lower()), None)
        if fever_fact:
            r = await c.patch(f"/api/sessions/{sid}/facts/{fever_fact['id']}",
                              json={"action": "accept"}, headers=H)
            check("Accept fever fact",   r.status_code == 200, r.text[:80])
            updated = r.json()
            accepted = next((f for f in updated["extracted_facts"] if f["id"] == fever_fact["id"]), {})
            check("Fever confirmed",     accepted.get("review_status") == "confirmed")
            check("Confirmed_by set",    bool(accepted.get("confirmed_by")))
            new_soap = " ".join(updated["soap"].values()).lower()
            check("SOAP now has fever",  "fever" in new_soap, f"S: {updated['soap'].get('S','')[:60]}")

        # ── 7. FINALIZE + FHIR UNLOCK ────────────────────────────
        section("7. Finalize all → FHIR unlocks")
        r = await c.post(f"/api/sessions/{sid}/facts/finalize", headers=H)
        check("Finalize",            r.status_code == 200, r.text[:80])
        check("Confirmed count > 0", r.json().get("confirmed", 0) > 0, str(r.json().get("confirmed")))

        r = await c.get(f"/api/sessions/{sid}/fhir", headers=H)
        check("FHIR unblocked (200)", r.status_code == 200, f"got {r.status_code}")
        fhir = r.json()
        check("FHIR has resourceType", fhir.get("resourceType") == "Bundle")

        r = await c.get(f"/api/sessions/{sid}/investigation-order", headers=H)
        check("Investigation order unblocked", r.status_code in (200, 404))  # 404 = no investigations, still unblocked

        # ── 8. ANALYTICS ─────────────────────────────────────────
        section("8. Analytics endpoints")
        r = await c.get("/api/analytics/dashboard", headers=H)
        check("Dashboard analytics", r.status_code == 200, r.text[:80])

        r = await c.get("/api/analytics/revenue-summary", headers=H)
        check("Revenue summary",     r.status_code == 200, r.text[:80])
        rev = r.json()
        check("Revenue has dhis_clinic_amount", "dhis_clinic_amount" in rev)

        # ── 9. DOCTOR AVAILABILITY ───────────────────────────────
        section("9. Doctor availability (appointment booking)")
        avail = [
            {"day_of_week": 0, "start_time": "09:00", "end_time": "13:00", "slot_duration_minutes": 15},
            {"day_of_week": 1, "start_time": "09:00", "end_time": "13:00", "slot_duration_minutes": 15},
        ]
        r = await c.put("/api/doctor/availability", json=avail, headers=H)
        check("Save availability", r.status_code == 200, r.text[:80])

        r = await c.get("/api/doctor/availability", headers=H)
        check("Fetch availability", r.status_code == 200)
        check("Has 2 slots",        len(r.json().get("slots", [])) == 2)

        r = await c.get("/api/doctor/appointments", headers=H)
        check("Fetch appointments", r.status_code == 200)

        # ── 10. PATIENT PORTAL ───────────────────────────────────
        section("10. Patient portal")
        # Update session with patient phone so portal can find it
        test_phone = "9999988888"
        r = await c.patch(f"/api/sessions/{sid}", json={"patient_phone": test_phone, "patient_name": "Test Patient"}, headers=H)
        r2 = await c.get(f"/api/public/patient-summary?phone={test_phone}")
        check("Patient portal", r2.status_code in (200, 404), f"got {r2.status_code}")  # 404 = no records by phone yet

        # ── 11. SESSION LIST ─────────────────────────────────────
        section("11. Sessions")
        r = await c.get("/api/sessions", headers=H)
        check("List sessions",      r.status_code == 200)
        sessions = r.json() if isinstance(r.json(), list) else r.json().get("sessions", [])
        check("Session in list",    any(s["id"] == sid for s in sessions), f"{len(sessions)} sessions")

        r = await c.get(f"/api/sessions/{sid}", headers=H)
        check("Get session by id",  r.status_code == 200)
        check("Session is complete", r.json().get("status") == "complete")

    # ── SUMMARY ──────────────────────────────────────────────────
    total = pass_count + fail_count
    colour = "\033[92m" if fail_count == 0 else "\033[91m"
    print(f"\n{colour}{'━'*55}")
    print(f" {pass_count}/{total} passed   {fail_count} failed")
    print(f"{'━'*55}\033[0m\n")
    sys.exit(0 if fail_count == 0 else 1)

asyncio.run(main())

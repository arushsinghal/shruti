# 17 — ABDM / DHIS: Lipi as a Digital Solution Company (DSC)

**Last updated:** 2026-06-29  
**Status:** Pre-registration — sandbox onboarding in progress

---

## What This Is — The Double Payout

NHA pays **two parties** for every ABHA-linked record: the **clinic** (facility) and the **software company** (DSC). Both payouts are real government money deposited monthly.

**The critical constraint:** the clinic only receives their government payout if the software they use is ABDM v3 compliant and registered as a DSC. A clinic that doesn't use Lipi (or another compliant DSC) earns ₹0 from DHIS — even if they see 200 patients a day. This is not optional for them if they want the money.

**What this means for adoption:**
- The clinic's financial incentive is to switch TO Lipi, not away from it
- Switching to a different (non-DSC) EMR means losing their government income stream
- Lipi's DSC registration becomes a structural lock-in — not UX, not habit, but economics

---

## Who Gets Paid What (per ABHA-linked record)

| Party | Share | Category 1 (Discharge/Lab reports) | Category 2 (OPD consultations) |
|---|---|---|---|
| **Clinic / Facility** | 75% | **₹15.00** | **₹7.50** |
| **Lipi (DSC)** | 25% | **₹5.00** | **₹2.50** |
| **Total NHA payout** | 100% | ₹20.00 | ₹10.00 |

- Threshold: first 100 transactions/month/facility are unpaid (anti-abuse floor)
- Both parties paid monthly via NHA dashboard
- Backdated claims accepted up to 3 months

**Revenue estimate — 1 clinic, 1 doctor, 50 OPDs/day (Category 2):**

| Party | Daily | Monthly |
|---|---|---|
| **Clinic earns** | ₹375 | **₹11,250** |
| **Lipi earns (DSC)** | ₹125 | **₹3,750** |

At 100 doctors on platform:
- Clinic network earns: ₹11.25 lakh/month (their money, their incentive to keep us)
- Lipi earns: **₹3.75 lakh/month** in passive DSC income alone

---

## Scheme Rules

- **Incentive cap per facility:** ₹5 Crore lifetime
- **Transaction cap:** 1 per patient per day, 5 per patient per month (across all categories)
- **Facility eligibility:** Must be registered on the Health Facility Registry (HFR)
- **Software eligibility:** Must be ABDM v3 API compliant (Milestones M1, M2, M3)
- **Backdated claims:** Accepted up to 3 months prior to the month of submission
- **Payout cadence:** Monthly, via NHA dashboard

---

## v3 API Compliance Deadline

**CRITICAL:** Transactions from **July 2026 onwards** will only be paid out if the DSC software is fully v3 compliant.  
Non-compliant systems lose both their own payout and their partner facilities' payouts.

Milestones required:
- **M1:** ABHA creation/verification (OTP + biometric flows)
- **M2:** Health record linking (prescription, diagnostic report, consultation note)
- **M3:** Health Information Exchange (HIE-CM push + consent management)

---

## Onboarding Checklist (for Arush to complete)

### Step 1 — Sandbox Registration (do this week)
- [ ] Go to https://sandbox.abdm.gov.in → create developer account
- [ ] Register Lipi as a Digital Solution Company (DSC)
- [ ] Note down: Client ID, Client Secret, DSC ID

### Step 2 — Integration Milestones
- [ ] M1: Implement ABHA creation/fetch API (patient phone → ABHA ID)
- [ ] M2: Tag every FHIR bundle we already generate with the patient's ABHA ID + DSC ID
- [ ] M3: Push to HIE-CM after doctor signs the note

### Step 3 — Facility Onboarding
- [ ] Each partner clinic must register on HFR (can do this ourselves as part of onboarding)
- [ ] Link clinic's HFR ID to Lipi DSC ID in our system

### Step 4 — Go Live & Claims
- [ ] Deploy to ABDM production (after sandbox testing + certificates)
- [ ] Add DSC ID to every transaction log
- [ ] Monthly: pull claim report from NHA dashboard and reconcile

---

## What Lipi Already Has

| Needed | Status |
|---|---|
| FHIR R4 bundle generation | ✅ `FHIRMapperService` already built |
| Clinical facts → structured JSON | ✅ `ClinicalExtractorService` |
| Doctor sign-off gate | ✅ `routes_notes.py` process_clinical |
| ABHA ID field on sessions | ✅ `sessions.abha_number` column exists |
| HIE push endpoint | ❌ `abdm_gateway.py` — not yet built |
| ABHA creation/fetch | ❌ needs M1 API integration |
| Transaction tracking for DHIS | ❌ needs a `dhis_transactions` table |

---

## Code to Build (after sandbox creds arrive)

```
backend/app/services/abdm_gateway.py
  - get_or_create_abha(phone, name, dob) → abha_id
  - push_health_record(fhir_bundle, abha_id, session_id) → transaction_id
  - claim_dhis_transaction(transaction_id, category) → logged for monthly batch

backend/app/api/routes_abdm.py
  - POST /api/sessions/{id}/link-abha   → M1 flow
  - POST /api/sessions/{id}/push-record → M2/M3 flow (called after doctor signs)
```

Trigger in `routes_notes.py` after `process_clinical` — if `session.abha_number` is set and doctor has signed, auto-push to HIE.

---

## Pitch Framing (for clinic conversations)

> "Lipi makes your software essentially free. The government pays you — and us — for every patient record that gets digitized. Your assistant does nothing extra. When the doctor speaks, Lipi writes the note and silently files the ABDM record in the background. The government payout hits your account monthly. We take a 10% processing cut of your share."

---

## References

- ABDM Sandbox: https://sandbox.abdm.gov.in
- HFR Registration: https://facility.ndhm.gov.in
- DHIS Guidelines Corrigendum 7: NHA official circular (on request)
- v3 API Docs: ABDM developer portal → API Reference → v3

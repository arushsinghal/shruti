# 20 — Product Vision: From Documentation to Doctor Revenue

**Date:** 2026-06-30
**Status:** Vision locked — executing
**Related:** [[19_SERVICE_PIVOT]] · [[18_YC_PITCH_STRATEGY]] · [[03_PRODUCT_STRATEGY]]

---

## The Honest Assessment

The current product is right as a wedge. It is wrong as a destination.

Documentation saves doctor time. That's real. But time is not what doctors in India are desperate about — money is. A busy specialist is not losing sleep over spending 3 minutes writing notes. They're losing sleep over TPA claim rejections, patients who don't come back, and the chaos of running a practice solo.

If Lipi stays a documentation product, it will always compete against the ₹15,000/month clerk who sits in the corner and writes everything by hand. You will never win that fight on price. You might win on quality, but quality of documentation is invisible until something goes wrong medico-legally.

**The product becomes right the moment it ties to doctor revenue.**

---

## What Doctors in Indian Private Practice Actually Lose Money On

### 1. TPA / Insurance Claim Rejections
Every rejected claim costs ₹3,000–50,000. Rejections happen because documentation wasn't structured correctly — wrong ICD-10 code, no justification for investigations ordered, missing co-morbidity documentation.

A cardiologist seeing 20 patients/day with 8–10 on insurance: one rejection a day = ₹10,000 lost. Monthly that's ₹2–3 lakh walking out the door.

### 2. Patients Who Don't Follow Up
A specialist's revenue depends on return visits. Patient sends one message, doctor doesn't reply fast enough, they go elsewhere. Lost follow-up = ₹500–2,000 per return visit × 5–10 patients/week = ₹25,000–80,000/month not realised.

### 3. Lab Revenue Leakage
Doctor orders labs. Patient goes wherever. If the doctor has a tie-up with a diagnostic center, every lab not directed there is revenue lost. This is fixable with one integration.

---

## What the Product Should Become

One WhatsApp voice note from the doctor → three outputs, not one.

**Output 1 — SOAP Note** *(already built)*
Structured clinical note, signed, filed.

**Output 2 — TPA Claim Packet** *(build next)*
- ICD-10 coded diagnoses
- Clinical justification for investigations ordered
- Co-morbidities documented
- Procedure codes
- Pre-filled TPA form, ready to submit
- Doctor signs the same way as the SOAP note

**Output 3 — Patient Care Continuation** *(partially built)*
- Prescription to patient WhatsApp ✅
- Directed lab order to partner diagnostic center
- Follow-up reminder at day 7 and day 30
- If patient doesn't confirm → doctor alert

---

## The Product in One Sentence

> Every Indian private specialist's consultation ends with one doctor signature that files the note, submits the insurance claim, sends the prescription, orders the labs, and books the follow-up — all before the next patient walks in.

---

## Why This Is the Right Vision

| Current | Right Product |
|---|---|
| Saves 3 min/patient on notes | Recovers ₹2–3 lakh/month in claim rejections |
| Doctor doesn't notice value | Doctor sees it in their bank account |
| Competes with clerk (₹15k/month) | Competes with nothing — no one does this end-to-end |
| ₹100–150/consultation | ₹500–2,000/consultation |
| Nice to have | Can't cancel |

---

## What to Build (in order)

### Phase 1 — Already done
- WhatsApp voice note → SOAP note
- SOAP → signed via no-login mobile link
- Prescription auto-dispatched to patient WhatsApp on sign
- Per-consultation billing records

### Phase 2 — TPA Revenue Recovery
**ICD-10 mapping layer**
The extraction engine already outputs canonical diagnoses ("Diabetes Mellitus," "Hypertension," "Ischemic Heart Disease"). Map these to ICD-10 codes — it is a lookup table. The diagnoses exist. The codes are public data. This is a weekend of work.

**TPA claim template generator**
Each major TPA (Star Health, United India, HDFC Ergo, New India, Care Health) has a standard pre-auth and claim form. Build one template per TPA. Fill from SOAP + facts. Tedious to build once, runs forever. Doctor signs once, claim goes out pre-coded.

### Phase 3 — Patient Retention Loop
**Directed lab ordering**
When investigations are extracted, show doctor "send to [partner lab]" alongside patient WhatsApp dispatch. Negotiate one referral tie-up with a diagnostic chain to start (Metropolis, Dr. Lal PathLabs have partner programs).

**Patient retention alert**
If patient doesn't reply to day-7 follow-up reminder, notify doctor. One notification = one return visit recovered = ₹1,000–3,000 revenue. That single feature is worth more to the doctor than the SOAP note.

---

## Pricing Implication

| Product | Price |
|---|---|
| Documentation only | ₹100–150/consultation |
| Documentation + TPA claim | ₹500–750/consultation |
| Full loop (doc + TPA + labs + follow-up) | ₹1,500–2,000/consultation |

At 20 patients/day on the full loop: ₹30,000–40,000/day per doctor. ₹7–10 lakh/month per doctor. Gross margin at scale: 85–90%.

---

## The Competitive Moat

Documentation quality → structured data → ICD-10 accuracy → fewer rejections → doctor economics improve → doctor can't leave without losing the TPA history and the patient follow-up chain.

Switching cost is not "they'll lose their notes." Switching cost is "they'll lose their claim accuracy score and their patient retention system." That is a real moat. Documentation alone is not.

---

## What This Is NOT

- Not an EMR / EHR (don't build the full patient record system — too slow, too capital-intensive)
- Not a pharmacy play (don't try to own the prescription dispensing)
- Not a telemedicine product (don't add video/chat — that's a different behavior)
- Not a B2G play (government hospitals cannot pay — ignore them for now)

The moat is: structured clinical data + downstream revenue recovery + patient retention. Everything else is distraction.

---

## Open Questions

- [ ] Which TPA to integrate first? (Star Health has largest network of empanelled doctors)
- [ ] Do we need a TPA portal login per doctor, or can we submit via API?
- [ ] What's the split between insurance and cash patients for our target doctor segment?
- [ ] Lab referral: commission model or fixed fee per dispatch?
- [ ] At what stage does the TPA claim story go into the YC application?

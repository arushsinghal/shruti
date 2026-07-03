# 19 — Service Pivot: From Tool to AI-Native Service

**Date:** 2026-06-30
**Status:** Decision made — executing
**Related:** [[18_YC_PITCH_STRATEGY]] · [[03_PRODUCT_STRATEGY]] · [[14_BUILD_PLAN]]

---

## The Core Shift

> Doctor never opens a dashboard. They get a WhatsApp message with a link to sign.

We are not building a co-pilot anymore. We are delivering an outcome.

The YC framing (AI native services companies): companies that **provide the outcome** vs. build a tool the customer uses internally. The tool is the smaller opportunity. The service is the generational one.

---

## What Changes vs. What We Already Have

| Layer | Current (tool) | Service |
|---|---|---|
| Input | Doctor opens app, pastes/records | Voice note to WhatsApp OR ambient phone recording |
| Processing | Already built ✅ | Same pipeline, runs automatically |
| QC | Doctor confirms facts on screen | Internal reviewer clears in 60 seconds |
| Output | Dashboard with SOAP + PDF | WhatsApp: "Ramesh Kumar note ready → [sign]" |
| Sign | Doctor clicks Sign Note in browser | Doctor taps link on phone, one-tap sign |
| Patient delivery | Doctor manually shares | Auto-sends prescription PDF to patient WhatsApp |
| Billing | ₹/month | ₹/consultation |

**The clinical engine doesn't change. We're wiring the service wrapper around it.**

---

## The 3-Person Operation (Pilot Phase)

1. **Arush** — sales, product, manual ops
2. **1 MBBS intern / trained transcriptionist** — QC reviewer
   - Gets internal dashboard: AI output + confidence score
   - High confidence (>85% of notes) → approve in 15 seconds
   - Low confidence → fix in 60 seconds
   - 1 person covers 150+ consultations/day
3. **Co-founder** — keeps building

This is not a software company anymore. It is an operation. The product is the operation.

---

## Build Sequence (3 Weeks)

### Week 1 — Minimum Viable Service
*Start with Dr. Narang tomorrow. Zero new code.*

1. Doctor sends voice note to Twilio WhatsApp number
2. Sarvam transcribes it (already wired)
3. Pipeline processes it (already works)
4. Reviewer gets Slack notification with output
5. Reviewer approves → doctor gets WhatsApp link → taps sign

Run manually for 5–10 pilot consultations. Validate the workflow before automating it.

### Week 2 — QC Dashboard
- Internal page: list of consultations, AI output, confidence score, approve/edit button
- Reviewer works from here instead of Slack
- Track: **time from voice note → note delivered** (primary SLA metric)

### Week 3 — Auto-Delivery
- On approval → auto-send WhatsApp to doctor with signing link
- On sign → auto-send prescription PDF to patient WhatsApp
- Per-consultation billing counter

---

## Technical Reality

**Zero changes to:**
- Sarvam ASR (voice → transcript) ✅
- Clinical extraction engine ✅
- SOAP generation ✅
- Prescription PDF ✅
- WhatsApp share to patient ✅

**3 pieces to wire together (~1 week total):**

1. **WhatsApp → auto-pipeline webhook** (1–2 days)
   - Voice note received → download audio → Sarvam → auto-create session → auto-process → ping reviewer
   - All individual steps exist. Writing the glue.

2. **QC reviewer dashboard** (1 day)
   - ~100-line React page talking to existing endpoints
   - Approve button triggers WhatsApp to doctor

3. **Mobile signing flow** (1 day)
   - Extend `/patient-download/` token route (already exists)
   - Instead of just PDF download: show SOAP + one-tap sign button
   - No login required — signed JWT proves identity

---

## Pricing

**Drop monthly subscriptions. Per consultation:**

| Tier | Price |
|---|---|
| Standard consultation | ₹75–100 |
| Complex (Cardiology, Neurology, etc.) | ₹150 |
| Pilot (first 50 consultations) | Free |

**Unit economics example — Dr. Narang:**
- 20 patients/day × ₹150 = ₹3,000/day
- ₹75,000/month from one doctor
- COGS: reviewer time + Sarvam ASR + infra ≈ ₹8,000/month
- Gross margin on one doctor: ~90%

**Pilot framing:** "First 50 consultations free. We prove it works, then we price." Zero friction to say yes.

**Never:** cost-plus pricing or straight-line undercutting. Price on value (vs. cost of a medical secretary: ₹25,000–40,000/month for far less).

---

## What to Say to Dr. Narang

Don't demo the browser.

> "Doctor, we're changing our model. You don't use a product — we handle your documentation. After each patient, your resident or you sends a 2-minute voice note to this WhatsApp number. Within 3 minutes you get a ready-to-sign note back on WhatsApp. For your OPD of 20 patients, that's 20 notes delivered while you're still in clinic. You approve them in 5 minutes. First 50 consultations on us — no tool to learn, nothing to install."

Then hand him the WhatsApp number. Say "try it right now with the last patient you just saw."

---

## Why We Fit the YC AI Services Framework

| YC Criterion | Lipi |
|---|---|
| Low trust (outcome not process) | ✅ Doctors want a signed note, not a tool |
| Low judgment at task level | ✅ 90% of documentation is mechanical. Physician sign-off is the narrow human-in-loop |
| High intelligence threshold | ✅ Hinglish + Indian clinical shorthand is genuinely hard. Not commoditized. |
| Regulation as moat | ✅ NMC number, DPDPA, prescription format requirements raise the bar for competitors |

**The TAM:** 70M+ consultations/month in India × ₹100/note = ₹7,000 crore/month addressable. This is the market that doesn't exist in software but exists in services.

---

## The Model Risk to Track

The YC video asks: *"Are you using humans because the work genuinely needs judgment, or to paper over product gaps?"*

**Honest answer right now: both.**
- Reviewer catches real edge cases (Hinglish ambiguity, medication dosing edge cases)
- Reviewer also covers current product gaps (low confidence scores on rare terminology)

**That's fine for the pilot.** The trajectory is what matters:
- As extraction confidence improves → reviewer touches fewer notes
- Gross margin improves automatically
- This is the **AI operating leverage** story: same revenue, falling COGS, margin approaching software levels

Track: % of notes auto-approved without reviewer edit. This is the single most important internal metric.

---

## Stickiness in the Service Model

Once a doctor has received 3 months of WhatsApp notes from us:
- Their patient records live inside Lipi (switching = starting from scratch)
- Their patients expect WhatsApp prescriptions (social lock-in)
- Their assistant's workflow runs through us (two-person dependency)
- The TPA claim PDFs are generated here (money loop lock-in)

The service model creates **stronger stickiness** than the tool model because the doctor never had to learn anything — they can't opt out of something they never opted into.

---

## Open Questions

- [ ] Do we need a separate Twilio number per doctor, or one shared inbox with doctor identification by sender number?
- [ ] Consent model: one-time onboarding consent vs. per-session — legal review needed
- [ ] QC reviewer hiring: MBBS intern vs. trained transcriptionist vs. experienced nurse?
- [ ] At what consultation volume does the reviewer become the bottleneck?
- [ ] Hospital-level contracts vs. individual doctor contracts (AIIMS angle)?

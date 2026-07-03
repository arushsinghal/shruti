# 18 — YC Pitch Strategy

> Last updated: 2026-06-30
> Status: Working draft — update as traction milestones hit

---

## The Honest Starting Point

Current YC odds without changes: **~25%**
Target: **70%+**
Gap: revenue, co-founder, product completeness, and the DHIS story landing cleanly.

---

## What YC Actually Is (Process)

YC does not take a slide deck. The process is:

1. **Written application** (~20 questions, answers capped at 150–250 words each)
2. **2-minute video** (founders introduce themselves, show product)
3. **10-minute interview** (if invited — fast Q&A, sometimes a quick demo)

The seed deck (10 slides) is for angels and seed investors *after* YC, not for YC itself. Prepare it in parallel but it is not the YC submission artifact.

---

## Probability Ladder

| Milestone                                    | Cumulative YC odds |
| -------------------------------------------- | ------------------ |
| Today (4 pilot doctors, no revenue)          | ~25%               |
| 3+ paying clinics (any price)                | ~50%               |
| Patient WhatsApp intake built + demo video   | ~55%               |
| ABDM live + one real DHIS transaction logged | ~60%               |
| Co-founder joins                             | ~70%               |
| One organic (non-network) doctor paying      | ~73%               |
| YC referral from known alum                  | ~78%               |

Revenue is the single biggest lever. Everything else is marginal by comparison.

---

## Revenue Strategy (Do This Week)

### Pricing right now (pre-ABDM)
**₹2,000/month flat per clinic.** No per-consult tracking, no complexity. Doctor pays via UPI standing instruction. You have MRR.

Do not do per-consult billing until ABDM is live. Reason: the compelling per-consult pitch is "₹20/consult, government pays back ₹7.50 via DHIS, net ₹12.50." Without DHIS flowing, the math doesn't land.

### Pricing after ABDM live
Switch to ₹20–50/consult depending on clinic size:
- Top specialists (your 4): ₹50/consult — 2% of their consultation fee, they don't notice
- Mid-tier specialists: ₹30/consult
- GPs charging ₹300/consult: ₹2,000/month flat is safer — per-consult eats 10%+ of revenue

### The net-zero pitch (only true after ABDM)
> "Pay ₹20/consult to Lipi. Government deposits ₹7.50/consult via DHIS for every ABDM-linked record. Net cost: ₹12.50 per consult — less than one chai per patient. A clinic doing 30 consults/day earns ₹67,500/month in DHIS income it wasn't earning before."

This is the most differentiated thing about Lipi. No AI scribe company outside India has a government subsidising their distribution.

---

## The Core Insight (Slide 4 in the seed deck)

This is the slide YC partners will remember. Every other AI scribe company has the problem, solution, product, and traction slides. Only Lipi has this:

**NHA pays the clinic ₹7.50/consult** via DHIS for every ABDM-linked health record.
**NHA pays Lipi ₹2.50/consult** as a registered DSC software partner.
**Clinic's net cost approaches ₹0** — government subsidises the adoption.
**Lock-in:** clinic only earns DHIS income when using ABDM v3 DSC-certified software. Switching to an uncertified competitor means losing that income stream entirely.

This creates a distribution mechanism no competitor has: government pays both the clinic and Lipi monthly, automatically, with a built-in switching cost.

---

## YC Written Application — Draft Answers

### "What does your company do?" (50 words)
> Lipi runs the OPD for Indian clinics. Doctor sends a 2-minute voice note after each consultation. We generate the clinical note, dispatch lab orders to the patient's WhatsApp, schedule follow-ups, collect payments, and file ABDM records — so the government deposits DHIS income into the clinic's bank account monthly.

### "What have you built?"
> Working product. WhatsApp voice note → structured SOAP note in under 60 seconds. Auto-dispatches lab orders and follow-up reminders to patients. FHIR R4 generation for ABDM compliance. Revenue dashboard showing DHIS pending claims, lab orders sent, and follow-ups confirmed. Live with 4 clinics including [Medanta chairman], [presidential surgeon], [top neurologist].

### "How do you make money?"
> ₹2,000/month per clinic today. Post-ABDM: shifting to ₹20/consult usage-based pricing. Additionally: ₹2.50/consult DHIS DSC income from NHA (paid to Lipi as registered DSC software), lab affiliate commissions, and Razorpay payment settlement fees. Multiple revenue streams activate from the same clinical record with zero additional work.

### "What is your monthly revenue?"
> [Fill in real number before submitting. Even ₹6,000 MRR is infinitely better than ₹0.]

### "Why is this a big market?"
> India has 100M+ OPD visits per month and 600,000 registered doctors. Every clinic documents manually today. The government's ABDM mandate requires digitisation by 2027 — and pays clinics ₹7.50/consult to do it. We are distribution-subsidised by government policy. The US AI scribe market ($3B+) is the floor; India's OPD volume is 4x larger.

### "Why you?"
> [Write this last. Should include: personal connection to the problem, specific insight about DHIS that came from reading the ABDM compliance docs, why Indian doctors specifically, and what you've already done that proves you can execute.]

### "What do you understand about your market that others don't?"
> Indian doctors don't need another app. They need their existing WhatsApp workflow to become intelligent. Every solution that requires doctors to open a new app fails. We work inside WhatsApp — the only interface Indian doctors already use 100% of the time. Second: the government is actively paying to subsidise ABDM adoption via DHIS. Building a DSC-certified product means NHA funds our customer acquisition. No competitor has understood this as a distribution mechanism.

---

## YC Video Script — 2 Minutes Exactly

**0:00–0:20 — Hook**
"I'm Arush. Indian doctors waste 45 minutes every day on paperwork. For a doctor seeing 30 patients, that's 15 consultations they never see. We built Lipi to give that time back — and to make the clinic earn money in the process."

**0:20–0:50 — Product demo (screen record)**
Show: doctor sends a voice note on WhatsApp → SOAP note appears in 45 seconds → lab order dispatched to patient's WhatsApp → follow-up reminder scheduled → revenue dashboard shows DHIS pending claim. Real product, real speed, no mockups.

**0:50–1:10 — Traction**
"We're live with [Medanta chairman name and title], [presidential surgeon name and title], and [top neurologist name and title]. [X] consultations processed. [Y] lab orders dispatched to patients."

**1:10–1:40 — The insight**
"The key thing most people miss: Indian government pays clinics ₹7.50 per ABDM-linked consultation via DHIS. They pay us ₹2.50/consult as the DSC software. Clinic's net cost approaches zero. And a clinic that switches to uncertified software loses that income permanently. No AI scribe company outside India has this."

**1:40–2:00 — Ask**
"We're applying to YC to complete ABDM integration, sign 50 paying clinics, and prove the government-subsidised distribution model at scale."

Film in one take. iPhone is fine. No editing, no music, no graphics. YC prefers raw over polished.

---

## Seed Deck — 10 Slides (for angels after YC)

### Slide 1 — Title
**Lipi** — AI-native OPD service for India
[Name] [Email] [Date]

### Slide 2 — Problem
Indian doctor spends 45 min/day on paperwork. 600,000 doctors. 4.5 crore hours lost daily across India.
- No structured clinical records
- Lab orders coordinated by phone call
- Follow-ups missed (no system)
- ABDM mandate ignored (complex, no incentive)
- Insurance pre-auth = weeks of phone calls

### Slide 3 — Solution (3 columns)
Doctor sends 1 voice note. Lipi does everything else.

| Capture | Dispatch | Revenue |
|---|---|---|
| SOAP in 60 sec | Lab orders → patient WhatsApp | ABDM filed |
| Zero new apps | Follow-up reminders | DHIS income deposited |
| Works on existing WhatsApp | Payment link sent | Razorpay settlement |

### Slide 4 — The Government Pays (most important slide)
[Diagram: Doctor → Consultation → Lipi → ABDM → NHA → DHIS payment back to clinic + DSC payment to Lipi]

- NHA pays clinic **₹7.50/consult** via DHIS for every ABDM-linked record
- NHA pays Lipi **₹2.50/consult** as registered DSC software
- Clinic earning 30 consults/day = **₹67,500/month in new DHIS income**
- **Lock-in:** switching to uncertified software = losing this income permanently
- No US or global AI scribe company has government-subsidised distribution

### Slide 5 — Product
Screenshots: WhatsApp voice note intake → SOAP note → lab dispatch → patient portal → revenue dashboard. Real product. No mockups.

### Slide 6 — Traction
- **4 clinics live** including [Medanta chairman], [presidential surgeon], [top neurologist]
- **[X] consultations** processed
- **[X] lab orders** dispatched to patients
- **₹[X] MRR**
- [X]% month-over-month growth

### Slide 7 — Business Model
| Revenue stream | Timing | Rate |
|---|---|---|
| Clinic subscription | Now | ₹2,000/month |
| Per-consult fee | Post-ABDM | ₹20/consult |
| DHIS DSC income (from NHA) | Post-ABDM | ₹2.50/consult |
| Lab affiliate commission | Post-YC | ~₹50–200/order |
| Payment settlement fee | Post-YC | 0.5–1% |

All revenue streams activate from the same clinical record. Zero marginal cost per additional stream.

### Slide 8 — Market
- 600,000 registered doctors in India
- 100M+ OPD visits per month
- Government ABDM mandate → all clinics must digitise by 2027
- **TAM:** ₹3,600 crore/year at ₹50/consult at current OPD volume
- Expansion: Bangladesh, Sri Lanka, Indonesia — same FHIR-based national health stack

### Slide 9 — Team
[Photo + 2-3 lines each. If solo: be honest, say you're looking for co-founder, show what you've built solo as evidence of speed.]

### Slide 10 — Ask
Raising ₹[X] at [valuation].

Use of funds:
- ABDM v3 integration and production go-live (month 1–3)
- 50 paying clinics signed (month 3–6)
- 3 hires: 1 ops/sales, 1 backend engineer, 1 clinic success (month 2–5)

---

## What to Build Before YC (ordered by impact)

### Code (Claude builds):
1. ✅ **Patient WhatsApp intake** — BUILT. Patient texts clinic code → Lipi collects name, age, chief complaint, medications → sends doctor pre-visit brief. State machine: awaiting_clinic_code → awaiting_name → awaiting_age → awaiting_complaint → awaiting_medications → complete.
2. ✅ **Self-serve clinic onboarding** — BUILT. 3-step flow: NMC + specialty → clinic details + WhatsApp number → "You're live" screen with clinic code. Zero Arush involvement needed.
3. ✅ **Monthly value report** — BUILT. Background loop fires on 1st of each month per doctor: consults, labs, follow-ups, hours saved, DHIS income. Non-fatal — skips if doctor has no WhatsApp or zero consults.
4. ✅ **Appointment booking via WhatsApp** — BUILT. Patient texts "book" → sees 5 next available slots → picks one → doctor notified. Doctor sets availability in DoctorProfile (day/time/slot duration).
5. ✅ **Landing page** — "scribe" removed. Says "AI-native OPD service" throughout.
6. **Full ABDM pipeline** (Tasks 22–31) — after sandbox credentials received.
7. **Per-consult billing tracker** — after ABDM live, switch from flat to usage-based.

### Arush does:
1. Charge the 4 doctors ₹2,000/month — do this this week
2. Register on sandbox.abdm.gov.in → get ABDM credentials
3. Find co-founder (ops/hospital background or strong engineer)
4. Post demo in one IMA WhatsApp group → get one organic paying clinic
5. Ask Medanta chairman if he knows a YC founder → get referral
6. Film 2-min demo video with one real doctor using Lipi

---

## Positioning — What to Say vs. Not Say

| Say | Don't say |
|---|---|
| "AI-native OPD service" | "AI scribe" |
| "Runs the clinic's OPD operations" | "Documentation tool" |
| "Government subsidises our distribution" | "We're ABDM compliant" |
| "Net cost approaches ₹0 after DHIS" | "We save doctors time" (too generic) |
| "Clinic loses DHIS income if they switch" | "We have strong retention" |
| "WhatsApp-native, zero behavior change" | "Easy to use" |

---

## Open Questions to Resolve Before Submitting

- [ ] Real MRR number (convert pilots to paying)
- [ ] Co-founder decision (solo or find one)
- [ ] ABDM sandbox credentials obtained
- [ ] Demo video filmed with real named doctor
- [ ] YC referral secured (ask the top 4 doctors)
- [ ] One organic (non-network) paying clinic

---

## Related Docs
- [[17_ABDM_DHIS_DSC_COMPLIANCE]] — full DHIS/ABDM technical spec
- [[09_STRATEGIC_ROADMAP]] — broader product roadmap
- [[03_PRODUCT_STRATEGY]] — positioning and north star
- [[14_BUILD_PLAN]] — what's built vs. what's pending

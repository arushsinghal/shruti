# Lipi — Roadmap, VC Strategy & AI Model Arsenal

## Is it demo ready?

**Mostly yes.** The full pipeline works end-to-end (validated 2026-06-28):
- Hinglish voice → 25 extracted facts (zero-LLM, deterministic)
- Doctor confirms in one click → SOAP generates from confirmed facts only
- Investigation order PDF with doctor letterhead and MCI number
- FHIR R4 ABDM bundle (20 resources per consultation)
- Work queue auto-creates 4 tasks post-consultation

**One bug fixed (2026-06-28):** Allergy negation false positive — "Koi drug allergy nahi hai" was incorrectly extracting `drug` as an allergen. Fixed in `clinical_extractor.py:_extract_allergies` by calling `_is_negated()` before appending.

---

## Valuation — honest benchmark

**Current stage:** Pre-revenue, working product, LOIs from top Indian surgeons, zero paying customers.

- India seed, pre-revenue: **₹8–15 Cr pre-money (~$1–1.8M)**
- Tier-1 US/global VC (deep-tech AI health framing): **$3–6M pre-money**
- With first paying customer: add $1–2M to either range

**Do not approach VCs before converting one LOI to paid.** One ₹1,499/mo invoice changes the conversation from "prototype" to "company."

---

## What moves the number — ordered by impact

### 1. First paying customer (this week)
Convert one LOI. Don't negotiate, don't build more features. One paid invoice changes your VC narrative completely.

### 2. The Medanta chairman story
Dr. Anil Bhan at Medanta using Lipi live = clinical validation most India health-AI startups would spend $500K to acquire. Frame it as: "5 consultations under Dr. Bhan's supervision." Worth a 2–3x multiplier if credible.

### 3. Cost story — 40x margin
- Cost: ₹2.50/consultation (Sarvam ASR only)
- Price: ₹100/consultation or ₹1,499/mo
- This is the business model slide. Say: *"₹2.50 cost, ₹100 price, zero humans in the loop after doctor's one confirmation click."*

### 4. ABDM compliance as regulatory moat
Lipi generates valid HL7 FHIR R4 bundles with NRCES NHA profiles today. When Ayushman Bharat Digital Mission mandates ABDM-compliant records, Lipi is the only scribe that's already ready.

### 5. The demo — record a live consultation
30-minute session with Dr. Bhan or Dr. Sawhney, with consent, recorded. Doctor speaks Hindi, Lipi extracts 20+ facts in real-time, doctor clicks confirm, investigation order PDF appears with his letterhead ready to hand to the patient. This video is worth more than any deck.

---

## VC questions — pre-prepared answers

**"Why can't GPT-4 just do this?"**
It can't guarantee zero hallucination. Every fact in Lipi's SOAP traces to the exact sentence in the transcript (evidence spans). GPT-4 can't show you *why* it said "metformin 500mg." In clinical settings, accountability requires provenance — that's a regulatory constraint, not a preference.

**"What stops Google/Anthropic from shipping this in 6 months?"**
Hinglish extraction is trained on real Indian OPD vocabulary that doesn't exist in public datasets. Our ontology (Dr. Bhan's cardiac cases, Dr. Gupta's neurology cases) is proprietary. Plus ABDM compliance and MCI verification are India-specific moats. Big Tech will build a generic scribe. Not a Hinglish-specific, ABDM-compliant, zero-hallucination one.

**"What's the learning flywheel?"**
Every doctor correction goes into the confidence system. After 3 doctors at 3 clinics confirm the same pattern, it auto-promotes to global knowledge. The system gets better the more doctors use it, at zero marginal training cost.

---

## AI Model Arsenal — where each model earns its keep

The core moat is **zero-LLM extraction** (transcript → facts). This must stay deterministic.
Everything **after the doctor's confirmation click** can use any model — those outputs are labeled "AI suggestion", not "extracted fact", and they build on confirmed ground truth.

| Stage | Model | Rationale |
|---|---|---|
| Extraction (transcript → facts) | **None (deterministic)** | The moat. Keyword + fuzzy + regex. Zero hallucination claim holds. |
| Differential diagnosis (post-confirmation) | **Claude Opus 4.8** | Highest clinical reasoning. Given confirmed vitals + symptoms + diagnoses, generate 2-3 differentials with red-flag warnings. Labeled "AI suggestion, review required." |
| Insurance pre-auth letter draft | **Claude Sonnet 4.6** | After confirmed SOAP, draft Star Health / ICICI Lombard pre-auth in required format. Facts are ground truth, letter is formatting. |
| Patient WhatsApp summary (Hindi) | **Gemini 2.5 Flash** | Speed matters. Post-confirmation, 3-line patient summary: "Aapki taklif X hai, Y le lo, Z din mein aana." |
| Synthetic training data (offline) | **Claude Opus 4.8** | Generate 10,000 Hindi/Hinglish transcripts to expand extraction ontology. Run offline, never in live pipeline. |
| WhatsApp ASR | **Sarvam AI** | ₹2.50/consultation, best Hinglish accuracy in market |
| Hindi TTS (WhatsApp voice replies) | **Sarvam Bulbul** | Natural-sounding Hindi voice output |

**The pitch line:** "Our extraction is zero-LLM and deterministic. Once the doctor confirms the facts, we use Claude Opus for differential diagnosis and Gemini for patient communication — so AI only ever operates on confirmed ground truth, never raw speech."

---

## In-Hospital Service Rails — the lock-in play

**The insight no one else has articulated:** Once Lipi extracts "ECG, X-Ray, HbA1c" from the consultation, that data is structured in a FHIR ServiceRequest. Today it prints as paper. The patient walks it to three separate counters. Lipi can close that loop entirely.

**Zero-Friction Care Loop:**
```
Doctor orders investigations in Lipi
     ↓ auto-dispatched as FHIR ServiceRequest
Lab system receives → generates queue token
     ↓ WhatsApp to patient
"Your slot: 11:20am. Token #47. Pay here: [UPI link]"
     ↓ patient pays on phone
No payment counter. No registration counter. Go straight to lab.
     ↓ lab uploads results
Results appear in Lipi session. Doctor reviews in same screen.
```

**What this does to YC positioning:**
- Each button in the Lipi UI corresponds to a human job eliminated: transcriptionist, Rx writer, patient educator, lab registration clerk, cashier, EMR data entry operator
- The per-consultation cost to a private clinic (transcription + Rx + lab admin + EMR) is ₹900–4,000 today
- Lipi replaces all of it for ₹20/month flat
- Once the lab token system runs through Lipi, switching cost becomes infrastructure-level — same reason hospitals don't change their HIS

**Architecture note — already 80% built:**
- FHIR ServiceRequest resources are already in the existing bundle
- WhatsApp channel is already building (Phase 2 dev)
- Razorpay is already planning
- Adds: lab webhook dispatch endpoint, patient token notification, results ingestion — ~10 days total

**Pitch line for YC:**
> "Every consultation generates a paper investigation slip, a trip to the payment counter, a trip to lab registration, and a manual entry into the EMR. Lipi removes all four — the lab receives the order digitally, the patient gets a WhatsApp token and pays on their phone, the result comes back into the same session. One consultation, zero paper, zero queues."

---

## Highest-Leverage Improvements

### This week (before any VC meeting)

| # | What | Effort | Impact |
|---|---|---|---|
| 1 | Get one doctor to pay | 0 engineering | Highest — changes valuation narrative |
| 2 | Differential diagnosis with Claude Opus 4.8 | 2 days | Adds "deep AI" story on top of zero-LLM moat |
| 3 | ~~Allergy negation fix~~ | Done 2026-06-28 | Demo-safe |

### Next 2 weeks (the Gustaf / YC demo)

| # | What | Effort | Impact |
|---|---|---|---|
| 4 | WhatsApp native flow | 1 week | The demo: doctor speaks → investigation order back via WhatsApp, zero login |
| 5 | Per-consultation billing (Razorpay) | 3 days | Enables "service company" story, ₹50/consultation |

### Design — the weakest layer, must fix before demo

**Updated 2026-06-28:** Frontend design is currently the most underdeveloped part of the product. The clinical pipeline is strong; the UI does not match that quality. Every screen a doctor or YC partner sees needs to look like a professional medical tool, not a prototype.

**Priority design screens (all must be done before the Dr. Bhan video):**

| Screen | Problem | Fix needed |
|--------|---------|------------|
| Review & Sign Note | Functional but not clinical-grade. Grounded fact cards exist but page feels like a web app. | Medical typography, trust-signal visual hierarchy, clearer approve/reject affordance |
| SOAP Document display | Text in a card. Dr. Bhan needs to feel he's signing a real medical record. | Section headers, clinical font sizing, document-like layout, print CSS |
| Consultation page recap cards | Crowded. Presenting With / Vitals / Assessment / Medications / Investigations need to scan in 2 seconds. | Better visual weight, spacing, color coding per category |
| Mobile / tablet view | Unverified. Indian OPD doctors are not at desks. If this breaks on a 6-inch phone, the product doesn't work. | Full responsive pass on Consultation + Review pages |
| मरीज पर्ची (patient slip) | Patient takes this home or receives on WhatsApp. Must look like a real prescription slip. | Card design: patient name, diagnosis in Hindi, medications, follow-up date, doctor stamp |
| Dashboard empty state | New doctor sees nothing before first consultation. Demo-killing. | Empty state illustration + "Start your first consultation" CTA |
| Loading states | 3–5 second processing gap with no feedback. User doesn't know what's happening. | "Finding symptoms… medications… vitals…" extraction progress indicator |
| Referral & Discharge outputs | Printed documents. Need letterhead template, clean hierarchy. | Document design with clinic branding, proper print CSS |

**Effort:** 4–5 days total design + implementation. Not optional — this is the demo screen.

---

## Demo Script (to reproduce the full pipeline)

```
1. Login → New Consultation → patient: "Ramesh Kumar", mode: Health
2. Paste transcript (Hindi/Hinglish with symptoms, meds, vitals, investigations)
3. POST /sessions/{id}/process-clinical → 25 candidate facts extracted
4. Review page → confirm/reject each fact → SOAP populates live
5. Header → "Investigation Order" → new tab, printable PDF with doctor letterhead
6. /tasks → 4 auto-created work items, "View Order" on investigation task
7. GET /sessions/{id}/fhir → 20-resource ABDM bundle (gates on all facts reviewed)
```

**Test credentials:** `testdoc` / `testpass123` (Dr. Arush Singhal, Singhal Multispeciality Clinic, MCI-DL-123456)

---

## Architecture Reminder — the safety guarantee

```
Transcript
    ↓ [zero-LLM: keyword + fuzzy + regex]
Candidate Facts (all start as "candidate")
    ↓ [SOAP is empty until here]
Doctor's one confirmation click  ← THE SAFETY GATE
    ↓
Confirmed Facts
    ↓                    ↓                      ↓
SOAP (deterministic)  Investigation Order  FHIR ABDM Bundle
    ↓
[POST-GATE ONLY] Claude Opus → Differential Diagnosis (labeled AI suggestion)
[POST-GATE ONLY] Gemini Flash → Patient WhatsApp summary in Hindi
```

Prior patient history (from `patient_memory` table) is stored separately in `prior_context` — it NEVER merges into the current-visit SOAP. Enforced by structural incompatibility: `current_state.medications` is a dict, `prior_context.medications` is a list.

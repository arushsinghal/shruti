# Strategic Roadmap — From Scribe to AI-Native Healthcare Services Company

> **Date:** 2026-06-26
> **Context:** Gustaf Alströmer (YC) RFS on healthcare administration. Eka.Care is the primary competitor at ₹1,499/mo for AI scribe. Our extraction pipeline is fully deterministic (zero LLM, zero hallucination, ₹2.50/consultation).

---

## Core Positioning

**We are NOT a scribe company. We are a healthcare document automation company.**

The doctor speaks once. We produce every document that consultation generates — SOAP note, prescription, lab orders, referral letter, insurance claim, discharge summary, MRD coding. All from one audio input. All deterministic. All with provenance.

> "Lipi turns one doctor consultation into every document the clinic needs — prescription, lab orders, referral, insurance claim, discharge summary. Speak once, sign everything."

---

## Why Not Compete With Eka on Scribe

| | Eka | Lipi |
|---|---|---|
| What they are | Platform (EMR + EHR + ABDM + scribe) | Workflow tool (speak → all documents) |
| Business model | Get doctors onto their ecosystem | Eliminate 3 hours of daily paperwork |
| Extraction | LLM-based (can hallucinate) | Deterministic (cannot hallucinate) |
| Requires | Full practice migration | Nothing — just speak |
| Competes with | Practo, every EMR | The assistant's pen and paper |
| Funding | $40M+, NVIDIA partnership | Bootstrapped |
| Pricing | ₹1,499/mo (scribe only) | ₹999-4,999/mo (scribe → full admin) |

**Eka says:** "Move your entire practice onto our platform."
**We say:** "Keep whatever system you use. Just speak for 5 minutes."

---

## Three Phases

### Phase 1: Wedge In (Now → Month 3)

**Identity:** Free/cheap scribe that doctors try because it's simple.

**Actions:**
- Give SOAP away at ₹999/month or free (5 consults/day)
- Only goal: get into 20-30 clinics
- Don't sell features — sell the demo: "speak 5 minutes, get signed prescription"
- Target doctors whose assistants are overloaded, not tech-savvy doctors wanting an app
- No app download, no EMR migration, no ABDM setup — just PWA on existing phone

**Differentiation from Eka:**
- Zero setup friction (vs Eka's full platform onboarding)
- Zero hallucination guarantee
- Evidence provenance on every extracted fact

**Revenue:** ₹999/mo × 20-30 doctors = ₹20K-30K MRR

---

### Design Sprint — Before Any Demo (2026-06-28 addition)

**Frontend design is currently the weakest layer of the product.** The extraction pipeline, FHIR bundle, CDS, and doctor gate are all strong. The UI does not match that quality. A YC partner or Dr. Bhan looking at the screen right now sees a functional prototype, not a clinical-grade product.

**This is not optional polish.** Design is on the critical path for two reasons:
1. The Dr. Bhan video (worth +8pp YC probability) must show a UI that looks like something a senior cardiologist would trust
2. Doctor adoption in early clinics depends entirely on the review screen feeling safe and fast — not like a web demo

**8 screens that need design work before the demo:**

1. **Review & Sign Note page** — the doctor's primary surface. Grounded fact cards exist but the page lacks clinical visual authority. Needs: medical typography, color-coded category badges with more visual weight, clearer ✗ rejection, better source quote styling.

2. **SOAP Document display** — currently text in a card. Must look like a real medical record the doctor is signing. Needs: S/O/A/P section headers with clinical formatting, document-like white background, print CSS that outputs a clean PDF.

3. **Consultation page recap cards** — Presenting With / Vitals / Assessment / Medications / Investigations need to scan in under 2 seconds. Currently cramped. Needs: visual hierarchy, spacing, per-category color coding consistent with Review page.

4. **Mobile / tablet view** — completely unverified. Indian OPD doctors are on phones. If Consultation + Review pages break on a 375px screen, the product doesn't work for 80% of target users.

5. **मरीज पर्ची (patient slip)** — patient receives this on WhatsApp or as printout. Must look like a real prescription receipt: patient name, diagnosis in Hindi, medications with dosage, follow-up date, doctor stamp. Currently unknown output quality.

6. **Dashboard empty state** — first-time doctor sees a blank screen. Kills demos. Needs: empty state illustration, "Start your first consultation" primary CTA, quick tip on what Lipi does.

7. **Loading / extraction progress** — 3–5 second gap between transcript submit and facts appearing. No feedback currently. Needs: "Finding symptoms… medications… vitals…" animated progress so doctor knows the pipeline is working.

8. **Referral letter & Discharge summary output** — these get printed or emailed. Need letterhead template, clean font hierarchy, proper print CSS.

**Effort: 4–5 days total. Must be done before any live demo or video recording.**

---

### Phase 2: Own the Paper (Months 3-9)

**Identity:** The thing that produces every document after a consultation.

**Build in this order** (each builds on the previous):

1. **Investigation order forms** — Already extract investigations. Template-fill a lab requisition PDF. ~1 week.
2. **Referral letters** — Component exists. Add doctor letterhead template + patient history summary. ~1 week.
3. **Insurance pre-auth forms** — Pick ONE TPA first (Star Health or ICICI Lombard). Map extracted data to their form fields. ~2-3 weeks. **This is the money feature.**
4. **Discharge summaries** — Aggregate multi-visit SOAP into one document. ~2-3 weeks.

**Pricing shift:** ₹2,999-4,999/month
- No longer selling "transcription"
- Selling "your assistant finishes 2 hours early every day"

**Why Eka can't follow:**
- LLM hallucination on an insurance form → claim rejected → doctor loses money → trust destroyed
- Our deterministic extraction + evidence provenance = every field on every form traces back to the transcript
- Insurance companies will require this audit trail
- Our learning flywheel means every cardiologist's corrections benefit every other cardiologist

**Revenue:** ₹3,999/mo × 50-100 doctors = ₹2-4L MRR

---

### Phase 2.5: In-Hospital Service Rails (Months 6-9)

**Identity:** The operating layer the hospital runs on, not the tool doctors use.

**The insight:** Once Lipi is in a hospital, the investigation order is already structured (ECG, X-Ray, blood tests extracted and in the FHIR bundle). Today that data prints as a paper slip. The patient takes it to three different counters: lab registration → payment counter → lab collection. Each counter has a queue.

**Zero-Friction Care Loop** — what this phase builds:

```
Doctor orders "ECG, X-Ray, HbA1c" in Lipi
         ↓
[Lipi dispatches FHIR ServiceRequest to lab system]
         ↓
Patient's WhatsApp: "Lab token #47. Your slot: 11:20am. Pay here: [UPI link]"
         ↓
Patient pays on phone (no payment counter queue)
Patient goes directly to lab (no registration counter)
         ↓
Lab uploads results → appear in Lipi session automatically
Doctor reviews results in same Lipi session
```

**Three components to build:**

| Component | What it does | Effort | Builds on |
|-----------|-------------|--------|-----------|
| Lab dispatch endpoint | POST /sessions/{id}/lab-dispatch → sends FHIR ServiceRequest to lab LIS via webhook | 3 days | Existing FHIR bundle (ServiceRequest already in it) |
| Patient digital token | Generates queue token, sends to patient phone via WhatsApp with slot time | 2 days | Existing WhatsApp flow |
| Payment at dispatch | Razorpay UPI QR / payment link embedded in lab notification | 2 days | Existing Razorpay integration |
| Results ingestion | Lab POSTs results back → attach to session, alert doctor | 3 days | Existing session storage |

**Why this creates lock-in:**
Once the hospital lab's token system runs through Lipi, you cannot rip out Lipi without disrupting lab operations. This is infrastructure-level switching cost — the same reason hospitals don't change their HIS systems. We get there without asking them to migrate anything.

**Patient journey: before vs after**

| Step | Today (paper slip) | With Lipi rails |
|------|-------------------|-----------------|
| 1 | Take paper to lab registration counter | Nothing — order dispatched automatically |
| 2 | Queue at registration (10-20 min) | Phone notification with token + UPI link |
| 3 | Go to payment counter | Pay on phone (30 sec) |
| 4 | Queue at payment (10-20 min) | Done |
| 5 | Return to lab with token | Go directly to lab at slot time |
| 6 | Wait for tests | Wait for tests |

**3 steps → 1 step for the patient. 0 paper. 0 separate queues.**

**Revenue model shift:**
- Per-lab-dispatch fee: ₹5-10 per order (hospital passes this on as convenience fee)
- Payment processing: 0.5% of Razorpay volume flows through Lipi
- This is transactional revenue on top of subscription — recurring whether or not the doctor uses the scribe

**Why this is defensible:**
Eka can't follow. They're a platform company — adding hospital operations rails means building relationships with 500 different lab LIS vendors, training ops staff, handling payment disputes. That's a services company, not a SaaS company. Lipi is already building in this direction.

---

### Phase 3: Become the Service (Months 9-18)

**Identity:** AI-native healthcare services company (Gustaf's vision).

Stop selling software. Start selling outcomes:

| Service | What we do | Revenue model |
|---------|-------------|---------------|
| Insurance claim filing | Auto-generate + submit claims to TPAs | % of claim value (2-5%) |
| Revenue cycle management | Track claim status, flag rejections, resubmit | Monthly retainer |
| Compliance documentation | Auto-generate NABH/JCI audit docs | Per-hospital contract |
| Multi-clinic analytics | Aggregate clinical patterns across network | Data licensing (anonymized) |

**The math:** A 20-doctor clinic spends ₹2-5L/month on admin staff doing this work. We do it for ₹50K-1L/month.

**Why Eka can't follow here:**
- Eka is a SaaS platform company
- Becoming a services company = hiring ops, building TPA relationships, handling claim rejections
- That's a different company with different DNA
- They would have to fundamentally change their business model

**Revenue:** ₹50K-1L/mo × 10-20 clinic chains = ₹5-20L MRR

---

## Differentiation Stack

```
Phase 1: Same market as Eka, but simpler + cheaper + no hallucination
     ↓
Phase 2: Different market entirely (documents, not transcription)
     ↓
Phase 3: Eka would need to become a services company to compete
```

---

## Who Pays and Why

| Customer | What they pay for | Price tolerance |
|----------|-------------------|----------------|
| Solo doctor | "I don't want to type" (scribe) | ₹1,000-1,500/mo |
| Doctor + assistant | "Eliminate 3 hours of paperwork" (admin) | ₹3,000-5,000/mo |
| Clinic chain (5-20 docs) | "Standardize all docs + insurance" | ₹15,000-50,000/mo |
| Hospital | "Auto-generate insurance claims, reduce rejections" | ₹1-5L/mo |

We start at row 1 to get in the door. The money is in rows 2-4.

---

## Cost Structure (After Diarization Removal)

| Component | Cost per consultation |
|-----------|---------------------|
| Sarvam ASR (₹30/hr × 5 min) | ₹2.50 |
| Clinical extraction | ₹0 (deterministic, local) |
| SOAP generation | ₹0 (Python templates, no Gemini) |
| CDS alerts | ₹0 (rule-based) |
| ICD-10 coding | ₹0 (local mapper) |
| **Total** | **₹2.50** |

**Monthly at 30 patients/day:** ₹1,875

**With IndicWhisper (free, untested):** ₹0 → monthly floor = ₹200 hosting only

**Break-even pricing:** ₹1,999/mo (Sarvam) or ₹499/mo (IndicWhisper)

---

## Technical Moats

1. **Deterministic extraction** — zero hallucination by architecture, not prompt engineering
2. **Evidence provenance** — every fact has `{start_char, end_char, source_sentence}`. No proof = no fact.
3. **Learning flywheel** — doctor corrections → Bayesian confidence → auto-promoted at 0.9 + 3 clinics + 3 confirmations → all doctors benefit. **Verified 2026-07-02: this is the intended mechanism, not current reality.** The `extraction_knowledge`/`fact_corrections` tables exist and `reload_knowledge()` runs at startup, but the live doctor review endpoint (`routes_fact_review.py`) does not call `record_correction()`/`record_false_positive()` anywhere — confirmed by direct grep, zero matches. No live doctor correction currently reaches the flywheel. See `16_FULL_APP_REVIEW.md`'s F2 status for the full picture. Do not claim this moat as operational externally until the review endpoint is wired.
4. **Hindi/Hinglish keyword maps** — hand-curated, not available in any open-source library
5. **$0 extraction cost** — allows pricing that LLM-based competitors structurally cannot match
6. **PHI-free knowledge base** — learning flywheel stores vocabulary facts, not patient data

---

## The One Thing To Do This Week

**Sit in one OPD for one full day.** Not to demo Lipi. To watch.

Bring a notebook and write down:
1. Every document the assistant produces after each consultation
2. How many minutes each document takes
3. Which documents cause the most frustration
4. Which documents involve calling insurance companies

That notebook is the product roadmap, pricing model, and pitch deck in one.

**Don't decide from the laptop. Decide from the clinic.**

---

## Eka Intel

- **EkaScribe Pro:** ₹1,499/month, unlimited consultations
- **EkaScribe Free:** 5 consultations/day
- **Eka Doc Pro (full EMR):** ₹18,749/year (~₹1,563/mo)
- **Eka Clinic Pro:** ₹1,00,000/year (5 doctors + 15 staff)
- **Model:** Parrotlet (5B params, Whisper V3 Large encoder + medical decoder, trained on 100+ hrs Indian medical speech from 5 medical colleges)
- **NVIDIA partnership** for offline model
- **~100K doctors on platform** (total, mostly EMR — scribe paying users likely <1%)
- **India has 800K active OPD doctors** — 99%+ untouched

---

## Links

- [[01_CURRENT_STATE]] — What's built today
- [[02_ARCHITECTURE_MAP]] — Technical architecture
- [[04_COMPETITORS]] — Competitive landscape
- [[06_API_COSTS]] — Cost analysis
- [[10_CONTINUAL_LEARNING_SYSTEM]] — Future research direction for evidence-grounded continual learning
- [[12_IMPLEMENTATION_GAP_REGISTER]] — Current built/not-built register and priority order
- [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]] - YC/research framing for on-the-job learning service agents
- [[16_FULL_APP_REVIEW]] — verified current status of the flywheel and other "moat" claims against running code
- [[21_FRONTIER_RESEARCH_DIRECTIONS]] — read before any "should we become a medical AI research company" framing; has the safe-claim discipline this roadmap follows
- [[FLYWHEEL_DESIGN]] — Learning flywheel details
- [[TECHNICAL_SPEC]] — Full technical specification

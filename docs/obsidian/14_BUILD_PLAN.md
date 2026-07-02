# Build Plan — YC-Ready Backlog

> Date: 2026-06-27 (revised)
> Status: Active — ordered for maximum YC chance
> **Verified against running code 2026-07-02 — two sections below conflict with current architecture, see notes inline at "Model Routing Rule" and "Block 0.1":** (1) GLiNER is not wired into the production extraction path at all right now (`routes_notes.py` bypasses it entirely) — Block 0.1's "60 → 78/100" plan assumes a GLiNER classification layer that doesn't currently run in production. (2) "SOAP formatting: Gemini Flash" contradicts the current zero-Gemini-in-extraction/SOAP policy confirmed 2026-07-02 — `soap_generator.py` is 100% rule-based today, and a Gemini-enhancement attempt was added and then deliberately reverted this session. Read `02_ARCHITECTURE_MAP.md`'s "Current Implementation Pointers" section before treating this build plan as current state.
> Traction assumption: ₹10k+/month MRR handled externally. Domain co-founder handled externally.
> Related: [[00_HOME]], [[03_PRODUCT_STRATEGY]], [[09_STRATEGIC_ROADMAP]], [[10_CONTINUAL_LEARNING_SYSTEM]], [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]], [[12_IMPLEMENTATION_GAP_REGISTER]], [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

---

## The Non-Negotiable Framing

Lipi must not become a company that calls APIs and orchestrates LLMs.

The extraction pipeline is the technical moat: deterministic Python, zero LLM, hand-curated Hinglish semantic maps. Preserve it. Never replace it with a generative model call for "better extraction." Doing so destroys the zero-hallucination architectural guarantee and makes every clinical output unauditable.

Gustaf Alströmer's AI-native service company framing fits Lipi exactly — healthcare administration is explicitly called out. But to claim it in a YC application, the product must actually do the work downstream, not just assist. The SOAP note is capture. Investigation orders, patient messages, work queue, and pre-auth — that is the service.

---

## Model Routing Rule

**In Claude Code development:**
- Opus: architecture decisions, safety boundary design, learning system design, anything hard to reverse
- Sonnet: implementation, feature code, tests, UI, debugging

**In the product itself:**
- Clinical extraction: zero LLM, deterministic Python only (the moat)
- NER enrichment: GLiNER in extractive mode only (span must exist verbatim)
- Intent classification (status, category, negation): GLiNER with custom labels — not a generative model
- SOAP formatting: **stale as of 2026-07-02 — this line says Gemini Flash, but current production SOAP generation is 100% deterministic rule-based, zero LLM.** A Gemini SOAP-enhancement path was prototyped and explicitly reverted this session. If reintroducing, the certainty-marker handling (`(denied)`/`(uncertain)` suffixes from `provenance.py`) must be preserved — the reverted version did not do this.
- Admin document generation: Python templates + Gemini Flash for prose from structured facts
- Learning signal: deterministic confidence scoring, not LLM-generated lessons
- Pre-auth form filling: template mapping from approved facts only — never LLM inference on clinical fields

---

## YC Ready Checklist

Complete these in order. When all are checked, the application is ready to submit.

- [ ] Clinical extraction accuracy at ~78/100 (GLiNER classification layer)
- [ ] Branch committed, demo runs clean from transcript to SOAP
- [ ] Memory → SOAP safety guard live and tested
- [ ] LearningEvent correction ledger capturing every doctor action
- [ ] Investigation order generator live (downstream service output #1)
- [ ] Patient follow-up message generator live (downstream service output #2)
- [ ] Assistant work queue live (the demo moment that proves service company)
- [ ] Cost per consultation: real number from real consultations
- [ ] Augnito teardown written and accurate
- [ ] Mobile core flow verified on Android Chrome
- [ ] One insurance pre-auth form mapped to a real TPA
- [ ] Flywheel analytics: acceptance rate, edit rate, review time visible
- [ ] The killer demo runs end-to-end in under 5 minutes

---

## The Killer Demo (Target State)

This is what the demo needs to do before applying:

1. Doctor speaks consultation — live or pre-recorded
2. Sarvam transcribes
3. Lipi extracts facts — medications with status, vitals, diagnoses, allergies, investigations
4. Doctor sees evidence review: "3 facts to confirm" — approves in 60 seconds
5. Investigation order auto-generated: ready to send to lab
6. Patient WhatsApp message drafted: "Dear Mr. Verma, please get ECG and HbA1c at XYZ lab before your next visit"
7. Work queue populates: [Send investigation order ✓] [Send patient message — doctor approval] [Pre-auth checklist — 3 items missing]
8. Doctor approves all in 30 seconds
9. Screen: "Consultation complete. 3 documents generated. 2 tasks queued."

That is the service company demo. Everything below exists to make it real.

---

## Block 0 — Accuracy (In Progress, ~3 days)

### 0.1 GLiNER classification layer — replace regex intent classification

Model: Opus for design, Sonnet for implementation | Effort: 2-3 days

**Status check 2026-07-02: verify this before starting.** GLiNER is currently NOT wired into the production request path at all — `routes_notes.py`'s live pipeline calls `ClinicalExtractorService.extract()` directly, bypassing `clinical_pipeline.py` (the only place GLiNER runs), which is currently exercised only by `test_e2e.py`. The ontology-based keyword/fuzzy layer has grown to ~3,222 hand-curated entries since this plan was written, which changes the marginal value case for GLiNER (smaller unknown-term gap than when this block was scoped) against its cost (753MB local model, cold-start latency, an unverified merge/filter layer). Confirm this tradeoff is still worth it before starting — see `21_FRONTIER_RESEARCH_DIRECTIONS.md` for the current thinking on the ontology size, and decide explicitly rather than assuming this block's premise still holds.

**This is the architectural change that was expected to take extraction from 60 → 78/100 — re-verify the current accuracy baseline before assuming that gap still exists.**

The problem: regex-based classification of status, category, and negation cannot generalize across Hinglish variation. Every new phrasing requires a new pattern. A generative LLM call would break the zero-LLM guarantee. GLiNER is already in the pipeline and is purely extractive — spans must exist verbatim, no text generation possible.

The change: extend GLiNER label set to cover classification, not just entity boundary detection.

New labels to add alongside existing NER labels:
```
MEDICATION_NEW          — shuru karo, naya prescription, start
MEDICATION_CONTINUE     — jari rakho, continue karo, same
MEDICATION_HOLD         — avoid karo, mat dena, band karo, hold
MEDICATION_RESTARTED    — dobara shuru, restart, band tha ab shuru
MEDICATION_INCREASED    — badhao, increase, dose up
MEDICATION_REDUCED      — kam karo, reduce, dose down
NEGATED_MEDICATION      — bilkul nahi, do not give, mat lena
ALLERGY_MENTION         — se allergy, se reaction, se problem
SYMPTOM_ACTIVE          — current complaint
SYMPTOM_HISTORICAL      — pehle tha, purana
DIAGNOSIS_CONFIRMED     — ki diagnosis hai, confirmed
```

Keep regex only for structured vitals patterns (BP 138/86, weight 62 kg, HbA1c 8.2%) where the format is bounded and extraction IS the classification.

Register as D016 in 07_DECISIONS.md.

Acceptance: re-run complex Hinglish test transcript. 17/18 → 18/18. No regression on existing tests.

### 0.2 Commit the branch

Model: Sonnet | Effort: 1 hour

All Hinglish hardening is uncommitted. Commit pilot-prod-hardening before anything else. This is the demo baseline. Every future diff is dirty without it.

---

## Block 2.2 — Dynamic Drug Alias Learning (Week 2, ~2 days)

Model: Sonnet | Effort: 2 days | On top of Block 2.1 (LearningEvent ledger)

**Context:** the static allowlist in `clinical_extractor.py` covers ~200 common Indian brand names (Dolo, Crocin, Ecosprin, Stamlo, Glycomet, etc.). That handles 70,000+ branded formulations exactly 0% of the time when the brand isn't in the list. Regional brands, uncommon formulations, new market entries, and ASR phonetic variants ("Doloe", "Krosin") all fail silently today.

**What this builds:** when a LearningEvent records a drug name correction, write to `clinic_drug_aliases`:

```
alias          — what the doctor said / what ASR produced ("telma", "krosin", "doloe")
canonical      — what it maps to ("telmisartan", "paracetamol", "paracetamol")
dose_hint      — "40mg", "650mg" if present in correction
clinic_id      — scoped to clinic first
doctor_id      — scoped to doctor within clinic
confirmed_count — increments with each confirmation
status         — learning | trusted (trusted after 3 confirmations)
```

At extraction time in `_canonical_med()`, query this table before the static allowlist gate. A clinic-trusted alias is treated identically to a static entry.

**The 30-second YC demo:**
Consultation 1: Dr. Sharma says "Telma 40." Unknown brand. He corrects it: Telmisartan 40mg. Lipi records.
Consultation 2: Dr. Sharma says "Telma 40" again. Lipi extracts Telmisartan 40mg. Tag on screen: *"Learned from Dr. Sharma."*

That single exchange demonstrates the entire moat: correction → clinic-specific knowledge → better extraction → compounding. No competitor can show this.

**Why this is different from the static list:** the static list is built by engineers. This list is built by doctors using the product. It captures regional variation (Pune says Telma, Delhi says Telmikind, same molecule), ASR errors, new market launches, and per-doctor brand preferences — none of which can be pre-populated.

---

## Block 1 — Safety (Week 1, ~2 days)

Must be done before any real patient sees the product.

### 1.1 Memory → SOAP separation guard

Model: Sonnet | Effort: 3 hours | Register as D012

Add `current_visit_only=True` gate in `memory_context.py:resolve_memory()`. Old allergies, medications, and diagnoses from prior visits must not enter the current SOAP unless the doctor explicitly restates them in the current consultation.

Architecture:
- `current_visit_state`: facts from this consultation only
- `past_context`: patient memory sidebar — visible, never automatically merged into SOAP
- CDS uses current approved facts only
- Doctor can "confirm from history" — explicit action, not automatic

Test: prove old penicillin allergy from visit 1 does not appear in visit 2 SOAP unless restated.

### 1.2 IU dosage unit support

Model: Sonnet | Effort: 2 hours

Add IU to the dose regex. Vitamin D 60,000 IU weekly and Insulin 10 IU before dinner are extremely common in Indian OPD. Two tests. One hour of work.

---

## Block 2 — Flywheel Foundation (Week 1, ~1 day)

**Critical sequencing rule: build this before the service surfaces, not after. Every pilot correction is permanently wasted signal without it.**

### 2.1 LearningEvent correction ledger

Model: Opus for schema design, Sonnet for wiring | Effort: 1 day

The most leveraged item in the backlog. Every accept/edit/reject/add action in the doctor review UI must produce a structured event. Without this, pilots generate zero reusable signal.

Schema:
```
id, session_id, doctor_id, clinic_id
actor: system | doctor | assistant | ops
event_type: fact_added | fact_deleted | fact_modified | evidence_changed |
            task_completed | task_blocked | document_corrected | claim_rejected
before_json, after_json, evidence_refs
reason: false_positive | missing_fact | normalization | dose_frequency |
        asr_spelling | allergy_context | style_preference | admin_rule | other
scope_candidate: patient | doctor | clinic | specialty | global
created_at
```

Wire into every accept/edit/reject/add in `routes_notes.py`. Wire into task completion in `routes_admin.py` once built.

---

## Block 3 — Service Company Surface (Weeks 1-2, ~1 week)

These three together change the demo from "AI scribe tool" to "AI-native service company."

### 3.1 Investigation order generator

Model: Sonnet | Effort: 1-2 days

First downstream output a human was doing before. Template-fill from approved investigation facts only. Output: document with patient/doctor/clinic fields, ordered investigations list, evidence per item, doctor review required status. Missing fields stay missing — never inferred.

Never an LLM call. Never adds investigations not in approved facts.

Generates a LearningEvent when completed or corrected.

### 3.2 Patient follow-up message generator

Model: Sonnet | Effort: 1 day

WhatsApp message to patient drafted from approved follow-up, investigation orders, and medications. "Dear [name], please get [investigations] at [lab] before your next visit on [date]. Take [medications] as prescribed." 

WhatsApp infra is already wired. This is template substitution from approved facts. One day. Doctor approves before sending.

Generates a LearningEvent on send/edit/cancel.

### 3.3 Assistant work queue

Model: Sonnet | Effort: 3-4 days | The key demo moment

After doctor approves facts, Lipi auto-generates a structured task list. This is what makes the demo a service company demo, not a note app demo.

DB table:
```
assistant_work_items
- id, session_id, user_id
- task_type: evidence_review | investigation_order | referral_letter |
             follow_up_message | insurance_preauth | missing_info | final_approval
- title, status: pending → needs_review → in_progress → done | blocked | cancelled
- owner_role: doctor | assistant | ops
- priority: critical | high | medium | low
- due_at, notes, blocker_reason, source
- created_at, updated_at
```

API:
```
GET  /api/sessions/{session_id}/work-queue
GET  /api/admin/work-queue
PATCH /api/admin/work-queue/{item_id}
```

Every task completion or block generates a LearningEvent. Task outcome data is how Lipi learns which workflows complete reliably and which get stuck.

---

## Block 4 — Economics (Week 2, ~2 days)

You cannot pitch service company margins without a real cost number.

### 4.1 Cost-per-consultation ledger

Model: Sonnet | Effort: 1 day

Per session: audio minutes, Sarvam ASR cost from real billing, Gemini formatting cost if used, messaging cost, infra allocation, total INR. Surface in admin dashboard.

If cost is ₹3/consultation and price is ₹33 (₹999/month ÷ 30 sessions), that is an 11x gross margin story at scale. This needs to be a real number from real consultations, not an estimate.

Update 06_API_COSTS.md with real data weekly during pilots.

### 4.2 Flywheel analytics dashboard

Model: Sonnet | Effort: 1-2 days

Metrics per session and aggregated:
- Fact acceptance rate, edit rate, deletion rate, addition rate
- False-positive deletion rate
- Missing-fact addition rate  
- Doctor review time per consultation
- Task completion rate and blocker categories
- Document edit rate
- Extractor layer breakdown (keyword / regex / GLiNER / custom label)
- Cost per consultation

This is the dashboard that proves Lipi is getting better. It turns pilot data into visible product improvement signal. "You corrected us 3 times on this symptom — here is what changed" — no competitor can show a doctor that.

---

## Block 5 — Competitive Clarity (Week 2, ~1-2 days)

### 5.1 Augnito teardown

Model: Opus | Effort: 1 day

04_COMPETITORS.md is a research framework with no filled-in data. Augnito is a real India-specific medical dictation player. YC will ask about them directly.

Investigate and document with verified dated claims:
- Pricing model
- Hindi/Hinglish coverage — how deep vs Lipi's Hinglish extraction
- Extraction approach: LLM-based inference vs structured
- Evidence provenance: do they show source spans? Can they audit?
- Hospital vs OPD focus
- Service outputs beyond notes: do they have work queue, orders, pre-auth?
- Setup friction for a 3-doctor clinic in India

The differentiators that matter for YC:
- Augnito is English-first documentation. Lipi is Hinglish-native administration.
- Augnito is hospital-focused. Lipi is OPD clinic-focused.
- Augnito is a note tool. Lipi is a service — investigation orders, follow-ups, pre-auth.
- Augnito has no learning loop. Lipi compounds every correction.

Keep only verified claims. No stale intel.

### 5.2 Mobile core flow verification

Model: Sonnet | Effort: 1 day

Walk the full flow on Android Chrome: login → create consultation → record → process → evidence review → approve → print/share. Fix broken action buttons or text overflow. Test PWA install. Indian doctors use phones — if this doesn't work on mobile the product doesn't work.

---

## Block 6 — The Money Workflow (Week 3, ~4 days)

### 6.1 One insurance pre-auth form for one real TPA

Model: Opus for architecture, Sonnet for implementation | Effort: 3-4 days

Pick ONE real TPA form from a pilot clinic. Map approved facts only to form fields. Missing fields stay missing — never infer policy ID, procedure, admission reason, or cost from the transcript. Every clinical field traces to an evidence span.

This is the service company's first money workflow. Gustaf's framing explicitly names insurance. When a clinic's pre-auth takes 2 hours of staff time and Lipi does it in 5 minutes with an audit trail, the product justifies its price on one consultation.

The safety story here is the moat: an LLM-based competitor can hallucinate a diagnosis certainty or infer a procedure code — claim rejected, doctor loses ₹50K, trust destroyed. Lipi's architecture makes that impossible. When regulators eventually require audit trails for AI-generated claims, this becomes structural lock-in.

Capture rejection reasons when forms fail. Every rejection → LearningEvent.

---

## After YC Application — Learning Moat

These are not needed for the application but are what the application is promising. Build them during or after batch.

### MemoryCandidate pipeline from LearningEvents

When LearningEvents accumulate past a threshold (same doctor edits same section 3 times, same false positive from same extractor phrase, same TPA field causes rejection), generate a MemoryCandidate:

```
candidate_type: preference | vocabulary | workflow_rule | form_requirement | failure_signature
scope: patient | doctor | clinic | specialty | global
safety_class: safe | review_required | clinical_boundary (never auto-promote)
status: proposed | shadow | approved | rejected | retired
```

Scope detection and safety_class assignment require Opus. Wrong scope → false global rules applied everywhere. Wrong safety_class → clinical safety incident.

### Doctor preference and clinic workflow memory

Per-doctor: note structure preferences, prescription style, diagnosis wording, correction patterns. Scope: doctor only.
Per-clinic: prescription format, WhatsApp wording, follow-up cadence, assistant handoff format. Never clinical facts.

Every stored preference tracks accepted/rejected counts and rollback path.

### Shadow playbook and Lesson Review Queue

PlaybookRule objects that propose before they execute. Admin sees: "For Dr. Rao's referral letters, include symptom duration when available — based on 3 accepted edits. Approve / edit / reject?"

This is what no competitor can copy. It requires months of reviewed traces. It gets richer with every clinic. The queue is where corrections become auditable operational learning.

### Specialty-specific extraction routing

Cardiology and gynecology first. `SpecialtyEnum` exists in the codebase but the extractor ignores it. Wire specialty into `clinical_extractor.py`. Additive and evidence-backed. Tests for each specialty before claiming support.

### Stage 2 specialized models (after 1000+ reviewed consultations)

Fine-tune only narrow components: visit type classifier, task trigger classifier, doctor style formatter, false positive predictor, rejection reason classifier. Clinical facts still require evidence and doctor review. These replace heuristics with learned classifiers that are cheaper, faster, and more accurate.

---

## Parked — Do Not Build Before Market Proof

- Custom ASR training — D008 accepted. Sarvam plain STT default. Build after market proof.
- ABHA/ABDM integration — only format validation now. Real integration needs NHA registry access. Do not claim it until the end-to-end flow exists.
- Billing self-serve / Razorpay — manual billing is fine under 50 clinics.
- Diarization by default — D007 accepted. Track speaker confusion incidents. Add diarization only when incidents materially affect clinical records.
- RL for clinical facts — D003 and D004 non-reversible. RL only for narrow workflow policy (task ordering, reminder timing, queue priority). Never clinical facts, diagnoses, prescriptions, or safety alerts.

---

## Execution Order Summary

```
Week 1
  Block 0 — GLiNER classification layer (accuracy 60 → 78)
  Block 0 — Commit branch
  Block 1 — Memory → SOAP guard + IU dosage
  Block 2 — LearningEvent ledger (must come before service surfaces)
  Block 3 — Investigation order generator
  Block 3 — Patient follow-up message generator

Week 2
  Block 2.2 — Dynamic drug alias learning
  Block 3 — Assistant work queue
  Block 4 — Cost-per-consultation ledger
  Block 4 — Flywheel analytics dashboard
  Block 5 — Augnito teardown
  Block 5 — Mobile core flow verification

Week 3
  Block 6 — One insurance pre-auth form (Star Health or pilot TPA)
  YC APPLICATION READY
```

---

## Decision Records To Add

- D012: Memory → SOAP separation (Block 1.1)
- D013: Production ASR path documentation (Sarvam plain STT as default, Gemini optional, no offline claim)
- D014: Pilot mode — manual promotion before 3-clinic threshold (for D1 learning loop during pilots)
- D015: GLiNER chunking for transcripts over 15 minutes
- D016: GLiNER custom label classification replaces regex intent classification (Block 0.1)

---

## Related Notes

- [[07_DECISIONS]] — add D012 through D016 as each is built
- [[06_API_COSTS]] — fill with real data from pilots
- [[04_COMPETITORS]] — fill Augnito table with verified dated claims (Block 5.1)
- [[10_CONTINUAL_LEARNING_SYSTEM]] — LearningEvent, MemoryCandidate, PlaybookRule schemas
- [[12_IMPLEMENTATION_GAP_REGISTER]] — cross-reference each block against gap register
- [[03_PRODUCT_STRATEGY]] — Gustaf framing, positioning, YC pitch rule

# Implementation Gap Register

Date: 2026-06-27
Verified against running code: 2026-07-02 (see inline "verified 2026-07-02" notes for what changed)

Purpose: single source of truth for what appears built, what is not built, and what must be verified before pilots, scale, or YC/service-company positioning.

Rule: this note tracks product and engineering gaps only. Do not paste code here. Code remains in `backend/` and `frontend/`. If this register disagrees with code, inspect code and update this note.

Related:
- [[01_CURRENT_STATE]]
- [[03_PRODUCT_STRATEGY]]
- [[06_API_COSTS]]
- [[09_STRATEGIC_ROADMAP]]
- [[10_CONTINUAL_LEARNING_SYSTEM]]
- [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]]
- [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

## Current Honest Positioning

Current safe positioning:

> Lipi is an evidence-backed OPD documentation workflow product with early service-company surfaces.

Target positioning after work queue, ledger, and one money workflow:

> Lipi is an AI-native OPD administration service that turns one consultation into reviewed records, clinic tasks, patient communication, admin documents, and measurable operational savings.

Do not claim full AI-native service-company execution until the admin workflow surfaces are actually wired and used.

## Built Surface To Verify Before Demos

These appear present in the codebase or prior inspection, but should be runtime-verified before pilots or external claims:

- Local evidence-backed clinical extraction pipeline.
- Provenance fields on extracted facts: extractor, evidence spans, confidence, certainty, review status.
- GLiNER enrichment path — **verified 2026-07-02: code exists (`gliner_extractor.py`, `clinical_pipeline.py`) but is NOT wired into the production request path.** `routes_notes.py` calls its own local `_run_health_pipeline()`, which invokes `ClinicalExtractorService.extract()` directly and never touches `clinical_pipeline.run_health_pipeline()` (the only function that calls GLiNER). GLiNER is exercised only by `test_e2e.py`. `ENABLE_GLINER=False` by default, unset in deploy config. Treat GLiNER as dead code from production's perspective until explicitly wired in.
- SOAP generation with structured `S/O/A/P` output. **Verified 2026-07-02: currently 100% deterministic rule-based (`soap_generator.py`), zero LLM in the live SOAP path.**
- CDS engine for allergy conflicts, cross-reactivity, drug-drug interactions, missing dose/frequency, symptom-based alerts, and vital-based alerts.
- Doctor fact review routes for accept/edit/reject/finalize flows.
- Evidence Review UI surface.
- Learning flywheel primitives: `fact_corrections`, `extraction_knowledge`, confidence scoring, admin review queue, promoted knowledge reload.
- Patient memory / patient timeline primitives.
- PHI scrubbing and audio deletion processing.
- Sarvam ASR paths, including upload/transcribe/manual transcript flows.
- Batch/diarization service code, but production diarization status must be verified.
- WhatsApp prescription sharing and follow-up reminders.
- FHIR export, ICD-10 mapping, and HTML prescription rendering.
- JWT auth, session management, audit logging, and usage analytics.
- Clinic management and clinic member APIs.
- Note signing / audit hash.
- Billing: **verified 2026-07-02, table structure changed since this register was written.** `billing_records` was split into two clean tables: `billing_records` (Lipi's own SaaS plan billing — clinic_name/plan_name/amount_inr/status) and `consultation_billing` (per-consultation patient fee — session_id/user_id/amount/currency/notes). Previously these were incorrectly sharing one table with two incompatible schemas across SQLite/Postgres. Fixed live on Postgres with zero data loss.

## Immediate Engineering Hygiene

### 1. Commit Current Known-Good State

Status: not done.

Why it matters:
- Uncommitted work can be lost.
- It is hard to compare future changes without a baseline.
- Pilot readiness requires a known branch/commit.

Acceptance:
- Intentional backend, frontend, and docs changes are reviewed.
- A named branch and commit exist for the known-good state.
- Generated artifacts are excluded unless intentionally tracked.

### 2. Reconcile Product Claims With Runtime Reality

Status: not done.

Risk:
- Some docs or copy may imply no patient data leaves the clinic.
- Current product can use Sarvam cloud ASR and WhatsApp/Twilio when enabled.
- Gemini may exist for formatting structured content.

Safer wording:
- "Clinical extraction is local and evidence-backed."
- "External services are used only for explicit transcription/messaging/formatting workflows when enabled."
- "Gemini, if used, formats structured facts and must not create clinical facts."

Acceptance:
- Public copy and technical docs do not overclaim privacy/offline behavior.
- Sarvam, WhatsApp/Twilio, and optional Gemini paths are explicit.

## Before Real Patients

### 3. Memory To SOAP Separation

Status: not done.

Problem:
- Memory resolution can accept multiple visits' facts.
- If prior-visit facts ever enter current SOAP state, old facts can appear as if spoken today.

Required architecture:
- `current_visit_state`: facts from the current consultation only.
- `past_context`: patient memory/sidebar context only.
- SOAP, CDS, orders, referrals, and admin outputs use current approved facts unless the doctor explicitly confirms past context in the current visit.

Acceptance:
- Tests prove old allergy/diagnosis/medication does not enter SOAP unless restated or doctor-confirmed.
- UI shows patient timeline separately from current note.
- Admin outputs label any past-context use clearly.

### 4. GLiNER Chunking For Long Consultations

Status: not done, and lower priority than this section implies — GLiNER is not wired into production at all right now (see Built Surface note above). Solve the wiring question first (worth it or not, given ~3,222-entry curated ontology already covers most terms — see `21_FRONTIER_RESEARCH_DIRECTIONS.md` discussion) before investing in chunking for a path nothing currently calls.

Problem:
- Long transcripts may be passed to GLiNER as one string.
- 20-30 minute OPD visits can exceed practical model context or degrade NER quality.

Required behavior:
- Split transcript into sentence or paragraph chunks while preserving character offsets.
- Run GLiNER per chunk.
- Reconstruct global `start_char` and `end_char`.
- Deduplicate overlapping candidates.
- Keep extractive guarantee: every GLiNER fact must map back to transcript text.

Acceptance:
- Long-transcript test proves correct global evidence spans.
- No duplicate candidates across chunk boundaries.
- No confirmed fact without valid transcript span.

### 5. IU Dosage Unit Support

Status: not done.

Problem:
- Prescription extraction may cover `mg`, `ml`, `mcg`, and `g`, but Indian OPD commonly uses IU.

Examples:
- `Vitamin D 60000 IU weekly`
- `Insulin 10 IU before dinner`

Acceptance:
- Medication regex captures IU dosage.
- SOAP/prescription renderer preserves IU exactly.
- Tests cover Vitamin D and insulin IU prescriptions.

### 6. Production Diarization Decision

Status: unclear / must verify.

Problem:
- Sarvam batch ASR service may include diarization.
- Production WebSocket/simple STT path may not include speaker labels.
- Without speaker separation, the system can confuse "doctor says take aspirin" with "patient says I was taking aspirin."

Required decision:
- Verify the current production consultation path: plain STT, streaming STT, batch ASR, and diarization.
- Keep Sarvam plain STT default unless real usage proves diarization is needed.
- If diarization is off, add review UI affordances and do not overclaim speaker attribution.

Acceptance:
- One documented runtime path exists for pilots.
- If diarization is enabled, speaker labels are persisted and displayed.
- If diarization is disabled, extraction review clearly handles speaker ambiguity.

### 7. D1 Learning Loop Fix

Status: partially built, likely not spinning enough for early pilots.

Problem:
- Auto-promotion requires repeated confirmations across clinics.
- Early pilots may have only one or two clinics, so nothing auto-promotes.
- Passive edits and deleted false positives may not produce enough structured signal.

Required behavior:
- Capture added, deleted, and modified facts as learning events.
- Capture correction reason: false positive, missed fact, normalization, dose/frequency, ASR spelling, allergy context, or other.
- Add conservative pilot mode where manual admin promotion can apply before the 3-clinic threshold.

Acceptance:
- Every accept/edit/reject/add action produces a structured correction event.
- Admin review queue shows enough non-PHI context.
- Manual promoted knowledge reloads into extractor without restart or with an explicit safe reload action.
- Pilot rules are separated from scale rules.

### 8. Mobile Core Flow Check

Status: partial / unverified.

Acceptance:
- A doctor can complete: login -> create consultation -> record/upload -> process -> evidence review -> print/share.
- No broken action buttons or text overflow on common phone sizes.
- PWA install path is tested on Android Chrome before claiming mobile readiness.

## Before Scaling Clinics

### 9. Specialty-Specific Extraction Routing

Status: not done.

Problem:
- `SpecialtyEnum` exists, but extraction behavior may remain mostly general.

Examples:
- Cardiology: STEMI, NSTEMI, troponin, ECG, echo, chest-pain red flags.
- Gynecology: LMP, GA, anomaly scan, bleeding, pregnancy context.
- Pediatrics: weight-based dosing, fever age context, vaccination notes.
- Dermatology: lesion morphology, topical medications, distribution.

Acceptance:
- Extractor receives specialty context explicitly.
- Specialty maps are additive and evidence-backed.
- At least two specialties have tests before claiming specialty support.

### 10. Assistant Work Queue

Status: not built.

Required:
- Session-level admin task creation.
- Clinic/global work queue.
- Task owner: doctor, assistant, or Lipi ops.
- Task status: pending, needs_review, needs_info, blocked, in_progress, done, cancelled.
- Due time/SLA, notes, blocker reason, completion reason.

Why it matters:
- This is the main transition from software tool to AI-native service company.

### 11. Investigation Order Generator

Status: not built, or only partially covered by printable outputs.

Required:
- Generate order only from approved investigation facts or doctor-entered items.
- Include patient, doctor, and clinic fields.
- Preserve evidence per investigation where useful.
- Missing fields remain missing.

### 12. Referral Letter Hardening

Status: partially built.

Needed:
- Ensure referral letter uses approved facts only after evidence review.
- Include doctor-reviewed status.
- Avoid inferring diagnosis certainty from SOAP prose.
- Preserve current visit versus past context separation.

### 13. Cost-Per-Consultation Ledger

Status: not built as a complete per-session ledger.

Required:
- ASR minutes per session.
- Sarvam cost estimate.
- Messaging cost.
- Gemini formatting cost if used.
- Infrastructure allocation.
- Human ops cost if Lipi ops completes tasks.
- Total INR per consultation.

Why it matters:
- Indian clinic pricing requires strict marginal cost discipline.
- Service-company margins cannot be proven without this.

### 14. Flywheel Analytics Dashboard

Status: partial.

Required:
- Fact acceptance rate.
- Fact edit rate.
- Deleted false positives.
- Missing facts added by doctors.
- Correction reason categories.
- Extractor/layer quality.
- Doctor review time.
- Document edit rate.
- Task completion and blocker reasons.
- Cost per consultation.

Why it matters:
- This proves whether Lipi is improving.

### 15. One Insurance Pre-Auth Form

Status: **built, verified 2026-07-02** — this entry was stale. Two real entry points exist in `frontend/src/pages/ReviewNote.tsx`: a "TPA Claim" modal (policy/insurer/TPA fields → PDF) and an "Insurance Claim →" link to `frontend/src/pages/TPAClaim.tsx`. Backend: `backend/app/api/routes_tpa.py`, `/sessions/{id}/tpa-claim`. Both gated behind `session?.status === 'complete'` — if a session isn't in that exact status, neither button renders (no error shown, just absent — worth a UX pass so it's not mistaken for missing).

Remaining gap versus the original ask: still only one generic TPA form shape, not mapped to a specific real payer's exact required fields, and no captured rejection-reason loop yet.

### 16. Internal Ops Console

Status: not built.

Required:
- View clinic work items.
- Assign owner.
- Track SLA.
- Add notes.
- Escalate to doctor.
- Track completion and failure reasons.

Why it matters:
- Lipi humans can complete service work while software learns.

## Before Broader Scale

### 17. Billing Self-Serve And Quotas

Status: partially built manually.

Built:
- Billing records table.
- Some analytics around revenue paid/due.

Not built:
- Razorpay/Stripe integration.
- Subscription tiers.
- Session quota enforcement.
- Trial limits.
- Invoice/payment automation.

Acceptance:
- Clinic plan controls quota/limits.
- Payment status affects access according to policy.
- Billing events are auditable.

### 18. ABHA/ABDM Integration

Status: not built.

Built:
- ABHA format validation only.

Not built:
- NHA registry lookup.
- ABHA-linked record flows.
- ABDM consent/account linking.

Acceptance:
- Do not claim ABDM integration until API access and end-to-end flow exist.
- UI copy says "ABHA number capture/validation" if only local validation exists.

### 19. Local Fallback ASR

Status: partial/stub.

Problem:
- `local_asr.py` may exist, but a production fallback is not real unless the model and runtime are configured.

Acceptance:
- If offline/local ASR is offered, it is real and labeled.
- If not real, hide product claims.
- Stub ASR remains disabled for pilots unless explicitly demo mode.

### 20. Dosage Range CDS

Status: not built.

Examples:
- Prednisolone 200mg.
- Excessive daily paracetamol total.
- Pediatric dosing mismatch without weight.

Acceptance:
- Start with a small high-safety medication list.
- CDS always uses `doctor_review_required`.
- Do not overbuild full pharmacology before pilot proof.

### 21. Specialty Prescription Templates

Status: not built.

Acceptance:
- Build only if pilot demand appears.
- Template selection remains deterministic and doctor-reviewable.

## Priority Order

### Today

1. Commit the current known-good state.
2. Create clean issues/backlog from this register.
3. Reconcile public/docs privacy claims with actual Sarvam/WhatsApp/Gemini behavior.

### Before Real Patients

1. Memory to SOAP separation.
2. GLiNER chunking.
3. IU dosage support.
4. Production diarization decision.
5. D1 learning loop fix.
6. Mobile core-flow check.

### Before Scaling Clinics

1. Assistant Work Queue.
2. Cost-Per-Consultation Ledger.
3. Investigation Order Generator.
4. Referral Letter Hardening.
5. Flywheel Analytics Dashboard.
6. One Insurance Pre-Auth Form.
7. Internal Ops Console.
8. Billing self-serve and quotas.

## Relationship To Research Direction

The advanced on-the-job learning direction depends on these implementation gaps being closed.

Do not start with RL or model training. Start with:
- Evidence review.
- Experience ledger.
- Work queue.
- Task outcomes.
- Cost ledger.
- Clinic playbooks.
- Lesson review.
- Deterministic verifiers.

These create the real traces needed for future continual learning.

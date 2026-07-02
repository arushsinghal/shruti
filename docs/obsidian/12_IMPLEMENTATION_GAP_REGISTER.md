# Implementation Gap Register

Date: 2026-06-27
Verified against running code: 2026-07-02 (see inline "verified 2026-07-02" notes for what changed)
**Re-verified against running code: 2026-07-03** — several items below were marked "not built" in error; the code was already there and just never reconciled back into this register. See "verified 2026-07-03" notes. Read those before treating any "not built" status as current — check the code, not just this file, going forward.

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
- **Investigation order generator — verified 2026-07-03: BUILT.** `investigation_order_renderer.py`, wired into `routes_notes.py` (`GET /sessions/{id}/investigation-order`) and `routes_public.py` (patient-facing HTML link, sent via WhatsApp in `diagnostic_dispatch.py`). Item #11 below was stale — do not treat it as "not built."
- **Assistant work queue — verified 2026-07-03: BUILT.** `routes_tasks.py`: real task table (`task_type`, `status`, `owner`, `due`, `notes`, `completed_at`), role-scoped so an assistant sees every doctor's queue in their clinic (`_owner_clause`). `GET /tasks`, `PATCH /tasks/{id}`, `POST /tasks/{id}/send-followup`, `POST /tasks/{id}/dispatch-prescription`. Frontend: `Tasks.tsx` (235 lines), `AssistantDashboard.tsx` (690 lines), `AssistantIntake.tsx` (347 lines), `ClinicInbox.tsx` (242 lines). Item #10 below was stale.
- **Internal ops console — verified 2026-07-03: BUILT.** `OpsDashboard.tsx` (189 lines). Item #16 below was stale.
- **Patient follow-up WhatsApp message — verified 2026-07-03: BUILT.** `send-followup` / `dispatch-prescription` endpoints in `routes_tasks.py`.
- **Assistant/service-company framing in product copy — verified 2026-07-03: present.** `Landing.tsx` testimonial: "My assistants now get a WhatsApp task list before the patient leaves... Lipi queues all of it" / "The assistant's queue builds itself." Not just internal docs — this is live marketing copy.
- **Correction flywheel write path — verified 2026-07-03: NOW WIRED (was the single biggest gap, closed 2026-07-02/03).** `learning_service.record_correction()` / `record_false_positive()` are called from every doctor action in `routes_fact_review.py` (accept/edit/reject/add fact) and from SOAP hallucination flags in `routes_notes.py::post_soap_feedback()`. Previously built but never called — see [[07_DECISIONS]].
- **Indian brand-name CDS resolution — verified 2026-07-03: BUILT 2026-07-03.** `backend/app/services/_indian_brands.py` merges the existing 280-entry `indian_brands.tsv` ontology with a curated FDC-component map (29 FDCs, e.g. Combiflam → ibuprofen+paracetamol). Wired into `cds_engine.py` so drug-drug interaction checks fire on real Indian brand-name prescriptions, not just generics.
- **Memory→SOAP visit-boundary guardrail — verified 2026-07-03: BUILT 2026-07-03.** `resolve_memory()` now raises `ValueError` unless `allow_multi_visit=True` is explicitly passed when more than one fact-set is given. All 7 production call sites already pass single-item lists (verified), so behavior is unchanged today — this closes the risk described in item #3 below for any *future* multi-visit history feature. Item #3 is now a closed risk, not an open gap — the guardrail exists but the eventual `current_visit_state`/`past_context` split for a real timeline UI feature is still not built.
- **Frequency extraction gap — verified 2026-07-03: FIXED.** "weekly", "monthly", and meal-relative timing ("before dinner" etc.) were missing from the frequency regex and normalization map — common for Vitamin D/insulin IU prescriptions. Fixed 2026-07-03. (Note: item #5 below, "IU dosage unit support," was already stale before this fix — IU dosage itself was already parsed correctly; only frequency around IU prescriptions was broken. Corrected inline at item #5.)
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

Status: **stale — verified 2026-07-03: IU dosage itself was already parsed correctly** (`clinical_extractor.py` regex already included `iu|units?`). The actual bug was that **frequency** extraction had no pattern for "weekly", "monthly", or meal-relative timing ("before dinner") — so "Vitamin D 60000 IU weekly" captured the dose but dropped the frequency. Fixed 2026-07-03.

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

Status: **built, verified 2026-07-03** — this entry was stale. `backend/app/api/routes_tasks.py` implements a real task table (`task_type`, `status`, `owner`, `due`, `notes`, `completed_at`, `session_id`, `user_id`), role-scoped so an assistant sees every doctor's queue in their clinic via `_owner_clause()`. Routes: `GET /tasks`, `PATCH /tasks/{id}`, `POST /tasks/{id}/send-followup`, `POST /tasks/{id}/dispatch-prescription`. Frontend surfaces: `Tasks.tsx`, `AssistantDashboard.tsx` (690 lines), `AssistantIntake.tsx`, `ClinicInbox.tsx`.

Remaining gap versus the original ask: task `status` values and `owner_role` scoping should be double-checked against the exact enum this note originally specified (pending/needs_review/needs_info/blocked/in_progress/done/cancelled) — verify the actual status values in the DB schema before assuming full parity; the queue mechanics are real, but the precise status vocabulary hasn't been diffed against this spec.

### 11. Investigation Order Generator

Status: **built, verified 2026-07-03** — this entry was stale. `investigation_order_renderer.py` renders from approved investigation facts, wired into `routes_notes.py` (`GET /sessions/{id}/investigation-order`, doctor-facing) and `routes_public.py` (`GET /public/investigation-order/{session_id}`, patient-facing HTML, linked out via WhatsApp in `diagnostic_dispatch.py`).

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

Status: **built, verified 2026-07-03** — this entry was stale. `frontend/src/pages/OpsDashboard.tsx` (189 lines) exists.

Remaining gap: verify feature-by-feature against the original spec (assign owner, SLA tracking, escalate to doctor, completion/failure reason capture) — confirmed the page exists and is substantial, not that every listed requirement is covered. Do that check before claiming full parity externally.

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

**Updated 2026-07-03 — reflects verified code state, not the original 2026-06-27 plan.**

### Done as of 2026-07-03

1. ✅ Commit the current known-good state — committed to `pilot-prod-hardening`.
2. ✅ Memory→SOAP separation guardrail (`allow_multi_visit` opt-in on `resolve_memory()`).
3. ✅ IU dosage / frequency extraction bug (weekly, monthly, meal-relative timing).
4. ✅ D1 learning loop fix — correction flywheel write path wired into every doctor action.
5. ✅ Indian brand-name CDS resolution (fixes DDI checks silently missing brand-name prescriptions).
6. Assistant Work Queue, Investigation Order Generator, Internal Ops Console, One Insurance Pre-Auth Form — **discovered already built**, not actually completed today, but the register previously said "not built" in error.

### Still Before Real Patients

1. GLiNER chunking — moot unless GLiNER gets wired into the production path at all (currently bypassed entirely, see "Built Surface" note above).
2. Production diarization decision — still unverified which ASR path runs in production.
3. Mobile core-flow check — still unverified end-to-end on Android Chrome.
4. Reconcile public/docs privacy claims with actual Sarvam/WhatsApp/Gemini behavior — still open.

### Still Before Scaling Clinics

1. Cost-Per-Consultation Ledger — confirmed not built (no `cost_per_consultation`/`CostLedger` code found).
2. Referral Letter Hardening — status unchanged, still partial.
3. Flywheel Analytics Dashboard — confirmed not built as specified. `routes_analytics.py` exists but covers billing/appointments/revenue, not fact-acceptance-rate / edit-rate / correction-reason metrics.
4. TPA form is still one generic shape, not mapped to a specific real payer's exact fields.
5. Billing self-serve and quotas — still manual, no Razorpay/Stripe integration.
6. Dynamic drug alias learning (Telma → telmisartan, per-doctor) — confirmed not built.
7. Specialty-specific extraction routing — confirmed not built as a real `SpecialtyEnum`-driven system (only a couple of hardcoded comments reference specialty, no actual routing logic).

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

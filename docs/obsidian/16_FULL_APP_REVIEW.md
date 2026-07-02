# Full App Review — Security, Clinical Safety, Product, YC

Date: 2026-06-28
Reviewer: end-to-end code audit (grounded in actual source, not assumptions)
Scope: backend services, API routes, storage, auth, learning loop, extraction pipeline
Related: [[14_BUILD_PLAN]], [[15_AUGNITO_TEARDOWN]], [[09_STRATEGIC_ROADMAP]]

> Method note: findings below were verified by reading the actual files. Files read in full:
> repository.py, routes_auth.py, routes_ws.py, security.py, soap_generator.py, phi_scrubber.py,
> config.py, learning_service.py, main.py, memory_context.py, db.py, routes_sessions.py,
> whatsapp_service.py, ollama_extractor.py, cds_engine.py, routes_notes.py, prescription_renderer.py.
> Sampled/grepped (not read line-by-line): clinical_extractor.py (1600+ lines), provenance.py.
> NOT audited this pass: routes_analytics.py, routes_audio.py, fhir_mapper.py, medical_ontology.py,
> memory_service.py, gliner_extractor.py. A second pass should cover these.

---

## Status Update — Verified Against Running Code, 2026-07-02

Re-checked F1, F2, F3, S3, P5 directly against current source. Do not treat the findings below as still-open without reading this first.

- **F1 (Ollama LLM injecting facts) — RESOLVED.** `grep -n "ollama" backend/app/api/routes_notes.py` returns nothing. The live `_run_health_pipeline()` calls `ClinicalExtractorService.extract()` directly. No Ollama path exists in the current production pipeline.
- **F2 (learning flywheel dead) — PARTIALLY RESOLVED.** `extraction_knowledge` and `fact_corrections` tables now exist in `db.py` (both SQLite and Postgres paths). `async_reload_knowledge()` is now called in `main.py` lifespan at startup. **Still open:** `routes_fact_review.py` (the real, current doctor accept/edit/reject endpoint) does not call `record_correction()` or `record_false_positive()` anywhere — confirmed by direct grep, zero matches. `routes_learning.py` exists but only exposes an admin alias-revoke endpoint, not correction capture. The infrastructure exists; nothing currently writes live corrections into it. This is the one part of F2 still genuinely true.
- **F3 (no backend confirmation gate) — RESOLVED, but the shape changed from what this doc assumed.** The fix wasn't "block until confirmed" — it's the opt-out review model in `routes_fact_review.py` + `provenance.py`: `facts_from_non_rejected()` populates the draft SOAP with certainty markers (`(denied)`/`(uncertain)`) so nothing renders as falsely affirmed, while `facts_from_confirmed()` hard-gates FHIR/structured exports on explicit per-fact `confirmed` status. Verified end-to-end via browser testing 2026-07-02, including a real clinical-safety bug fix (negated symptoms were rendering as affirmed until fixed today).
- **S3 (`get_doctor_profile` missing) — RESOLVED.** Exists in `repository.py:354`.
- **P5 (Twilio settings undefined) — RESOLVED.** `twilio_account_sid`, `twilio_auth_token`, `twilio_whatsapp_number` all defined in `config.py`.

None of this changes Section 2 (Security) or Section 3 (Data Integrity) findings — those were not re-checked this pass and should be treated as still open unless separately verified.

## THE THREE FINDINGS THAT MATTER MOST (original audit, 2026-06-28 — see status update above for what's changed)

These three contradict the core story Lipi tells doctors and YC. Fix these before anything else.

### F1. The "no LLM in the pipeline" moat is not structurally true
**Severity: Critical (moat integrity) / High (runtime safety)**
`routes_notes.py:76-84` (`_run_health_pipeline`): after deterministic extraction, the code runs:
```python
if ollama.is_available():
    ollama_facts = ollama.extract(transcript)   # this is an LLM (llama3.2)
    facts = merge_with_keywords(facts, ollama_facts)
```
`merge_with_keywords` (ollama_extractor.py:151) injects Ollama-derived **diagnoses, allergies, symptoms, investigations, follow-up, and even medications** into the facts that flow into `generate_soap()`. An LLM IS creating clinical facts in the transcript→SOAP path, with no verbatim/provenance check. Ollama diagnoses (line 183-186) are added with zero evidence span.

- **Why it matters:** This directly contradicts the #1 non-negotiable and the moat pitch. If a YC technical partner greps the repo, the story collapses. And Ollama can hallucinate a diagnosis that was never said.
- **Mitigating reality:** Ollama only runs if `localhost:11434` answers. In a Docker prod deploy without Ollama, the pipeline IS deterministic. So runtime risk depends entirely on deployment.
- **Fix:** Make determinism structural, not incidental. Either (a) delete the Ollama path entirely, or (b) hard-gate it behind an explicit config flag that defaults OFF AND make it provenance-checked — every Ollama-suggested span must exist verbatim in the transcript (same rule as GLiNER), and Ollama must NEVER add diagnoses/allergies, only re-rank what deterministic extraction already found. Document the guarantee in code so it can't regress.

### F2. The learning flywheel — the "10-year moat" — is not connected to anything
**Severity: Critical (it's the core moat, and it's dead code)**
The flywheel exists as well-written classes but is wired to nothing in the running app:
- `record_correction()` / `record_false_positive()` — **no live endpoint calls them.** `learning_service` is not imported in any route (`app/api/` has zero references). There is **no `/facts` review/edit endpoint** in the current tree.
- `infer_from_diff()` — **never called.**
- `reload_knowledge()` — docstring says "Called once at app startup (from lifespan)" but `main.py` lifespan does NOT call it. So promoted rules are never loaded into the extractor at runtime.
- `extraction_knowledge` table — **never created** by any `CREATE TABLE` in the codebase. On a fresh DB the learning queries fail outright.

- **Why it matters:** Every YC claim about "corrections compound, the model gets smarter from usage" is currently vaporware in code. The prior session believed `routes_notes.review_extracted_fact` wired this up — that code is NOT in the current working tree (lost in the git stash incident, or never committed).
- **Fix (in order):** (1) Add `CREATE TABLE extraction_knowledge` + `fact_corrections` to `db.py init_db` and the SQLITE_MIGRATIONS list. (2) Call `async_reload_knowledge()` in `main.py` lifespan after `init_db()`. (3) Build the doctor fact-review endpoint (accept/edit/reject) that calls `record_correction` / `record_false_positive`. (4) Re-run `async_reload_knowledge()` after each promotion. Until (1)-(4) exist, do not claim the flywheel works.

### F3. "Every fact requires doctor confirmation" is not enforced in the backend
**Severity: High (clinical claim vs reality)**
`routes_notes.process_clinical` extracts facts and immediately writes `clinical_facts`, `memory_state`, `soap_note`, `cds_suggestions` and sets `status=complete`. There is no review gate. `provenance.py` has `review_status`/`confirmed_by` fields but they **default to `"confirmed"` / `"system"`** (provenance.py:169-170) — i.e. facts are auto-confirmed as the system, not a human — and provenance does not appear wired into the live pipeline. The `soap_feedback` table captures accept/edit/reject but only *after* the fact, and nothing blocks an unreviewed SOAP from being printed/exported.

- **Why it matters:** The doctor-approval gate is the safety story for a clinical product. Right now it's a frontend convention, not a backend guarantee, with no audit that any given fact was human-reviewed.
- **Fix:** Add a real `review_status` on stored facts defaulting to `candidate`; block FHIR export / prescription / investigation-order generation unless the doctor has explicitly confirmed; record who confirmed and when. This also feeds F2's learning loop cleanly.

---

## SECTION 1 — CLINICAL SAFETY

| # | Sev | What | Fix |
|---|-----|------|-----|
| C1 | Critical | F1 above — LLM (Ollama) injects diagnoses/allergies into SOAP path with no provenance | Hard-gate + provenance-check or remove |
| C2 | High | F3 above — no backend confirmation gate; provenance defaults to system-confirmed | Add candidate→confirmed gate, block exports until confirmed |
| C3 | High | CDS allergy/interaction lists are good but partial. Cross-reactivity map (cds_engine.py:9-86) covers penicillin/sulfa/NSAID/cephalosporin/statin/ACE but **misses**: carbamazepine/phenytoin cross-reactivity, iodine/contrast, codeine/opioids, local anaesthetic (-caine) class. Drug-interaction list (4 rules) misses common Indian combos: metformin+contrast, warfarin+antibiotics (azithromycin/ciprofloxacin), digoxin+diuretics, methotrexate+NSAID, SSRIs+tramadol (serotonin syndrome). | Expand both maps; have the doctor advisor review the list quarterly |
| C4 | High | PHI scrubber is US-centric and misses Indian PHI. `_PHONE_REGEX` (phi_scrubber.py:25) matches US 3-3-4 format — **Indian 10-digit mobiles are NOT scrubbed**. No Aadhaar (12-digit), no ABHA (14-digit), no PAN. spaCy NER is disabled, so a bare name ("Ramesh ko bukhar hai") survives. | Add Indian patterns: `\b[6-9]\d{9}\b` (mobile), `\b\d{4}\s?\d{4}\s?\d{4}\b` (Aadhaar), `\b\d{2}-?\d{4}-?\d{4}-?\d{4}\b` (ABHA). DPDPA exposure otherwise. |
| C5 | Medium | Negation verified working in tests (17/17, 18/18) but only sampled in code. "ibuprofen nahi dena" correctly excluded per tests. | Keep the regression tests; add more adversarial negation cases |

## SECTION 2 — SECURITY

| # | Sev | What | Fix |
|---|-----|------|-----|
| S1 | High | **No rate limiting anywhere.** `/auth/token` is brute-forceable; `process-clinical` and the WS audio stream can burn unlimited Sarvam/Gemini spend. An authenticated user could rack up ₹10k+ in API cost in minutes. | Add slowapi / a reverse-proxy rate limit. Cap per-user sessions/day. |
| S2 | High | **WS audio upload has no size limit** (routes_ws.py:61-68, `while True: f.write(chunk)`). A client can fill the disk. | Enforce a max-bytes cap per stream; close at limit. |
| S3 | High | **`repo.get_doctor_profile()` does not exist** in `SessionRepository`. Both `prescription_renderer.py:39` and the new `investigation_order_renderer.py:161` call it → `AttributeError` at render time. (This means the prescription print path is currently broken too, and my 3.1 investigation-order render was only import-verified, not run end-to-end.) | Add `get_doctor_profile(user_id)` to repository.py (read from a `doctor_profiles` table or return `{}`), or guard the call. ~10 min. |
| S4 | Medium | `get_current_user` (routes_auth.py:28) **never checks `is_active`.** A deactivated user keeps full access until their 24h token expires. | Check `if not user["is_active"]: raise credentials_exception`. |
| S5 | Medium | **Open registration** (`/auth/register`) with no invite/clinic binding. Harmless today, but becomes the attack surface the moment the learning loop (F2) goes live — register N accounts → poison promoted aliases globally (`load_promoted_knowledge` is global, not clinic-scoped; the `unique_clinics` counter in learning_service.py:204-211 is self-admittedly broken — it increments per *user*, not per real distinct clinic). | Before wiring F2: gate registration (invite/clinic), scope promotions per-clinic, fix the unique-clinic count to dedupe real clinic IDs, keep auto-promote conservative. |
| S6 | Medium | Demo creds in source: `demo_username="arush"`, `demo_password="1234"` (config.py:18-19). Gated behind `seed_demo_user` (default False), so not seeded by default — but if ever enabled in prod, known account exists. | Remove defaults; require env if demo seeding is on. |
| S7 | Low/Med | JWT passed as WS query param (`?token=`) — lands in proxy/server access logs. | Use a short-lived ticket or subprotocol header. |
| S8 | Low | `access_token_expire_minutes=1440` (24h), no refresh/revocation. Leaked token valid all day. | Shorten to ~60min + refresh token. |
| — | Good | SQL is fully parameterised (repository.py). Authorization is correctly enforced — every `get_session`/`update_session` filters by `user_id`. CORS uses `allow_credentials=False` with explicit origins. `secret_key` has no default (fails closed). XSS: HTML renderers escape via `html.escape`. SOAP generation is 100% deterministic (no LLM) — the moat works *here*. |

## SECTION 3 — DATA INTEGRITY

| # | Sev | What | Fix |
|---|-----|------|-----|
| D1 | High | `extraction_knowledge` / `fact_corrections` tables never created (see F2). Learning is dead on a fresh DB. | Add to schema + migrations. |
| D2 | Medium | No real migration framework — hand-rolled `SQLITE_MIGRATIONS` list (db.py:164), and PG path has no migration list at all (schema drift between SQLite and PG). | Adopt Alembic, or at least mirror migrations across both engines. |
| D3 | Medium | `list_sessions` loads all user rows then slices in Python (routes_sessions.py:44-49, already TODO'd). Fine <500 sessions, full scan after. | Push LIMIT/OFFSET into SQL. |
| D4 | Medium | Pipeline exception handling: `process_clinical` wraps the pipeline in try/except and 500s, but a mid-pipeline failure after partial writes could leave `status` inconsistent. | Write status transitions atomically; set `status=failed` on exception. |
| D5 | Low | Audio deletion after processing is best-effort (routes_notes.py:152-158); if `unlink` fails, PHI audio persists on disk unencrypted. | Encrypt audio at rest; add a sweeper for orphaned `*_live.webm`. |

## SECTION 4 — EXTRACTION QUALITY (sampled, not exhaustive)

Tests pass 17/17 and 18/18 on the two reference transcripts, so the core is solid. Likely gaps to **test** (not confirmed missing):
- Med status: verify "band kar diya", "phir se shuru karo", "dose aadha kar do", "double kar do", "zyada ho gaya" all classify correctly.
- Vitals: confirm SpO2 ("oxygen 95"), temperature in °F ("temperature 101"), random sugar ("sugar random 180", "RBS 180") are captured.
- Follow-up: confirm "teen din baad", "agle mahine", "ek mahine baad" resolve.
- Investigations: confirm Indian abbreviations LFT/KFT/TFT/USG/2D-echo/Widal/CRP all extract.
- Long transcripts: Ollama prompt truncates at 4000 chars (ollama_extractor.py:103); deterministic extractor behavior on 30-min transcripts unverified.

## SECTION 5 — LEARNING LOOP
Covered in F2 + S5. Summary: well-designed, completely unwired, table missing, global promotion + open registration + broken clinic-count = must be hardened *before* it goes live, not after.

## SECTION 6 — PRODUCT GAPS (vs YC bar)

1. **Service-company surfaces barely exist.** Investigation order (3.1) just built but render path is broken (S3). Follow-up message (3.2), assistant work queue (3.3) not built. Without these Lipi is still a scribe. This is the single biggest product gap.
2. **No assistant-facing surface.** The whole pitch is "AI-native service company" but there is no work queue, no task list, nothing the *assistant* (not doctor) logs into. The demo moment doesn't exist yet.
3. **Prescription is missing India-required fields** — no Schedule H/H1 indicator, no generic-substitution line, no "drugs dispensed" register hook. A real Indian Rx needs these.
4. **No patient-facing surface** beyond a WhatsApp link. The secure-link portal is referenced but not audited here.
5. **WhatsApp will crash on send.** `settings.twilio_account_sid/auth_token/whatsapp_number` are referenced in whatsapp_service.py:63-65 but **not defined in `config.py`** → `AttributeError` before the mock fallback. Directly blocks 3.2. Fix config first.

## SECTION 7 — YC READINESS

- **Strongest asset:** deterministic SOAP generation genuinely has no LLM (verified). That part of the moat is real.
- **Weakest:** the two things you pitch hardest — zero-LLM *extraction* and the compounding learning flywheel — are exactly the two that don't hold up in code today (F1, F2). A technical DD would find this.
- **"Why not Augnito + a work queue?"** Your honest answer (Hinglish-native + provenance + OPD economics) is good, but only once F1/F2/F3 are real. Right now the differentiated parts are partially aspirational.
- **Metrics to show:** acceptance rate, edit rate per field, cost/consultation, corrections→promotions count. None are currently computed (no analytics audited, learning unwired).

## SECTION 8 — CODE QUALITY

- Logging: WhatsApp logs phone numbers (whatsapp_service.py) — borderline PHI in logs. Audit all `logger.info` for identifiers.
- `routes_clinics.py` exists but is **not mounted** in main.py — dead route file.
- Exceptions: `process_clinical` returns `detail=f"Processing error: {e}"` (routes_notes.py:140) — leaks internal error text to client. Return a generic message; log the detail.
- No health check beyond `routes_health` (not audited). No security headers (HSTS, X-Content-Type-Options).

---

## FINAL DELIVERABLES

### Top 10 to fix before pilot (in order)
1. **F1** — Hard-gate/remove the Ollama LLM path so the pipeline is *structurally* deterministic.
2. **F3** — Enforce doctor confirmation in the backend before any export/print.
3. **S3** — Add `get_doctor_profile` (prescription + investigation-order render are broken without it).
4. **C4** — Indian PHI scrubbing (Aadhaar, Indian mobile, ABHA) — DPDPA exposure.
5. **S1** — Rate limiting (cost-bomb + brute force).
6. **S2** — WS audio size cap (disk-fill DoS).
7. **P5** — Define Twilio settings in config (WhatsApp/3.2 crashes otherwise).
8. **D1/F2** — Create learning tables + call `reload_knowledge` at startup.
9. **S4** — Check `is_active` in `get_current_user`.
10. **C3** — Expand CDS interaction/cross-reactivity lists (advisor-reviewed).

### Top 5 product gaps hurting YC / retention
1. Assistant work queue (the demo moment) — doesn't exist.
2. Investigation order + follow-up message — half-built / blocked by S3 + Twilio.
3. Learning flywheel not actually compounding (F2).
4. Prescription missing India-required fields.
5. No metrics/analytics dashboard to prove value.

### YC verdict
Not ready to apply *on the technical story* yet — not because the ideas are wrong but because the two headline moats (zero-LLM extraction, compounding learning) are partially aspirational in code (F1, F2). The deterministic SOAP core is real and defensible. Close F1/F2/F3 and build the assistant work queue, and the pitch matches the code. Single biggest gap: **the flywheel must actually run.**

### Moat assessment
Real and hard to replicate: Hinglish-native deterministic extraction + provenance + OPD-economic fit. Replicable in <12 months by a funded competitor IF they decide to enter Indian OPD — your defense is being in clinics first with live correction data. But that defense only exists once F2 (the learning loop) is actually wired and accumulating data. Today it accumulates nothing.

### Readiness scores
- Pilot safety: **5/10** (deterministic SOAP good; Ollama path, no confirmation gate, Indian PHI gaps drag it down)
- YC application: **4/10** (great narrative, but DD would expose F1/F2; no service surfaces yet)
- Technical defensibility: **6/10** (the architecture is genuinely differentiated; execution gaps are closable in 2-3 weeks)

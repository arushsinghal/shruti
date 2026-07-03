# 27 — Clinical Memory Assistant ("Jarvis") — Build Spec

**Author:** Opus (Claude)
**Date:** 2026-07-03
**Status:** Spec, not yet built. Ready to hand to an implementer.
**Related:** [[02_ARCHITECTURE_MAP]] · [[10_CONTINUAL_LEARNING_SYSTEM]] · [[17_ABDM_DHIS_DSC_COMPLIANCE]] · [[07_DECISIONS]]

---

## 0. The compliance constraint — read this before writing any code

This is not a preference, it's a hard requirement, verified 2026-07-03 against current law and policy:

- **DPDP Act 2023** is permissive on cross-border transfer (Section 16, blacklist model, no countries currently restricted), and its transfer provisions don't even take effect until May 2027. DPDP is not the binding constraint here.
- **ABDM's Health Data Management Policy is the binding constraint, already in force:** *"No personal data shall be stored beyond the geographical boundaries of India."* Every patient record this feature touches is ABHA-linked health data under that policy. It controls, regardless of what DPDP permits.
- Draft DPDP Rules also signal the government may name health data specifically for mandatory in-India-only storage even under the future cross-border regime. Build for that outcome now.

**D017 (proposed, add to `07_DECISIONS.md` once accepted):** No patient data — raw or retrieved — is ever sent to a foreign-hosted inference API for this feature. Inference and the retrieval index both run on India-hosted infrastructure only. This is structural, not a runtime toggle.

**What this rules out:** direct calls to Anthropic, OpenAI, Google, or any other foreign-hosted LLM API with patient context in the prompt, for this feature, under any circumstance.

**What this requires:**
- **Inference:** Sarvam's LLM offering (same vendor already used for ASR, Indian company, on-shore) as the default. If capability is insufficient, fall back to a self-hosted open-weight model (Llama / Qwen / DeepSeek class) on India-region cloud compute (AWS `ap-south-1` Mumbai, Azure Central India) — never a foreign SaaS inference endpoint.
- **Retrieval index:** `pgvector` on the existing Postgres instance. No new vector-DB vendor, no new cross-border question, already India-hosted.
- **PHI minimization regardless of hosting:** prompts reference patients by internal ID, not name/ABHA number. Retrieval pulls structured facts, not raw transcripts, wherever the summarized form is sufficient.

Verify current Sarvam LLM model capability against this use case before committing; this spec assumes it's viable but that hasn't been benchmarked yet.

---

## 1. What this is

A persistent, per-doctor retrieval assistant that sits on every authenticated screen after login. It answers questions like "how did I treat a similar case last time" or "what was this patient on before" by searching that doctor's own confirmed consultation history — never another doctor's patients, never silently injecting anything into the current record.

**The core design principle, inherited from the rest of the product:** retrieval only, never auto-injection. Same "no proof, no fact" discipline that governs extraction applies here to retrieval — every answer must cite the specific past visit it came from. This is not a chatbot that talks about medicine in general; it is a search interface over one doctor's own confirmed work, with citations.

---

## 2. Why this is a real moat, not a gimmick

No EMR or scribe competitor can ship this — they don't have the corpus. This only works after months of doctor-confirmed, evidence-backed consultations exist per doctor, which is exactly what the correction flywheel has been quietly accumulating. This is the first feature that turns that accumulated data into something the doctor directly experiences as valuable, rather than just an accuracy improvement they don't see.

---

## 3. Safety boundaries (non-negotiable, mirrors existing D003/D004 discipline)

1. **Retrieval only, never write.** This feature never modifies `clinical_facts`, `memory_state`, or `soap_note`. It only reads and displays. No exceptions.
2. **Scoped to one doctor's own patients.** No cross-doctor, no cross-clinic aggregation in v1. That's a different, harder feature requiring the flywheel's scope/promotion machinery — not this one.
3. **Current-patient boundary respected.** When a session is open, the assistant may reference the current patient's own past visits freely (continuity of care), but must never surface another patient's data into that context. Mirrors the `allow_multi_visit` guardrail already added to `memory_context.py` — this feature is a second, independent enforcement point for the same boundary.
4. **Every answer cites its source.** Minimum: patient (or "this patient" if same-session), visit date, and a link to that visit's record. An answer with no citation is a bug, not a feature.
5. **De-identified prompts.** Internal patient/session IDs in prompts, not names or ABHA numbers. Resolve to display names only in the UI layer, after the model response.
6. **Only confirmed facts are indexed.** Candidate/rejected facts never enter the retrieval index — same gate `facts_from_confirmed()` already applies to FHIR export.

---

## 4. Data model

New tables (SQLite + Postgres, following the existing `db.py` migration pattern):

```sql
CREATE TABLE IF NOT EXISTS clinical_memory_chunks (
    id TEXT PRIMARY KEY,
    doctor_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    visit_date TEXT NOT NULL,
    chunk_type TEXT NOT NULL,       -- 'diagnosis' | 'medication' | 'plan' | 'visit_summary'
    chunk_text TEXT NOT NULL,       -- de-identified structured summary, not raw transcript
    embedding VECTOR(1536),         -- pgvector; dimension depends on chosen on-shore embedding model
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_memory_chunks_doctor ON clinical_memory_chunks(doctor_id);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_patient ON clinical_memory_chunks(patient_id);
```

Chunks are generated once, when a session's facts move to `confirmed` status (hook into the same place `record_correction()` already fires in `routes_fact_review.py`) — not from raw transcripts. Re-generate/append on each finalized visit, never edit historical chunks in place (append-only, matches the audit-trail discipline elsewhere).

---

## 5. Retrieval architecture

```
Doctor query ("how did I treat this before?")
  → embed query (on-shore embedding model)
  → pgvector similarity search, WHERE doctor_id = current_doctor
    (+ WHERE patient_id = current_patient if a session is open and doctor asks about "this patient")
  → top-k chunks retrieved, each carrying session_id + visit_date
  → assembled into prompt with de-identified IDs
  → on-shore LLM (Sarvam) generates answer
  → UI resolves session_id → patient name/date for display, attaches "View visit" links
```

New backend service: `backend/app/services/clinical_memory_service.py`
- `index_session(session_id)` — called on fact confirmation, generates chunks + embeddings
- `query(doctor_id, query_text, patient_id=None, k=5)` — retrieval + generation, returns `{answer, citations: [{session_id, visit_date, snippet}]}`

New routes: `backend/app/api/routes_memory_assistant.py`
- `POST /assistant/query` — `{query, session_id?}` → answer + citations. `session_id` optional; when present, biases retrieval toward that patient first.

---

## 6. Config / API keys needed

Add to `backend/app/utils/config.py` `Settings`, following the existing pattern:

```python
sarvam_llm_api_key: str = ""       # if Sarvam exposes a separate key from ASR
memory_assistant_enabled: bool = False   # feature flag, default off until benchmarked
embedding_model_path: str = ""     # if self-hosted embedding model
```

No foreign LLM keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) should ever be read by this feature — enforce this with a code-level assertion in `clinical_memory_service.py`, not just a policy note, so a future contributor can't accidentally wire in a foreign provider.

---

## 7. UI placement and design

Matches the existing Lipi design language exactly — same tokens already used across `Landing.tsx` / `Dashboard.tsx` / `ProductShowcase.tsx`: `bg-bg-warm`, `text-text-dark`, `primary`/`primary-dark`, `rounded-3xl`, `border-slate-200/80`, Motion (`framer-motion`) for transitions.

**Placement:** a persistent floating trigger, bottom-right, on every authenticated page (`Dashboard`, `Consultation`, `PatientProfile`, `PatientTimeline`, `ReviewNote`) — collapsed by default, expands into a panel on click. Never auto-opens, never interrupts the doctor's flow.

**Collapsed state:** small circular button, `bg-primary text-white`, matches the existing "श" logo mark styling. Subtle pulse only if there's a genuinely new relevant surfacing (e.g., "3 similar past visits found for this patient") — otherwise static, no idle animation (per the taste-skill's "motion must be motivated" rule — this is a utility panel, not a marketing surface).

**Expanded panel:** `rounded-3xl border border-slate-200/80 bg-white shadow-[0_40px_90px_-40px_rgba(27,94,59,0.35)]` — same shadow/radius language as `ProductShowcase`. Structure:
- Header: doctor's name + "Clinical memory" label, collapse button
- If a session is open: a pinned "This patient" context strip showing the current patient's name and a one-line summary of prior visits, always visible
- Below: query input + conversation thread
- Every assistant response renders as a card with the answer text and a citations row below it — small pills, each showing visit date + patient name (or "this patient"), clickable to open that visit's record

**Empty state:** "Ask about a past case, or a patient's history. Every answer traces back to the actual visit." — not a gimmick empty state, functional.

**Mobile:** collapses to a bottom sheet rather than a floating panel; same content, full-width.

---

## 8. Build phases

**Phase 1 (ship first, safest, most contained):** same-patient-only retrieval. Doctor opens a patient's session, asks "what did we try last time," gets an answer scoped only to that one patient's own history. No cross-patient search yet. This alone proves the retrieval + citation UX and de-risks the on-shore inference pipeline before widening scope.

**Phase 2:** cross-patient search within one doctor's full patient base ("find a similar case I've seen before"). Requires the doctor to explicitly search rather than it being ambient in every session — an intentional friction point so it's never confused with the current patient's own record.

**Phase 3 (not in this spec, future):** anything cross-doctor or cross-clinic. This needs the flywheel's scope/promotion/safety-gating machinery from `10_CONTINUAL_LEARNING_SYSTEM.md`, not a simple RAG panel. Do not build this without that infrastructure existing first.

---

## 9. Open questions before implementation starts

- [ ] Benchmark Sarvam's current LLM offering against this use case — does it handle retrieval-augmented clinical Q&A well enough, or is a self-hosted fallback needed from day one?
- [ ] Embedding model choice — must also be on-shore-inferable; confirm what's available before locking the `VECTOR(1536)` dimension in the schema above.
- [ ] Chunk regeneration policy when a doctor edits a previously confirmed fact after the fact (rare, but the append-only chunk store needs a defined behavior — new chunk superseding old, not silent overwrite).
- [ ] Rate/cost limits per doctor per day, since this is now a second LLM cost center alongside Sarvam ASR — needs to feed the cost-per-consultation ledger once that's built (see `12_IMPLEMENTATION_GAP_REGISTER.md`).

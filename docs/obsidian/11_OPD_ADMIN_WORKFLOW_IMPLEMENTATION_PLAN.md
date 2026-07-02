# OPD Admin Workflow Implementation Plan

> Date: 2026-06-27
> Status: Build plan saved after implementation was undone
> Scope: Product and engineering plan only. No backend/frontend code lives in this note.
> Related: [[00_HOME]], [[02_ARCHITECTURE_MAP]], [[05_VALIDATION_PLAN]], [[06_API_COSTS]], [[09_STRATEGIC_ROADMAP]], [[10_CONTINUAL_LEARNING_SYSTEM]]

## One-Line Goal

Build Lipi's first hero workflow as an evidence-backed OPD admin worker:

```text
doctor speaks once
-> Lipi extracts evidence-backed facts
-> doctor reviews and approves facts
-> Lipi creates assistant work queue and admin documents
-> clinic finishes post-consultation work faster
-> correction and cost data feed the learning flywheel
```

This should make Lipi feel like a healthcare administration service, not just an AI scribe.

## Non-Negotiable Boundary

Do not touch the clinical extraction layer for this roadmap unless there is a direct evidence/provenance bug.

Do not modify these for feature work:
- `backend/app/services/clinical_extractor.py`
- clinical fact extraction logic
- memory/conflict clinical logic
- rule/fuzzy/regex/GLiNER extraction behavior

The admin workflow should consume existing reviewed facts:
- `session.extracted_facts`
- `session.clinical_facts`
- `facts_from_confirmed(...)`
- existing evidence spans
- existing doctor review status

Clinical rules remain:
- No proof -> no fact.
- Doctor review required.
- Gemini formatting only, not clinical fact creation.
- Admin outputs must not invent medical content.
- Missing fields stay missing.
- Pre-auth fields must not be inferred.

## Hero Feature

The hero feature should be:

## Evidence-Backed OPD Admin Work Queue

After the consultation, Lipi should show:
- evidence review status
- assistant tasks
- investigation order
- referral letter
- pre-auth readiness
- cost per consultation
- flywheel metrics
- internal ops queue

This is stronger than "AI scribe" because it sells completed post-consultation work.

## Build Order

### 1. Evidence Review UI

Purpose:
- Prove "no proof -> no fact."
- Give doctor fast accept/edit/reject flow.
- Make evidence spans visible beside every fact.

Current surface:
- `frontend/src/components/FactsReviewEditor.tsx`
- existing backend fact review routes in `routes_notes.py`

Expected behavior:
- Facts show category, value, confidence, extractor, certainty, source sentence.
- Doctor can accept, edit, reject.
- Rejected facts never enter final admin outputs.
- Edited doctor facts are marked as doctor-created/reviewed.

Why it matters:
- Trust foundation.
- Creates correction signal.
- Differentiates from black-box scribe output.

### 2. Assistant Work Queue

Purpose:
- Turn the reviewed consultation into service work.

Tasks to generate:
- evidence review pending
- final record approval
- investigation order
- referral letter
- follow-up reminder
- insurance pre-auth readiness
- missing info collection

Suggested backend API:

```text
GET   /api/sessions/{session_id}/admin-workflow
GET   /api/admin/work-queue
PATCH /api/admin/work-queue/{item_id}
```

Suggested DB table:

```text
assistant_work_items
- id
- session_id
- user_id
- task_type
- title
- status: pending | needs_review | needs_info | blocked | in_progress | done | cancelled
- owner_role: doctor | assistant | ops
- priority: critical | high | medium | low
- due_at
- notes
- source
- created_at
- updated_at
```

Why it matters:
- This is the first "AI-native service company" surface.
- It lets Lipi humans or clinic assistants complete work while automation improves.

### 3. Investigation Order Generator

Purpose:
- Convert approved investigation intent into a printable/shareable order.

Inputs:
- approved `investigation` facts
- patient name, age, sex
- doctor name
- evidence spans

Output:
- document type: `investigation_order`
- items list
- evidence per item
- doctor review required status
- missing fields if no investigations found

Safety:
- Do not add investigations that were not said or entered by doctor.
- If no evidence, show missing/needs review.

Why it matters:
- Very achievable.
- Immediate assistant value.
- Clear demo moment after evidence review.

### 4. Referral Letter Generator

Purpose:
- Draft a referral letter from approved facts and patient context.

Inputs:
- approved symptoms
- approved diagnoses/impression
- approved investigations
- approved medications
- follow-up plan
- patient demographics

Output:
- doctor review required draft
- reason for referral
- body text
- evidence references

Safety:
- "Working assessment noted by doctor" only when diagnosis/impression is present.
- Do not create diagnosis certainty.
- Missing reason remains missing.

Why it matters:
- Strong visible value.
- Uses existing approved facts.
- Helps clinics immediately.

### 5. Cost-Per-Consultation Ledger

Purpose:
- Make unit economics visible from day one.

Suggested backend API:

```text
GET /api/admin/cost-ledger
```

Per-session fields:
- session id
- estimated audio minutes
- Sarvam cost
- local extraction cost
- document generation cost
- total INR
- notes

Initial estimate:
- Sarvam plain STT: INR 30/hour
- default 5 minute consultation: INR 2.50
- local extraction: INR 0
- local templates: INR 0

Why it matters:
- Indian clinic pricing depends on margin discipline.
- Supports YC/service-company story.
- Exposes when API costs break pricing.

### 6. Flywheel Analytics Dashboard

Purpose:
- Show whether Lipi is improving.

Suggested backend API:

```text
GET /api/admin/flywheel-analytics
```

Metrics:
- total facts
- confirmed facts
- candidate facts
- rejected facts
- confirmation rate
- rejection rate
- facts added
- facts deleted
- facts modified
- extraction precision
- extraction recall
- feedback by field/type
- pipeline layer accepted/rejected counts

Why it matters:
- This is the moat dashboard.
- It turns doctor corrections into measurable learning signal.
- It tells which extractor layer or workflow causes human work.

### 7. One Insurance Pre-Auth Form

Purpose:
- Build one payer/form MVP, not generic insurance automation.

Recommended first form:
- Star Health pre-auth MVP or one real TPA form from pilot clinic.

Fields:
- payer/form name
- patient name
- age
- sex
- policy/member id
- diagnosis/impression
- chief complaint
- investigation summary
- proposed procedure/admission
- estimated cost
- vitals if available
- missing fields list

Safety:
- Do not infer policy id, procedure, admission, or cost.
- Missing fields must be collected.
- Every clinical field should trace to approved fact/evidence.

Why it matters:
- Highest business-value feature.
- But should come after evidence review and admin queue.

### 8. Internal Ops Console

Purpose:
- Let Lipi act as a service company before full automation.

Suggested route:

```text
/ops
```

Views:
- assistant work queue across sessions
- queue summary
- task status updates
- cost ledger
- flywheel analytics
- links back to consultation

Why it matters:
- Human-in-loop service delivery.
- Lets Lipi complete work while learning.
- Creates data for future automation.

## Suggested Backend Files

Add:

```text
backend/app/services/admin_workflow.py
backend/app/api/routes_admin.py
```

Modify:

```text
backend/app/main.py
```

Do not modify for this roadmap:

```text
backend/app/services/clinical_extractor.py
backend/app/services/clinical_pipeline.py
```

Optional later:

```text
backend/app/storage/db.py
backend/app/storage/repository.py
```

Use DB migrations only if queue persistence needs to be first-class. A first cut can create `assistant_work_items` lazily in `routes_admin.py`, then move to formal migrations later.

## Suggested Frontend Files

Add:

```text
frontend/src/components/AdminWorkflowPanel.tsx
frontend/src/pages/OpsConsole.tsx
```

Modify:

```text
frontend/src/types/clinical.ts
frontend/src/lib/api.ts
frontend/src/pages/Consultation.tsx
frontend/src/pages/Dashboard.tsx
frontend/src/App.tsx
```

Do not rewrite:

```text
frontend/src/components/FactsReviewEditor.tsx
```

Only integrate with it. It is already the right foundation.

## Suggested API Shape

### Session Admin Workflow

```text
GET /api/sessions/{session_id}/admin-workflow
```

Returns:

```text
{
  session,
  evidence_review,
  work_items,
  documents: {
    investigation_order,
    referral_letter,
    insurance_preauth
  },
  cost
}
```

### Work Queue

```text
GET /api/admin/work-queue
PATCH /api/admin/work-queue/{item_id}
```

### Cost Ledger

```text
GET /api/admin/cost-ledger
```

### Flywheel Analytics

```text
GET /api/admin/flywheel-analytics
```

## Product UX

Consultation page after facts are reviewed:

```text
Clinical result
Evidence-backed OPD admin workflow
  - evidence review summary
  - assistant work queue
  - investigation order
  - referral letter
  - insurance pre-auth readiness
  - per-consultation cost
```

Dashboard:

```text
Add "Ops Console" link
```

Ops Console:

```text
top metrics
work queue
cost ledger
flywheel analytics
```

## Runtime Verification Plan

Before calling it done:

```text
python3 -m py_compile backend/app/services/admin_workflow.py backend/app/api/routes_admin.py backend/app/main.py
cd frontend && npx tsc --noEmit --noUnusedLocals false --pretty false
cd frontend && npm run build
cd backend && uv run python -m pytest tests/ -q
```

Then run:

```text
cd backend && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

Verify:

```text
GET http://127.0.0.1:8000/api/health
Open http://127.0.0.1:5173
Create/login user
Create consultation
Submit demo transcript
Process clinical pipeline
Review facts
See admin workflow panel
Open /ops
Update work item status
Check cost ledger and flywheel metrics
```

## Known Runtime Blockers Observed

During this session, app startup was attempted after code work was undone.

Observed:
- Frontend Vite eventually became ready at `http://127.0.0.1:5173/`, but startup was very slow.
- Backend startup did not reach `/api/health`.
- Backend failed while loading FastAPI/Pydantic because environment metadata appears broken around `email-validator`.
- Earlier `uv run pytest` also failed because `.venv` metadata for `aiosqlite-0.22.1 2.dist-info` has invalid version text.

This means runtime verification needs environment repair before full app confidence.

Likely cleanup:
- recreate backend `.venv`
- reinstall backend dependencies from lock/requirements
- ensure `email-validator` has valid metadata
- ensure `aiosqlite` dist-info directory is not duplicated/corrupt

Do not confuse these environment blockers with clinical extraction logic.

## What Was Not Touched In The Planned Implementation

The planned implementation should not change clinical extraction behavior.

It should not change:
- extraction dictionaries
- fuzzy matching
- regex matching
- GLiNER extraction
- negation handling
- clinical memory resolution
- SOAP generation semantics
- CDS safety rules

It should only consume already-reviewed facts and build admin workflow outputs.

## Why This Is The Right First Build

This roadmap gives the best balance of achievable and differentiated:

- Evidence review builds trust.
- Work queue makes Lipi a service, not a note app.
- Investigation orders and referral letters are fast to ship.
- Cost ledger proves margins.
- Flywheel analytics makes improvement measurable.
- One pre-auth form creates the money wedge.
- Ops console lets humans complete service work while the system learns.

The moat is not the first UI. The moat is the loop:

```text
approved fact
-> admin task
-> document output
-> human correction
-> cost and outcome data
-> better workflow next time
```

## First Commit Scope

Keep first commit small:

1. Add backend admin workflow service.
2. Add admin routes.
3. Wire admin router into app.
4. Add frontend API types/helpers.
5. Add `AdminWorkflowPanel`.
6. Add `/ops` page.
7. Add dashboard link.
8. Run typecheck and backend compile.

Do not fix unrelated dirty worktree files in the same commit.

## Hero Pitch After Build

> Lipi is not an AI scribe. Lipi is an evidence-backed OPD admin worker. Doctor speaks once, approves facts once, and Lipi turns the consultation into tasks, orders, referral letters, follow-up work, pre-auth readiness, and a learning flywheel.

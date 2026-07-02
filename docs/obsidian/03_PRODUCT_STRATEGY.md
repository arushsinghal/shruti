# Product Strategy

## Positioning

Lipi is an AI-native OPD administration service for Indian clinics.

It begins with consultation capture because that is the highest-friction daily habit. The larger product is the workflow after the consultation: reviewed records, patient timeline, assistant tasks, follow-ups, referrals, investigation orders, insurance/admin readiness, and operating memory for the clinic.

Do not position Lipi as only an AI scribe. The scribe is the entry point. The service is completed clinic work.

## Current Wedge

Start where doctors already lose time:

1. Doctor speaks naturally during or after an OPD visit.
2. Lipi transcribes and extracts evidence-backed facts.
3. Doctor reviews, accepts, edits, or rejects facts.
4. Lipi produces doctor-approved records and outputs.
5. The clinic receives follow-up tasks, patient memory, and admin documents.

The wedge works only if review is faster and safer than manual documentation.

## What Lipi Is Not

- Not an autonomous doctor.
- Not a diagnosis engine.
- Not a model that invents missing clinical facts.
- Not a generic EMR migration project.
- Not an ASR research project before market proof.
- Not a pure RL or frontier-agent research lab before the clinic service works.

## YC Framing Rule

YC's AI-native service-company framing strengthens Lipi if the pitch is service-first:

> Lipi does OPD administration work for Indian clinics. A doctor speaks once; Lipi creates reviewed records, prescriptions, referrals, follow-ups, and admin tasks. Every correction becomes a safe learning signal, so Lipi gets better at the clinic's workflow over time.

It weakens Lipi if the pitch becomes research-first:

> We are doing RL, recursive agents, continual learning, sparse attention, or test-time training for healthcare.

The research direction matters, but it is the moat behind the service. Lead with the work Lipi completes, the workflow it replaces, the margin it can earn, and the evidence trail that makes it safe.

## Product Phases

### Phase 1: Capture And Review

Goal:
- Make consultation capture reliable enough for repeated clinic use.

Proof:
- Doctor can review faster than writing manually.
- Extracted facts show evidence.
- Unsupported facts do not appear as clinical truth.
- Sarvam plain STT is good enough for common OPD language mix.
- Cost per consultation is measured.

### Phase 2: Patient Timeline

Goal:
- Make prior context useful in future visits without contaminating current-visit clinical truth.

Proof:
- Allergies, medications, diagnoses, follow-ups, and prior instructions are retrievable and auditable.
- Past context is shown separately from current facts.
- Old facts do not enter current SOAP unless restated or doctor-confirmed.

### Phase 3: Assistant Workflow

Goal:
- Turn approved records into tasks.

Examples:
- Follow-up reminders.
- Investigation order.
- Referral draft.
- Patient instruction message.
- Billing or visit summary.
- Pre-auth readiness checklist.

Proof:
- Assistant can see owner, status, due time, notes, blockers, and completion reason.
- Lipi captures what humans fixed, not just what it generated.

### Phase 4: Clinic Operating Layer

Goal:
- Lipi becomes the memory and workflow layer for small and mid-sized Indian clinics.

Examples:
- Doctor preferences.
- Clinic playbooks.
- Specialty templates.
- Payer/form checklists.
- Usage and margin analytics.
- Internal ops console.

Proof:
- Repeated corrections reduce future edit time.
- Tasks complete faster.
- Admin outputs are accepted more often.
- Gross margin per consultation is visible.

## Immediate Product Roadmap

Build these before advanced research work:

1. Evidence Review UI.
2. Assistant Work Queue.
3. Investigation Order Generator.
4. Referral Letter Generator.
5. Cost-Per-Consultation Ledger.
6. Flywheel Analytics Dashboard.
7. One Insurance Pre-Auth Form.
8. Internal Ops Console.

Why this order:
- Evidence review proves "no proof -> no fact."
- Work queue turns Lipi from tool into service.
- Investigation/referral outputs create visible value quickly.
- Cost ledger proves margins.
- Flywheel analytics turns review data into product improvement.
- One pre-auth form becomes the first money workflow.
- Ops console lets Lipi humans complete work while the system learns.

## Strategic Differentiators

- Evidence-backed clinical extraction.
- Doctor approval at the clinical boundary.
- Indian OPD workflow orientation.
- Hindi/Hinglish/English capture.
- Patient timeline and follow-up memory.
- Admin output generation after clinical review.
- Correction traces that record accept/edit/reject/delete actions.
- Cost tracking per consultation.
- Service-company path beyond documentation.
- Future clinic playbooks and lesson review queue.

## Moat Thesis

The moat is not "we call a better model."

The moat is the reviewed service trace:

```text
audio -> transcript -> evidence-backed facts -> doctor review -> admin task -> document -> assistant action -> outcome -> reusable lesson
```

Competitors can copy a scribe screen. It is harder to copy a compounding ledger of doctor-approved facts, evidence spans, correction patterns, task outcomes, clinic preferences, payer requirements, and verifiers that prevent unsafe reuse.

## Non-Goals For Now

- Broad EMR replacement.
- Autonomous diagnosis.
- Autonomous prescription.
- Training ASR before market proof.
- Complex diarization before real usage shows need.
- RL for clinical fact creation.
- Product copy that claims features not implemented.

## Key Metrics

- Consultations captured per clinic per week.
- Doctor review time per consultation.
- Percent facts accepted without correction.
- False-positive facts deleted by doctor.
- Missing facts added by doctor.
- Assistant tasks generated per consultation.
- Task completion rate and blocker reasons.
- Follow-up completion rate.
- Patient timeline reuse rate.
- Cost per consultation.
- Gross margin per consultation per clinic.

## Pricing Questions

- Price per doctor, per clinic, per consultation, or hybrid?
- Which workflows justify moving from scribe pricing to service pricing?
- Does WhatsApp/follow-up automation belong in base tier?
- What usage level makes Sarvam, messaging, and LLM formatting costs acceptable?
- What is the minimum workflow value before charging?
- Can pre-auth or revenue-cycle work support success-based pricing?

## Related Notes

- [[04_COMPETITORS]]
- [[05_VALIDATION_PLAN]]
- [[06_API_COSTS]]
- [[08_OPEN_QUESTIONS]]
- [[09_STRATEGIC_ROADMAP]]
- [[10_CONTINUAL_LEARNING_SYSTEM]]
- [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]]
- [[12_IMPLEMENTATION_GAP_REGISTER]]
- [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

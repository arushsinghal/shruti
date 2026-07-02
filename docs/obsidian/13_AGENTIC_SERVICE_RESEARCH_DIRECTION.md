# Agentic Service Research Direction

Date: 2026-06-27

Status: Future company research direction. This is not the current product headline.

Related:
- [[00_HOME]]
- [[03_PRODUCT_STRATEGY]]
- [[07_DECISIONS]]
- [[09_STRATEGIC_ROADMAP]]
- [[10_CONTINUAL_LEARNING_SYSTEM]]
- [[11_OPD_ADMIN_WORKFLOW_IMPLEMENTATION_PLAN]]
- [[12_IMPLEMENTATION_GAP_REGISTER]]

## Core Thesis

Lipi should become an AI-native healthcare administration service that gets better on the job.

This does not mean "remember every transcript." It means learning the small, reusable operational lessons that make a human assistant better over time:

- How a specific doctor wants outputs written.
- Which fields a clinic always needs.
- Which facts the extractor often misses or overcalls.
- Which document changes doctors repeatedly make.
- Which assistant tasks get blocked.
- Which payer or form rejects submissions.
- Which workflow reduces review time.

The core principle:

> Lipi should remember how work gets done, not blindly remember what patients said.

Clinical truth remains evidence-backed. Operational learning can improve workflows, templates, routing, retrieval, missing-field checklists, and admin completion.

## Why This Matters

Modern frontier models are already strong at language and reasoning. Bigger context windows also let systems see more history than before. But real service work still fails for reasons that are not solved by raw intelligence alone.

Real clinic work is messy:

- Each doctor has shorthand, style, and habits.
- Each clinic has informal SOPs.
- Each assistant knows local rituals that are not written anywhere.
- Each specialty has different document expectations.
- Each city or region has different language mix and disease patterns.
- Each payer or TPA may reject forms for different missing fields.
- Patients may need reminders to go to a family member, not always directly to them.
- A phrase that means "current medicine" for one doctor may mean "past medication" for another.

This knowledge is local, sparse, operational, and fast-changing. It often cannot be stuffed into one global training run. The right system has to learn from actual work while preserving safety.

## YC Framing: Strengthens Or Weakens?

This direction strengthens the YC story if framed correctly.

Strong framing:

> Lipi is an AI-native OPD administration service for Indian clinics. A doctor speaks once; Lipi produces reviewed records, prescriptions, referrals, follow-ups, and admin tasks. Every correction becomes a safe learning signal, so Lipi gets better at each clinic's workflow over time.

This matches the AI-native service-company thesis because Lipi is trying to do the work, not merely sell a tool.

Weak framing:

> Lipi is researching RL, recursive agents, sparse attention, test-time training, and continual learning for healthcare.

That sounds abstract, unfocused, and risky for healthcare. It makes the company look like a research project before it has proven the service wedge.

Rule:

> Product first. Service delivery second. Learning moat third. Research jargon last, and only when the audience asks.

## Differentiation From Eka And Generic Scribes

Generic scribe flow:

```text
transcript -> LLM note -> doctor edits note
```

Common weakness:
- Output may be hard to trace.
- Corrections improve only if the vendor retrains a broad model.
- The product usually ends at documentation.
- It does not naturally capture task outcomes, assistant work, payer failures, or clinic playbooks.

Lipi target flow:

```text
audio -> transcript -> evidence-backed facts -> doctor review -> admin tasks -> documents -> assistant action -> outcome -> reusable lesson
```

The differentiation is the full trace:

- Which extractor produced the fact.
- Which evidence span supports it.
- Whether the doctor accepted, edited, deleted, or added it.
- Which output used it.
- Which assistant task was created.
- Whether the task completed, blocked, or failed.
- Whether the lesson is reusable.
- Which scope it belongs to: patient, doctor, clinic, specialty, payer, region, or global.

That trace can become a compounding service data moat if captured cleanly.

## What The Agent Should Learn

### Clinic Preferences

- Prescription format.
- Referral letter format.
- Follow-up cadence.
- WhatsApp wording.
- Print/share defaults.
- Assistant handoff format.

### Doctor Preferences

- Note structure.
- Diagnosis wording style.
- Investigation order style.
- Common correction patterns.
- Signature and letterhead format.

### Specialty Playbooks

- Cardiology chest-pain tasks.
- Gynecology LMP/GA/anomaly-scan fields.
- Pediatrics weight/dose/vaccine context.
- Dermatology lesion and topical medication structure.
- Chronic disease follow-up checklist patterns.

### Payer And Admin Rules

- Pre-auth mandatory fields.
- Claim rejection reasons.
- TPA-specific document checklists.
- Billing coding requirements.
- Missing-field patterns.

### Extraction And Workflow Failure Modes

- Recurring false positives.
- Recurring missing facts.
- Phrases that require confirmation.
- Fields assistants repeatedly add manually.
- Task types that often get blocked.
- Documents that doctors repeatedly edit.

## What The Agent Must Not Learn Unsafely

Hard boundaries:

- Do not turn past patient facts into current clinical facts.
- Do not generate diagnosis certainty.
- Do not auto-prescribe.
- Do not treat model memory as medical truth.
- Do not train on raw PHI without a separate privacy, consent, and compliance architecture.
- Do not hide the audit trail.
- Do not let a learned preference override doctor review.
- Do not use RL or online learning to decide clinical facts, diagnoses, prescriptions, or alerts.

Clinical truth must follow this path:

```text
transcript evidence or explicit doctor input -> candidate fact -> doctor review -> approved output
```

Operational learning can improve workflow, document structure, task routing, missing-field checklists, and assistant handoffs.

## Architecture Direction

### 1. Experience Ledger

Every consultation should create an operational trace:

```text
session_id
clinic_id
doctor_id
specialty
city_or_region
transcript_metadata
extracted_facts
evidence_spans
doctor_review_actions
documents_generated
admin_tasks_generated
assistant_edits
task_completion_status
blocked_or_failure_reason
cost
review_time
```

The ledger is not a raw transcript memory store. It is the source for safe learning signals.

### 2. Clinic Memory

Store reusable non-PHI operational memory:

```text
clinic preference
doctor preference
document template rule
assistant handoff rule
TPA checklist rule
follow-up workflow rule
```

Each memory item should have:

- Scope: global, country, specialty, clinic, doctor, payer/form.
- Source trace.
- Confidence.
- Created date.
- Last used date.
- Accepted count.
- Rejected count.
- Version history.
- Rollback path.

### 3. Skill Library

Store versioned service skills:

- Generate referral letter.
- Generate investigation order.
- Prepare follow-up reminder.
- Prepare pre-auth checklist.
- Fill one TPA form.
- Create assistant task.
- Summarize patient timeline for current visit.

Each skill should define:

- Input schema.
- Required facts.
- Missing-field policy.
- Safety guard.
- Output schema.
- Verifier.
- Success/failure metrics.

### 4. Verifier Layer

The verifier matters more than the generator.

Before output is shown, shared, or exported:

- Clinical fields must trace to approved facts or explicit doctor input.
- Missing fields stay missing.
- Uncertain or negated facts do not become active facts.
- Patient memory is labeled as past context.
- Doctor review is required for clinical output.
- Generated admin output should show evidence references where useful.

### 5. Lesson Review Queue

After corrections, generate candidate lessons:

```text
Candidate lesson:
For Dr. Rao's referral letters, include symptom duration when available.

Source:
3 accepted referral edits.

Scope:
doctor-specific.

Action:
approve / edit / reject.
```

Lessons should be proposed, not silently trusted.

## Learning Stack

### Near Term: Context Engineering

Most achievable and most useful now:

- Scoped retrieval.
- Clinic playbooks.
- Doctor preference cards.
- Task templates.
- Evidence-backed prompt context for formatting only.
- Deterministic verifiers.
- Flywheel analytics.

This can reduce edits without training new models.

### Medium Term: Human Feedback And Skill Promotion

Use:

- Accept/edit/reject/delete counts.
- Task completion status.
- Assistant corrections.
- Document rejection reasons.
- Admin review of reusable lessons.

Promote only lessons that pass thresholds and review.

### Later: Offline Supervised Learning Or Distillation

Use approved traces to train or rank:

- Document style choices.
- Task ordering.
- Missing-field prediction.
- Assistant handoff generation.
- Retrieval/routing policies.

This should be offline, evaluated, rollbackable, and never used as direct medical truth.

### Later: RL Or Bandits

RL can be useful for workflow policy, not clinical facts.

Possible safe uses:

- Task ordering.
- Reminder timing.
- Which checklist to show first.
- Which assistant handoff format reduces edits.
- Which document template works best for a clinic.

Forbidden uses:

- Deciding clinical facts.
- Creating diagnoses.
- Prescribing.
- Suppressing safety alerts.
- Bypassing doctor review.

## Product Path

Build the concrete service surfaces first:

1. Evidence Review UI.
2. Assistant Work Queue.
3. Investigation Order Generator.
4. Referral Letter Generator.
5. Cost-Per-Consultation Ledger.
6. Flywheel Analytics Dashboard.
7. One Insurance Pre-Auth Form.
8. Internal Ops Console.

These are not separate from the research direction. They are how the learning data is created.

## Best Hero Feature Candidate

The most achievable and defensible hero feature is:

> Evidence-backed Assistant Work Queue with a Clinic Learning Loop.

Why:

- Evidence review proves safety.
- Work queue proves Lipi is a service, not just a note tool.
- Every task creates outcome data.
- Every correction creates a learning signal.
- Clinic playbooks become visible and editable.
- The feature improves with usage without requiring risky model training.

This is harder to copy than a scribe UI because it combines provenance, workflow execution, corrections, outcomes, and clinic-specific memory.

## Failure Modes

### Clinical Memory Leakage

Risk:
- Past patient facts enter current SOAP as if spoken today.

Guard:
- Separate current-visit facts from past context.
- Require explicit doctor confirmation before using past facts as current truth.

### False Lessons

Risk:
- One odd correction becomes a broad rule.

Guard:
- Scope lessons narrowly.
- Require repeated confirmation or manual admin approval.
- Track rejection counts and rollback.

### Overfitting To One Doctor

Risk:
- A doctor-specific preference affects global output.

Guard:
- Every memory item needs a scope.
- Promotions from doctor to clinic to specialty to global require evidence.

### PHI Leakage

Risk:
- Raw patient details become reusable memory.

Guard:
- Store operational lessons, not raw transcripts.
- Scrub PHI.
- Keep source trace access controlled.

### Automation Overreach

Risk:
- System starts acting without doctor or assistant approval.

Guard:
- Doctor review for clinical outputs.
- Human approval for outbound admin actions until validation supports more automation.

### Cost Drift

Risk:
- Smart workflows become too expensive for Indian clinic pricing.

Guard:
- Track cost per consultation.
- Attribute cost by ASR, LLM formatting, messaging, storage, and human ops.
- Prefer local deterministic checks where possible.

## Evals

Learning is real only if metrics improve.

Track:

- Doctor review time per consultation.
- Fact acceptance rate.
- False-positive deletion rate.
- Missing-fact addition rate.
- Document edit rate.
- Assistant task completion time.
- Blocked-task rate.
- Pre-auth rejection rate.
- Follow-up completion rate.
- Cost per consultation.
- Gross margin per consultation.
- Unsupported clinical fact count.
- Patient-memory leakage count.
- Rollback events.

## Claims We Can Make Carefully

Safe internal claim:

> Lipi is building evidence-grounded continual learning for healthcare administration workflows.

Safe external claim after product proof:

> Lipi learns reusable operational patterns from doctor-approved and assistant-reviewed work traces.

Safe YC claim:

> Lipi is an AI-native OPD administration service. The more clinics use it, the better it gets at their reviewed workflows.

Avoid claiming:

- Autonomous healthcare agent.
- Self-improving doctor.
- Real-time RL for clinical decisions.
- Fully automated insurance claims before proof.
- Model learns directly from PHI.
- Replaces doctors.
- No human review required.

## What To Do Next

Near-term product work:

1. Ensure Evidence Review UI is fast and trusted.
2. Build Assistant Work Queue with task owner, status, due time, notes, blocker, and completion reason.
3. Add Experience Ledger events behind review, document, and task actions.
4. Add Cost-Per-Consultation Ledger.
5. Add Flywheel Analytics: accepted, edited, deleted, added facts; document edits; task outcomes.
6. Add Clinic Playbook memory with human approval.
7. Add Lesson Review Queue.
8. Build one insurance pre-auth workflow only after the evidence/task loop is stable.

Research work should wait for real traces. The first edge comes from better instrumentation, scoped memory, and verifiers, not from training a new model.

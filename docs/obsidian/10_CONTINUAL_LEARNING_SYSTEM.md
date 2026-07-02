# Future Research - Evidence-Grounded Continual Learning System

> Date: 2026-06-27
> Status: Future research direction
> Related: [[00_HOME]], [[03_PRODUCT_STRATEGY]], [[05_VALIDATION_PLAN]], [[07_DECISIONS]], [[09_STRATEGIC_ROADMAP]], [[13_AGENTIC_SERVICE_RESEARCH_DIRECTION]]

## One-Line Thesis

Lipi should become an AI-native healthcare administration worker that improves on the job from doctor-approved, evidence-backed traces.

This is not "remember the transcript." This is learning reusable operational judgment:
- Which facts were accepted, rejected, edited, or deleted.
- Which evidence spans supported each accepted fact.
- Which admin tasks were needed after the consultation.
- Which documents were corrected by doctor or assistant.
- Which clinic, doctor, specialty, city, and workflow patterns repeat.
- Which failures created real human work.

The long-term differentiator is not a bigger scribe model. It is a system that learns the healthcare admin job safely, clinic by clinic and specialty by specialty.

## Research Question

Can Lipi safely build a continually improving healthcare administration service by learning from structured correction traces, without allowing the model to silently invent clinical facts or make autonomous medical decisions?

## Why Real-World Clinic Work Is Hard

The real world is not a clean benchmark. Every deployment has local knowledge that is hard to put into a single training run:

- One doctor has personal shorthand, habits, and preferred note structure.
- One assistant knows which documents must be printed, WhatsApped, signed, or filed.
- One clinic has local forms, staff roles, billing rituals, and follow-up routines.
- One specialty has repeated visit patterns, but each doctor handles them differently.
- One city or region has language mix, seasonal disease patterns, payer behavior, and patient expectations.
- One TPA or insurer rejects forms for missing fields that never appear in a generic SOAP-note benchmark.
- One patient has long-running context that matters only inside that patient's timeline.
- One deployment changes over time as staff, forms, pricing, workflows, and doctor preferences change.

This is why "train a better model once" is not enough. A static model can know medicine and language, but it will not automatically know the operating details of a specific clinic on Tuesday morning.

Humans get good at this job through on-the-job learning. They see what the doctor corrects, remember which form caused trouble, notice which assistant gets stuck, and adapt. Lipi's research direction is to capture that same kind of job learning, but as structured, inspectable, evidence-backed memory.

## Why This Cannot Be Stuffed Into One Training Run

Some knowledge is general and belongs in a model. But the most valuable service knowledge is often deployment-specific, recent, sparse, and operational.

Examples:

- "This doctor wants pediatric doses written in this exact format."
- "This clinic's assistant sends lab orders by WhatsApp first, then prints them."
- "For this TPA, pre-auth fails unless estimated length of stay is included."
- "This cardiologist often says 'same as last time,' which must resolve to the latest active medication."
- "In this clinic, follow-up reminders go to the son for elderly patients, not always the patient."
- "This extractor often misreads a Hinglish phrase as a symptom when it is actually negated."

These are not stable global facts. They are small pieces of working knowledge. They are too narrow, too local, and too fast-changing to wait for a full retraining cycle.

The system should therefore improve through two tracks:

1. Runtime learning through context engineering, scoped memory, retrieval, and playbooks.
2. Offline learning through supervised fine-tuning or distillation only after enough approved traces exist.

The near-term moat is not "we trained the biggest model." The moat is "we know what to remember, what to ignore, where to scope it, and how to reuse it safely."

## Hard Boundaries

These boundaries do not change for this research direction:

- No proof -> no fact.
- Clinical facts require transcript evidence, structured doctor input, or explicit doctor correction.
- Doctor review is required before clinical output becomes final.
- Gemini may format structured content, but must not create clinical facts.
- Clinical extraction, memory resolution, and conflict detection remain local and auditable.
- Sarvam plain STT remains the default ASR path until market data says otherwise.
- Diarization is enabled only if real workflow evidence shows it is needed.
- Cost per consultation remains a first-class metric.
- Do not train ASR before market proof.
- Do not train on raw PHI without a separate privacy, consent, and compliance design.

Learning can improve suggestions, retrieval, templates, workflow routing, admin completion, and formatting. It must not silently create medical truth.

## Why This Matters

Most scribes turn speech into notes. Lipi can turn clinical work into a supervised learning stream.

Every consultation can produce:
- Raw input: audio, transcript, timestamps.
- Model output: extracted facts, evidence spans, tasks, documents.
- Human feedback: doctor approval, edits, deletions, additions, assistant actions.
- Outcome data: task completed, document accepted, claim rejected, follow-up sent, cost incurred.

That means every doctor using Lipi creates training signal while doing normal work. If captured correctly, this becomes a compounding data moat:

```text
more consultations
-> more reviewed traces
-> better clinic and specialty playbooks
-> fewer edits
-> more admin work completed
-> stronger service margin
-> more consultations
```

## What The System Learns

The unit of learning is not a full transcript. The unit of learning is a reusable delta.

Examples:
- A phrase maps to a clinical concept only when evidence supports it.
- A doctor prefers a specific note structure for diabetic follow-ups.
- A clinic expects a printed prescription plus WhatsApp copy.
- A cardiology visit with chest pain usually needs ECG/lab/admin follow-up tasks.
- A TPA pre-auth form fails unless duration, diagnosis, investigation, estimate, and planned procedure are present.
- A specific extractor layer produces false positives for a Hinglish phrase.
- A certain follow-up reminder wording gets accepted more often by this clinic.
- A claim rejection reason maps back to a missing admin field.

This is the difference between memory and learning:

| Bad memory | Useful learning |
|---|---|
| Store whole transcripts | Store approved reusable patterns |
| Retrieve everything | Retrieve only context relevant to this task |
| Personalization hidden in model weights | Inspectable doctor and clinic preferences |
| LLM creates new facts | Evidence-backed facts only |
| One correction changes everyone | Promotion requires repeated confirmation and safety gates |
| Optimizes note generation | Optimizes completed admin work |

## Learning Loop

```text
Consultation capture
-> evidence-backed extraction
-> proposed facts, tasks, and documents
-> doctor or assistant review
-> correction delta captured
-> memory candidate generated
-> safety and scope check
-> shadow evaluation
-> promote to patient, doctor, clinic, specialty, or global playbook
-> retrieve in next similar workflow
-> measure improvement
```

The key artifact is the correction delta:

```text
before: what Lipi proposed
after: what human approved
evidence: transcript span or structured human input
actor: doctor, assistant, system
scope: patient, doctor, clinic, specialty, global
reason: false positive, missing fact, wrong category, style preference, admin rule
outcome: accepted, rejected, completed, failed, needs review
```

## Memory Layers

| Layer              | Scope             | Stores                                                                         | Learns                                   | Must Not Do                                |
| ------------------ | ----------------- | ------------------------------------------------------------------------------ | ---------------------------------------- | ------------------------------------------ |
| Session memory     | One consultation  | latest instructions, negations, corrections, evidence spans                    | active state inside current visit        | invent facts outside evidence              |
| Patient memory     | One patient       | active problems, allergies, meds, investigations, follow-ups, unresolved tasks | continuity across visits                 | leak one patient into another              |
| Doctor memory      | One doctor        | style, preferred templates, common edit patterns                               | reduce doctor-specific correction burden | override clinical evidence                 |
| Clinic memory      | One clinic        | workflows, assistant roles, document formats, WhatsApp habits                  | complete clinic admin work faster        | force one clinic's workflow globally       |
| Specialty playbook | Specialty         | common visit types, admin checklists, safe form requirements                   | improve repeated specialty workflows     | become diagnosis or prescription authority |
| Form/TPA memory    | Payer/form        | required fields, rejection reasons, evidence needed                            | reduce claim/pre-auth errors             | fabricate missing fields                   |
| Ops memory         | Lipi service team | task failure modes, escalation rules, SLA gaps                                 | improve service delivery                 | hide human intervention                    |
| Model corpus       | Future            | de-identified approved traces                                                  | train or distill specialized models      | train prematurely on raw PHI               |

## Context Engineering First, RL Later

The first serious version should not be reinforcement learning. The reward signal is too messy early, and unsafe exploration is unacceptable in clinical workflows.

Start with:
- Structured event logs.
- Explicit memory objects.
- Retrieval by patient, doctor, clinic, specialty, city, visit type, and task type.
- Confidence thresholds.
- Shadow mode evaluation before promotion.
- Human approval for higher-scope playbooks.
- Deterministic clinical safety checks.

RL may become useful later for narrow workflow policies where the reward is clear:
- Which admin task to show next.
- Which template to pick.
- Which assistant queue item to prioritize.
- Which reminder channel to try.
- Which extraction layer to trust for a known low-risk category.

RL should not decide clinical facts, diagnoses, prescriptions, or safety-critical medical recommendations.

## Test-Time Learning Direction

The near-term test-time learning story is memory and retrieval, not weight updates.

At runtime, Lipi should select a compact context pack:
- current transcript evidence
- active patient facts
- doctor preferences relevant to this document
- clinic workflow rules
- specialty playbook for visit type
- known form requirements
- recent similar correction patterns
- cost and safety constraints

This creates the effect of an experienced worker without retraining the base model on every session.

Future deeper directions:
- Persistent working memory for long patient timelines.
- Sparse retrieval over large clinic history.
- KV-cache-like reuse for repeated document generation contexts.
- Distillation from "experienced Lipi" traces into cheaper task-specific models.
- Active learning: ask humans only for corrections that would improve future behavior.
- Recursive improvement loops where high-confidence approved traces generate new evals.

Large context alone is not the moat. The moat is selecting the few pieces of context that make the next action better.

## What Can Learn Now

These are safe, near-term learning targets:

- Doctor note style.
- Doctor prescription formatting style.
- Clinic document templates.
- Specialty vocabulary and Hinglish phrase maps.
- False positive suppression by extractor layer.
- Missing fact patterns by visit type.
- Follow-up reminder preferences.
- Investigation order formatting.
- Referral letter structure.
- Insurance pre-auth field completeness.
- Admin task routing.
- Cost-aware model/vendor path selection.
- Time-to-approval reduction patterns.

## What Must Not Learn Automatically

These require explicit safety review and should not be auto-promoted:

- New diagnosis rules.
- Prescription dose logic.
- Drug safety rules.
- Clinical treatment pathways.
- Global changes from one doctor's behavior.
- Clinical facts without evidence spans.
- ASR acoustic model training before market proof.
- Any memory that contains raw PHI without a privacy design.

## Proposed Data Objects

Lipi already has the start of the flywheel through original extracted facts, corrections, evidence spans, precision/recall, and pipeline logs. Future objects should make learning explicit.

### LearningEvent

Captures what happened.

```text
id
session_id
patient_id optional
doctor_id
clinic_id optional
actor: system | doctor | assistant | ops
event_type: fact_added | fact_deleted | fact_modified | evidence_changed | task_completed | document_corrected | claim_rejected
before_json
after_json
evidence_refs
reason
scope_candidate
created_at
```

### MemoryCandidate

Captures what the system thinks it learned.

```text
id
source_event_ids
candidate_type: preference | vocabulary | workflow_rule | form_requirement | failure_signature
scope: patient | doctor | clinic | specialty | city | global
statement
trigger_conditions
proposed_action
confidence
safety_class
status: proposed | shadow | approved | rejected | retired
reviewed_by
created_at
```

### PlaybookRule

Captures promoted operational knowledge.

```text
id
scope
specialty
visit_type
trigger
action
required_evidence
exclusions
confidence
promotion_basis
last_evaluated_at
status
```

### EvaluationRun

Captures whether learning helped.

```text
id
metric
scope
baseline_window
comparison_window
result
notes
created_at
```

## Promotion Policy

Do not let one correction become global behavior.

Suggested promotion path:

```text
single correction
-> memory candidate
-> patient or doctor scoped suggestion
-> repeated confirmations
-> clinic scoped playbook
-> specialty scoped shadow mode
-> global candidate only after multi-clinic validation
```

Promotion gates:
- Same pattern confirmed multiple times.
- No unresolved safety objection.
- Evidence exists for clinical facts.
- Improvement measured against baseline.
- Clear rollback path.
- Scope remains narrow by default.

## Metrics

The learning system should optimize human labor reduction under safety constraints.

Primary metrics:
- Doctor edits per consultation.
- False positive fact rate.
- Missing fact rate.
- Evidence-span correction rate.
- Time to doctor approval.
- Assistant touches per consultation.
- Admin task completion rate.
- Document rejection rate.
- Insurance/pre-auth rejection rate.
- Follow-up completion rate.
- Cost per consultation.
- Automation rate by task type.

Safety metrics:
- Unsupported clinical fact count.
- Doctor-overridden critical item count.
- Retrieved irrelevant memory count.
- Cross-patient contamination incidents.
- Unsafe auto-promotion count.
- Human review bypass count.

Business metrics:
- Hours saved per clinic per week.
- Gross margin per consultation.
- Retention by clinic.
- Expansion from scribe to admin outputs.
- Revenue per doctor or clinic.

## Failure Modes

| Failure mode | What happens | Guardrail |
|---|---|---|
| False memory consolidation | wrong correction becomes future rule | require evidence, repeated confirmation, review |
| Unsafe generalization | one doctor's habit applied globally | scope memory narrowly by default |
| Cross-patient contamination | another patient's fact retrieved | patient isolation and retrieval tests |
| Style confused with truth | wording preference treated as medical fact | separate formatting memory from clinical memory |
| Reward hacking | system optimizes approval speed but misses facts | track false negatives and safety events |
| PHI leakage | raw patient data enters training corpus | de-identification and consent gates |
| Stale protocol | old form or workflow keeps being used | expiry dates and revalidation |
| Irrelevant retrieval | wrong context enters a note | retrieval evals and provenance display |
| Automation overreach | system acts without approval | explicit doctor/assistant approval gates |
| Eval overfitting | improves internal metrics, not clinic work | measure real admin completion and edits |

## Model Strategy

### Stage 1: No Training

Use deterministic extraction, structured memory, retrieval, templates, and analytics.

Goal: prove the job loop and capture high-quality traces.

### Stage 2: Small Specialized Models

Train or fine-tune only narrow components after enough approved data:
- visit type classifier
- task trigger classifier
- doctor style formatter
- rejection reason classifier
- false positive predictor
- specialty vocabulary mapper

Clinical facts still require evidence and review.

### Stage 3: Distillation

Use expensive, reviewed, high-quality traces to train cheaper task-specific workers.

Pattern:

```text
experienced Lipi traces
-> cleaned approved corpus
-> task-specific model
-> shadow evaluation
-> gated production use
```

This is where Lipi can become a core AI company, not just an application layer.

Veteran-teacher path:

```text
expensive experienced system
-> observes many reviewed sessions
-> extracts only reusable operational knowledge
-> creates playbooks and training examples
-> teaches cheaper specialized models
-> cheaper models run routine clinic work
-> hard cases route back to experienced system or human ops
```

The "teacher" does not need to be one model. It can be the whole experienced Lipi system: deterministic extractors, retrieval, doctor corrections, assistant outcomes, evals, and human ops traces. The student model learns the repeatable parts of the job after they have been proven in production.

### Stage 4: Narrow RL

Only after the service workflow has clear rewards:
- task completed
- document accepted
- doctor edit avoided
- assistant touch avoided
- cost reduced
- SLA met

No RL for clinical truth creation.

## Difficulty

This direction is hard, but the difficulty is manageable if built in layers.

Hard parts:
- Capturing clean feedback without slowing doctors down.
- Separating clinical truth from style preference.
- Scoping memory correctly: patient, doctor, clinic, specialty, city, or global.
- Preventing one wrong correction from becoming system behavior.
- Measuring improvement honestly instead of trusting demos.
- Building retrieval that brings in the right tiny memory, not a large noisy context pack.
- Avoiding PHI leakage in training and analytics.
- Knowing when to use rules, retrieval, fine-tuning, or human ops.
- Designing evals for messy service work, not just note quality.

Easier first cuts:
- Logging every edit and deletion.
- Showing evidence spans.
- Tracking doctor approval time.
- Tracking task completion.
- Creating doctor-specific formatting memory.
- Creating clinic-specific workflow preferences.
- Creating shadow playbooks that do not auto-act.
- Measuring whether retrieved memory reduced edits.

The research is deep. The first implementation does not need to be. The first version can be a disciplined event ledger plus scoped retrieval.

## Smallest Edge That Compounds

The smallest useful edge is:

```text
When a doctor or assistant corrects Lipi, store the correction as a structured reusable lesson, then use it only in the next matching low-risk context.
```

That gives compounding without heavy ML.

First compounding edge:
- If a doctor edits the same section style three times, remember it as a doctor preference.
- If a clinic repeatedly sends the same follow-up message, remember it as a clinic workflow.
- If a false positive appears from the same extractor and phrase, suppress or down-rank that pattern.
- If a pre-auth form is rejected for the same missing field, add that field to the form completeness checklist.
- If a visit type repeatedly creates the same admin task, suggest that task in shadow mode.

This is enough to create visible improvement:

```text
week 1: Lipi needs many edits
week 2: Lipi remembers local style and workflow
week 4: Lipi handles common admin tasks with fewer touches
month 3: Lipi has clinic and specialty playbooks
month 6: approved traces can train narrow student models
```

The defensible moat is not one algorithm. It is the loop:

```text
capture work
-> capture correction
-> extract reusable lesson
-> scope it safely
-> retrieve it at the right time
-> measure whether work reduced
-> promote or retire
```

## Implementation Difficulty By Layer

| Layer | Difficulty | Time To First Value | Compounding Value |
|---|---|---|---|
| Correction event ledger | Low | Immediate | High, because every future learning loop needs it |
| Doctor preference memory | Low-medium | 1-2 weeks | Medium-high, reduces repeated edits |
| Clinic workflow memory | Medium | 2-4 weeks | High, moves Lipi from scribe to service |
| Retrieval context pack | Medium | 2-4 weeks | High, makes memory usable at runtime |
| Shadow playbooks | Medium | 3-6 weeks | High, validates learning safely |
| Promotion/eval system | Medium-high | 4-8 weeks | Very high, prevents unsafe scaling |
| Specialist fine-tunes | High | After data volume | High, lowers cost and latency |
| Narrow RL | Very high | Much later | Unknown until workflow rewards are stable |

Recommended sequence:

1. Build logs before learning.
2. Build scoped memory before model training.
3. Build retrieval before fine-tuning.
4. Build evals before promotion.
5. Build human ops console before claiming full automation.

## YC Narrative

Short version:

> Lipi is building the learning operating system for AI-native healthcare administration in India. Every OPD consultation creates an evidence-backed trace of what the doctor said, what the AI proposed, what the doctor corrected, and what admin work got completed. That lets Lipi improve at the job clinic by clinic, specialty by specialty, without forcing clinics to migrate software.

Sharper version:

> We are not building an AI scribe. We are replacing the post-consultation admin worker. The core technology is an evidence-grounded continual learning system that turns doctor corrections and admin outcomes into reusable clinic and specialty playbooks.

## First Implementation Tickets

1. Add complete correction event ledger for facts, tasks, documents, and admin outputs.
2. Generate memory candidates from doctor edits and assistant actions.
3. Add doctor and clinic preference store.
4. Add specialty playbook store in shadow mode.
5. Add evaluation dashboard for edit burden, precision, recall, approval time, admin completion, and cost.
6. Add retrieval layer that injects only relevant memories into the next consultation or admin task.
7. Add playbook promotion workflow with scope, confidence, reviewer, and rollback.
8. Add ops console so Lipi humans can complete service tasks while the system learns.

## Open Research Questions

- What is the smallest memory object that creates measurable improvement?
- How much learning comes from doctor preferences versus specialty patterns?
- Which admin task creates the strongest paid wedge: referral, lab order, follow-up, pre-auth, or claims?
- How many confirmations are needed before promotion from doctor to clinic to specialty?
- How should Lipi separate clinical correctness from formatting preference?
- How should patient-level memory be retrieved without cross-patient leakage?
- What can be de-identified safely enough for model training?
- Which tasks need deterministic rules versus learned ranking?
- What is the right human-in-loop ops workflow before automation?
- How does Lipi prove learning improved outcomes, not just demo quality?
- What knowledge should stay in context memory versus become model weights?
- How can an experienced Lipi system teach a cheaper student model without copying PHI?
- What is the minimum correction volume needed before fine-tuning is better than retrieval?
- Which deployment-specific lessons expire and need revalidation?
- How should Lipi detect that a retrieved memory made the task worse?

## Core Principle

Lipi should learn like an excellent clinic admin worker:

- remember what matters
- forget what is unsafe or irrelevant
- ask when evidence is missing
- follow the doctor's final decision
- improve repeated workflows
- make every consultation cheaper, faster, and more complete

The deepest version of Lipi is not a scribe with memory. It is a continually improving healthcare administration service with evidence-backed learning at the center.

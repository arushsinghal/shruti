# Validation Plan

## Goal

Prove that Lipi solves a repeated OPD administration problem before investing in expensive automation or ASR training.

## Core Hypotheses

### H1: Consultation Capture Saves Time

Doctors can produce an acceptable visit record faster with Lipi than with manual note writing or assistant-only documentation.

Evidence to collect:
- Time from consultation end to approved record
- Doctor review duration
- Manual correction count
- Reason for each correction

### H2: Evidence-Backed Facts Build Trust

Doctors trust the output when every clinical fact can be traced to proof.

Evidence to collect:
- Fact acceptance rate
- Fact rejection rate
- Missing-fact categories
- Unsupported-fact incidents
- Doctor comments on evidence display

### H3: Assistant Workflow Is The Expansion Wedge

The clinic values follow-up, patient timeline, and admin outputs beyond the SOAP note.

Evidence to collect:
- Assistant tasks generated per consultation
- Follow-up reminders scheduled and completed
- Patient instructions sent
- Referral or investigation outputs used
- Reuse of timeline in later visits

### H4: Sarvam Plain STT Is Sufficient For Market Proof

Plain STT handles enough real OPD audio to validate the workflow.

Evidence to collect:
- Transcript correction rate
- Language mix
- Background noise issues
- Speaker confusion incidents
- Cases where diarization would have changed outcome

### H5: Cost Per Consultation Supports The Business

Vendor and infrastructure costs fit expected pricing.

Evidence to collect:
- ASR cost per consultation
- Optional Gemini formatting cost per consultation
- Messaging cost per consultation
- Storage and infrastructure cost per consultation
- Gross margin estimate by clinic usage level

## Pilot Instrumentation

Track these fields per consultation:
- Clinic
- Doctor
- Specialty
- Consultation duration
- Audio duration
- Language mix
- ASR provider and mode
- Diarization used: yes/no
- Gemini formatting used: yes/no
- Doctor review time
- Number of accepted facts
- Number of corrected facts
- Number of rejected facts
- Unsupported fact count
- Follow-up generated: yes/no
- Admin output generated: yes/no
- Patient timeline updated: yes/no
- Total estimated API cost

## Validation Gates

### Gate 1: Usability

Pass if a doctor can complete capture, review, and final output without operational support for routine cases.

### Gate 2: Trust

Pass if unsupported facts are rare and every accepted clinical fact has visible proof.

### Gate 3: Workflow Pull

Pass if the clinic asks to use Lipi beyond the demo because it helps daily OPD operations.

### Gate 4: Economic Feasibility

Pass if cost per consultation supports the intended pricing with room for support and infrastructure.

## What Not To Build Yet

- Custom ASR training
- Broad diarization system
- Autonomous clinical recommendations
- Large integrations before repeated usage
- Multi-specialty template sprawl before workflow proof

## Interview Prompts

For doctors:
- Which part of post-consultation documentation is slowest?
- What would make you distrust an AI-generated record?
- Which corrections are acceptable versus unacceptable?
- Would source evidence make you more comfortable approving output?

For assistants:
- What tasks happen after the doctor finishes the visit?
- Which patient follow-ups are missed today?
- What information do you need from the doctor to complete admin work?

For clinic owners:
- What is the cost of documentation delay?
- What workflow improvement would justify payment?
- How many consultations per day would use Lipi?

## Related Notes

- [[03_PRODUCT_STRATEGY]]
- [[06_API_COSTS]]
- [[08_OPEN_QUESTIONS]]

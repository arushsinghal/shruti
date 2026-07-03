# Open Questions

## Product

- What is the smallest daily workflow where Lipi becomes habit-forming for a clinic?
- Is the buyer the doctor, clinic owner, hospital department, or assistant-led admin team?
- Which OPD specialties show the strongest pull first?
- Which output matters most after the note: prescription, follow-up, referral, investigation list, or patient summary?
- What must Lipi do better than a trained assistant?

## Clinical Safety

- What evidence display is fastest for doctor review?
- Which unsupported-fact incident categories are unacceptable even if rare?
- How should uncertain, negated, and superseded facts appear in the UI?
- What is the minimum audit trail needed for pilot clinics?
- Which clinical outputs require an explicit doctor approval step?

## ASR And Audio

- Is Sarvam plain STT sufficient across real clinic noise and language mix?
- How often does speaker confusion affect the clinical record?
- Would diarization reduce review time enough to justify cost?
- What audio capture constraints should clinics follow?
- Which ASR errors are clinically dangerous versus merely annoying?

## Memory And Timeline

- Which patient memory fields produce the most value in the next visit?
- How should prior allergies, medications, and diagnoses be surfaced without overwhelming the doctor?
- When should old facts expire or require reconfirmation?
- How should doctor corrections update memory?
- What patient timeline view helps assistants versus doctors?

## Assistant And Admin Workflow

- Which tasks should an assistant see immediately after doctor approval?
- Should follow-up reminders be clinic-managed, patient-managed, or both?
- What WhatsApp messages are acceptable without additional doctor review?
- What admin outputs are specialty-specific?
- Which workflow should be manual until repeated usage proves automation value?

## Validation

- What is the target doctor review time per consultation?
- What fact acceptance rate is good enough for paid pilots?
- How many consultations are needed before judging ASR quality?
- What correction taxonomy should be used during pilots?
- What is the threshold for market proof before considering ASR training?

## Costs And Pricing

- What is the acceptable cost per consultation at the first paid price point?
- Does pricing work better per doctor, clinic, or consultation?
- How should low-volume clinics cover fixed infrastructure cost?
- Which vendor cost has the highest variance?
- How should Gemini formatting be priced if optional?

## Go-To-Market

- Which doctor segment feels the pain most urgently?
- What is the shortest demo that proves the workflow?
- What proof matters more: time saved, patient follow-up, record quality, or assistant workload?
- What compliance or trust objection blocks pilots?
- Which integrations are required for a sale versus nice-to-have?

## Technical

- Which code paths currently own evidence-backed extraction?
- Where should cost-per-consultation events be recorded?
- What tests prove "no proof -> no fact"?
- How should Gemini formatting be guarded against adding unsupported content?
- What is the safest rollback path if ASR or external API calls fail during a clinic day?

## Related Notes

- [[01_CURRENT_STATE]]
- [[03_PRODUCT_STRATEGY]]
- [[05_VALIDATION_PLAN]]
- [[06_API_COSTS]]
- [[12_IMPLEMENTATION_GAP_REGISTER]]

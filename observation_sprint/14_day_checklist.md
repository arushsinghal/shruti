# 14-Day Observation Sprint Checklist

A day-by-day guide to executing a structured pilot deployment of Lipi.

---

## Pre-Sprint (Days -2 to -1)
- [ ] Set up doctor user account in Lipi.
- [ ] Review the doctor consent script and sign agreement.
- [ ] Prepare clinic hardware (microphone positioning, laptop placement, Wi-Fi verification).
- [ ] Create `observation_sprint/cases/` directory for storing local ground truth cases.

---

## Week 1: Core Deployment & Initial Feedback
### Day 1: Pilot Launch & Verification
- [ ] Deploy Lipi on the doctor's desk.
- [ ] Run 3 practice sessions using demo cases to verify audio recording levels and network connectivity.
- [ ] Confirm consent flows work seamlessly.

### Days 2–3: Early Observations (5–10 consultations)
- [ ] Obtain verbal patient consent before recording.
- [ ] Observe and take notes on doctor dictation behavior.
- [ ] Check if the PHI scrubber hides patient names and phone numbers correctly.
- [ ] Save the first 5 transcripts and write their matching `case_XXX_gt.json` files.
- [ ] Run eval harness on these early cases and check precision/recall.

### Days 4–5: Refinement & UI Feedback
- [ ] Collect feedback from the doctor on SOAP note formatting.
- [ ] Track any medication extraction issues or vitals patterns.
- [ ] Log failure cases in `failure_log_template.csv`.

---

## Week 2: Scaling & Final Metric Audit
### Days 6–10: Data Collection Sprint (25–30 consultations)
- [ ] Target 5-6 recorded consultations per day.
- [ ] Maintain the `consultation_log_template.csv` for each session.
- [ ] Ensure raw audio files are automatically deleted after note generation.

### Days 11–12: Ground Truth & Evaluation
- [ ] Complete ground truth json files for all observed sessions.
- [ ] Run evaluation harness on the entire directory:
  ```bash
  python -m eval.run_eval --dir ../observation_sprint/cases/ --output ../observation_sprint/eval_results.json
  ```
- [ ] Calculate overall F1-score for Symptoms, Medications, Vitals, and Diagnoses.

### Days 13–14: paid Pilot Conversion & Next Steps
- [ ] Review failure logs and prepare the final pilot report.
- [ ] Present results (accuracy numbers and time saved) to the doctor.
- [ ] Send the conversion message (see `dr_sawhney_paid_pilot_message.md`) to secure paid subscription.

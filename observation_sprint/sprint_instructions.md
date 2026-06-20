# Lipi Observation Sprint Instructions

This guide covers how to execute the 14-day observation sprint to validate Lipi in a real OPD clinic setting (e.g., Dr. Sawhney's clinic).

## Sprint Goal
Deploy Lipi as a pilot assist tool, observe 30–50 real Hinglish clinical sessions, generate evaluation metrics, and identify core product gaps.

---

## Step-by-Step Workflow

### 1. Patient Consent
Before starting any session, obtain the patient's verbal consent.
- Read/speak the Hindi/English script (see [patient_consent_script.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/patient_consent_script.md)).
- Click "Patient has been informed and has consented" in Lipi to unlock the recording/upload controls.

### 2. Audio Recording / Live Dictation
- Place the microphone device near the doctor.
- Record the conversation. Make sure to capture the doctor-patient dialogue clearly.
- Lipi automatically transcribes the audio using the Sarvam API.

### 3. Verification & Corrections
- The doctor reviews the live transcript in real-time.
- If there are typos, ASR errors, or translation gaps, the doctor can edit the text transcript in the Review workflow.
- Complete the clinical processing and export the SOAP note.

### 4. Create Ground Truth (Offline Evaluation)
For each case:
- Save the raw audio/transcript text to `observation_sprint/cases/case_XXX.txt`.
- Scribes/observers label the true clinical entities spoken in the session into `observation_sprint/cases/case_XXX_gt.json` using the schema in [manual_label_schema.md](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/manual_label_schema.md).

### 5. Run the Eval Harness
Run the offline evaluation harness to compare Lipi's extraction against the ground truth:
```bash
cd backend
uv run python -m eval.run_eval --dir ../observation_sprint/cases/ --output ../observation_sprint/eval_results.json
```

### 6. Fill the Failure Log
Analyze discrepancies in the output and document them in [failure_log_template.csv](file:///Users/arushsinghal/Documents/clinical-decision-support-system/observation_sprint/failure_log_template.csv):
- **True Positive (TP)**: Lipi correctly extracted the entity.
- **False Positive (FP)**: Lipi extracted an entity that was not in the ground truth or was negated/incorrectly parsed.
- **False Negative (FN)**: Lipi missed an entity that was present in the ground truth.

---

## Metrics & Target Thresholds

During this pilot, we aim for the following benchmarks:
- **ASR Word Error Rate (WER)**: < 25% for Hinglish/Hindi audio.
- **Clinical Fact Extraction Precision**: > 90% (to avoid dangerous false information).
- **Clinical Fact Extraction Recall**: > 80% (to minimise doctor manual typing).
- **Medication Extraction Accuracy**: > 95% (precision/recall on drug names).

# Lipi Ground Truth Labeling Schema & Instructions

This document provides instructions for clinical scribes or observers on how to create ground-truth JSON files for evaluated consultations.

## Ground Truth JSON Format

Each ground truth file should be named `case_XXX_gt.json` matching the corresponding transcript `case_XXX.txt`.

### Fields Specification

| Field | Type | Description | Example |
|---|---|---|---|
| `case_id` | String | Unique identifier | `"case_001"` |
| `doctor` | String | Doctor's name or code | `"Dr. Sawhney"` |
| `date` | String | Date of observation | `"2026-06-20"` |
| `symptoms` | List of Strings | Symptoms mentioned | `["fever", "cough", "body ache"]` |
| `medications` | List of Objects | Prescribed medications with dosage/frequency | `[{"name": "paracetamol", "dosage": "500mg", "frequency": "TDS"}]` |
| `vitals` | List of Strings | Patient vitals recorded | `["BP 120/80 mmHg", "Temp 98.6 F"]` |
| `allergies` | List of Strings | Known drug/food allergies | `["penicillin"]` |
| `investigations` | List of Strings | Lab tests or imaging ordered | `["CBC", "Chest X-ray"]` |
| `diagnoses` | List of Strings | Clinical impression or diagnoses | `["Acute Viral Pharyngitis"]` |
| `follow_up` | List of Strings | Follow-up instructions | `["in 3 days"]` |
| `labs` | List of Strings | Lab parameters (if any) | `["Hb 12.5"]` |
| `advice` | List of Strings | Lifestyle advice or warnings | `["Plenty of fluids", "Bed rest"]` |
| `red_flags` | List of Strings | Danger signs to look out for | `["breathlessness", "high fever > 103"]` |

---

## Labeling Guidelines

1. **Exact Extraction from Transcript Only**: Do not infer information that was not explicitly spoken in the consultation. If a doctor did not say a specific dose, do not add it to the ground truth.
2. **Medication Structure**:
   - `name`: Lowercase generic or brand name, e.g. `"paracetamol"`.
   - `dosage` or `dose`: e.g. `"500mg"`.
   - `frequency`: e.g. `"twice daily"`, `"TDS"`, `"OD"`.
3. **Set-based Fields**:
   - Symptoms, allergies, diagnoses, investigations, follow-up, advice, and red flags are simple flat arrays of strings.
4. **Normalisation Handling**:
   - The eval harness automatically normalises values by converting to lowercase and stripping parentheticals (e.g. `"fever (3 days)"` matches `"fever"`). However, try to keep entries to the core clinical entity name where possible.

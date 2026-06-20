# Lipi — 2-Minute Doctor Demo Script

Use this script to demo Lipi to prospective pilot doctors in 2 minutes.

---

## Preparation
1. Open Lipi on your web browser.
2. Log in with the doctor account.
3. Keep a test patient profile or scenario ready.

---

## Step-by-Step Demo Flow

### Step 1: Initialize Session (20 seconds)
1. Click **"New Consultation"** on the Dashboard.
2. Enter a mock patient name (e.g., *"Rajesh Kumar"*) and select **"Health / Clinical"** mode.
3. Point out the **Consent Gate**: *"Before we can record any audio, patient privacy regulations require us to confirm verbal consent. This ensures patient trust and compliance with DPDPA regulations."*
4. Click **"Patient has been informed and has consented"**.

### Step 2: Record or Run Pitch Demo (60 seconds)
1. Point to the audio uploader: *"We can record a live doctor-patient conversation in Hindi/Hinglish, or upload an audio file. For this demo, let's run our pre-baked Hinglish consultation scenario."*
2. Click **"Run VC Pitch Demo Scenario"**.
3. Watch the live progress sequencer as it runs:
   - *Transcribing audio...*
   - *Extracting clinical facts...*
   - *Resolving clinical memory...*
   - *Generating SOAP note...*
4. Explain: *"The transcription is done using the Sarvam API, which is highly tuned for Hinglish terms. Then, our local NLP parser extracts clinical facts. Notice the **PHI scrubbed** badge — patient identifiers like phone numbers are removed locally before the text is written to the database."*

### Step 3: Review Clinical Extraction (30 seconds)
1. Show the extracted components on the right pane:
   - **Symptoms**: e.g., fever, headache, nausea.
   - **Medications**: Generic names, dosages (e.g., *Azithromycin 500 mg*), and frequencies.
   - **Vitals**: e.g., *Temp 38.6 C*, *BP 128/82*.
   - **Allergies**: Point out the *Penicillin* allergy.
2. Explain the **Clinical Decision Support (CDS)** suggestions: *"Lipi automatically flags potential safety issues. For example, it lists penicillin allergy reactions as high-urgency alerts, prompting the doctor to verify alternative prescriptions."*

### Step 4: Export SOAP Note (10 seconds)
1. Click **"Export Final SOAP Note"**.
2. Show the editable SOAP note template.
3. Show that the raw audio file has been deleted automatically from the server to protect data privacy.
4. Conclude: *"Lipi gives you a complete draft of the consultation note in under a minute, which you can edit, export to FHIR, or copy. It saves 3-4 hours of documentation per day."*

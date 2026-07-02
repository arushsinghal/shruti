# Lipi — Complete Product & Technical Context

> **Purpose of this document:** Hand this to any AI assistant (ChatGPT, Claude, etc.) to give it full context on Lipi for product refinement, roadmap planning, competitive analysis, or strategic discussions. This is a living snapshot as of June 2026.

---

## 1. What Lipi Is

Lipi is an **AI clinical scribe for Indian OPD (outpatient) doctors**. A doctor speaks during a consultation in Hindi, Hinglish, or English. Lipi transcribes the audio, extracts structured clinical facts, generates a SOAP note + Indian-format prescription, flags drug safety alerts, and shares the output via WhatsApp — all without sending patient data to any external LLM.

**One-liner:** "Voice-to-prescription for Indian doctors, with zero hallucination by design."

**Key differentiator:** The entire clinical extraction pipeline is deterministic and local. No GPT, no Gemini, no LLM is used for extracting clinical facts. This means:
- Zero hallucination — if the doctor didn't say it, it doesn't appear
- $0/consultation marginal cost (vs ~$0.05/consultation with GPT)
- No patient data leaves the device for extraction
- Fully auditable — same input always produces same output

An LLM (Gemini) is used ONLY for formatting the SOAP note text (not for extraction).

---

## 2. Traction & Market Validation

### Doctors Currently Using Lipi
- **Dr. Anil Bhan** — Chairman of Cardiac Surgery at Medanta (widely considered India's best hospital)
- **Dr. Thukral** — Surgeon to the Hon. President of India
- **Dr. Sawhney** — Active pilot clinic
- **Dr. Sandhya** — Dentist
- **Dr. Divya** — Pediatric Surgeon
- **Dr. Praveen Gupta** — One of India's top neurologists

LOIs secured from these doctors. The specialty diversity (cardiac, neuro, dental, pediatric surgery, presidential surgeon) validates that the system works across specialties.

### Market Context
- India has ~1.3M registered doctors, ~800K in active OPD practice
- Average OPD doctor sees 30-60 patients/day
- Documentation is almost entirely manual — no Epic/Cerner penetration in India
- Doctor's assistant handles post-consultation paperwork (prescriptions, referrals, insurance forms) manually
- Doctors lose 2-4 hours/day to documentation
- WhatsApp is the universal communication channel (patients expect prescriptions via WhatsApp)

### Competitive Landscape
- **Augnito** (India) — speech-to-text only, no clinical extraction, no SOAP
- **Nabla / Abridge / Ambience** (US) — LLM-based (hallucination risk), US-focused, English-only, expensive
- **Practo** (India) — practice management, no AI scribe
- No competitor offers deterministic extraction + Hindi/Hinglish support + WhatsApp delivery

---

## 3. Technical Architecture

### Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Pydantic v2, uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod), dual-driver support |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, Framer Motion |
| ASR | Sarvam AI API (model `saaras:v3`) — best Hindi/Hinglish ASR in India |
| Clinical NLP | spaCy (sentence segmentation), GLiNER (NER), rapidfuzz (fuzzy matching) |
| LLM | Google Gemini `gemini-2.0-flash` — ONLY for SOAP text formatting |
| Auth | JWT (python-jose + bcrypt) |
| Deploy | Docker multi-stage, Render (Singapore region) |
| Mobile | PWA (Progressive Web App) — installable on Android/iOS |

### Clinical Extraction Pipeline (The Core IP)

This is Lipi's most important technical component. It's a 4-layer deterministic pipeline:

```
Layer 0: ASR Normalization
  → Rejoin split words, fix 50+ common drug misspellings
  → e.g., "para ceta mol" → "paracetamol"

Layer 1: Keyword Maps
  → Hand-curated dictionaries in English + Hinglish + Devanagari
  → Symptoms: ~200 terms including Hindi ("bukhar"→fever, "sar dard"→headache)
  → Medications: ~500 known drugs with common misspellings
  → Investigations: ~80 lab tests and imaging studies
  → Diagnoses: ~100 common OPD diagnoses

Layer 2: Fuzzy Matching (rapidfuzz, edit distance 1)
  → Catches remaining ASR spelling errors
  → SymSpell index built ONLY from seed vocabulary (not full ontology)
  → Expanded ontology (OpenFDA, ICD-10, abbreviations) used for exact match only

Layer 3: GLiNER NER (Named Entity Recognition)
  → 780MB PyTorch model, pre-loaded at startup
  → Extractive only — draws boxes around words in the transcript
  → Post-filtered: only spans that appear verbatim are kept
  → Merged with Layer 1+2 results
```

**Critical design decision:** The expanded medical ontology (7,293 terms from OpenFDA, ICD-10, medical abbreviations) is loaded for exact matching only. The fuzzy matching index (SymSpell) is built exclusively from the hand-curated seed vocabulary (~1,290 terms) + Hinglish variants. This prevents false positives from fuzzy-matching against the massive ontology.

### Evidence/Provenance System

Every extracted fact has `evidence_spans` with character-level proof:
```json
{
  "fact": "paracetamol 500mg",
  "evidence_spans": [
    {
      "start_char": 142,
      "end_char": 159,
      "source_sentence": "paracetamol 500mg teen baar dena"
    }
  ]
}
```
**No proof = no fact.** If the system can't point to where in the transcript a fact came from, that fact is not included.

### Pipeline Data Flow

```
transcript → run_health_pipeline() → raw facts dict
raw facts → memory.resolve_memory([facts]) → state (merged with prior visits)
state → soap_generator.generate_soap(state) → {"S", "O", "A", "P"}
state → cds_engine.generate_cds(state) → [drug safety alerts]
state → icd10_mapper → WHO ICD-10 codes on all diagnoses
state → fhir_mapper → HL7 FHIR R4 Bundle (international standard)
```

### Extraction Output Shape
```json
{
  "symptoms": ["fever", "cough", "headache"],
  "medications": [
    {"name": "paracetamol", "dosage": "500mg", "frequency": "TDS", "duration": "5 days"}
  ],
  "vitals": ["BP 120/80", "Temp 38.6°C"],
  "allergies": ["penicillin"],
  "diagnoses": ["acute upper respiratory infection"],
  "investigations": ["CBC", "chest X-ray"],
  "follow_up": ["Follow up in 3 days"]
}
```

---

## 4. Product Features (What's Built Today)

### Core Clinical Flow
1. **Audio Recording** — live mic recording or file upload
2. **ASR Transcription** — Sarvam AI for Hindi/Hinglish/English, Whisper fallback
3. **Clinical Fact Extraction** — 4-layer deterministic pipeline (see above)
4. **Facts Review** — Doctor can edit/correct extracted facts before SOAP generation
5. **SOAP Note Generation** — Structured note with Indian prescription formatting
6. **Clinical Decision Support (CDS)** — Drug allergy alerts, cross-reactivity warnings
7. **Prescription Print** — Indian-format printable prescription (Tab./Syp./Inj., OD/BD/TDS)
8. **WhatsApp Sharing** — Send prescription to patient via WhatsApp (Twilio)
9. **Patient Memory** — Cross-visit memory: allergies, medications, diagnoses persist
10. **Follow-up Reminders** — Schedule and track follow-up appointments

### Safety & Compliance
- **PHI Scrubbing** — Names, phones, Aadhaar, ABHA, MRN/UHID, emails, pincodes removed BEFORE database storage
- **Consent Gate** — Recording only starts after explicit patient consent
- **Audit Trail** — Every action logged with timestamp and user
- **FHIR R4 Export** — International healthcare data standard
- **ICD-10 Coding** — WHO standard codes on all diagnoses

### Learning Flywheel
When a doctor corrects a fact (e.g., changes "paracetemol" to "paracetamol"), that correction feeds back into the system:
```
Doctor correction → fact_corrections table → aggregated into extraction_knowledge
→ Bayesian confidence scoring → auto-promoted when confidence ≥ 0.9 + 3 clinics + 3 confirmations
→ injected as overlay rules into the extractor → fewer corrections next time
```
The knowledge table is PHI-free by construction — it contains only drug names, symptom synonyms, and ASR patterns.

### Additional Generators
- **Medico-legal Document Generator** — For FIR/legal cases
- **Referral Letter Component** — Specialist referral with history summary
- **Discharge Summary Component** — Multi-visit aggregation
- **Patient Instructions (Hindi)** — Hindi-language patient instructions

### Frontend Pages
| Page | Function |
|------|----------|
| Dashboard | Session list, create new consultation (health/legal mode) |
| Consultation | Record audio → review facts → generate SOAP |
| ReviewNote | Final SOAP note, prescription, WhatsApp share, follow-up |
| Analytics | Practice metrics, billing, usage stats |
| AuditLogs | Compliance audit trail |
| DoctorProfile | Profile management, NMC number |
| PatientTimeline | Cross-visit patient history |
| PatientDownloadPortal | Public (token-gated) prescription download for patients |

---

## 5. Database Schema (16 Tables)

| Table | Purpose |
|-------|---------|
| `sessions` | Consultation sessions with status, transcript, facts, SOAP |
| `users` | Doctor accounts |
| `doctor_profiles` | Specialization, NMC number, clinic details |
| `clinics` | Multi-clinic support |
| `clinic_members` | Doctor-clinic associations |
| `patient_memory` | Cross-visit clinical memory per patient |
| `audit_log` | Every action logged for compliance |
| `usage_events` | Product analytics |
| `extraction_feedback` | Doctor feedback on extraction quality |
| `soap_feedback` | Doctor feedback on SOAP note quality |
| `consent_logs` | Patient consent records |
| `follow_up_reminders` | Scheduled follow-ups |
| `billing_records` | Billing/subscription tracking |
| `practice_settings` | Per-doctor preferences |
| `fact_corrections` | Raw doctor corrections (feeds flywheel) |
| `extraction_knowledge` | Aggregated knowledge entries with confidence scores |

---

## 6. Drug Safety System (CDS Engine)

| Check | Example | Alert Level |
|-------|---------|-------------|
| Direct allergy | Allergic to penicillin, prescribed penicillin V | Critical |
| Cross-reactivity | Allergic to penicillin, prescribed amoxicillin | Critical |
| Cross-class | Allergic to penicillin, prescribed ceftriaxone | Critical |
| Missing dosage | Metformin with no dose specified | Medium |
| Missing frequency | Atorvastatin with no schedule | Medium |
| High BP alert | BP ≥ 180/110 detected | High |
| Fever workup | Fever present, no CBC ordered | Low |
| Diabetes monitoring | Diabetes documented, no HbA1c ordered | Medium |

**Cross-reactivity classes covered:** Penicillins, cephalosporins, sulfonamides, NSAIDs/aspirin, fluoroquinolones, macrolides, statins, ACE inhibitors.

All CDS logic is deterministic. No LLM. Same input → same output. Every alert carries `safety_label = "doctor_review_required"` — the system never claims diagnostic certainty.

---

## 7. Indian-Specific Design Decisions

1. **Hindi/Hinglish support** — Keyword maps include 200+ Hindi medical terms ("bukhar"→fever, "sar dard"→headache, "ulti"→vomiting)
2. **Indian prescription format** — `Tab. Paracetamol 500mg PO TDS x 5 days`. Infers form prefix (Tab./Syp./Inj./Inh.). Maps frequencies: "twice daily"→BD, "raat ko"→HS
3. **WhatsApp delivery** — Patients expect prescriptions via WhatsApp, not email or portal
4. **NMC validation** — National Medical Commission number format verification
5. **ABHA support** — Ayushman Bharat Health Account (14-digit) format validation
6. **Aadhaar/ABHA PHI scrubbing** — India-specific PII patterns
7. **Sarvam ASR** — Best-in-class for Hindi/Hinglish medical terminology
8. **PWA** — Works on budget Android phones (₹8,000-15,000 devices common in clinics)

---

## 8. Cost Structure

| Item | Cost | Notes |
|------|------|-------|
| Clinical extraction | $0/consultation | Fully deterministic, local |
| ASR (Sarvam) | ~$0.006/min | ~5 min avg consultation = ~$0.03 |
| SOAP formatting (Gemini) | ~$0.002/consultation | Only text formatting, not extraction |
| Hosting (Render) | ~$25/month | Singapore region |
| **Total per consultation** | **~$0.032** | |
| **If using GPT for extraction** | **~$0.05/consultation** | Would make $20/mo pricing unprofitable at 30 patients/day |

At 30 patients/day × 25 working days = 750 consultations/month:
- Our cost: ~$24/month → $20/month subscription is profitable
- GPT cost: ~$37.50/month → $20/month subscription loses money

---

## 9. Planned Pricing

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Limited consultations/day, basic SOAP |
| Pro | $20/month (~₹1,700) | Unlimited consultations, full CDS, WhatsApp, memory |
| Teams | $50/seat/month | Multi-doctor clinic, shared knowledge base, analytics |

---

## 10. The Gustaf Alströmer Vision (Healthcare Administration)

Gustaf Alströmer (YC Group Partner) published an RFS identifying healthcare administration as a massive opportunity: "Most healthcare administration in the US is done by a human assistant. Building an AI-native service company that replicates and improves upon human assistants using a combination of AI, software, and humans-in-the-loop."

### Where Lipi Fits

SOAP note generation is **step 1 of 7** in the full healthcare administration workflow that happens after every consultation:

| Step | What | Our Status |
|------|------|------------|
| 1 | **SOAP Note** — consultation → structured note | ✅ Built & working |
| 2 | **Prescription Generation** — SOAP → formatted Rx | ✅ Built (prescription renderer) |
| 3 | **Investigation Orders** — SOAP → lab/imaging requisition forms | 🔜 Template from extracted investigations |
| 4 | **Referral Letters** — SOAP → specialist referral with history | 🔜 Component exists, needs template |
| 5 | **Discharge Summary** — multi-visit SOAP → discharge doc | 🔜 Component exists, needs aggregation |
| 6 | **Insurance/TPA Claims** — procedures → pre-auth & claim forms | ❌ Payer-specific templates needed |
| 7 | **MRD Coding** — SOAP → ICD-10 codes for medical records | ✅ ICD-10 mapper built |

**Key insight:** Every step after SOAP is a deterministic template fill from structured data we already extract. Same architecture — no LLM, zero hallucination, $0/consultation. We're not replacing the assistant — we're giving them tools that pre-fill 80% of each document.

### India-Specific Opportunity
- No Epic/Cerner — healthcare admin is 100% manual in India
- Doctor's assistant handles steps 2-7 by hand after every consultation
- 30 patients/day × 7 admin steps = 210 manual document tasks/day
- Automating even 3 of these steps saves the assistant 2-3 hours/day

---

## 11. Observation Sprint (Pilot Protocol)

A structured 14-day deployment protocol for new clinic pilots:
- **Week 1:** Deploy, run 5-10 consultations, collect ground truth, measure initial accuracy
- **Week 2:** Scale to 25-30 consultations, run eval harness, calculate F1 scores, present results
- **Target metrics:** ASR WER < 25%, Extraction Precision > 90%, Extraction Recall > 80%, Medication Accuracy > 95%
- **Eval harness:** Automated comparison of Lipi output vs human-labeled ground truth
- **Conversion:** Present accuracy numbers + time saved → paid subscription

---

## 12. Safety Rules (Non-Negotiable)

1. **Never hallucinate** — if not in transcript, write "not specified"
2. All CDS output: `safety_label = "doctor_review_required"` always
3. Never auto-prescribe or claim diagnosis certainty
4. Allergy-medication conflicts = urgency: critical
5. Patient data never sent to external LLMs for extraction
6. PHI scrubbed before persistent storage
7. Doctor is final authority on everything
8. Audio files deleted after transcription
9. Prescription links are time-limited and require patient verification

---

## 13. Technical Specifications for Reference

### Indian Prescription Formatting
```
Tab. Paracetamol 500mg PO TDS x 5 days
Syp. Amoxicillin 250mg PO BD x 7 days
Inj. Ceftriaxone 1g IV OD x 3 days
Inh. Salbutamol 100mcg INH SOS
```

Frequency mappings: OD (once daily), BD (twice daily), TDS (three times daily), QID (four times daily), HS (at bedtime/"raat ko"), SOS (as needed), AC (before food), PC (after food)

### SOAP Note Keys
Always single uppercase letters: `{"S": "...", "O": "...", "A": "...", "P": "..."}`

### NMC Number Format
Regex: `^[A-Z]{2,3}-?\d{4,7}$` (e.g., MH-12345, KA-1234)

### ABHA Number Format
14 digits after stripping dashes/spaces

### Session Modes
- `health` — standard clinical scribe
- `legal` — medico-legal documentation (FIR, legal reports)

---

## 14. What Makes Lipi Defensible

1. **Deterministic extraction** — zero hallucination by architecture, not by prompt engineering
2. **Hindi/Hinglish keyword maps** — hand-curated, not available in any open-source NLP library
3. **Learning flywheel** — every doctor correction makes the system better for all doctors
4. **$0 extraction cost** — allows aggressive pricing that LLM-based competitors can't match
5. **Doctor network** — India's top surgeons are already using it
6. **Evidence/provenance system** — every fact has character-level proof from the transcript
7. **Multi-specialty validation** — cardiac, neuro, dental, pediatric surgery, general medicine

---

## 15. Key Files (for code-level context)

| File | What it does |
|------|-------------|
| `backend/app/services/clinical_extractor.py` | The core 4-layer extraction pipeline |
| `backend/app/services/clinical_pipeline.py` | Orchestrator: extractor + GLiNER merge |
| `backend/app/services/medical_ontology.py` | Ontology loading, SymSpell indices |
| `backend/app/services/soap_generator.py` | SOAP note + Indian Rx formatting |
| `backend/app/services/cds_engine.py` | Drug safety alerts |
| `backend/app/services/provenance.py` | Evidence/provenance tracking |
| `backend/app/services/learning_service.py` | Learning flywheel |
| `backend/app/services/phi_scrubber.py` | PHI removal |
| `backend/app/services/memory_context.py` | Cross-visit patient memory |
| `backend/app/api/routes_notes.py` | Main clinical pipeline route (25 internal deps) |
| `frontend/src/pages/Consultation.tsx` | Main consultation page |
| `frontend/src/components/FactsReviewEditor.tsx` | Doctor correction interface |
| `frontend/src/components/ClinicalResults.tsx` | SOAP display + sub-documents |

---

## 16. Open Questions for Product Refinement

1. **Which admin steps (3-7) should we build next?** Need OPD observation data to know which ones cause the most pain.
2. **Should we build a mobile-native app or stay PWA?** PWA works but has limitations (no background recording, limited offline).
3. **How to handle multi-doctor clinics?** Current architecture supports it but UX isn't optimized for clinic-level workflows.
4. **Regional language expansion** — Tamil, Telugu, Bengali, Marathi are the next 4 languages by OPD volume.
5. **Integration with existing HMS/PMS** — Some clinics use Practo or custom software. API integration vs. standalone?
6. **Pricing for India** — Is $20/month (₹1,700) right? Some doctors spend ₹500/month on their assistant's chai budget.
7. **Insurance claim automation** — India's TPA system is fragmented (30+ TPAs, each with different forms). How to approach?
8. **ABDM integration** — India's national health ID system (ABHA). Required for government hospital integration.
9. **Voice-first UI** — Should the doctor be able to navigate the app entirely by voice during consultation?
10. **Offline mode** — Many Indian clinics have unreliable internet. Can we run ASR locally (Whisper) + sync later?

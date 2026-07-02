# Augnito Competitive Teardown

Date: 2026-06-28
Status: Internal only — verify time-sensitive claims before using in external pitch materials
Related: [[04_COMPETITORS]], [[03_PRODUCT_STRATEGY]], [[09_STRATEGIC_ROADMAP]], [[14_BUILD_PLAN]]

---

## What Augnito Is

Augnito is an Indian medical speech recognition and clinical documentation company founded by Rustom Lawyer, headquartered in Mumbai. Their core product is voice-to-text medical dictation trained on Indian English accents and medical terminology.

Products (verify current naming before citing):
- **Augnito Spectra** — ambient AI listening in the consultation room, generates structured notes
- **Augnito Voice Services** — API layer for integrating speech recognition into hospital software
- **Augnito One** — standalone dictation app for individual doctors

Target customer: large hospitals, multi-specialty chains, hospital IT departments. Apollo, Fortis, and similar enterprise accounts are their natural buyers.

---

## Their Approach

- **Speech recognition first** — core technology is ASR trained on Indian medical English. Structured output is secondary.
- **English-first** — designed for English-speaking doctors dictating in formal medical English. Hindi/Hinglish is not the native use case.
- **Hospital/EMR integration** — sells to hospital IT, integrates into existing EMR systems (Cerner, Epic, homegrown). Not a standalone OPD workflow.
- **LLM-based structuring** — downstream note generation uses generative models to convert free dictation into structured notes. No public documentation of evidence provenance per extracted fact.
- **Enterprise contracts** — pricing is enterprise, not per-seat SaaS for a 3-doctor clinic. Setup requires IT involvement.

---

## The Real Differentiators (What Lipi Has That Augnito Does Not)

### 1. Hinglish-native extraction

Augnito is English-first dictation. Real Indian OPD is code-switched — "jari rakhna hai", "avoid karo abhi", "shuru karo", "se bhi reaction hua tha". Augnito's ASR handles Indian English accents well. It does not handle Hinglish clinical intent natively.

Lipi's extraction pipeline is built for exactly this: 50+ Hinglish status patterns, medication status in mixed Hindi-English, allergy disambiguation in Hinglish context. This is the pipeline Augnito cannot replicate by switching ASR models.

### 2. Zero-hallucination extraction with evidence provenance

Augnito uses a generative model to convert free dictation into structured notes. Generative models hallucinate. There is no public claim from Augnito that every extracted fact traces back to a verbatim transcript span.

Lipi's architecture makes hallucination structurally impossible in the extraction path: deterministic Python only, GLiNER in extractive mode (spans must exist verbatim), no LLM in the transcript → SOAP pipeline. Every fact has an evidence span. Every fact requires doctor confirmation before it enters the record.

This becomes a regulatory moat when Indian health regulators eventually require audit trails for AI-generated clinical records. Lipi already has this. Augnito would need to rebuild.

### 3. OPD service company vs hospital dictation tool

Augnito sells dictation. The doctor still:
- Sends investigation orders manually
- Messages patients manually
- Fills pre-auth forms manually
- Manages the assistant work queue manually

Lipi turns one approved consultation into: SOAP note + investigation order + patient WhatsApp message + assistant work queue + pre-auth checklist. This is not a dictation comparison. Augnito is a tool. Lipi is the service.

This matches Gustaf Alströmer's AI-native service company framing exactly. Augnito is not competing in this category.

### 4. Learning loop

Every doctor correction in Lipi feeds into `extraction_knowledge` with Bayesian confidence scoring. After 3 clinics confirm an alias, it auto-promotes. `_canonical_med()` starts recognising "Telma" → Telmisartan across that clinic without retraining any model.

Augnito ships a static model. You get what you get. Their accuracy does not improve from clinic usage data unless they release a new model version.

### 5. OPD economics

Augnito pricing is enterprise. A 3-doctor OPD clinic in Pune cannot buy Augnito — the setup friction and contract minimum rule it out. Lipi is built for exactly that clinic: ₹999/month Pro, ₹50/seat Teams, no IT department required.

---

## Where Augnito Is Stronger

Be honest about this in the pitch.

- **ASR quality** — Augnito's speech recognition is likely better than Sarvam for pure English medical dictation. Their ASR training dataset for Indian medical English is larger and more mature.
- **Hospital integration** — Augnito has real EMR integrations. Lipi does not. For hospitals that want EMR integration, Augnito wins today.
- **Brand and trust** — Augnito has enterprise hospital accounts with named references. Lipi is pre-scale.
- **Funding** — Augnito has institutional backing and a larger team. Lipi is a startup.

Do not pretend these don't exist. YC partners will ask.

---

## How To Answer "What About Augnito?" In The YC Interview

Short answer (15 seconds):

> "Augnito is English-first hospital dictation. We are Hinglish-native OPD administration. They sell to hospital IT departments on enterprise contracts. We sell to the 3-doctor clinic in Pune that can't afford enterprise software. And we don't just transcribe — we turn one consultation into investigation orders, patient messages, and pre-auth drafts. Augnito doesn't do any of that."

If they push deeper:

> "The deeper difference is architectural. Augnito uses a generative model to structure notes — which means hallucination risk and no evidence trail per fact. Our extraction is deterministic — every fact traces to a verbatim transcript span, and nothing enters the record without doctor confirmation. When regulators require audit trails for AI clinical records, that becomes lock-in."

---

## US Ambient AI Scribes (Abridge, Nabla, Suki, Ambience)

Brief positioning — detailed teardown not needed for YC unless asked:

- All built for US EHR workflows (Epic, Cerner). Zero India OPD fit.
- Pricing in USD, designed for US physician reimbursement economics. Not viable for Indian clinics at ₹999/month.
- English only. No Hinglish.
- All use LLMs for note generation. None have public evidence provenance per fact.
- None have work queue, investigation orders, or pre-auth for Indian TPAs.

Dismiss quickly if asked: "US ambient scribes are built for Epic integration and US physician billing. The Indian OPD market is structurally different — different language, different economics, different workflow. They are not competing here."

---

## The Status Quo Competitor

This is the real answer to "what do doctors use today":

- Doctor writes notes by hand or dictates to assistant
- Assistant types prescriptions in Word or on paper
- Investigation orders written on paper slips
- Patient follow-up via personal WhatsApp
- Pre-auth forms filled by staff from memory
- Total time per consultation: 8-12 minutes of admin

Lipi replaces this entirely for ₹33/consultation (₹999/month ÷ 30 sessions). The real competitor is the clipboard and WhatsApp, not Augnito.

---

## Verification Checklist

Before using any claim externally, verify:

- [ ] Augnito current product names and pricing (their website, last checked: not verified)
- [ ] Whether Augnito Spectra supports Hindi/Hinglish (demo or public docs)
- [ ] Whether Augnito has a provenance/evidence trail claim anywhere public
- [ ] Named hospital accounts they claim publicly
- [ ] Any recent funding rounds or headcount

Claims in this document about Augnito's architecture (LLM-based structuring, no evidence provenance) are based on public positioning and product category inference, not internal knowledge. Verify before citing as fact in external materials.

---

## Related Notes

- [[04_COMPETITORS]] — full competitor framework and research queue
- [[03_PRODUCT_STRATEGY]] — Lipi positioning and wedge
- [[09_STRATEGIC_ROADMAP]] — path from scribe to service company
- [[14_BUILD_PLAN]] — what to build to make these claims real

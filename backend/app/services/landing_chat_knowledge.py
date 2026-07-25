"""Curated knowledge base for the public landing-page chatbot.

Every chunk here must be traceable to something actually shipped and stated
elsewhere on the site (Landing.tsx, Research.tsx, Pricing.tsx). This is not a
clinical knowledge source, the chatbot answers questions about Lipi the
product and company only, never medical questions.
"""

KNOWLEDGE_CHUNKS: list[dict[str, str]] = [
    {
        "id": "product",
        "title": "What Lipi is",
        "text": (
            "Lipi is an AI-native OPD (outpatient department) service for Indian doctors. "
            "A doctor speaks once during a consultation, and Lipi turns that into "
            "doctor-reviewed clinical notes, prescriptions, investigation orders, "
            "follow-up reminders, patient WhatsApp updates, and ABDM-ready records. "
            "Lipi is not just a scribe: most scribing products only draft the note. "
            "Lipi uses the consultation as the trigger for the whole OPD service, "
            "including billing, assistant task queues, and government record filing."
        ),
    },
    {
        "id": "zero_hallucination",
        "title": "Zero-hallucination architecture",
        "text": (
            "Lipi's clinical fact extraction is fully deterministic, not generative. "
            "No large language model sits in the clinical fact path. Every fact "
            "(symptom, medication, vital, diagnosis) is pulled through rule-based and "
            "evidence-based extraction and traces back to the exact sentence the doctor "
            "spoke. Nothing becomes an official record until the doctor explicitly "
            "reviews and confirms it. This is a structural safety gate, not a disclaimer."
        ),
    },
    {
        "id": "research_hinglish",
        "title": "Hinglish negation research",
        "text": (
            "Most published clinical negation detection research (NegEx, ConText) is "
            "built for English. Hindi negates differently: 'nahi' typically comes after "
            "the object and before the verb, and doctors code-switch between Hindi and "
            "English mid-sentence. Lipi built and benchmarked its own negation and "
            "uncertainty layer specifically for Hinglish OPD speech, reaching 85.2% "
            "macro-F1 on an internal 200-sentence benchmark, which is published publicly "
            "on GitHub (github.com/Lipi-Research/lipi-research-datasets) alongside the "
            "annotation methodology and a literature comparison."
        ),
    },
    {
        "id": "research_learning",
        "title": "Continual learning without model weights",
        "text": (
            "Lipi does not fine-tune or retrain any model on patient data. Instead, "
            "doctor corrections become candidate rules that are promoted into the "
            "deterministic ontology only after explicit human review, and patient "
            "history is assembled as context at inference time. This gives the "
            "practical effect of continual learning, improving over time, without "
            "ever touching model weights or risking silent drift."
        ),
    },
    {
        "id": "research_amr",
        "title": "AMR (antimicrobial resistance) research",
        "text": (
            "Around 80% of India's antibiotic consumption happens in primary care, but "
            "0% of ICMR AMRSN and NCDC NARS-Net surveillance samples come from "
            "primary-care settings. Lipi's research quantifies this gap across 12 "
            "site-years of source reports. This is a gap analysis, not a deployed "
            "surveillance claim, but Lipi is structurally positioned to help close it "
            "because it already generates structured OPD documentation at that layer."
        ),
    },
    {
        "id": "research_ddi",
        "title": "Drug-drug interaction dataset",
        "text": (
            "Lipi has mapped 80 drug-drug interaction pairs specifically for the Indian "
            "formulary, including Indian brand names and generic equivalents, sourced "
            "from openFDA, the WHO/MoHFW National List of Essential Medicines (India), "
            "NPPA pricing data, and PubMed. This dataset is published publicly on "
            "GitHub. Western DDI checkers are usually built for Western branded-drug "
            "databases and don't handle Indian brand-generic confusion well."
        ),
    },
    {
        "id": "whatsapp",
        "title": "WhatsApp care automation",
        "text": (
            "After a doctor reviews and signs a consultation, Lipi can send the signed "
            "prescription, test order links, follow-up reminders, and appointment "
            "booking prompts directly to the patient over WhatsApp. Patients can reply "
            "HAAN (yes) or NAHI (no) to confirm or reschedule, or reply with a number to "
            "pick an appointment slot. The doctor remains the final clinical authority "
            "at every step."
        ),
    },
    {
        "id": "abdm",
        "title": "ABDM and government compliance",
        "text": (
            "ABDM (Ayushman Bharat Digital Mission) is India's national digital health "
            "framework. Under the NMC Code of Ethics, Clause 1.3, every registered "
            "doctor must maintain structured patient records and produce them within 72 "
            "hours of a request. Lipi automatically produces ABDM-ready, ABHA-linked, "
            "HL7 FHIR R4 structured records as a byproduct of the consultation, along "
            "with DHIS (Digital Health Incentive Scheme) filing that can generate "
            "government payouts to the clinic."
        ),
    },
    {
        "id": "pricing",
        "title": "Pricing",
        "text": (
            "Lipi has three tiers: Pay-as-you-go at 100 rupees per consultation for "
            "solo doctors trying Lipi; Clinic Pro at 1,499 rupees per doctor per month, "
            "which includes unlimited consultations, WhatsApp automation, lab "
            "dispatch, UPI payment collection, and ABDM filing, often largely offset by "
            "government DHIS payouts; and a custom Hospital/Chain tier with volume "
            "pricing, multi-doctor admin, and dedicated onboarding. Exact DHIS payout "
            "figures are being finalized and may vary by source on the site, for a "
            "definitive number, contact the team directly."
        ),
    },
    {
        "id": "languages",
        "title": "Language support",
        "text": (
            "Lipi supports 11+ Indian languages including Hindi, Hinglish (Hindi-English "
            "code-switching), and English, handling code-switching, self-corrections, "
            "and regional vocabulary natively."
        ),
    },
    {
        "id": "company",
        "title": "Company and contact",
        "text": (
            "Lipi is currently onboarding pilot doctors directly. To get in touch, "
            "request early access, or ask a research collaboration question, email "
            "arushsinghal98@gmail.com. Lipi is built in India."
        ),
    },
    {
        "id": "boundaries",
        "title": "What this assistant will not do",
        "text": (
            "This assistant answers questions about the Lipi product, research, "
            "pricing, and company only. It does not provide medical advice, does not "
            "diagnose, and does not answer clinical questions about a patient's "
            "symptoms or treatment. For clinical questions, consult a doctor."
        ),
    },
]

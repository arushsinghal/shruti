"""Shared PDF generation for prescriptions, referrals, OPD register, and TPA claims."""

from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# ICD-10 map — top 300 diagnoses in Indian outpatient practice
# ---------------------------------------------------------------------------
ICD10: dict[str, str] = {
    "hypertension": "I10", "htn": "I10", "essential hypertension": "I10",
    "type 2 diabetes": "E11", "t2dm": "E11", "diabetes mellitus": "E11", "diabetes": "E11",
    "type 1 diabetes": "E10",
    "upper respiratory tract infection": "J06.9", "urti": "J06.9", "cold": "J06.9",
    "pneumonia": "J18.9", "community acquired pneumonia": "J18.9",
    "acute bronchitis": "J20.9", "bronchitis": "J20.9",
    "asthma": "J45.9", "bronchial asthma": "J45.9",
    "copd": "J44.1", "chronic obstructive pulmonary disease": "J44.1",
    "gastritis": "K29.7", "acute gastritis": "K29.0",
    "gastroenteritis": "K52.9", "diarrhoea": "A09", "diarrhea": "A09",
    "gerd": "K21.0", "acid reflux": "K21.0", "gastroesophageal reflux": "K21.0",
    "peptic ulcer": "K27.9", "duodenal ulcer": "K26.9",
    "irritable bowel syndrome": "K58.9", "ibs": "K58.9",
    "urinary tract infection": "N39.0", "uti": "N39.0",
    "acute kidney injury": "N17.9", "ckd": "N18.9", "chronic kidney disease": "N18.9",
    "fever": "R50.9", "pyrexia": "R50.9",
    "malaria": "B54", "dengue": "A97.9", "typhoid": "A01.0",
    "covid-19": "U07.1", "covid": "U07.1",
    "hypothyroidism": "E03.9", "hyperthyroidism": "E05.9", "thyroid disorder": "E07.9",
    "anaemia": "D64.9", "anemia": "D64.9", "iron deficiency anaemia": "D50.9",
    "migraine": "G43.9", "headache": "R51",
    "vertigo": "R42", "dizziness": "R42",
    "anxiety": "F41.9", "anxiety disorder": "F41.9",
    "depression": "F32.9", "depressive episode": "F32.9",
    "insomnia": "G47.0",
    "osteoarthritis": "M19.9", "arthritis": "M13.9", "rheumatoid arthritis": "M06.9",
    "back pain": "M54.5", "low back pain": "M54.5", "lbp": "M54.5",
    "cervical spondylosis": "M47.812",
    "knee pain": "M25.561",
    "gout": "M10.9",
    "eczema": "L20.9", "atopic dermatitis": "L20.9", "dermatitis": "L30.9",
    "psoriasis": "L40.9", "urticaria": "L50.9",
    "acne": "L70.0",
    "conjunctivitis": "H10.9", "stye": "H00.0",
    "otitis media": "H66.9", "ear infection": "H66.9",
    "sinusitis": "J32.9", "acute sinusitis": "J01.9",
    "tonsillitis": "J35.0", "pharyngitis": "J02.9", "sore throat": "J02.9",
    "coronary artery disease": "I25.10", "cad": "I25.10", "angina": "I20.9",
    "heart failure": "I50.9", "cardiac failure": "I50.9",
    "atrial fibrillation": "I48.91", "afib": "I48.91",
    "stroke": "I64", "tia": "G45.9",
    "epilepsy": "G40.909", "seizure": "G40.909",
    "parkinson": "G20", "parkinson's disease": "G20",
    "dementia": "F03.90", "alzheimer": "G30.9",
    "obesity": "E66.9", "overweight": "E66.9",
    "vitamin d deficiency": "E55.9", "vitamin b12 deficiency": "E53.8",
    "pregnancy": "Z34.90", "antenatal": "Z34.90",
    "hypothyroidism in pregnancy": "O99.284",
    "gestational diabetes": "O24.419",
    "hepatitis b": "B18.1", "hepatitis c": "B18.2", "hepatitis a": "B15.9",
    "tuberculosis": "A15.9", "tb": "A15.9", "pulmonary tuberculosis": "A15.0",
    "hiv": "B20", "aids": "B20",
    "chronic liver disease": "K76.9", "cirrhosis": "K74.6",
    "jaundice": "R17", "cholecystitis": "K81.9", "gallstones": "K80.20",
    "appendicitis": "K37",
    "hernia": "K46.9", "inguinal hernia": "K40.90",
    "fracture": "T14.8",
    "sprain": "T14.3", "ligament sprain": "T14.3",
    "wound": "T14.0", "laceration": "T14.1",
    "burn": "T30.0",
}


def _icd10(diagnosis: str) -> str:
    d = diagnosis.lower().strip()
    return ICD10.get(d, "")


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontSize=14, spaceAfter=2,
                             textColor=colors.HexColor("#1e293b")),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=11, spaceBefore=10,
                             spaceAfter=3, textColor=colors.HexColor("#334155")),
        "body": ParagraphStyle("BODY", parent=base["Normal"], fontSize=9, leading=14,
                               textColor=colors.HexColor("#334155")),
        "small": ParagraphStyle("SMALL", parent=base["Normal"], fontSize=7.5, leading=11,
                                textColor=colors.HexColor("#64748b")),
        "mono": ParagraphStyle("MONO", parent=base["Code"], fontSize=8, leading=12,
                               fontName="Courier", textColor=colors.HexColor("#475569")),
        "center": ParagraphStyle("CTR", parent=base["Normal"], fontSize=9,
                                 alignment=TA_CENTER, textColor=colors.HexColor("#334155")),
        "right": ParagraphStyle("RT", parent=base["Normal"], fontSize=8,
                                alignment=TA_RIGHT, textColor=colors.HexColor("#64748b")),
        "rx": ParagraphStyle("RX", parent=base["Normal"], fontSize=28, leading=30,
                              textColor=colors.HexColor("#1e293b"), fontName="Helvetica-Bold"),
        "warn": ParagraphStyle("WARN", parent=base["Normal"], fontSize=7.5, leading=11,
                               textColor=colors.HexColor("#92400e"),
                               backColor=colors.HexColor("#fef3c7")),
    }


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"))


def _parse_soap(soap_raw) -> dict:
    if not soap_raw:
        return {}
    if isinstance(soap_raw, str):
        try:
            return json.loads(soap_raw)
        except Exception:
            return {}
    return soap_raw or {}


def _parse_facts(facts_raw) -> dict:
    if not facts_raw:
        return {}
    if isinstance(facts_raw, str):
        try:
            return json.loads(facts_raw)
        except Exception:
            return {}
    return facts_raw or {}


def _footer(session_id: str, label: str):
    def _fn(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(2 * cm, 1.2 * cm, f"Lipi Health — {label} — Session {session_id[:8]}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm,
                               f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC — For physician review")
        canvas.restoreState()
    return _fn


# ---------------------------------------------------------------------------
# 1. PRESCRIPTION
# ---------------------------------------------------------------------------

def build_prescription_pdf(
    *,
    session_id: str,
    patient_name: str,
    patient_age: str,
    patient_sex: str,
    doctor_name: str,
    doctor_nmc: str,
    doctor_specialization: str = "",
    clinic_name: str,
    clinic_address: str,
    clinic_phone: str,
    soap_raw: Any,
    facts_raw: Any,
    date_str: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A5,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=2 * cm,
                            title="Prescription")
    S = _styles()
    W = A5[0] - 3 * cm
    soap = _parse_soap(soap_raw)
    facts = _parse_facts(facts_raw)
    meds = facts.get("medications") or []

    story = []

    # ── Clinic header ──
    story.append(Paragraph(f"<b>{clinic_name}</b>", S["h1"]))
    if clinic_address:
        story.append(Paragraph(clinic_address, S["small"]))
    if clinic_phone:
        story.append(Paragraph(f"Ph: {clinic_phone}", S["small"]))
    story.append(_hr())
    story.append(Spacer(1, 0.2 * cm))

    # Doctor + date row
    spec_line = f"{doctor_specialization}  |  NMC Reg. No.: {doctor_nmc or 'N/A'}" if doctor_specialization else f"NMC Reg. No.: {doctor_nmc or 'N/A'}"
    doc_row = Table(
        [[Paragraph(f"<b>{doctor_name}</b>", S["body"]),
          Paragraph(f"Date: {date_str}", S["right"])],
         [Paragraph(spec_line, S["small"]), Paragraph("", S["small"])]],
        colWidths=[W * 0.65, W * 0.35]
    )
    doc_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story.append(doc_row)
    story.append(_hr())
    story.append(Spacer(1, 0.2 * cm))

    # Patient row
    age_sex = f"{patient_age or '—'} / {patient_sex or '—'}"
    pt_row = Table(
        [[Paragraph(f"<b>Patient:</b> {patient_name or 'N/A'}", S["body"]),
          Paragraph(f"Age/Sex: {age_sex}", S["body"])]],
        colWidths=[W * 0.6, W * 0.4]
    )
    pt_row.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(pt_row)
    story.append(_hr())
    story.append(Spacer(1, 0.3 * cm))

    # Rx symbol + medications
    story.append(Paragraph("℞", S["rx"]))
    story.append(Spacer(1, 0.2 * cm))

    if meds:
        med_rows = [
            [Paragraph("<b>#</b>", S["small"]),
             Paragraph("<b>Drug</b>", S["small"]),
             Paragraph("<b>Dose/Strength</b>", S["small"]),
             Paragraph("<b>Freq</b>", S["small"]),
             Paragraph("<b>Duration</b>", S["small"]),
             Paragraph("<b>Instructions</b>", S["small"])]
        ]
        for i, m in enumerate(meds, 1):
            if isinstance(m, dict):
                name = m.get("name") or ""
                dosage = m.get("dosage") or m.get("dose") or ""
                freq = m.get("frequency") or ""
                dur = m.get("duration") or ""
            else:
                name, dosage, freq, dur = str(m), "", "", ""
            med_rows.append([
                Paragraph(str(i), S["body"]),
                Paragraph(f"<b>{name.capitalize()}</b>", S["body"]),
                Paragraph(dosage, S["body"]),
                Paragraph(freq.upper() if freq.lower() in {"od", "bd", "tds", "qid", "sos", "prn", "stat"} else freq, S["body"]),
                Paragraph(dur, S["body"]),
                Paragraph("After meals" if freq else "", S["small"]),
            ])
        t = Table(med_rows, colWidths=[0.5 * cm, W * 0.28, W * 0.18, W * 0.1, W * 0.15, W * 0.2])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
    else:
        plan_text = soap.get("P") or soap.get("plan") or ""
        if plan_text:
            story.append(Paragraph(plan_text, S["body"]))
        else:
            story.append(Paragraph("<i>No medications recorded.</i>", S["small"]))

    story.append(Spacer(1, 0.4 * cm))

    # Follow-up
    follow_up = facts.get("follow_up") or []
    if follow_up:
        fu = follow_up[0] if isinstance(follow_up, list) else str(follow_up)
        story.append(Paragraph(f"<b>Follow-up:</b> {fu}", S["body"]))
        story.append(Spacer(1, 0.2 * cm))

    # Diagnosis
    diagnoses = facts.get("diagnoses") or []
    if diagnoses:
        story.append(Paragraph(f"<b>Diagnosis:</b> {', '.join(diagnoses)}", S["body"]))
        story.append(Spacer(1, 0.3 * cm))

    story.append(_hr())
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"<b>{doctor_name}</b>", S["body"]))
    if doctor_nmc:
        story.append(Paragraph(f"NMC Reg. No.: {doctor_nmc}", S["small"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<i>This prescription requires physician verification before dispensing. "
        "AI-assisted draft — not a certified medical device output.</i>", S["warn"]))

    def rx_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(1.5 * cm, 1 * cm, "Lipi Health — For physician review only")
        canvas.drawRightString(A5[0] - 1.5 * cm, 1 * cm, f"Session {session_id[:8]}")
        canvas.restoreState()

    doc.build(story, onFirstPage=rx_footer, onLaterPages=rx_footer)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 2. REFERRAL LETTER
# ---------------------------------------------------------------------------

def build_referral_pdf(
    *,
    session_id: str,
    patient_name: str,
    patient_age: str,
    patient_sex: str,
    doctor_name: str,
    doctor_nmc: str,
    clinic_name: str,
    clinic_phone: str,
    to_doctor: str,
    to_specialty: str,
    reason: str,
    urgency: str,
    soap_raw: Any,
    facts_raw: Any,
    date_str: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                            topMargin=2.5 * cm, bottomMargin=2.5 * cm,
                            title="Referral Letter")
    S = _styles()
    W = A4[0] - 5 * cm
    soap = _parse_soap(soap_raw)
    facts = _parse_facts(facts_raw)

    story = []

    story.append(Paragraph(f"<b>{clinic_name}</b>", S["h1"]))
    if clinic_phone:
        story.append(Paragraph(f"Ph: {clinic_phone}", S["small"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Date: {date_str}", S["right"]))
    story.append(Spacer(1, 0.5 * cm))

    # Urgency badge
    if urgency.lower() == "urgent":
        story.append(Paragraph("<b>⚠ URGENT REFERRAL</b>", ParagraphStyle(
            "URG", parent=S["body"], textColor=colors.HexColor("#dc2626"),
            backColor=colors.HexColor("#fee2e2"), fontSize=10)))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(f"To: <b>Dr. {to_doctor}</b>", S["body"]))
    if to_specialty:
        story.append(Paragraph(f"Specialty: {to_specialty}", S["body"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Dear Doctor,", S["body"]))
    story.append(Spacer(1, 0.2 * cm))

    age_sex = f"{patient_age or '—'}/{patient_sex or '—'}"
    story.append(Paragraph(
        f"I am referring <b>{patient_name or 'the patient'}</b> ({age_sex}) "
        f"under your care for further evaluation and management.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Reason
    story.append(Paragraph("<b>Reason for Referral:</b>", S["body"]))
    story.append(Paragraph(reason or "As clinically indicated.", S["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # Clinical summary
    story.append(Paragraph("<b>Clinical Summary:</b>", S["h2"]))
    story.append(_hr())
    story.append(Spacer(1, 0.15 * cm))

    subjective = soap.get("S") or soap.get("subjective") or ""
    assessment = soap.get("A") or soap.get("assessment") or ""
    plan_text = soap.get("P") or soap.get("plan") or ""

    if subjective:
        story.append(Paragraph(f"<b>History:</b> {subjective}", S["body"]))
    diagnoses = facts.get("diagnoses") or []
    if diagnoses:
        story.append(Spacer(1, 0.1 * cm))
        icd_list = ", ".join(
            f"{d} ({_icd10(d)})" if _icd10(d) else d for d in diagnoses
        )
        story.append(Paragraph(f"<b>Diagnosis:</b> {icd_list}", S["body"]))
    vitals = facts.get("vitals") or []
    if vitals:
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph(f"<b>Vitals:</b> {', '.join(vitals)}", S["body"]))

    meds = facts.get("medications") or []
    if meds:
        story.append(Spacer(1, 0.1 * cm))
        med_strs = []
        for m in meds:
            if isinstance(m, dict):
                parts = [m.get("name", "")]
                if m.get("dosage"): parts.append(m["dosage"])
                if m.get("frequency"): parts.append(m["frequency"])
                med_strs.append(" ".join(p for p in parts if p))
            else:
                med_strs.append(str(m))
        story.append(Paragraph(f"<b>Current Medications:</b> {', '.join(med_strs)}", S["body"]))

    investigations = facts.get("investigations") or []
    if investigations:
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph(f"<b>Investigations Ordered:</b> {', '.join(investigations)}", S["body"]))
    if assessment:
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph(f"<b>Assessment:</b> {assessment}", S["body"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "Kindly evaluate and advise. Please do not hesitate to contact me for further information.",
        S["body"]
    ))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(f"Yours sincerely,", S["body"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<b>{doctor_name}</b>", S["body"]))
    if doctor_nmc:
        story.append(Paragraph(f"NMC Reg. No.: {doctor_nmc}", S["small"]))
    story.append(Paragraph(clinic_name, S["small"]))

    doc.build(story, onFirstPage=_footer(session_id, "Referral Letter"),
              onLaterPages=_footer(session_id, "Referral Letter"))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 3. OPD REGISTER
# ---------------------------------------------------------------------------

def build_opd_register_pdf(
    *,
    sessions: list[dict],
    date_label: str,
    clinic_name: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="OPD Register")
    S = _styles()
    W = A4[0] - 3 * cm
    story = []

    story.append(Paragraph(f"<b>{clinic_name} — OPD Register</b>", S["h1"]))
    story.append(Paragraph(f"Date: {date_label}  |  Total patients: {len(sessions)}", S["small"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_hr())
    story.append(Spacer(1, 0.2 * cm))

    header = [
        Paragraph("<b>S.No</b>", S["small"]),
        Paragraph("<b>Time</b>", S["small"]),
        Paragraph("<b>Patient</b>", S["small"]),
        Paragraph("<b>Age/Sex</b>", S["small"]),
        Paragraph("<b>Diagnosis</b>", S["small"]),
        Paragraph("<b>ICD-10</b>", S["small"]),
        Paragraph("<b>Treatment Summary</b>", S["small"]),
        Paragraph("<b>Doctor</b>", S["small"]),
        Paragraph("<b>Referred</b>", S["small"]),
    ]
    rows = [header]
    for i, s in enumerate(sessions, 1):
        facts = _parse_facts(s.get("clinical_facts") or s.get("facts"))
        diagnoses = facts.get("diagnoses") or []
        dx_str = diagnoses[0] if diagnoses else (s.get("diagnosis") or "—")
        icd = _icd10(dx_str)
        meds = facts.get("medications") or []
        med_names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in meds[:2]]
        tx_str = ", ".join(med_names) or "—"
        created = str(s.get("created_at", ""))[:16].replace("T", " ")
        time_str = created[11:16] if len(created) > 10 else "—"
        age = s.get("patient_age") or "—"
        sex = (s.get("patient_sex") or "—")[0].upper() if s.get("patient_sex") else "—"
        rows.append([
            Paragraph(str(i), S["small"]),
            Paragraph(time_str, S["small"]),
            Paragraph(s.get("patient_name") or "—", S["small"]),
            Paragraph(f"{age}/{sex}", S["small"]),
            Paragraph(dx_str[:30], S["small"]),
            Paragraph(icd, S["small"]),
            Paragraph(tx_str[:35], S["small"]),
            Paragraph((s.get("doctor_name") or "—")[:15], S["small"]),
            Paragraph("N", S["small"]),
        ])

    col_w = [0.7 * cm, 1.2 * cm, 2.5 * cm, 1.3 * cm, 3 * cm, 1.5 * cm, 3 * cm, 2 * cm, 1 * cm]
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "This register is auto-generated by Lipi Health from digital consultation records. "
        "Verify against source sessions for medico-legal purposes.",
        S["warn"]
    ))

    def opd_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(1.5 * cm, 1 * cm, f"Lipi Health — OPD Register — {clinic_name}")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=opd_footer, onLaterPages=opd_footer)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 4. TPA / INSURANCE CLAIM PACKAGE
# ---------------------------------------------------------------------------

def build_tpa_claim_pdf(
    *,
    session_id: str,
    patient_name: str,
    patient_age: str,
    patient_sex: str,
    policy_number: str,
    insurer_name: str,
    tpa_name: str,
    doctor_name: str,
    doctor_nmc: str,
    clinic_name: str,
    clinic_address: str,
    consultation_fee: int,
    soap_raw: Any,
    facts_raw: Any,
    billing_rows: list[dict],
    date_str: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                            topMargin=2.5 * cm, bottomMargin=2.5 * cm,
                            title="TPA Claim")
    S = _styles()
    W = A4[0] - 5 * cm
    soap = _parse_soap(soap_raw)
    facts = _parse_facts(facts_raw)

    story = []

    story.append(Paragraph("<b>HEALTH INSURANCE CLAIM FORM</b>", ParagraphStyle(
        "CLM", parent=S["h1"], fontSize=16, alignment=TA_CENTER)))
    story.append(Paragraph("(As per IRDAI standard format)", ParagraphStyle(
        "SUB", parent=S["small"], alignment=TA_CENTER)))
    story.append(Spacer(1, 0.4 * cm))
    story.append(_hr())
    story.append(Spacer(1, 0.3 * cm))

    # Section A — Patient details
    story.append(Paragraph("<b>SECTION A — PATIENT DETAILS</b>", S["h2"]))
    a_data = [
        ["Patient Name", patient_name or "—", "Date of Consultation", date_str],
        ["Age", patient_age or "—", "Sex", patient_sex or "—"],
        ["Policy Number", policy_number or "TO BE FILLED", "Insurer", insurer_name or "—"],
        ["TPA Name", tpa_name or "—", "Pre-auth No.", "—"],
    ]
    ta = Table([[Paragraph(k, S["small"]), Paragraph(v, S["body"]),
                 Paragraph(k2, S["small"]), Paragraph(v2, S["body"])]
                for k, v, k2, v2 in a_data],
               colWidths=[3 * cm, W / 2 - 3 * cm, 3 * cm, W / 2 - 3 * cm])
    ta.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ta)
    story.append(Spacer(1, 0.3 * cm))

    # Section B — Provider details
    story.append(Paragraph("<b>SECTION B — PROVIDER DETAILS</b>", S["h2"]))
    b_data = [
        ["Treating Doctor", doctor_name or "—", "NMC Reg. No.", doctor_nmc or "—"],
        ["Clinic / Hospital", clinic_name or "—", "Address", (clinic_address or "—")[:40]],
    ]
    tb = Table([[Paragraph(k, S["small"]), Paragraph(v, S["body"]),
                 Paragraph(k2, S["small"]), Paragraph(v2, S["body"])]
                for k, v, k2, v2 in b_data],
               colWidths=[3 * cm, W / 2 - 3 * cm, 3 * cm, W / 2 - 3 * cm])
    tb.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tb)
    story.append(Spacer(1, 0.3 * cm))

    # Section C — Diagnosis
    story.append(Paragraph("<b>SECTION C — DIAGNOSIS</b>", S["h2"]))
    diagnoses = facts.get("diagnoses") or []
    if diagnoses:
        dx_rows = [["#", "Diagnosis", "ICD-10 Code"]]
        for i, d in enumerate(diagnoses, 1):
            dx_rows.append([str(i), d, _icd10(d) or "—"])
        tdx = Table(dx_rows, colWidths=[1 * cm, W - 4 * cm, 3 * cm])
        tdx.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tdx)
    else:
        story.append(Paragraph("No diagnosis recorded.", S["small"]))
    story.append(Spacer(1, 0.3 * cm))

    # Section D — Clinical notes (abbreviated SOAP)
    story.append(Paragraph("<b>SECTION D — CLINICAL SUMMARY</b>", S["h2"]))
    subj = soap.get("S") or ""
    obj = soap.get("O") or ""
    plan_text = soap.get("P") or ""
    if subj:
        story.append(Paragraph(f"<b>Presenting Complaint:</b> {subj}", S["body"]))
    if obj:
        story.append(Paragraph(f"<b>Clinical Findings:</b> {obj}", S["body"]))
    if plan_text:
        story.append(Paragraph(f"<b>Treatment Plan:</b> {plan_text}", S["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # Section E — Bill
    story.append(Paragraph("<b>SECTION E — ITEMIZED BILL</b>", S["h2"]))
    bill_header = [["S.No", "Description", "Amount (₹)"]]
    total = 0
    if billing_rows:
        for i, b in enumerate(billing_rows, 1):
            amt = int(b.get("amount") or 0)
            total += amt
            bill_header.append([str(i), b.get("notes") or "Consultation", f"₹{amt:,}"])
    else:
        total = consultation_fee or 0
        bill_header.append(["1", "Outpatient Consultation", f"₹{total:,}"])
    bill_header.append(["", "<b>Total Claimed</b>", f"<b>₹{total:,}</b>"])
    tbill = Table(
        [[Paragraph(c, S["small"] if r == 0 else S["body"]) for c in row]
         for r, row in enumerate(bill_header)],
        colWidths=[1 * cm, W - 4 * cm, 3 * cm]
    )
    tbill.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0fdf4")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbill)
    story.append(Spacer(1, 0.5 * cm))

    # Declaration
    story.append(_hr())
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "I hereby declare that the information furnished above is true and correct to the best of my knowledge. "
        "I authorize the release of medical information necessary to process this claim.",
        S["small"]
    ))
    story.append(Spacer(1, 0.6 * cm))
    sig_row = Table(
        [[Paragraph("Patient / Authorized Signatory", S["small"]),
          Paragraph("Treating Doctor", S["small"])]],
        colWidths=[W / 2, W / 2]
    )
    story.append(sig_row)
    story.append(Spacer(1, 0.8 * cm))
    sig_row2 = Table(
        [[Paragraph("___________________________", S["body"]),
          Paragraph(f"<b>{doctor_name}</b>  _______________", S["body"])]],
        colWidths=[W / 2, W / 2]
    )
    story.append(sig_row2)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "This claim package is auto-generated by Lipi Health. "
        "Attach original prescriptions, lab reports, and policy copy before submission to TPA.",
        S["warn"]
    ))

    doc.build(story, onFirstPage=_footer(session_id, "TPA Claim"),
              onLaterPages=_footer(session_id, "TPA Claim"))
    return buf.getvalue()

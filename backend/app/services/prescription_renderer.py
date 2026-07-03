"""Prescription HTML rendering service."""

from datetime import datetime
from html import escape

from app.services import provenance
from app.storage.repository import SessionRepository

repo = SessionRepository()

_SCHEDULE_H1_DRUGS = {
    "tramadol",
    "codeine",
    "buprenorphine",
    "fentanyl",
    "morphine",
    "oxycodone",
    "hydrocodone",
    "alprazolam",
    "diazepam",
    "clonazepam",
    "lorazepam",
    "zolpidem",
    "nitrazepam",
}

_SCHEDULE_H_KEYWORDS = {
    "antibiotic",
    "amoxicillin",
    "azithromycin",
    "ciprofloxacin",
    "metronidazole",
    "cefixime",
    "doxycycline",
    "cetirizine",
    "omeprazole",
    "pantoprazole",
    "metformin",
    "amlodipine",
    "atenolol",
    "atorvastatin",
    "losartan",
    "telmisartan",
}


def _esc(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _schedule_label(med_name: str) -> str:
    name_lower = med_name.lower()
    if any(drug in name_lower for drug in _SCHEDULE_H1_DRUGS):
        return "Sch. H1"
    if any(drug in name_lower for drug in _SCHEDULE_H_KEYWORDS):
        return "Sch. H"
    return ""


async def render_prescription_html(session_id: str, doctor_user_id: str) -> str:
    """Generate printable HTML prescription for a session."""

    session = await repo.get_session(session_id, doctor_user_id)
    if not session:
        raise ValueError("Session not found")

    state: dict = session.memory_state or {}

    # Confirmation gate (task 8): a reviewed session must have at least one
    # doctor-confirmed fact before a prescription can be printed. Legacy or
    # manually-constructed sessions (no _extracted_facts) bypass the gate.
    extracted = state.get("_extracted_facts")
    if extracted is not None and provenance.review_counts(extracted)["confirmed"] == 0:
        raise PermissionError(
            "No doctor-confirmed facts yet. Confirm at least one fact before "
            "generating a prescription."
        )

    meds: dict = state.get("medications", {}) or {}
    diagnoses_coded: list = state.get("diagnoses_coded", []) or [{"text": d} for d in state.get("diagnoses", [])]
    follow_up: list = state.get("follow_up", []) or []
    allergies: list = state.get("allergies", []) or []
    vitals: list = state.get("vitals", []) or []
    cds: list = session.cds_suggestions or []
    critical_cds = [c for c in cds if c.get("urgency") == "critical"]

    doc_profile = await repo.get_doctor_profile(doctor_user_id)
    patient = _esc(session.patient_name or "Patient")
    doctor = _esc(session.doctor_name or (doc_profile or {}).get("name") or "Doctor")
    mci_number = _esc((doc_profile or {}).get("mci_number", ""))
    clinic_name = _esc((doc_profile or {}).get("clinic_name", ""))
    clinic_address = _esc((doc_profile or {}).get("clinic_address", ""))
    clinic_phone = _esc((doc_profile or {}).get("clinic_phone", ""))
    date_str = _esc(
        session.created_at.strftime("%d %b %Y") if session.created_at else datetime.utcnow().strftime("%d %b %Y")
    )

    def alert_banner() -> str:
        if not critical_cds:
            return ""
        items = "".join(f"<li>{_esc(c.get('suggestion', 'Safety alert'))}</li>" for c in critical_cds)
        return (
            "<div class=\"alert\">"
            "<strong>Critical safety alerts</strong>"
            f"<ul>{items}</ul>"
            "</div>"
        )

    def vital_list() -> str:
        if not vitals:
            return "<span class=\"muted\">Not recorded</span>"
        return ", ".join(_esc(v) for v in vitals)

    def allergy_badges() -> str:
        if not allergies:
            return "<span class=\"muted\">No known allergies recorded</span>"
        return "".join(f"<span class=\"badge danger\">{_esc(a)}</span>" for a in allergies)

    def dx_list() -> str:
        if not diagnoses_coded:
            return "<li class=\"muted\">Not recorded</li>"
        rows = []
        for dx in diagnoses_coded:
            text = dx.get("text", dx) if isinstance(dx, dict) else dx
            rows.append(f"<li>{_esc(text)}</li>")
        return "".join(rows)

    def rx_rows() -> str:
        if not meds:
            return "<tr><td colspan=\"4\" class=\"muted\">No medicines recorded</td></tr>"
        rows = []
        for med_name, details in meds.items():
            details = details or {}
            label = _schedule_label(str(med_name))
            display_name = str(med_name).title()
            label_html = f" <span class=\"badge schedule\">{_esc(label)}</span>" if label else ""
            rows.append(
                "<tr>"
                f"<td><strong>{_esc(display_name)}</strong>{label_html}</td>"
                f"<td>{_esc(details.get('dosage') or details.get('dose') or '')}</td>"
                f"<td>{_esc(details.get('frequency') or '')}</td>"
                f"<td>{_esc(details.get('duration') or '')}</td>"
                "</tr>"
            )
        return "".join(rows)

    def followup_list() -> str:
        if not follow_up:
            return "<li class=\"muted\">Not recorded</li>"
        return "".join(f"<li>{_esc(item)}</li>" for item in follow_up)

    reg_line = f"<div class=\"reg\">Reg. No.: {mci_number}</div>" if mci_number else ""
    sig_reg = f"<br><span>{mci_number}</span>" if mci_number else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prescription - {patient}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f5f5f5;
      color: #1a1a1a;
      font-family: Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.45;
    }}
    .page {{
      max-width: 760px;
      margin: 24px auto;
      background: #fff;
      border: 1px solid #d1d5db;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      gap: 20px;
      padding: 18px 22px;
      border-bottom: 2px solid #0f766e;
    }}
    .header h1 {{ margin: 0 0 4px; font-size: 20pt; color: #0f766e; }}
    .clinic {{ text-align: right; font-size: 10pt; color: #374151; }}
    .reg {{ font-size: 10pt; color: #374151; }}
    .body {{ padding: 18px 22px 8px; }}
    .patient-bar {{
      display: grid;
      grid-template-columns: 1fr 1fr 120px;
      gap: 12px;
      padding: 10px 12px;
      border: 1px solid #d1fae5;
      background: #f0fdf4;
      margin-bottom: 16px;
    }}
    .label {{ display: block; color: #6b7280; font-size: 9pt; text-transform: uppercase; }}
    .value {{ font-weight: 700; }}
    section {{ margin: 14px 0; }}
    h2 {{ margin: 0 0 6px; color: #0f766e; font-size: 12pt; border-bottom: 1px solid #e5e7eb; }}
    ul {{ margin: 6px 0 0 18px; padding: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 700; }}
    .badge {{ display: inline-block; border-radius: 4px; padding: 2px 6px; margin: 0 4px 4px 0; font-size: 9pt; }}
    .danger {{ background: #fee2e2; color: #991b1b; }}
    .schedule {{ background: #fef3c7; color: #92400e; }}
    .muted {{ color: #6b7280; }}
    .alert {{ border: 1px solid #fca5a5; background: #fee2e2; color: #7f1d1d; padding: 10px 12px; margin-bottom: 16px; }}
    .footer {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      padding: 14px 22px 20px;
      border-top: 1px solid #e5e7eb;
      font-size: 9pt;
      color: #4b5563;
    }}
    .sig-line {{ min-width: 190px; border-top: 1px solid #111827; padding-top: 6px; text-align: center; color: #111827; }}
    .no-print {{ text-align: center; padding: 16px; display: flex; gap: 12px; justify-content: center; }}
    .no-print button {{ padding: 10px 28px; border-radius: 6px; font-size: 11pt; cursor: pointer; }}
    .primary {{ background: #0f766e; color: #fff; border: 0; }}
    .secondary {{ background: #fff; color: #374151; border: 1px solid #d1d5db; }}
    @page {{ margin: 1cm; }}
    @media print {{
      body {{ margin: 1cm; background: #fff; }}
      .page {{ margin: 0; border: 0; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="header">
      <div>
        <h1>{doctor}</h1>
        {reg_line}
        <div class="muted">Prescription - {date_str}</div>
      </div>
      <div class="clinic">
        {f'<div><strong>{clinic_name}</strong></div>' if clinic_name else ''}
        {f'<div>{clinic_address}</div>' if clinic_address else ''}
        {f'<div>{clinic_phone}</div>' if clinic_phone else ''}
      </div>
    </header>
    <div class="body">
      <div class="patient-bar">
        <div><span class="label">Patient</span><span class="value">{patient}</span></div>
        <div><span class="label">Doctor</span><span class="value">{doctor}</span></div>
        <div><span class="label">Date</span><span class="value">{date_str}</span></div>
      </div>
      {alert_banner()}
      <section><h2>Vitals</h2><p>{vital_list()}</p></section>
      <section><h2>Known Allergies</h2><p>{allergy_badges()}</p></section>
      <section><h2>Diagnoses</h2><ul>{dx_list()}</ul></section>
      <section>
        <h2>Medications (Rx)</h2>
        <table>
          <thead><tr><th>Medicine</th><th>Dose</th><th>Frequency</th><th>Duration</th></tr></thead>
          <tbody>{rx_rows()}</tbody>
        </table>
      </section>
      <section><h2>Follow-up Instructions</h2><ul>{followup_list()}</ul></section>
    </div>
    <footer class="footer">
      <span>
        Generated by Lipi. Doctor review required. This prescription is not a substitute for clinical judgment.<br>
        This prescription is valid for 30 days from date of issue. Schedule H/H1 drugs are valid for use in state of issue only.
      </span>
      <div class="sig-line">{doctor}{sig_reg}<br>Signature</div>
    </footer>
  </main>
  <div class="no-print">
    <button class="primary" onclick="window.print()">Print / Save as PDF</button>
    <button class="secondary" onclick="window.close()">Close Window</button>
  </div>
</body>
</html>"""

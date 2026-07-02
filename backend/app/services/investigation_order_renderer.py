"""Investigation order HTML rendering service."""

from datetime import datetime
from html import escape

from app.services import provenance
from app.storage.repository import SessionRepository

repo = SessionRepository()

_CATEGORY_MAP: dict[str, str] = {
    "cbc": "Blood Tests",
    "complete blood count": "Blood Tests",
    "hba1c": "Blood Tests",
    "fasting blood sugar": "Blood Tests",
    "fbs": "Blood Tests",
    "blood sugar": "Blood Tests",
    "rbs": "Blood Tests",
    "random blood sugar": "Blood Tests",
    "lipid profile": "Blood Tests",
    "thyroid profile": "Blood Tests",
    "tsh": "Blood Tests",
    "t3": "Blood Tests",
    "t4": "Blood Tests",
    "lft": "Blood Tests",
    "liver function test": "Blood Tests",
    "kft": "Blood Tests",
    "kidney function test": "Blood Tests",
    "creatinine": "Blood Tests",
    "uric acid": "Blood Tests",
    "serum iron": "Blood Tests",
    "ferritin": "Blood Tests",
    "tibc": "Blood Tests",
    "vitamin d": "Blood Tests",
    "vitamin b12": "Blood Tests",
    "esr": "Blood Tests",
    "crp": "Blood Tests",
    "dengue": "Blood Tests",
    "malaria": "Blood Tests",
    "widal": "Blood Tests",
    "hiv": "Blood Tests",
    "hbsag": "Blood Tests",
    "hcv": "Blood Tests",
    "blood culture": "Blood Tests",
    "urine": "Urine Tests",
    "urine routine": "Urine Tests",
    "urine culture": "Urine Tests",
    "urine r/e": "Urine Tests",
    "xray": "Imaging",
    "x-ray": "Imaging",
    "usg": "Imaging",
    "ultrasound": "Imaging",
    "ct": "Imaging",
    "mri": "Imaging",
    "ecg": "Cardiac",
    "echo": "Cardiac",
}


def _esc(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _categorise(investigations: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for inv in investigations:
        key = inv.lower().strip()
        category = "Other"
        for pattern, cat in _CATEGORY_MAP.items():
            if pattern in key:
                category = cat
                break
        grouped.setdefault(category, []).append(inv)
    return grouped


def _category_rows(investigations: list[str]) -> str:
    if not investigations:
        return '<tr><td colspan="3" class="muted">No investigations ordered</td></tr>'
    grouped = _categorise(investigations)
    rows: list[str] = []
    serial = 1
    for category, items in grouped.items():
        rows.append(f'<tr><td colspan="3" class="category">{_esc(category)}</td></tr>')
        for item in items:
            rows.append(
                "<tr>"
                f'<td class="serial">{serial}.</td>'
                f"<td><strong>{_esc(item.title())}</strong></td>"
                '<td class="result">Result: ___________</td>'
                "</tr>"
            )
            serial += 1
    return "\n".join(rows)


async def render_investigation_order_html(session_id: str, doctor_user_id: str) -> str:
    """Generate printable HTML investigation order for a session."""

    session = await repo.get_session(session_id, doctor_user_id)
    if not session:
        raise ValueError("Session not found")

    state: dict = session.memory_state or {}

    # Confirmation gate (task 9): for sessions that went through the review
    # pipeline, require at least one doctor-confirmed fact before printing an
    # order. Legacy/manually-built sessions (no _extracted_facts) are unaffected.
    extracted = state.get("_extracted_facts")
    if extracted is not None and provenance.review_counts(extracted)["confirmed"] == 0:
        raise PermissionError(
            "No doctor-confirmed facts yet. Confirm at least one fact before "
            "generating an investigation order."
        )

    investigations: list[str] = state.get("investigations", []) or []
    diagnoses: list = state.get("diagnoses_coded", []) or [{"text": d} for d in state.get("diagnoses", [])]
    follow_up: list = state.get("follow_up", []) or []

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

    def dx_text() -> str:
        if not diagnoses:
            return "Not recorded"
        values = []
        for dx in diagnoses:
            values.append(dx.get("text", dx) if isinstance(dx, dict) else dx)
        return ", ".join(_esc(value) for value in values)

    def followup_text() -> str:
        if not follow_up:
            return '<span class="muted">Not recorded</span>'
        return "<br>".join(_esc(item) for item in follow_up)

    urgency_note = ""
    if investigations:
        urgency_note = (
            '<div class="notice">'
            "Order contains doctor-reviewed investigations only. No tests are inferred by Lipi."
            "</div>"
        )

    reg_line = f'<div class="reg">Reg. No.: {mci_number}</div>' if mci_number else ""
    sig_reg = f"<br><span>{mci_number}</span>" if mci_number else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Investigation Order - {patient}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #f5f5f5;
      color: #1f2937;
      font-family: Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.45;
    }}
    .page {{ max-width: 760px; margin: 24px auto; background: #fff; border: 1px solid #d1d5db; }}
    .header {{
      display: flex;
      justify-content: space-between;
      gap: 20px;
      padding: 18px 22px;
      border-bottom: 2px solid #1d4ed8;
    }}
    .header h1 {{ margin: 0 0 4px; color: #1d4ed8; font-size: 19pt; }}
    .clinic {{ text-align: right; font-size: 10pt; color: #4b5563; }}
    .reg {{ font-size: 10pt; color: #4b5563; }}
    .body {{ padding: 18px 22px; }}
    .patient-bar {{
      display: grid;
      grid-template-columns: 1fr 120px 110px;
      gap: 12px;
      padding: 10px 12px;
      border: 1px solid #bfdbfe;
      background: #eff6ff;
      margin-bottom: 16px;
    }}
    .label {{ display: block; color: #6b7280; font-size: 9pt; text-transform: uppercase; }}
    .value {{ font-weight: 700; }}
    .meta-row {{ margin-bottom: 14px; color: #374151; }}
    .section-label {{ color: #1d4ed8; font-weight: 700; margin: 14px 0 6px; }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid #d1d5db; margin-bottom: 18px; }}
    thead th {{ background: #f3f4f6; color: #374151; text-align: left; padding: 8px; border-bottom: 1px solid #d1d5db; }}
    tbody td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; vertical-align: middle; }}
    .category {{ background: #f8fafc; color: #6b7280; font-size: 9pt; text-transform: uppercase; letter-spacing: .6px; font-weight: 700; }}
    .serial {{ width: 34px; color: #6b7280; }}
    .result {{ width: 160px; color: #9ca3af; font-size: 10pt; }}
    .panel {{ border: 1px solid #e5e7eb; padding: 10px 12px; min-height: 48px; }}
    .columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .notice {{ border: 1px solid #bfdbfe; background: #eff6ff; color: #1e40af; padding: 9px 12px; margin-bottom: 14px; }}
    .muted {{ color: #6b7280; }}
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
    .primary {{ background: #1d4ed8; color: #fff; border: 0; }}
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
        <h1>Investigation Order</h1>
        <div><strong>{doctor}</strong></div>
        {reg_line}
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
        <div><span class="label">Date</span><span class="value">{date_str}</span></div>
        <div><span class="label">Ref. No.</span><span class="value">{_esc(session_id[:8].upper())}</span></div>
      </div>
      <div class="meta-row"><span class="label">Clinical Diagnosis</span><strong>{dx_text()}</strong></div>
      {urgency_note}
      <div class="section-label">Investigations Ordered</div>
      <table>
        <thead>
          <tr><th>#</th><th>Investigation</th><th>Result (lab use)</th></tr>
        </thead>
        <tbody>
          {_category_rows(investigations)}
        </tbody>
      </table>
      <div class="columns">
        <div>
          <div class="section-label">Follow-up</div>
          <div class="panel">{followup_text()}</div>
        </div>
        <div>
          <div class="section-label">Special Instructions</div>
          <div class="panel muted">Bring reports on follow-up visit.</div>
        </div>
      </div>
    </div>
    <footer class="footer">
      <span>Generated by Lipi. Doctor-reviewed. {date_str}</span>
      <div class="sig-line">{doctor}{sig_reg}<br>Signature &amp; Stamp</div>
    </footer>
  </main>
  <div class="no-print">
    <button class="primary" onclick="window.print()">Print / Save as PDF</button>
    <button class="secondary" onclick="window.close()">Close</button>
  </div>
</body>
</html>"""

"""TPA (Third Party Administrator) claim packet generation.

Assembles session data into a structured insurance pre-auth / claim object.
Covers Star Health, HDFC Ergo, New India Assurance, United India formats
(all share the same core fields).
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.api.routes_auth import get_current_user
from app.services.icd10_map import annotate_diagnoses
from app.storage.db import db_connect

logger = logging.getLogger(__name__)
router = APIRouter()


def _jl(v):
    if not v:
        return []
    if isinstance(v, list):
        return v
    try:
        r = json.loads(v)
        return r if isinstance(r, list) else []
    except Exception:
        return []


def _jd(v):
    if not v:
        return {}
    if isinstance(v, dict):
        return v
    try:
        r = json.loads(v)
        return r if isinstance(r, dict) else {}
    except Exception:
        return {}


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.rstrip("Z")).strftime("%d %b %Y")
    except Exception:
        return iso or ""


def _med_name(m) -> str:
    if isinstance(m, str):
        return m
    if isinstance(m, dict):
        return m.get("name") or m.get("drug") or str(m)
    return str(m)


@router.get("/internal/tpa-claim/{session_id}")
async def get_tpa_claim(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Return structured TPA claim data for a session."""
    async with db_connect() as db:
        async with db.execute(
            """SELECT s.id, s.patient_name, s.patient_age, s.patient_sex,
                      s.patient_phone, s.clinical_facts, s.soap_note,
                      s.signed_at, s.created_at, s.user_id,
                      u.full_name, u.nmc_number, u.specialization,
                      dp.clinic_name, dp.clinic_address, dp.clinic_phone
               FROM sessions s
               LEFT JOIN users u ON u.id = CAST(s.user_id AS INTEGER)
               LEFT JOIN doctor_profiles dp ON dp.user_id = s.user_id
               WHERE s.id = ?""",
            (session_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    (sid, patient_name, patient_age, patient_sex, patient_phone,
     facts_raw, soap_raw, signed_at, created_at, user_id,
     doctor_full_name, nmc_number, specialization,
     clinic_name, clinic_address, clinic_phone) = row

    facts = _jd(facts_raw)
    soap = _jd(soap_raw)

    raw_diagnoses = facts.get("diagnoses") or facts.get("diagnosis") or []
    annotated_dx = annotate_diagnoses(raw_diagnoses)
    medications = [_med_name(m) for m in (facts.get("medications") or [])]
    vitals = facts.get("vitals") or []
    investigations = facts.get("investigations") or []

    # Pull assessment from SOAP if available
    assessment = ""
    for key in ("A", "assessment", "Assessment", "a"):
        val = soap.get(key)
        if val:
            assessment = val if isinstance(val, str) else json.dumps(val)
            break

    consultation_date = _fmt_date(signed_at or created_at)

    return {
        "session_id": sid,
        "generated_at": datetime.utcnow().isoformat(),
        "patient": {
            "name": patient_name or "",
            "age": patient_age or "",
            "sex": patient_sex or "",
            "phone": patient_phone or "",
        },
        "doctor": {
            "name": doctor_full_name or "",
            "nmc_number": nmc_number or "",
            "specialization": specialization or "",
            "clinic_name": clinic_name or "",
            "clinic_address": clinic_address or "",
            "clinic_phone": clinic_phone or "",
        },
        "consultation": {
            "date": consultation_date,
            "signed": bool(signed_at),
        },
        "clinical": {
            "diagnoses": annotated_dx,
            "primary_icd10": annotated_dx[0]["icd10"] if annotated_dx else None,
            "primary_diagnosis": annotated_dx[0]["name"] if annotated_dx else "",
            "assessment": assessment,
            "medications": medications,
            "vitals": vitals,
            "investigations": investigations,
        },
    }


@router.get("/internal/tpa-claim/{session_id}/print", response_class=HTMLResponse)
async def get_tpa_claim_print(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> HTMLResponse:
    """Printable HTML version of the TPA claim packet."""
    data = await get_tpa_claim(session_id, current_user)

    p = data["patient"]
    doc = data["doctor"]
    cons = data["consultation"]
    clin = data["clinical"]

    dx_rows = "".join(
        f'<tr><td>{dx["name"]}</td><td class="mono">{dx["icd10"] or "—"}</td></tr>'
        for dx in clin["diagnoses"]
    )
    med_rows = "".join(f"<li>{m}</li>" for m in clin["medications"])
    inv_rows = "".join(f"<li>{inv}</li>" for inv in clin["investigations"])
    vital_rows = "".join(f"<li>{v}</li>" for v in clin["vitals"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TPA Claim — {p["name"]}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 13px; color: #111; padding: 32px; max-width: 800px; margin: 0 auto; }}
  h1 {{ font-size: 18px; font-weight: bold; margin-bottom: 4px; }}
  h2 {{ font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: .05em; color: #555; margin-bottom: 8px; margin-top: 20px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; border-bottom: 2px solid #1d4ed8; padding-bottom: 16px; }}
  .badge {{ background: #dbeafe; color: #1d4ed8; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: .05em; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  .field {{ margin-bottom: 8px; }}
  .label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: #888; margin-bottom: 2px; }}
  .value {{ font-size: 13px; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th {{ text-align: left; font-size: 11px; color: #555; text-transform: uppercase; padding: 4px 8px; background: #f8fafc; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #f1f5f9; }}
  .mono {{ font-family: monospace; font-size: 12px; color: #1d4ed8; font-weight: bold; }}
  ul {{ padding-left: 16px; margin-top: 6px; line-height: 1.9; }}
  .section {{ margin-top: 20px; }}
  .watermark {{ margin-top: 40px; text-align: center; font-size: 10px; color: #bbb; }}
  .signed {{ color: #16a34a; font-weight: bold; }}
  .unsigned {{ color: #dc2626; font-weight: bold; }}
  @media print {{
    body {{ padding: 16px; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>TPA Claim Packet</h1>
    <p style="color:#555;margin-top:4px;">Prepared by Lipi Clinical AI · {cons["date"]}</p>
  </div>
  <div style="text-align:right">
    <div class="badge">PRE-AUTH / CASHLESS</div>
    <p style="margin-top:6px;font-size:11px;color:#888;">Session: {session_id[:8].upper()}</p>
    <p style="font-size:11px;{'class=\"signed\"' if cons['signed'] else 'class=\"unsigned\"'}">
      {'✓ Doctor Signed' if cons['signed'] else '⚠ Awaiting Signature'}
    </p>
  </div>
</div>

<div class="grid">
  <div>
    <h2>Patient Details</h2>
    <div class="field"><div class="label">Name</div><div class="value">{p["name"] or "—"}</div></div>
    <div class="field"><div class="label">Age / Sex</div><div class="value">{p["age"] or "—"} / {p["sex"] or "—"}</div></div>
    <div class="field"><div class="label">Contact</div><div class="value">{p["phone"] or "—"}</div></div>
    <div class="field"><div class="label">Date of Consultation</div><div class="value">{cons["date"]}</div></div>
  </div>
  <div>
    <h2>Treating Doctor</h2>
    <div class="field"><div class="label">Name</div><div class="value">{doc["name"] or "—"}</div></div>
    <div class="field"><div class="label">NMC Reg. No.</div><div class="value">{doc["nmc_number"] or "—"}</div></div>
    <div class="field"><div class="label">Specialization</div><div class="value">{doc["specialization"] or "—"}</div></div>
    <div class="field"><div class="label">Clinic</div><div class="value">{doc["clinic_name"] or "—"}</div></div>
    <div class="field"><div class="label">Address</div><div class="value" style="font-size:12px">{doc["clinic_address"] or "—"}</div></div>
  </div>
</div>

<div class="section">
  <h2>Diagnosis (ICD-10)</h2>
  {"<p style='color:#888;font-style:italic'>No diagnoses extracted</p>" if not clin["diagnoses"] else f'''
  <table>
    <tr><th>Diagnosis</th><th>ICD-10 Code</th></tr>
    {dx_rows}
  </table>'''}
</div>

{"" if not clin["assessment"] else f'''
<div class="section">
  <h2>Clinical Assessment</h2>
  <p style="line-height:1.6;margin-top:6px">{clin["assessment"]}</p>
</div>'''}

<div class="grid" style="margin-top:20px">
  {"" if not clin["medications"] else f'''
  <div>
    <h2>Medications Prescribed</h2>
    <ul>{med_rows}</ul>
  </div>'''}
  {"" if not clin["vitals"] else f'''
  <div>
    <h2>Vitals Recorded</h2>
    <ul>{vital_rows}</ul>
  </div>'''}
</div>

{"" if not clin["investigations"] else f'''
<div class="section">
  <h2>Investigations Advised</h2>
  <ul>{inv_rows}</ul>
</div>'''}

<div class="section" style="margin-top:32px;border-top:1px solid #ddd;padding-top:16px">
  <div class="grid">
    <div>
      <p class="label">Doctor Signature</p>
      <div style="height:48px;border-bottom:1px solid #aaa;margin-top:8px;width:200px"></div>
      <p style="font-size:11px;color:#888;margin-top:4px">{doc["name"]} · {doc["nmc_number"] or "NMC No."}</p>
    </div>
    <div>
      <p class="label">Hospital / Clinic Stamp</p>
      <div style="height:48px;border:1px dashed #ccc;margin-top:8px;width:160px;border-radius:4px"></div>
    </div>
  </div>
</div>

<div class="watermark">
  Generated by Lipi Clinical AI · For insurance / TPA use only · Not a standalone medical certificate
</div>

<div class="no-print" style="margin-top:32px;text-align:center">
  <button onclick="window.print()" style="padding:10px 28px;background:#1d4ed8;color:white;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">
    Print / Save as PDF
  </button>
</div>
</body>
</html>"""

    return HTMLResponse(content=html)

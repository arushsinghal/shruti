"""Analytics API routes for aggregated clinical dashboard statistics."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel, Field

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect
from app.storage.repository import SessionRepository
from app.services.whatsapp_service import WhatsAppService
from app.utils.config import settings

router = APIRouter()
repo = SessionRepository()


class UsageEventRequest(BaseModel):
    event_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BillingRecordRequest(BaseModel):
    clinic_name: str
    plan_name: str
    amount_inr: int
    status: str


class FollowUpReminderRequest(BaseModel):
    phone_number: str
    consent: bool = False
    follow_up_text: str
    scheduled_for: Optional[str] = None


class ShareWhatsAppRequest(BaseModel):
    phone_number: str
    consent: bool = False


def get_val(row, key, index, default=0):
    if not row:
        return default
    try:
        if isinstance(row, dict) or hasattr(row, "keys"):
            val = row[key]
        else:
            val = row[index]
        return val if val is not None else default
    except Exception:
        return default


@router.post("/sessions/{session_id}/usage-event", status_code=201)
async def record_usage_event(
    session_id: str,
    body: UsageEventRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO usage_events (session_id, user_id, event_type, metadata_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, body.event_type, json.dumps(body.metadata), now),
        )
        await db.commit()
    return {"success": True, "event_type": body.event_type}


@router.post("/billing-records", status_code=201)
async def create_billing_record(
    body: BillingRecordRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    user_id = str(current_user["id"])
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO billing_records (user_id, clinic_name, plan_name, amount_inr, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, body.clinic_name, body.plan_name, body.amount_inr, body.status, now),
        )
        await db.commit()
    return {"id": cursor.lastrowid or 0, **body.model_dump(), "created_at": now}


@router.post("/sessions/{session_id}/share-whatsapp")
async def share_prescription_whatsapp(
    session_id: str,
    body: ShareWhatsAppRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not body.consent:
        raise HTTPException(status_code=400, detail="Patient consent is required before sharing prescription.")

    user_id = str(current_user["id"])
    # Actor-aware: a clinic assistant may share the doctor's prescription.
    session = await repo.get_session_for_actor(session_id, current_user)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status.value != "complete":
        raise HTTPException(status_code=400, detail="Prescription can be shared only after the note is complete.")

    # The prescription belongs to the doctor who owns the session, not the
    # assistant who triggers the share.
    doctor_user_id = session.user_id or user_id
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": session_id,
        "session_id": session_id,
        "doctor_user_id": doctor_user_id,
        "scope": "patient_prescription_share",
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    secure_link = f"/patient-download/{token}"
    doctor_name = session.doctor_name or current_user.get("full_name") or current_user.get("username") or "Doctor"
    result = await WhatsAppService.send_message(body.phone_number, doctor_name, secure_link)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("detail") or result.get("error") or "WhatsApp provider failed")

    await repo.log_audit(session_id, user_id, "prescription_shared", "whatsapp")
    return {"success": True, "token": token, "link": secure_link, "provider": result.get("provider")}


@router.post("/sessions/{session_id}/send-follow-up")
async def send_follow_up_reminder(
    session_id: str,
    body: FollowUpReminderRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not body.consent:
        raise HTTPException(status_code=400, detail="Patient consent is required before sending follow-up reminders.")

    user_id = str(current_user["id"])
    session = await repo.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    doctor_name = session.doctor_name or current_user.get("full_name") or current_user.get("username") or "Doctor"
    result = await WhatsAppService.send_follow_up_reminder(body.phone_number, doctor_name, body.follow_up_text)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("detail") or result.get("error") or "Follow-up failed")

    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO usage_events (session_id, user_id, event_type, metadata_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                "follow_up_reminder_sent",
                json.dumps({"scheduled_for": body.scheduled_for}),
                now,
            ),
        )
        await db.commit()
    return {**result, "status": "scheduled" if body.scheduled_for else "sent"}


class AvailabilitySlot(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 15


@router.get("/doctor/availability")
async def get_availability(current_user: dict = Depends(get_current_user)) -> dict:
    from app.services.appointment_booking import get_doctor_availability
    user_id = str(current_user["id"])
    slots = await get_doctor_availability(user_id)
    return {"slots": slots}


@router.put("/doctor/availability")
async def save_availability(
    slots: list[AvailabilitySlot],
    current_user: dict = Depends(get_current_user),
) -> dict:
    from app.services.appointment_booking import save_doctor_availability
    user_id = str(current_user["id"])
    await save_doctor_availability(user_id, [s.model_dump() for s in slots])
    return {"success": True, "count": len(slots)}


@router.get("/doctor/appointments")
async def get_appointments(current_user: dict = Depends(get_current_user)) -> dict:
    user_id = str(current_user["id"])
    async with db_connect() as db:
        async with db.execute(
            "SELECT id, patient_name, patient_phone, slot_datetime, chief_complaint, status FROM appointments WHERE clinic_user_id=? ORDER BY slot_datetime DESC LIMIT 50",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()

        appt_ids = [r[0] for r in rows]
        pre_visit_by_appt: dict[str, dict] = {}
        if appt_ids:
            placeholders = ",".join("?" for _ in appt_ids)
            async with db.execute(
                f"SELECT appointment_id, chief_complaint, current_medications, allergies, additional_notes, submitted_at "
                f"FROM pre_visit_forms WHERE appointment_id IN ({placeholders}) ORDER BY submitted_at DESC",
                tuple(appt_ids),
            ) as cur:
                for pr in await cur.fetchall():
                    # Keep only the most recent submission per appointment.
                    pre_visit_by_appt.setdefault(pr[0], {
                        "chief_complaint": pr[1], "current_medications": pr[2],
                        "allergies": pr[3], "additional_notes": pr[4], "submitted_at": pr[5],
                    })

    return {"appointments": [
        {
            "id": r[0], "patient_name": r[1], "patient_phone": r[2], "slot_datetime": r[3],
            "chief_complaint": r[4], "status": r[5], "pre_visit_form": pre_visit_by_appt.get(r[0]),
        }
        for r in rows
    ]}


@router.get("/doctor/practice-insights")
async def get_practice_insights(current_user: dict = Depends(get_current_user)) -> dict:
    """A doctor's own prescribing/treatment patterns, current 30 days vs the
    prior 30 days. All statistics are computed deterministically here; Gemini
    (see llm_client.narrate_practice_insight) only narrates these numbers in
    plain language and is explicitly barred from judging or grading them —
    this is a reflection tool, not an evaluation of the doctor's medicine.
    """
    user_id = str(current_user["id"])
    now = datetime.utcnow()
    current_start = (now - timedelta(days=30)).isoformat()
    prior_start = (now - timedelta(days=60)).isoformat()

    async def _count_and_facts(start: str, end: Optional[str]) -> tuple[int, list]:
        query = "SELECT clinical_facts FROM sessions WHERE user_id=? AND created_at>=?"
        params: list = [user_id, start]
        if end:
            query += " AND created_at<?"
            params.append(end)
        async with db_connect() as db:
            async with db.execute(query, tuple(params)) as cur:
                rows = await cur.fetchall()
        facts_list = []
        for row in rows:
            try:
                facts_list.append(json.loads(row[0]) if row[0] else {})
            except Exception:
                facts_list.append({})
        return len(rows), facts_list

    current_count, current_facts = await _count_and_facts(current_start, None)
    prior_count, _ = await _count_and_facts(prior_start, current_start)

    dx_counts: dict[str, int] = {}
    med_counts: dict[str, int] = {}
    for facts in current_facts:
        if not isinstance(facts, dict):
            continue
        for dx in (facts.get("diagnoses") or []):
            if isinstance(dx, str):
                dx_counts[dx] = dx_counts.get(dx, 0) + 1
        for med in (facts.get("medications") or []):
            name = med.get("name") if isinstance(med, dict) else (med if isinstance(med, str) else None)
            if name:
                med_counts[name] = med_counts.get(name, 0) + 1

    top_diagnoses = sorted(dx_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_medications = sorted(med_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    stats = {
        "consultations_current_period": current_count,
        "consultations_prior_period": prior_count,
        "top_diagnoses": [{"name": n, "count": c} for n, c in top_diagnoses],
        "top_medications": [{"name": n, "count": c} for n, c in top_medications],
    }

    from app.services.llm_client import LLMClientService
    narrative = LLMClientService().narrate_practice_insight(stats)

    return {"stats": stats, "narrative": narrative}


@router.get("/analytics/revenue-summary")
async def get_revenue_summary(current_user: dict = Depends(get_current_user)) -> dict:
    """Revenue streams summary for the current calendar month."""
    user_id = str(current_user["id"])
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    dhis_count = dsc_amount = clinic_amount = 0
    lab_dispatches = follow_ups_confirmed = follow_ups_sent = 0
    try:
        async with db_connect() as db:
            async with db.execute(
                "SELECT COUNT(*), COALESCE(SUM(dsc_amount),0), COALESCE(SUM(clinic_amount),0) FROM dhis_transactions WHERE user_id=? AND created_at>=?",
                (user_id, month_start),
            ) as cur:
                row = await cur.fetchone()
            dhis_count = int(row[0]) if row else 0
            dsc_amount = float(row[1]) if row else 0.0
            clinic_amount = float(row[2]) if row else 0.0

            async with db.execute(
                "SELECT COUNT(*) FROM lab_dispatch_log WHERE user_id=? AND dispatched_at>=? AND status='sent'",
                (user_id, month_start),
            ) as cur:
                row = await cur.fetchone()
            lab_dispatches = int(row[0]) if row else 0

            async with db.execute(
                "SELECT COUNT(*) FROM follow_up_reminders WHERE user_id=? AND status='confirmed' AND created_at>=?",
                (user_id, month_start),
            ) as cur:
                row = await cur.fetchone()
            follow_ups_confirmed = int(row[0]) if row else 0

            async with db.execute(
                "SELECT COUNT(*) FROM follow_up_reminders WHERE user_id=? AND status IN ('sent','pending') AND created_at>=?",
                (user_id, thirty_days_ago),
            ) as cur:
                row = await cur.fetchone()
            follow_ups_sent = int(row[0]) if row else 0
    except Exception:
        pass

    return {
        "month": now.strftime("%Y-%m"),
        "dhis_transactions": dhis_count,
        "dhis_clinic_amount": clinic_amount,
        "dhis_dsc_amount": dsc_amount,
        "lab_dispatches_sent": lab_dispatches,
        "follow_ups_confirmed": follow_ups_confirmed,
        "follow_ups_sent": follow_ups_sent,
    }


@router.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Retrieves aggregated telemetry and documentation insights from deployment sessions. Research prototype only — output requires physician review."""
    
    async with db_connect() as db:
        db.row_factory = None
        
        # 1. Total consultations
        async with db.execute("SELECT COUNT(*) AS total FROM sessions") as cur:
            row = await cur.fetchone()
            total_sessions = get_val(row, "total", 0)
        
        # 2. Sessions this week
        one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        async with db.execute(
            "SELECT COUNT(*) AS cnt FROM sessions WHERE created_at >= ?", (one_week_ago,)
        ) as cur:
            row = await cur.fetchone()
            sessions_this_week = get_val(row, "cnt", 0)
        
        # 3. Sessions completed (with SOAP notes)
        async with db.execute(
            "SELECT COUNT(*) AS cnt FROM sessions WHERE status = 'complete'"
        ) as cur:
            row = await cur.fetchone()
            completed_sessions = get_val(row, "cnt", 0)
        
        # 4. Cloud AI vs Deterministic split
        async with db.execute(
            "SELECT SUM(cloud_ai_consent) AS cloud, COUNT(*) - SUM(cloud_ai_consent) AS edge FROM sessions"
        ) as cur:
            row = await cur.fetchone()
            cloud_count = int(get_val(row, "cloud", 0, 0))
            edge_count = int(get_val(row, "edge", 1, 0))
            if edge_count < 0:
                edge_count = 0
        
        # 5. Consent logs recorded
        async with db.execute("SELECT COUNT(*) AS cnt FROM consent_logs") as cur:
            row = await cur.fetchone()
            consent_logs_recorded = get_val(row, "cnt", 0)

        async with db.execute(
            "SELECT COUNT(*) AS cnt FROM usage_events WHERE event_type = 'note_printed'"
        ) as cur:
            row = await cur.fetchone()
            notes_printed = get_val(row, "cnt", 0)

        async with db.execute(
            "SELECT COUNT(*) AS cnt FROM usage_events WHERE event_type = 'follow_up_reminder_sent'"
        ) as cur:
            row = await cur.fetchone()
            follow_up_reminders_sent = get_val(row, "cnt", 0)

        async with db.execute(
            "SELECT COALESCE(SUM(amount_inr), 0) AS total FROM billing_records"
        ) as cur:
            row = await cur.fetchone()
            revenue_total_inr = get_val(row, "total", 0)

        # 6. SOAP Feedback Tallies (Accept/Edit/Reject) & Categories Tally
        accepted_notes = 0
        edited_notes = 0
        rejected_notes = 0
        category_counts = {}

        async with db.execute("SELECT status, categories FROM soap_feedback") as cur:
            async for row in cur:
                # Driver-safe column lookup
                if isinstance(row, dict) or hasattr(row, "keys"):
                    status = row["status"]
                    categories_str = row["categories"]
                else:
                    status = row[0]
                    categories_str = row[1]

                if status == 'accept':
                    accepted_notes += 1
                elif status == 'edit':
                    edited_notes += 1
                elif status == 'reject':
                    rejected_notes += 1
                
                if categories_str:
                    try:
                        cats = json.loads(categories_str)
                        if isinstance(cats, list):
                            for cat in cats:
                                category_counts[cat] = category_counts.get(cat, 0) + 1
                    except Exception:
                        pass
        
        total_feedback = accepted_notes + edited_notes + rejected_notes
        if total_feedback > 0:
            acceptance_rate = round(accepted_notes / total_feedback, 4)
            edit_rate = round(edited_notes / total_feedback, 4)
        else:
            acceptance_rate = 0.0
            edit_rate = 0.0

        top_correction_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

        # 7. Estimated hours saved: 12 minutes (0.2 hours) per completed session
        estimated_hours_saved = round(completed_sessions * 0.2, 2)
        
        # 8. Aggregate top symptoms, vitals, medications, allergies across all clinical_facts
        symptom_counts: dict[str, int] = {}
        medication_counts: dict[str, int] = {}
        allergy_counts: dict[str, int] = {}
        vital_counts: dict[str, int] = {}

        async with db.execute("SELECT clinical_facts FROM sessions WHERE clinical_facts IS NOT NULL") as cur:
            async for row in cur:
                facts_json = row[0] if not (isinstance(row, dict) or hasattr(row, "keys")) else row["clinical_facts"]
                try:
                    facts = json.loads(facts_json)
                    for s in (facts.get("symptoms") or []):
                        if isinstance(s, str):
                            symptom_counts[s] = symptom_counts.get(s, 0) + 1
                    for m in (facts.get("medications") or []):
                        name = m.get("name") if isinstance(m, dict) else None
                        if name:
                            medication_counts[name] = medication_counts.get(name, 0) + 1
                    for a in (facts.get("allergies") or []):
                        if isinstance(a, str):
                            allergy_counts[a] = allergy_counts.get(a, 0) + 1
                    for v in (facts.get("vitals") or []):
                        if isinstance(v, str):
                            vital_counts[v] = vital_counts.get(v, 0) + 1
                except Exception:
                    pass

        top_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        top_medications = sorted(medication_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        top_allergies = sorted(allergy_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 9. Sessions per day (last 7 days)
        sessions_by_day = []
        for day_offset in range(6, -1, -1):
            day = datetime.utcnow() - timedelta(days=day_offset)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            day_end = day.replace(hour=23, minute=59, second=59).isoformat()
            async with db.execute(
                "SELECT COUNT(*) AS cnt FROM sessions WHERE created_at >= ? AND created_at <= ?",
                (day_start, day_end)
            ) as cur:
                row = await cur.fetchone()
                cnt = get_val(row, "cnt", 0)
            sessions_by_day.append({
                "date": day.strftime("%a"),
                "consultations": cnt
            })

        specialty_mix = []
        async with db.execute(
            "SELECT specialty, COUNT(*) AS cnt FROM sessions WHERE specialty IS NOT NULL AND specialty != '' GROUP BY specialty ORDER BY cnt DESC"
        ) as cur:
            rows = await cur.fetchall()
        for row in rows:
            specialty_mix.append({"name": row[0], "count": row[1]})

        # 10. Patient cohort: age/sex distribution and repeat-visit rate.
        # Grouped by phone directly (not patient_id) so this reflects full
        # history even for patients whose sessions predate the patients table.
        age_buckets = {"0-17": 0, "18-34": 0, "35-49": 0, "50-64": 0, "65+": 0, "unknown": 0}
        sex_counts: dict[str, int] = {}
        async with db.execute(
            "SELECT patient_age, patient_sex FROM sessions WHERE patient_phone IS NOT NULL AND patient_phone != ''"
        ) as cur:
            async for row in cur:
                age_raw, sex_raw = row[0], row[1]
                try:
                    age_val = int(str(age_raw).strip()) if age_raw else None
                except ValueError:
                    age_val = None
                if age_val is None:
                    age_buckets["unknown"] += 1
                elif age_val < 18:
                    age_buckets["0-17"] += 1
                elif age_val < 35:
                    age_buckets["18-34"] += 1
                elif age_val < 50:
                    age_buckets["35-49"] += 1
                elif age_val < 65:
                    age_buckets["50-64"] += 1
                else:
                    age_buckets["65+"] += 1
                sex_key = (sex_raw or "unknown").strip().upper() or "unknown"
                sex_counts[sex_key] = sex_counts.get(sex_key, 0) + 1

        repeat_visit_rate = 0.0
        total_unique_patients = 0
        async with db.execute(
            "SELECT patient_phone, COUNT(*) AS visit_count FROM sessions "
            "WHERE patient_phone IS NOT NULL AND patient_phone != '' GROUP BY patient_phone"
        ) as cur:
            phone_rows = await cur.fetchall()
        total_unique_patients = len(phone_rows)
        repeat_patients = sum(1 for r in phone_rows if r[1] > 1)
        if total_unique_patients > 0:
            repeat_visit_rate = round(repeat_patients / total_unique_patients, 4)

        patient_cohort = {
            "age_distribution": [{"bucket": k, "count": v} for k, v in age_buckets.items() if v > 0],
            "sex_distribution": [{"sex": k, "count": v} for k, v in sex_counts.items()],
            "total_unique_patients": total_unique_patients,
            "repeat_patients": repeat_patients,
            "repeat_visit_rate": repeat_visit_rate,
        }

        return {
        "overview": {
            "total_sessions": total_sessions,
            "sessions_this_week": sessions_this_week,
            "completed_sessions": completed_sessions,
            "cloud_ai_sessions": cloud_count,
            "edge_sessions": edge_count,
            "accepted_notes": accepted_notes,
            "edited_notes": edited_notes,
            "rejected_notes": rejected_notes,
            "acceptance_rate": acceptance_rate,
                "edit_rate": edit_rate,
                "estimated_hours_saved": estimated_hours_saved,
                "consent_logs_recorded": consent_logs_recorded,
                "notes_printed": notes_printed,
                "follow_up_reminders_sent": follow_up_reminders_sent,
                "revenue_total_inr": revenue_total_inr,
            },
        "top_symptoms": [{"name": name, "count": count} for name, count in top_symptoms],
        "top_medications": [{"name": name, "count": count} for name, count in top_medications],
            "top_allergies": [{"name": name, "count": count} for name, count in top_allergies],
            "sessions_by_day": sessions_by_day,
            "specialty_mix": specialty_mix,
            "top_correction_categories": [{"name": name, "count": count} for name, count in top_correction_categories],
            "patient_cohort": patient_cohort,
        }


# ---------------------------------------------------------------------------
# Internal: per-consultation billing invoice view
# ---------------------------------------------------------------------------

@router.get("/internal/billing/summary")
async def get_billing_summary(
    month: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Returns per-consultation billing records for invoice generation.
    month: YYYY-MM format (defaults to current month).
    Returns rows grouped by doctor with line-item detail.
    """
    import calendar
    from datetime import date, datetime

    if month:
        try:
            year, mon = int(month[:4]), int(month[5:7])
        except (ValueError, IndexError):
            year, mon = date.today().year, date.today().month
    else:
        year, mon = date.today().year, date.today().month

    last_day = calendar.monthrange(year, mon)[1]
    # consultation_billing.created_at is a real timestamptz column — asyncpg requires
    # actual datetime objects for comparisons, not ISO strings (unlike sessions.created_at,
    # which is TEXT and compares fine against strings).
    month_start = datetime(year, mon, 1)
    month_end = datetime(year, mon, last_day, 23, 59, 59)
    month_label = f"{date(year, mon, 1).strftime('%B %Y')}"

    user_id = str(current_user["id"])
    role = current_user.get("role", "doctor")

    rows = []
    total_inr = 0

    try:
        async with db_connect() as db:
            # Admins/internal users see all; doctors see only their own
            if role in ("admin", "internal"):
                async with db.execute(
                    """SELECT br.id, br.session_id, br.user_id, br.amount, br.currency,
                              br.notes, br.created_at,
                              s.patient_name, s.doctor_name, s.signed_at
                       FROM consultation_billing br
                       LEFT JOIN sessions s ON s.id = br.session_id
                       WHERE br.created_at >= ? AND br.created_at <= ?
                       ORDER BY br.created_at DESC""",
                    (month_start, month_end),
                ) as cur:
                    db_rows = await cur.fetchall()
            else:
                async with db.execute(
                    """SELECT br.id, br.session_id, br.user_id, br.amount, br.currency,
                              br.notes, br.created_at,
                              s.patient_name, s.doctor_name, s.signed_at
                       FROM consultation_billing br
                       LEFT JOIN sessions s ON s.id = br.session_id
                       WHERE br.user_id = ? AND br.created_at >= ? AND br.created_at <= ?
                       ORDER BY br.created_at DESC""",
                    (user_id, month_start, month_end),
                ) as cur:
                    db_rows = await cur.fetchall()

        for r in db_rows:
            amount = r[3] or 0
            total_inr += amount
            rows.append({
                "id": r[0],
                "session_id": r[1],
                "user_id": r[2],
                "amount_inr": amount,
                "currency": r[4] or "INR",
                "notes": r[5] or "WhatsApp consultation",
                "date": str(r[6])[:10] if r[6] else "",
                "patient_name": (r[7] or "—")[:20] + ("..." if len(r[7] or "") > 20 else ""),
                "doctor_name": r[8] or "—",
                "signed": bool(r[9]),
            })
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Billing summary query failed: %s", exc)

    return {
        "month": month_label,
        "month_key": f"{year:04d}-{mon:02d}",
        "total_inr": total_inr,
        "consultation_count": len(rows),
        "rows": rows,
    }

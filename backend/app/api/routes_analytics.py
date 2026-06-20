"""Analytics API routes for aggregated clinical dashboard statistics."""

import json
from datetime import datetime, timedelta

from fastapi import APIRouter
from app.storage.db import db_connect

router = APIRouter()


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
        },
        "top_symptoms": [{"name": name, "count": count} for name, count in top_symptoms],
        "top_medications": [{"name": name, "count": count} for name, count in top_medications],
        "top_allergies": [{"name": name, "count": count} for name, count in top_allergies],
        "sessions_by_day": sessions_by_day,
        "top_correction_categories": [{"name": name, "count": count} for name, count in top_correction_categories],
    }


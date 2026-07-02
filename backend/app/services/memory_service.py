"""
Patient memory service — persists extracted clinical facts across visits.

All values stored here are extractive spans from the clinical pipeline (Layer 1 +
GLiNER). No generative model involved. Data stays in the local Postgres/SQLite DB.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.storage.db import db_connect

logger = logging.getLogger(__name__)

_FIELDS = {"medications", "diagnoses", "allergies", "investigations", "symptoms"}


def _normalize_name(name: str) -> str:
    import re
    n = name.strip().lower()
    n = re.sub(r'\s+', ' ', n)
    for prefix in ('mr.', 'mr ', 'mrs.', 'mrs ', 'ms.', 'ms ', 'shri ', 'smt.', 'smt ', 'dr.', 'dr ', 'baby ', 'master '):
        if n.startswith(prefix):
            n = n[len(prefix):].strip()
            break
    return n


def _med_key(med: dict) -> str:
    return med.get("name", "").strip().lower()


async def upsert_patient_memory(
    patient_name: str,
    session_id: str,
    user_id: str,
    facts: dict,
    clinic_id: str | None = None,
    fact_provenance: list[dict] | None = None,
    confirmed_by: str | None = None,
) -> None:
    """Write doctor-confirmed facts from one session into the patient memory store.

    fact_provenance: list of ExtractedFact dicts (task 24). When provided, each
    written row carries fact_id, review_status, confirmed_by, confirmed_at.
    Only confirmed facts should be passed here — call this AFTER finalization.
    """
    if not patient_name or not user_id:
        return

    key = _normalize_name(patient_name)
    owner_id = str(user_id)
    now = datetime.now(timezone.utc).isoformat()

    # Build a quick lookup: category+normalized_value → fact metadata
    prov_lookup: dict[str, dict] = {}
    if fact_provenance:
        for fp in fact_provenance:
            if fp.get("review_status") == "confirmed":
                cat = fp.get("category", "")
                nv = fp.get("normalized_value", "").lower()
                prov_lookup[f"{cat}:{nv}"] = fp

    def _prov(category: str, value_key: str) -> tuple[str | None, str, str | None, str | None]:
        """Returns (fact_id, review_status, confirmed_by, confirmed_at)."""
        fp = prov_lookup.get(f"{category}:{value_key.lower()}")
        if fp:
            return (
                fp.get("id"),
                fp.get("review_status", "confirmed"),
                fp.get("confirmed_by") or confirmed_by,
                fp.get("metadata", {}).get("confirmed_at") or (now if fp.get("review_status") == "confirmed" else None),
            )
        return None, "confirmed", confirmed_by, now if confirmed_by else None

    async with db_connect() as db:
        # medications — stored as JSON objects {name, dosage, frequency}
        for med in facts.get("medications") or []:
            med_name = _med_key(med)
            if not med_name:
                continue
            value_json = json.dumps(med)
            fact_id, rev_status, conf_by, conf_at = _prov("medication", med_name)
            existing = await _fetch_one(
                db,
                "SELECT id, seen_count, value FROM patient_memory WHERE patient_name=? AND user_id=? AND field=? AND med_name=? AND superseded=0",
                (key, owner_id, "medication", med_name),
            )
            if existing:
                old_value = existing[2] or ""
                # Task 25: supersede old entry if dosage/value changed
                supersede = old_value != value_json
                if supersede:
                    await db.execute(
                        "UPDATE patient_memory SET superseded=1 WHERE id=? AND user_id=?",
                        (existing[0], owner_id),
                    )
                    await db.execute(
                        "INSERT INTO patient_memory (patient_name, user_id, clinic_id, field, med_name, value, source_session_id, first_seen_at, last_seen_at, seen_count, fact_id, review_status, confirmed_by, confirmed_at) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?,?)",
                        (key, owner_id, clinic_id, "medication", med_name, value_json, session_id, now, now, fact_id, rev_status, conf_by, conf_at),
                    )
                else:
                    await db.execute(
                        "UPDATE patient_memory SET value=?, last_seen_at=?, seen_count=seen_count+1, source_session_id=?, clinic_id=?, fact_id=?, review_status=?, confirmed_by=?, confirmed_at=? WHERE id=? AND user_id=?",
                        (value_json, now, session_id, clinic_id, fact_id, rev_status, conf_by, conf_at, existing[0], owner_id),
                    )
            else:
                await db.execute(
                    "INSERT INTO patient_memory (patient_name, user_id, clinic_id, field, med_name, value, source_session_id, first_seen_at, last_seen_at, seen_count, fact_id, review_status, confirmed_by, confirmed_at) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?,?)",
                    (key, owner_id, clinic_id, "medication", med_name, value_json, session_id, now, now, fact_id, rev_status, conf_by, conf_at),
                )

        # scalar list fields — diagnoses, allergies, investigations, symptoms
        for field in ("diagnoses", "allergies", "investigations", "symptoms"):
            for item in facts.get(field) or []:
                item_str = str(item).strip()
                if not item_str:
                    continue
                item_key = item_str.lower()
                fact_id, rev_status, conf_by, conf_at = _prov(field.rstrip("s"), item_key)
                existing = await _fetch_one(
                    db,
                    "SELECT id FROM patient_memory WHERE patient_name=? AND user_id=? AND field=? AND med_name=? AND superseded=0",
                    (key, owner_id, field, item_key),
                )
                if existing:
                    await db.execute(
                        "UPDATE patient_memory SET last_seen_at=?, seen_count=seen_count+1, source_session_id=?, clinic_id=?, fact_id=?, review_status=?, confirmed_by=?, confirmed_at=? WHERE id=? AND user_id=?",
                        (now, session_id, clinic_id, fact_id, rev_status, conf_by, conf_at, existing[0], owner_id),
                    )
                else:
                    await db.execute(
                        "INSERT INTO patient_memory (patient_name, user_id, clinic_id, field, med_name, value, source_session_id, first_seen_at, last_seen_at, seen_count, fact_id, review_status, confirmed_by, confirmed_at) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?,?)",
                        (key, owner_id, clinic_id, field, item_key, item_str, session_id, now, now, fact_id, rev_status, conf_by, conf_at),
                    )

        # vitals — store most recent reading per vital type
        for vital in facts.get("vitals") or []:
            vital_str = str(vital).strip()
            if not vital_str:
                continue
            vital_type = vital_str.split()[0].lower()
            fact_id, rev_status, conf_by, conf_at = _prov("vital", vital_type)
            existing = await _fetch_one(
                db,
                "SELECT id FROM patient_memory WHERE patient_name=? AND user_id=? AND field=? AND med_name=? AND superseded=0",
                (key, owner_id, "vital", vital_type),
            )
            if existing:
                await db.execute(
                    "UPDATE patient_memory SET value=?, last_seen_at=?, seen_count=seen_count+1, source_session_id=?, clinic_id=?, fact_id=?, review_status=?, confirmed_by=?, confirmed_at=? WHERE id=? AND user_id=?",
                    (vital_str, now, session_id, clinic_id, fact_id, rev_status, conf_by, conf_at, existing[0], owner_id),
                )
            else:
                await db.execute(
                    "INSERT INTO patient_memory (patient_name, user_id, clinic_id, field, med_name, value, source_session_id, first_seen_at, last_seen_at, seen_count, fact_id, review_status, confirmed_by, confirmed_at) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?,?)",
                    (key, owner_id, clinic_id, "vital", vital_type, vital_str, session_id, now, now, fact_id, rev_status, conf_by, conf_at),
                )

        await db.commit()
    logger.info("Patient memory updated: patient=%r user=%s session=%s", key, owner_id, session_id)


async def get_patient_memory(
    patient_name: str,
    user_id: str,
    confirmed_only: bool = True,
) -> Optional[dict]:
    """Return accumulated memory for a patient, grouped by field.

    confirmed_only (task 26): when True, only rows where review_status = 'confirmed'
    (or NULL for rows written before task 24) and superseded = 0 are returned.
    This prevents prior-session candidate facts (never doctor-confirmed) from
    contaminating the current consultation's prior-history panel.
    """
    if not patient_name or not user_id:
        return None

    key = _normalize_name(patient_name)
    owner_id = str(user_id)
    rows = []
    async with db_connect() as db:
        if confirmed_only:
            rows = await _fetch_all(
                db,
                "SELECT field, value, last_seen_at, seen_count FROM patient_memory "
                "WHERE patient_name=? AND user_id=? AND superseded=0 "
                "AND (review_status IS NULL OR review_status = 'confirmed') "
                "ORDER BY last_seen_at DESC",
                (key, owner_id),
            )
        else:
            rows = await _fetch_all(
                db,
                "SELECT field, value, last_seen_at, seen_count FROM patient_memory "
                "WHERE patient_name=? AND user_id=? AND superseded=0 ORDER BY last_seen_at DESC",
                (key, owner_id),
            )

    if not rows:
        return None

    result: dict = {
        "patient_name": patient_name,
        "medications": [],
        "diagnoses": [],
        "allergies": [],
        "investigations": [],
        "symptoms": [],
        "vitals": [],
        "visit_count": 0,
    }

    seen_sessions: set = set()
    for row in rows:
        field = row[0]
        value = row[1]
        last_seen = row[2]
        seen_count = row[3]

        if field == "medication":
            try:
                med = json.loads(value)
            except Exception:
                med = {"name": value}
            med["last_seen"] = last_seen
            result["medications"].append(med)
        elif field == "vital":
            result["vitals"].append({"reading": value, "last_seen": last_seen})
        elif field in ("diagnoses", "diagnosis"):
            result["diagnoses"].append({"value": value, "last_seen": last_seen})
        elif field == "allergies":
            result["allergies"].append({"value": value, "last_seen": last_seen})
        elif field == "investigations":
            result["investigations"].append({"value": value, "last_seen": last_seen})
        elif field == "symptoms":
            result["symptoms"].append({"value": value, "last_seen": last_seen})

    # Approximate visit count from max seen_count of any single item
    if rows:
        result["visit_count"] = max(int(r[3]) for r in rows)

    return result


# ── helpers ────────────────────────────────────────────────────────────────────

async def _fetch_one(db, query: str, params: tuple):
    async with db.execute(query, params) as cur:
        return await cur.fetchone()


async def _fetch_all(db, query: str, params: tuple) -> list:
    async with db.execute(query, params) as cur:
        return await cur.fetchall()

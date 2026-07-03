"""Supabase staging smoke for the Postgres cutover.

Reads DATABASE_URL and SECRET_KEY from the environment. Does not contain or
print credentials. Intended for one-off Phase 2 staging verification.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.storage.db import close_db_pool, db_connect, init_db


EXPECTED_TABLES = {
    "applied_migrations",
    "appointments",
    "assistant_tasks",
    "audit_logs",
    "billing_records",
    "clinic_members",
    "clinics",
    "consent_logs",
    "consultation_billing",
    "dhis_transactions",
    "doctor_availability",
    "doctor_profiles",
    "extraction_knowledge",
    "fact_corrections",
    "follow_up_reminders",
    "lab_dispatch_log",
    "patient_intake_sessions",
    "patient_interactions",
    "patient_memory",
    "patients",
    "pre_visit_forms",
    "sessions",
    "soap_feedback",
    "token_jti_blacklist",
    "usage_events",
    "users",
}


def _safe_body(body: Any) -> Any:
    if isinstance(body, dict):
        redacted = {}
        for key, value in body.items():
            if key in {"access_token", "token"}:
                redacted[key] = f"<redacted:{len(str(value))} chars>"
            else:
                redacted[key] = _safe_body(value)
        return redacted
    if isinstance(body, list):
        return [_safe_body(item) for item in body[:3]]
    return body


async def _json_response(response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text[:500]


async def _record(results: list[dict[str, Any]], name: str, response) -> Any:
    body = await _json_response(response)
    results.append(
        {
            "step": name,
            "status": response.status_code,
            "body": _safe_body(body),
        }
    )
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"{name} failed: {response.status_code} {body}")
    return body


async def verify_tables() -> list[str]:
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """,
            (),
        ) as cursor:
            rows = await cursor.fetchall()
    tables = [row[0] for row in rows]
    missing = sorted(EXPECTED_TABLES.difference(tables))
    if missing:
        raise RuntimeError(f"Missing expected tables: {missing}")
    return tables


async def main() -> None:
    if not os.environ.get("DATABASE_URL", "").startswith("postgresql://"):
        raise RuntimeError("DATABASE_URL must be a postgresql:// Supabase staging URI")
    if not os.environ.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set for auth smoke")

    await init_db()
    tables = await verify_tables()

    suffix = str(int(time.time()))
    username = f"staging_smoke_{suffix}"
    password = f"SmokePass-{suffix}"
    email = f"{username}@example.com"

    results: list[dict[str, Any]] = []
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://staging-smoke") as client:
        body = await _record(
            results,
            "register",
            await client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": "Dr. Staging Smoke",
                    "role": "doctor",
                },
            ),
        )
        user_id = str(body["id"])

        token_body = await _record(
            results,
            "login",
            await client.post(
                "/api/auth/token",
                data={"username": username, "password": password},
                headers={"content-type": "application/x-www-form-urlencoded"},
            ),
        )
        token = token_body["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        await _record(results, "list_sessions", await client.get("/api/sessions", headers=headers))

        session_body = await _record(
            results,
            "create_session",
            await client.post(
                "/api/sessions",
                json={
                    "patient_name": "Supabase Smoke Patient",
                    "doctor_name": "Dr. Staging Smoke",
                    "patient_phone": "+919999000111",
                    "patient_age": "42",
                    "patient_sex": "F",
                    "specialty": "general",
                    "cloud_ai_consent": False,
                    "mode": "health",
                },
                headers=headers,
            ),
        )
        session_id = session_body["id"]
        if session_body.get("patient_phone") != "+919999000111":
            raise RuntimeError(f"patient_phone did not round-trip: {session_body}")

        await _record(results, "get_session", await client.get(f"/api/sessions/{session_id}", headers=headers))

        await _record(results, "get_doctor_profile_empty", await client.get("/api/auth/doctor-profile", headers=headers))
        await _record(
            results,
            "put_doctor_profile",
            await client.put(
                "/api/auth/doctor-profile",
                json={
                    "name": "Dr. Staging Smoke",
                    "mci_number": "STAGE-123",
                    "clinic_name": "Lipi Staging Clinic",
                    "clinic_address": "Mumbai",
                    "clinic_phone": "+912200000000",
                    "whatsapp_phone": "+919999000111",
                },
                headers=headers,
            ),
        )
        await _record(results, "get_doctor_profile", await client.get("/api/auth/doctor-profile", headers=headers))

        await _record(results, "billing_status", await client.get("/api/billing/status", headers=headers))

        await _record(
            results,
            "put_doctor_availability",
            await client.put(
                "/api/doctor/availability",
                json=[{"day_of_week": 1, "start_time": "10:00", "end_time": "13:00", "slot_duration_minutes": 15}],
                headers=headers,
            ),
        )
        await _record(results, "get_doctor_availability", await client.get("/api/doctor/availability", headers=headers))
        await _record(results, "get_doctor_appointments", await client.get("/api/doctor/appointments", headers=headers))

    print(
        json.dumps(
            {
                "database": "supabase_staging",
                "tables_confirmed": tables,
                "expected_table_count": len(EXPECTED_TABLES),
                "user_id": user_id,
                "session_id": session_id,
                "responses": results,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    await close_db_pool()


if __name__ == "__main__":
    asyncio.run(main())

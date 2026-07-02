"""Clinic account and membership routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_auth import get_current_user
from app.storage.repository import SessionRepository

router = APIRouter()
repo = SessionRepository()


class ClinicUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    plan_name: str = "Pilot"
    plan_status: str = "trial"
    trial_starts_at: Optional[str] = None
    trial_ends_at: Optional[str] = None
    session_limit: int = Field(default=100, ge=0, le=100000)


class AddClinicMemberRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    role: str = "doctor"


class JoinClinicRequest(BaseModel):
    code: str = Field(min_length=4, max_length=20)


def _require_admin(clinic: dict) -> None:
    if clinic.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Clinic admin access required")


@router.get("/clinic/current")
async def get_current_clinic(current_user: dict = Depends(get_current_user)) -> dict:
    clinic = await repo.ensure_default_clinic(current_user)
    members = await repo.get_clinic_members(clinic["id"])
    return {"clinic": clinic, "members": members}


@router.put("/clinic/current")
async def update_current_clinic(
    body: ClinicUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if body.plan_status not in {"trial", "paid", "due", "cancelled"}:
        raise HTTPException(status_code=400, detail="Invalid clinic plan status")
    clinic = await repo.ensure_default_clinic(current_user)
    _require_admin(clinic)
    updated = await repo.update_clinic(
        clinic_id=clinic["id"],
        name=body.name,
        plan_name=body.plan_name,
        plan_status=body.plan_status,
        trial_starts_at=body.trial_starts_at,
        trial_ends_at=body.trial_ends_at,
        session_limit=body.session_limit,
    )
    updated["role"] = clinic.get("role")
    members = await repo.get_clinic_members(clinic["id"])
    return {"clinic": updated, "members": members}


@router.get("/clinic/invite-code")
async def get_invite_code(current_user: dict = Depends(get_current_user)) -> dict:
    """Return a short invite code derived from the doctor's clinic UUID."""
    clinic = await repo.ensure_default_clinic(current_user)
    raw = clinic["id"].replace("-", "").upper()
    code = raw[:6]
    return {"code": code, "clinic_id": clinic["id"], "clinic_name": clinic["name"]}


@router.post("/clinic/join", status_code=200)
async def join_clinic(
    body: JoinClinicRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Assistant joins a clinic using the 6-char invite code the doctor shared."""
    from app.storage.db import db_connect

    clinic = await repo.find_clinic_by_code(body.code)
    if not clinic:
        raise HTTPException(status_code=404, detail="Invalid clinic code. Ask your doctor for the correct code.")
    user_id = str(current_user["id"])
    if clinic["owner_user_id"] and clinic["owner_user_id"] == user_id:
        raise HTTPException(status_code=400, detail="You are the owner of this clinic.")

    async with db_connect() as db:
        async with db.execute(
            "SELECT 1 FROM clinic_members WHERE clinic_id = ? AND user_id = ?",
            (clinic["id"], user_id),
        ) as cursor:
            already = await cursor.fetchone()
        if not already:
            await db.execute(
                "INSERT INTO clinic_members (clinic_id, user_id, role) VALUES (?, ?, ?)",
                (clinic["id"], user_id, "staff"),
            )
            await db.commit()

    return {"success": True, "clinic": {"id": clinic["id"], "name": clinic["name"]}}


@router.get("/clinic/my-clinic-status")
async def my_clinic_status(current_user: dict = Depends(get_current_user)) -> dict:
    """Returns whether this user (assistant) is linked to a doctor's clinic."""
    from app.storage.db import db_connect
    user_id = str(current_user["id"])
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT c.id, c.name, c.owner_user_id, u.full_name, u.username
            FROM clinics c
            JOIN clinic_members cm ON cm.clinic_id = c.id
            JOIN users u ON CAST(u.id AS TEXT) = c.owner_user_id
            WHERE cm.user_id = ? AND c.owner_user_id != ?
            LIMIT 1
            """,
            (user_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        return {"linked": False}
    return {
        "linked": True,
        "clinic_id": row[0],
        "clinic_name": row[1],
        "doctor_id": row[2],
        "doctor_name": row[3] or row[4],
    }


@router.post("/clinic/members", status_code=201)
async def add_clinic_member(
    body: AddClinicMemberRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if body.role not in {"admin", "doctor", "staff"}:
        raise HTTPException(status_code=400, detail="Invalid clinic role")
    clinic = await repo.ensure_default_clinic(current_user)
    _require_admin(clinic)
    try:
        member = await repo.add_clinic_member(clinic["id"], body.identifier, body.role)
    except LookupError:
        raise HTTPException(status_code=404, detail="User not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "member": member}


# ---------------------------------------------------------------------------
# WhatsApp Clinic Inbox — triage queue for assistants
# ---------------------------------------------------------------------------

@router.get("/clinic/inbox")
async def get_clinic_inbox(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Returns all WhatsApp-originated sessions belonging to the current user's clinic,
    ordered newest first. The assistant uses this to triage and assign to doctors.
    """
    from app.storage.db import db_connect

    clinic = await repo.ensure_default_clinic(current_user)
    clinic_id = clinic["id"]

    async with db_connect() as db:
        # Also catch sessions where clinic_id is NULL but user is a clinic member
        # (covers WhatsApp sessions created before the clinic_id fix)
        async with db.execute(
            """
            SELECT DISTINCT s.id, s.patient_name, s.patient_phone, s.doctor_name,
                   s.status, s.created_at, s.soap_note, s.user_id, s.clinical_facts
            FROM sessions s
            WHERE s.initiated_by IN ('whatsapp', 'assistant')
              AND (
                s.clinic_id = ?
                OR (s.clinic_id IS NULL AND s.user_id IN (
                    SELECT user_id FROM clinic_members WHERE clinic_id = ?
                ))
              )
            ORDER BY s.created_at DESC
            LIMIT 100
            """,
            (clinic_id, clinic_id),
        ) as cur:
            rows = await cur.fetchall()

    import json as _json
    sessions = []
    for r in rows:
        soap_snippet = ""
        try:
            soap = _json.loads(r[6]) if r[6] and isinstance(r[6], str) else (r[6] or {})
            soap_snippet = (soap.get("A") or soap.get("assessment") or "")[:120]
        except Exception:
            pass
        sessions.append({
            "id": r[0],
            "patient_name": r[1] or "Unknown",
            "patient_phone": r[2] or "",
            "assigned_doctor_name": r[3] or "",
            "assigned_doctor_id": str(r[7]),
            "status": r[4],
            "created_at": str(r[5]),
            "soap_snippet": soap_snippet,
        })

    return {"sessions": sessions, "clinic_id": clinic_id}


class AssignDoctorRequest(BaseModel):
    doctor_user_id: str
    doctor_name: str = ""


@router.post("/clinic/sessions/{session_id}/assign")
async def assign_session_to_doctor(
    session_id: str,
    body: AssignDoctorRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Reassign a WhatsApp session to a specific doctor in the clinic."""
    from app.storage.db import db_connect

    clinic = await repo.ensure_default_clinic(current_user)
    clinic_id = clinic["id"]

    async with db_connect() as db:
        # Verify session belongs to this clinic
        async with db.execute(
            "SELECT id FROM sessions WHERE id=? AND clinic_id=?",
            (session_id, clinic_id),
        ) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="Session not found in this clinic")

        # Verify target doctor is in this clinic
        async with db.execute(
            "SELECT user_id FROM clinic_members WHERE clinic_id=? AND user_id=?",
            (clinic_id, body.doctor_user_id),
        ) as cur:
            if not await cur.fetchone():
                raise HTTPException(status_code=400, detail="Doctor is not a member of this clinic")

        # If no doctor_name provided, look it up
        doctor_name = body.doctor_name
        if not doctor_name:
            async with db.execute(
                "SELECT full_name, username FROM users WHERE id=?",
                (body.doctor_user_id,),
            ) as cur:
                row = await cur.fetchone()
                doctor_name = (row[0] or row[1]) if row else "Doctor"

        await db.execute(
            "UPDATE sessions SET user_id=?, doctor_name=? WHERE id=?",
            (body.doctor_user_id, doctor_name, session_id),
        )
        await db.commit()

    return {"success": True, "session_id": session_id, "assigned_to": doctor_name}


@router.get("/clinic/doctors")
async def list_clinic_doctors(current_user: dict = Depends(get_current_user)) -> dict:
    """List all doctors in the current user's clinic for the assignment dropdown."""
    from app.storage.db import db_connect

    clinic = await repo.ensure_default_clinic(current_user)
    clinic_id = clinic["id"]

    async with db_connect() as db:
        async with db.execute(
            """
            SELECT u.id, u.full_name, u.username, u.specialization, cm.role
            FROM clinic_members cm
            JOIN users u ON u.id = cm.user_id
            WHERE cm.clinic_id = ? AND cm.status != 'left'
            ORDER BY cm.role DESC, u.full_name
            """,
            (clinic_id,),
        ) as cur:
            rows = await cur.fetchall()

    doctors = [
        {
            "id": str(r[0]),
            "name": r[1] or r[2],
            "specialization": r[3] or "",
            "role": r[4],
        }
        for r in rows
    ]
    return {"doctors": doctors}

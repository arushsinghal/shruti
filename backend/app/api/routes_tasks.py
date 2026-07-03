"""Assistant task queue routes."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.services.whatsapp_service import WhatsAppService
from app.storage.db import db_connect
from app.storage.repository import SessionRepository
from app.utils.config import settings

router = APIRouter()
repo = SessionRepository()

_TASK_COLS = (
    "id, session_id, user_id, task_type, title, status, owner, due, notes, completed_at, created_at"
)


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    owner: Optional[str] = None


def _task_from_row(row) -> dict:
    return {
        "id": row[0],
        "session_id": row[1],
        "user_id": row[2],
        "task_type": row[3],
        "title": row[4],
        "status": row[5],
        "owner": row[6],
        "due": row[7],
        "notes": row[8],
        "completed_at": row[9],
        "created_at": row[10],
    }


def _owner_clause(role: Optional[str]) -> str:
    """SQL predicate scoping tasks to the caller.

    Doctors see their own tasks. Assistants see tasks belonging to any doctor
    whose clinic they are a member of (mirrors get_sessions_for_assistant), so
    a single clinic code links them to the doctor's entire queue. Both bind a
    single ``user_id`` parameter.
    """
    if role == "assistant":
        return (
            "user_id IN ("
            "SELECT c.owner_user_id FROM clinics c "
            "JOIN clinic_members cm ON cm.clinic_id = c.id "
            "WHERE cm.user_id = ?)"
        )
    return "user_id = ?"


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    user_id = str(current_user["id"])
    clause = _owner_clause(current_user.get("role"))
    async with db_connect() as db:
        if status:
            query = (
                f"SELECT {_TASK_COLS} FROM assistant_tasks "
                f"WHERE {clause} AND status = ? ORDER BY created_at DESC"
            )
            params = (user_id, status)
        else:
            query = (
                f"SELECT {_TASK_COLS} FROM assistant_tasks "
                f"WHERE {clause} ORDER BY created_at DESC"
            )
            params = (user_id,)
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
    return [_task_from_row(row) for row in rows]


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    user_id = str(current_user["id"])
    clause = _owner_clause(current_user.get("role"))
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        # Verify the caller may act on this task (own task, or a clinic task).
        async with db.execute(
            f"SELECT id FROM assistant_tasks WHERE id = ? AND {clause}",
            (task_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        # Access verified above; update by id alone (assistant id != task.user_id).
        if update.status is not None:
            completed_at = now if update.status == "done" else None
            await db.execute(
                "UPDATE assistant_tasks SET status = ?, completed_at = ? WHERE id = ?",
                (update.status, completed_at, task_id),
            )
        if update.notes is not None:
            await db.execute(
                "UPDATE assistant_tasks SET notes = ? WHERE id = ?",
                (update.notes, task_id),
            )
        if update.owner is not None:
            await db.execute(
                "UPDATE assistant_tasks SET owner = ? WHERE id = ?",
                (update.owner, task_id),
            )
        await db.commit()

        async with db.execute(
            f"SELECT {_TASK_COLS} FROM assistant_tasks WHERE id = ?",
            (task_id,),
        ) as cursor:
            updated = await cursor.fetchone()
    return _task_from_row(updated)


class SendFollowUpRequest(BaseModel):
    phone_number: str
    consent: bool = False
    follow_up_text: str


@router.post("/tasks/{task_id}/send-followup")
async def send_task_followup(
    task_id: str,
    body: SendFollowUpRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Task 30: Send a WhatsApp follow-up for a follow_up task and mark it done."""
    if not body.consent:
        raise HTTPException(status_code=400, detail="Patient consent required before sending follow-up.")

    user_id = str(current_user["id"])
    clause = _owner_clause(current_user.get("role"))
    now = datetime.utcnow().isoformat()

    async with db_connect() as db:
        async with db.execute(
            f"SELECT id, session_id, task_type, status, user_id FROM assistant_tasks "
            f"WHERE id = ? AND {clause}",
            (task_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        if row[2] != "follow_up":
            raise HTTPException(status_code=400, detail="This endpoint is only for follow_up tasks")

    # The session is owned by the doctor (row[4]), not necessarily the caller.
    session = await repo.get_session(row[1], row[4])
    doctor_name = (
        session.doctor_name if session else None
    ) or current_user.get("full_name") or current_user.get("username") or "Doctor"

    result = await WhatsAppService.send_follow_up_reminder(body.phone_number, doctor_name, body.follow_up_text)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("detail") or "WhatsApp delivery failed")

    async with db_connect() as db:
        await db.execute(
            "UPDATE assistant_tasks SET status = 'done', completed_at = ?, notes = ? WHERE id = ?",
            (now, f"Follow-up sent to {body.phone_number}", task_id),
        )
        await db.commit()

    return {**result, "task_id": task_id, "status": "done"}


class DispatchPrescriptionRequest(BaseModel):
    consent: bool = False


@router.post("/tasks/{task_id}/dispatch-prescription")
async def dispatch_prescription(
    task_id: str,
    body: DispatchPrescriptionRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """One-click prescription dispatch: phone is already on the session — no typing required.

    Generates the same signed prescription link as /sessions/:id/share-whatsapp,
    sends it via WhatsApp, and marks the task done. Requires the session to be
    complete and to have patient_phone stored from intake.
    """
    if not body.consent:
        raise HTTPException(status_code=400, detail="Patient consent required before sharing prescription.")

    user_id = str(current_user["id"])
    clause = _owner_clause(current_user.get("role"))
    now = datetime.utcnow().isoformat()

    async with db_connect() as db:
        async with db.execute(
            f"SELECT id, session_id, task_type, status, user_id FROM assistant_tasks WHERE id = ? AND {clause}",
            (task_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    if row[2] != "review_prescription":
        raise HTTPException(status_code=400, detail="This endpoint is only for review_prescription tasks")

    # Resolve session as the doctor who owns it (row[4] = task.user_id = doctor)
    session = await repo.get_session(row[1], row[4])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status.value != "complete":
        raise HTTPException(status_code=400, detail="Prescription can only be shared after the note is complete.")
    if not session.patient_phone:
        raise HTTPException(status_code=400, detail="No phone number on file. Use the WhatsApp modal to enter it manually.")

    doctor_user_id = session.user_id or row[4]
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": session.id,
        "session_id": session.id,
        "doctor_user_id": doctor_user_id,
        "scope": "patient_prescription_share",
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    secure_link = f"/patient-download/{token}"
    doctor_name = session.doctor_name or current_user.get("full_name") or current_user.get("username") or "Doctor"

    result = await WhatsAppService.send_message(session.patient_phone, doctor_name, secure_link)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("detail") or "WhatsApp delivery failed")

    async with db_connect() as db:
        await db.execute(
            "UPDATE assistant_tasks SET status = 'done', completed_at = ?, notes = ? WHERE id = ?",
            (now, f"Prescription sent to {session.patient_phone}", task_id),
        )
        await db.commit()

    return {"success": True, "task_id": task_id, "status": "done", "link": secure_link}

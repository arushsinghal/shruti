"""Session audit log routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect
from app.storage.repository import SessionRepository

router = APIRouter()
repo = SessionRepository()


@router.get("/audit")
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict:
    user_id = str(current_user["id"])
    async with db_connect() as db:
        async with db.execute(
            """
            SELECT id, session_id, user_id, action, detail, timestamp
            FROM audit_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
        async with db.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            total_row = await cursor.fetchone()
    entries = [
        {
            "id": row[0],
            "session_id": row[1],
            "user_id": row[2],
            "action": row[3],
            "event_type": row[3],
            "detail": row[4],
            "details": row[4],
            "timestamp": row[5],
            "resource_type": "session" if row[1] else "user",
            "resource_id": row[1],
        }
        for row in rows
    ]
    return {"entries": entries, "total": total_row[0] if total_row else 0}


@router.get("/sessions/{session_id}/audit")
async def get_session_audit(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await repo.get_audit_logs(session_id)

"""Learning alias administration routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect
from app.utils.config import settings

router = APIRouter()


@router.delete("/learning/aliases/{alias_id}")
async def revoke_alias(
    alias_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Admin: revoke promoted alias by setting status to revoked."""

    if current_user.get("username") != settings.shruti_admin_user:
        raise HTTPException(status_code=403, detail="Admin access required")

    async with db_connect() as db:
        await db.execute(
            "UPDATE extraction_knowledge SET status = 'revoked', promotion_status = 'revoked' WHERE id = ?",
            (alias_id,),
        )
        await db.commit()
    return {"ok": True, "alias_id": alias_id}

"""Doctor profile routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect

router = APIRouter()


class DoctorProfileUpdate(BaseModel):
    name: Optional[str] = None
    mci_number: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    whatsapp_phone: Optional[str] = None


@router.get("/auth/doctor-profile")
async def get_doctor_profile(current_user: dict = Depends(get_current_user)) -> dict:
    user_id = str(current_user["id"])
    async with db_connect() as db:
        try:
            async with db.execute(
                """
                SELECT name, mci_number, clinic_name, clinic_address, clinic_phone, whatsapp_phone
                FROM doctor_profiles
                WHERE user_id = ?
                """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
        except Exception:
            row = None
    if not row:
        return {}
    return {
        "name": row[0],
        "mci_number": row[1],
        "clinic_name": row[2],
        "clinic_address": row[3],
        "clinic_phone": row[4],
        "whatsapp_phone": row[5] if len(row) > 5 else None,
    }


@router.put("/auth/doctor-profile")
async def update_doctor_profile(
    data: DoctorProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    user_id = str(current_user["id"])
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO doctor_profiles (user_id, name, mci_number, clinic_name, clinic_address, clinic_phone, whatsapp_phone, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                mci_number = excluded.mci_number,
                clinic_name = excluded.clinic_name,
                clinic_address = excluded.clinic_address,
                clinic_phone = excluded.clinic_phone,
                whatsapp_phone = excluded.whatsapp_phone,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                data.name,
                data.mci_number,
                data.clinic_name,
                data.clinic_address,
                data.clinic_phone,
                data.whatsapp_phone,
                now,
            ),
        )
        await db.commit()
    return data.model_dump()

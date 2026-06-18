import json
from datetime import datetime
from typing import Optional, Any

import aiosqlite

from app.schemas.consultation import ConsultationSession, StatusEnum, ModeEnum
from app.storage.db import get_db_path

_SELECT = (
    "SELECT id, patient_name, doctor_name, created_at, status, "
    "audio_file_path, transcript, clinical_facts, memory_state, soap_note, cds_suggestions, "
    "cloud_ai_consent, diarized_transcript, mode, user_id "
    "FROM sessions"
)


def safe_json_loads_list(data: str) -> Any:
    if not data:
        return None
    try:
        val = json.loads(data)
        if isinstance(val, list):
            return val
        return [{"speaker": "Unknown", "text": str(val)}]
    except json.JSONDecodeError:
        return [{"speaker": "Unknown", "text": data}]

def safe_json_loads_dict(data: str) -> Any:
    if not data:
        return None
    try:
        val = json.loads(data)
        if isinstance(val, dict):
            return val
        return {"value": str(val)}
    except json.JSONDecodeError:
        return {"value": data}

def _row_to_session(row: aiosqlite.Row) -> ConsultationSession:
    return ConsultationSession(
        id=row[0],
        patient_name=row[1],
        doctor_name=row[2],
        created_at=datetime.fromisoformat(row[3]),
        status=StatusEnum(row[4]),
        audio_file_path=row[5],
        transcript=row[6],
        clinical_facts=safe_json_loads_dict(row[7]),
        memory_state=safe_json_loads_dict(row[8]),
        soap_note=safe_json_loads_dict(row[9]),
        cds_suggestions=safe_json_loads_list(row[10]),
        cloud_ai_consent=bool(row[11]) if len(row) > 11 else False,
        diarized_transcript=safe_json_loads_list(row[12]) if len(row) > 12 else None,
        mode=ModeEnum(row[13]) if (len(row) > 13 and row[13]) else ModeEnum.health,
        user_id=row[14] if len(row) > 14 else None,
    )


class SessionRepository:
    async def create_session(
        self,
        user_id: str,
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        cloud_ai_consent: bool = False,
        mode: ModeEnum = ModeEnum.health,
    ) -> ConsultationSession:
        session = ConsultationSession(
            patient_name=patient_name,
            doctor_name=doctor_name,
            cloud_ai_consent=cloud_ai_consent,
            mode=mode,
            user_id=user_id,
        )
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(
                "INSERT INTO sessions (id, patient_name, doctor_name, created_at, status, cloud_ai_consent, mode, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session.id, session.patient_name, session.doctor_name, session.created_at.isoformat(), session.status.value, 1 if session.cloud_ai_consent else 0, session.mode.value, session.user_id),
            )
            await db.commit()
        return session

    async def get_session(self, session_id: str, user_id: str) -> Optional[ConsultationSession]:
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute(f"{_SELECT} WHERE id = ? AND user_id = ?", (session_id, user_id)) as cursor:
                row = await cursor.fetchone()
        return _row_to_session(row) if row else None

    async def update_session(self, session: ConsultationSession) -> ConsultationSession:
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(
                """
                UPDATE sessions SET
                    patient_name = ?, doctor_name = ?, status = ?,
                    audio_file_path = ?, transcript = ?,
                    clinical_facts = ?, memory_state = ?, soap_note = ?, cds_suggestions = ?,
                    cloud_ai_consent = ?, diarized_transcript = ?, mode = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    session.patient_name,
                    session.doctor_name,
                    session.status.value,
                    session.audio_file_path,
                    session.transcript,
                    json.dumps(session.clinical_facts) if session.clinical_facts is not None else None,
                    json.dumps(session.memory_state) if session.memory_state is not None else None,
                    json.dumps(session.soap_note) if session.soap_note is not None else None,
                    json.dumps(session.cds_suggestions) if session.cds_suggestions is not None else None,
                    1 if session.cloud_ai_consent else 0,
                    json.dumps(session.diarized_transcript) if session.diarized_transcript is not None else None,
                    session.mode.value,
                    session.id,
                    session.user_id,
                ),
            )
            await db.commit()
        return session

    async def get_sessions_for_user(self, user_id: str) -> list[ConsultationSession]:
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute(f"{_SELECT} WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cursor:
                rows = await cursor.fetchall()
        return [_row_to_session(row) for row in rows]

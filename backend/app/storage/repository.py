import json
from datetime import datetime
from typing import Optional

import aiosqlite

from app.schemas.consultation import ConsultationSession, StatusEnum
from app.storage.db import get_db_path

_SELECT = (
    "SELECT id, patient_name, doctor_name, created_at, status, "
    "audio_file_path, transcript, clinical_facts, memory_state, soap_note, cds_suggestions, "
    "cloud_ai_consent, diarized_transcript "
    "FROM sessions"
)


def _row_to_session(row: aiosqlite.Row) -> ConsultationSession:
    return ConsultationSession(
        id=row[0],
        patient_name=row[1],
        doctor_name=row[2],
        created_at=datetime.fromisoformat(row[3]),
        status=StatusEnum(row[4]),
        audio_file_path=row[5],
        transcript=row[6],
        clinical_facts=json.loads(row[7]) if row[7] else None,
        memory_state=json.loads(row[8]) if row[8] else None,
        soap_note=json.loads(row[9]) if row[9] else None,
        cds_suggestions=json.loads(row[10]) if row[10] else None,
        cloud_ai_consent=bool(row[11]) if len(row) > 11 else False,
        diarized_transcript=row[12] if len(row) > 12 else None,
    )


class SessionRepository:
    async def create_session(
        self,
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        cloud_ai_consent: bool = False,
    ) -> ConsultationSession:
        session = ConsultationSession(
            patient_name=patient_name, 
            doctor_name=doctor_name, 
            cloud_ai_consent=cloud_ai_consent
        )
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(
                "INSERT INTO sessions (id, patient_name, doctor_name, created_at, status, cloud_ai_consent) VALUES (?, ?, ?, ?, ?, ?)",
                (session.id, session.patient_name, session.doctor_name, session.created_at.isoformat(), session.status.value, 1 if session.cloud_ai_consent else 0),
            )
            await db.commit()
        return session

    async def get_session(self, session_id: str) -> Optional[ConsultationSession]:
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute(f"{_SELECT} WHERE id = ?", (session_id,)) as cursor:
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
                    cloud_ai_consent = ?, diarized_transcript = ?
                WHERE id = ?
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
                    session.diarized_transcript,
                    session.id,
                ),
            )
            await db.commit()
        return session

    async def list_sessions(self) -> list[ConsultationSession]:
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute(f"{_SELECT} ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
        return [_row_to_session(row) for row in rows]

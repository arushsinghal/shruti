import json
import re
import uuid
from datetime import datetime
from typing import Optional, Any

from app.schemas.consultation import ConsultationSession, StatusEnum, ModeEnum, ConsentLogResponse
from app.storage.db import db_connect


def normalize_phone(phone: str) -> str:
    """Reduce to the last 10 digits so the same number in different formats
    ("+91 98765 43210", "919876543210", "9876543210") resolves to one patient.
    Matches the last-10-digits convention already used elsewhere in the
    codebase (e.g. ClinicInbox.tsx's patient_phone.slice(-10) for display)."""
    digits = re.sub(r"\D", "", phone or "")
    return digits[-10:] if len(digits) >= 10 else digits

_SELECT = (
    "SELECT id, patient_name, doctor_name, created_at, status, "
    "audio_file_path, transcript, clinical_facts, memory_state, soap_note, cds_suggestions, "
    "cloud_ai_consent, diarized_transcript, mode, user_id, abha_number, pmjay_beneficiary, specialty, "
    "patient_phone, initiated_by, patient_age, patient_sex "
    "FROM sessions"
)


def safe_json_loads_list(data: str) -> Any:
    if not data:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    try:
        val = json.loads(data)
        if isinstance(val, list):
            return val
        return [{"speaker": "Unknown", "text": str(val)}]
    except (json.JSONDecodeError, TypeError):
        return [{"speaker": "Unknown", "text": str(data)}]

def safe_json_loads_dict(data: str) -> Any:
    if not data:
        return None
    if isinstance(data, dict):
        return data
    try:
        val = json.loads(data)
        if isinstance(val, dict):
            return val
        return {"value": str(val)}
    except (json.JSONDecodeError, TypeError):
        return {"value": str(data)}

def _row_to_session(row: Any) -> ConsultationSession:
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
        abha_number=row[15] if len(row) > 15 else None,
        pmjay_beneficiary=bool(row[16]) if len(row) > 16 else False,
        specialty=row[17] if len(row) > 17 else None,
        patient_phone=row[18] if len(row) > 18 else None,
        initiated_by=row[19] if (len(row) > 19 and row[19]) else "doctor",
        patient_age=row[20] if len(row) > 20 else None,
        patient_sex=row[21] if len(row) > 21 else None,
    )


class SessionRepository:
    async def get_or_create_patient(
        self,
        phone: str,
        whatsapp_number: Optional[str] = None,
        name: Optional[str] = None,
        age: Optional[str] = None,
        sex: Optional[str] = None,
        abha_number: Optional[str] = None,
        pmjay_beneficiary: bool = False,
    ) -> Optional[str]:
        """Upsert the canonical patient record by phone number and return its id.

        Returns None if no phone was given — patient identity requires a phone
        number today; sessions without one simply get no patient_id (unchanged
        from before this table existed).
        """
        normalized = normalize_phone(phone)
        if not normalized:
            return None
        now = datetime.utcnow().isoformat()
        async with db_connect() as db:
            async with db.execute(
                "SELECT id FROM patients WHERE phone_number = ?", (normalized,)
            ) as cursor:
                row = await cursor.fetchone()
            if row:
                patient_id = row[0]
                # Refresh soft-changeable fields only; never overwrite with blanks.
                await db.execute(
                    "UPDATE patients SET "
                    "whatsapp_number = COALESCE(NULLIF(?, ''), whatsapp_number), "
                    "name = COALESCE(NULLIF(?, ''), name), "
                    "age = COALESCE(NULLIF(?, ''), age), "
                    "sex = COALESCE(NULLIF(?, ''), sex), "
                    "abha_number = COALESCE(NULLIF(?, ''), abha_number), "
                    "updated_at = ? "
                    "WHERE id = ?",
                    (whatsapp_number or "", name or "", age or "", sex or "", abha_number or "", now, patient_id),
                )
                await db.commit()
                return patient_id

            patient_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO patients "
                "(id, phone_number, whatsapp_number, name, age, sex, abha_number, pmjay_beneficiary, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    patient_id, normalized, (whatsapp_number or normalized), name, age, sex,
                    abha_number, 1 if pmjay_beneficiary else 0, now, now,
                ),
            )
            await db.commit()
            return patient_id

    async def create_session(
        self,
        user_id: str,
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        abha_number: Optional[str] = None,
        pmjay_beneficiary: bool = False,
        specialty: Optional[str] = None,
        cloud_ai_consent: bool = False,
        mode: ModeEnum = ModeEnum.health,
        clinic_id: Optional[str] = None,
        patient_phone: Optional[str] = None,
        patient_age: Optional[str] = None,
        patient_sex: Optional[str] = None,
        initiated_by: str = "doctor",
        whatsapp_number: Optional[str] = None,
    ) -> ConsultationSession:
        patient_id = None
        if patient_phone:
            try:
                patient_id = await self.get_or_create_patient(
                    phone=patient_phone,
                    whatsapp_number=whatsapp_number,
                    name=patient_name,
                    age=patient_age,
                    sex=patient_sex,
                    abha_number=abha_number,
                    pmjay_beneficiary=pmjay_beneficiary,
                )
            except Exception:
                # Patient-identity linking is additive; never let it block session creation.
                patient_id = None

        session = ConsultationSession(
            patient_name=patient_name,
            doctor_name=doctor_name,
            abha_number=abha_number,
            pmjay_beneficiary=pmjay_beneficiary,
            specialty=specialty,
            cloud_ai_consent=cloud_ai_consent,
            mode=mode,
            user_id=user_id,
            patient_phone=patient_phone,
            patient_age=patient_age,
            patient_sex=patient_sex,
            initiated_by=initiated_by,
            patient_id=patient_id,
        )
        async with db_connect() as db:
            await db.execute(
                "INSERT INTO sessions (id, patient_name, doctor_name, created_at, status, cloud_ai_consent, mode, user_id, abha_number, pmjay_beneficiary, specialty, clinic_id, patient_phone, patient_age, patient_sex, initiated_by, patient_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session.id, session.patient_name, session.doctor_name, session.created_at.isoformat(), session.status.value, 1 if session.cloud_ai_consent else 0, session.mode.value, session.user_id, session.abha_number, 1 if session.pmjay_beneficiary else 0, session.specialty, clinic_id, patient_phone, patient_age, patient_sex, initiated_by, patient_id),
            )
            await db.commit()
        return session

    async def get_session_public(self, session_id: str) -> Optional[ConsultationSession]:
        """Fetch a session by ID only — no user ownership check. For public patient-facing pages."""
        async with db_connect() as db:
            async with db.execute(f"{_SELECT} WHERE id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return None
            return _row_to_session(row)

    async def get_session(self, session_id: str, user_id: str) -> Optional[ConsultationSession]:
        async with db_connect() as db:
            async with db.execute(f"{_SELECT} WHERE id = ? AND user_id = ?", (session_id, user_id)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return None
            session = _row_to_session(row)
            async with db.execute(
                "SELECT consent_mode, consent_text_version, consent_hash, timestamp FROM consent_logs WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (session_id,)
            ) as cursor:
                log_row = await cursor.fetchone()
                if log_row:
                    session.consent_log = ConsentLogResponse(
                        consent_mode=log_row[0],
                        consent_text_version=log_row[1],
                        consent_hash=log_row[2],
                        timestamp=log_row[3]
                    )
        return session

    async def log_consent(
        self,
        session_id: str,
        user_id: str,
        consent_mode: str,
        consent_text_version: str,
        consent_payload_json: str,
        consent_hash: str,
        timestamp: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        async with db_connect() as db:
            await db.execute(
                "INSERT INTO consent_logs (session_id, user_id, consent_mode, consent_text_version, consent_payload_json, consent_hash, timestamp, user_agent, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, user_id, consent_mode, consent_text_version, consent_payload_json, consent_hash, timestamp, user_agent, ip_address),
            )
            await db.commit()


    async def update_session(self, session: ConsultationSession) -> ConsultationSession:
        async with db_connect() as db:
            await db.execute(
                """
                UPDATE sessions SET
                    patient_name = ?, doctor_name = ?, status = ?,
                    audio_file_path = ?, transcript = ?,
                    clinical_facts = ?, memory_state = ?, soap_note = ?, cds_suggestions = ?,
                cloud_ai_consent = ?, diarized_transcript = ?, mode = ?, specialty = ?
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
                session.specialty,
                session.id,
                    session.user_id,
                ),
            )
            await db.commit()
        return session

    async def get_sessions_for_user(self, user_id: str) -> list[ConsultationSession]:
        async with db_connect() as db:
            async with db.execute(f"{_SELECT} WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cursor:
                rows = await cursor.fetchall()
        return [_row_to_session(row) for row in rows]

    async def get_all_sessions(self) -> list[ConsultationSession]:
        async with db_connect() as db:
            async with db.execute(f"{_SELECT} ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
        return [_row_to_session(row) for row in rows]

    async def get_sessions_for_assistant(self, assistant_user_id: str) -> list[ConsultationSession]:
        """Return sessions owned by doctors in the same clinic(s) as this assistant."""
        async with db_connect() as db:
            async with db.execute(
                f"""
                {_SELECT}
                WHERE user_id IN (
                    SELECT c.owner_user_id
                    FROM clinics c
                    JOIN clinic_members cm ON cm.clinic_id = c.id
                    WHERE cm.user_id = ?
                )
                ORDER BY created_at DESC
                """,
                (assistant_user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [_row_to_session(row) for row in rows]

    async def get_session_for_actor(self, session_id: str, current_user: dict) -> Optional[ConsultationSession]:
        """Resolve a session the caller may act on.

        Returns the caller's own session, or — for an assistant — a session
        owned by a doctor in their clinic. Returns None if the caller has no
        access. Used by patient-facing actions (Rx share, follow-up) so an
        assistant can act on the doctor's sessions without owning them.
        """
        user_id = str(current_user["id"])
        own = await self.get_session(session_id, user_id)
        if own is not None:
            return own
        if current_user.get("role") != "assistant":
            return None
        async with db_connect() as db:
            async with db.execute(
                """
                SELECT user_id FROM sessions
                WHERE id = ? AND user_id IN (
                    SELECT c.owner_user_id
                    FROM clinics c
                    JOIN clinic_members cm ON cm.clinic_id = c.id
                    WHERE cm.user_id = ?
                )
                """,
                (session_id, user_id),
            ) as cursor:
                row = await cursor.fetchone()
        if not row:
            return None
        return await self.get_session(session_id, row[0])

    async def find_clinic_by_code(self, code: str) -> Optional[dict]:
        """Find a clinic whose UUID starts with the given 6-char hex code (case-insensitive)."""
        normalized = code.upper().replace("-", "").replace(" ", "")
        async with db_connect() as db:
            async with db.execute(
                "SELECT id, name, owner_user_id FROM clinics WHERE UPPER(REPLACE(id, '-', '')) LIKE ?",
                (normalized + "%",),
            ) as cursor:
                rows = await cursor.fetchall()
        if len(rows) != 1:
            return None
        r = rows[0]
        return {"id": r[0], "name": r[1], "owner_user_id": r[2]}

    async def get_doctor_profile(self, user_id: str) -> Optional[dict]:
        """Return doctor profile fields for printed documents (Rx, investigation orders).
        Returns None if no profile exists — callers must handle gracefully."""
        async with db_connect() as db:
            try:
                async with db.execute(
                    "SELECT name, mci_number, clinic_name, clinic_address, clinic_phone FROM doctor_profiles WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    return None
                return {
                    "name": row[0],
                    "mci_number": row[1],
                    "clinic_name": row[2],
                    "clinic_address": row[3],
                    "clinic_phone": row[4],
                }
            except Exception:
                return None

    async def save_feedback(
        self,
        session_id: str,
        user_id: str,
        status: str,
        original_soap: str,
        final_soap: str,
        delta: str,
        phi_scrubbed_original_soap: Optional[str],
        phi_scrubbed_final_soap: Optional[str],
        phi_scrubbed_delta: Optional[str],
        categories: str,
        timestamp: str,
    ) -> int:
        async with db_connect() as db:
            cursor = await db.execute(
                """
                INSERT INTO soap_feedback (
                    session_id, user_id, status, original_soap, final_soap, delta,
                    phi_scrubbed_original_soap, phi_scrubbed_final_soap, phi_scrubbed_delta,
                    categories, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, user_id, status, original_soap, final_soap, delta,
                    phi_scrubbed_original_soap, phi_scrubbed_final_soap, phi_scrubbed_delta,
                    categories, timestamp
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def log_usage_event(self, *args, **kwargs) -> None:
        if len(args) >= 4:
            event_type = str(args[0])
            user_id = str(args[1])
            session_id = str(args[2] or "")
            detail = json.dumps(args[3])
        else:
            user_id = str(kwargs.get("user_id", args[0] if args else ""))
            event_type = str(kwargs.get("event_type", args[1] if len(args) > 1 else ""))
            session_id = str(kwargs.get("session_id", ""))
            detail = str(kwargs.get("detail", args[2] if len(args) > 2 else ""))
        async with db_connect() as db:
            try:
                now = datetime.utcnow().isoformat()
                await db.execute(
                    "INSERT INTO audit_logs (session_id, user_id, action, detail, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, event_type, detail or "", now),
                )
                await db.execute(
                    "INSERT INTO usage_events (session_id, user_id, event_type, metadata_json, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, event_type, detail or "{}", now),
                )
                await db.commit()
            except Exception:
                pass

    async def log_audit(self, *args, **kwargs) -> None:
        if len(args) >= 5:
            action = str(args[0])
            user_id = str(args[1])
            resource_type = str(args[2])
            resource_id = str(args[3] or "")
            detail = str(args[4] or "")
            session_id = resource_id if resource_type == "session" else ""
        else:
            session_id = str(kwargs.get("session_id", args[0] if args else ""))
            user_id = str(kwargs.get("user_id", args[1] if len(args) > 1 else ""))
            action = str(kwargs.get("action", args[2] if len(args) > 2 else ""))
            detail = str(kwargs.get("detail", args[3] if len(args) > 3 else ""))
        async with db_connect() as db:
            try:
                now = datetime.utcnow().isoformat()
                await db.execute(
                    "INSERT INTO audit_logs (session_id, user_id, action, detail, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, action, detail or "", now),
                )
                await db.commit()
            except Exception:
                pass

    async def get_audit_logs(self, session_id: str) -> list[dict]:
        async with db_connect() as db:
            try:
                async with db.execute(
                    "SELECT id, session_id, user_id, action, detail, timestamp FROM audit_logs WHERE session_id = ? ORDER BY id DESC",
                    (session_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
                return [
                    {
                        "id": r[0],
                        "session_id": r[1],
                        "user_id": r[2],
                        "action": r[3],
                        "detail": r[4],
                        "timestamp": r[5],
                    }
                    for r in rows
                ]
            except Exception:
                return []

    async def ensure_default_clinic(self, current_user: dict | str) -> dict:
        user_id = str(current_user["id"] if isinstance(current_user, dict) else current_user)
        async with db_connect() as db:
            async with db.execute(
                """
                SELECT id, name, owner_user_id, plan_name, plan_status, trial_starts_at, trial_ends_at, session_limit
                FROM clinics
                WHERE owner_user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "owner_user_id": row[2],
                    "plan_name": row[3],
                    "plan_status": row[4],
                    "trial_starts_at": row[5],
                    "trial_ends_at": row[6],
                    "session_limit": row[7],
                    "role": "admin",
                }

            async with db.execute(
                """
                SELECT c.id, c.name, c.owner_user_id, c.plan_name, c.plan_status, c.trial_starts_at, c.trial_ends_at, c.session_limit, cm.role
                FROM clinics c
                JOIN clinic_members cm ON cm.clinic_id = c.id
                WHERE cm.user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "owner_user_id": row[2],
                    "plan_name": row[3],
                    "plan_status": row[4],
                    "trial_starts_at": row[5],
                    "trial_ends_at": row[6],
                    "session_limit": row[7],
                    "role": row[8],
                }

            import uuid

            clinic_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            await db.execute(
                """
                INSERT INTO clinics (id, name, owner_user_id, plan_name, plan_status, session_limit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (clinic_id, "My Clinic", user_id, "Pilot", "trial", 100, now),
            )
            await db.execute(
                "INSERT INTO clinic_members (clinic_id, user_id, role) VALUES (?, ?, ?)",
                (clinic_id, user_id, "admin"),
            )
            await db.commit()
            return {
                "id": clinic_id,
                "name": "My Clinic",
                "owner_user_id": user_id,
                "plan_name": "Pilot",
                "plan_status": "trial",
                "trial_starts_at": None,
                "trial_ends_at": None,
                "session_limit": 100,
                "role": "admin",
            }

    async def get_clinic_members(self, clinic_id: str) -> list[dict]:
        async with db_connect() as db:
            async with db.execute(
                """
                SELECT cm.user_id, cm.role, u.username, u.email, u.full_name
                FROM clinic_members cm
                LEFT JOIN users u ON CAST(u.id AS TEXT) = cm.user_id
                WHERE cm.clinic_id = ?
                ORDER BY cm.role, u.full_name, u.username
                """,
                (clinic_id,),
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {
                    "user_id": r[0],
                    "role": r[1],
                    "username": r[2],
                    "email": r[3],
                    "full_name": r[4],
                }
                for r in rows
            ]

    async def update_clinic(
        self,
        clinic_id: str,
        name: str,
        plan_name: str = "Pilot",
        plan_status: str = "trial",
        trial_starts_at: Optional[str] = None,
        trial_ends_at: Optional[str] = None,
        session_limit: int = 100,
    ) -> dict:
        async with db_connect() as db:
            await db.execute(
                """
                UPDATE clinics
                SET name = ?, plan_name = ?, plan_status = ?, trial_starts_at = ?, trial_ends_at = ?, session_limit = ?
                WHERE id = ?
                """,
                (name, plan_name, plan_status, trial_starts_at, trial_ends_at, session_limit, clinic_id),
            )
            await db.commit()
            return {
                "id": clinic_id,
                "name": name,
                "plan_name": plan_name,
                "plan_status": plan_status,
                "trial_starts_at": trial_starts_at,
                "trial_ends_at": trial_ends_at,
                "session_limit": session_limit,
            }

    async def add_clinic_member(self, clinic_id: str, identifier: str, role: str = "doctor") -> dict:
        async with db_connect() as db:
            async with db.execute(
                """
                SELECT id, username, email, full_name
                FROM users
                WHERE CAST(id AS TEXT) = ? OR username = ? OR email = ?
                LIMIT 1
                """,
                (identifier, identifier, identifier),
            ) as cursor:
                user = await cursor.fetchone()
            if not user:
                raise LookupError("User not found")

            member_user_id = str(user[0])
            async with db.execute(
                "SELECT owner_user_id FROM clinics WHERE id = ?",
                (clinic_id,),
            ) as cursor:
                clinic = await cursor.fetchone()
            if not clinic:
                raise ValueError("Clinic not found")

            await db.execute(
                """
                INSERT INTO clinic_members (clinic_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(clinic_id, user_id) DO UPDATE SET role = excluded.role
                """,
                (clinic_id, member_user_id, role),
            )
            await db.commit()
            return {
                "user_id": member_user_id,
                "role": role,
                "username": user[1],
                "email": user[2],
                "full_name": user[3],
            }

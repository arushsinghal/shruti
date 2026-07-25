from pathlib import Path
import aiosqlite
import logging
import contextlib
import sys
from typing import Any

from app.utils.config import settings

logger = logging.getLogger(__name__)
_pg_pool: Any = None

# Always resolve relative to the backend/ directory so the path is stable
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = Path(settings.data_dir) if settings.data_dir else _BACKEND_DIR
_DB_FILE = Path(settings.sqlite_db) if Path(settings.sqlite_db).is_absolute() else _DATA_DIR / settings.sqlite_db
_DB_PATH = str(_DB_FILE)

def get_db_path() -> str:
    return _DB_PATH

def is_postgresql() -> bool:
    # Use PostgreSQL if database_url is provided and starts with postgresql:// or postgres://,
    # except when running route/integration tests (detected by "test" in get_db_path())
    if settings.database_url and (
        settings.database_url.startswith("postgresql://") or 
        settings.database_url.startswith("postgres://")
    ):
        if "test" in get_db_path():
            return False
        return True
    return False


async def open_db_pool() -> None:
    """Create the shared PostgreSQL pool once per process.

    SQLite remains file-backed and does not use this pool.
    """
    global _pg_pool
    if not is_postgresql() or _pg_pool is not None:
        return

    import asyncpg

    _pg_pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
        statement_cache_size=0,  # required for Supabase PgBouncer pooler
    )
    logger.info(
        "PostgreSQL pool opened: min_size=%s max_size=%s",
        settings.postgres_pool_min_size,
        settings.postgres_pool_max_size,
    )


async def close_db_pool() -> None:
    """Close the shared PostgreSQL pool on application shutdown."""
    global _pg_pool
    if _pg_pool is None:
        return
    await _pg_pool.close()
    _pg_pool = None
    logger.info("PostgreSQL pool closed")


async def get_db_pool():
    """Return a ready PostgreSQL pool, lazily opening for scripts/tests."""
    await open_db_pool()
    return _pg_pool

# PostgreSQL tables schema
PG_CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    patient_name TEXT,
    doctor_name TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    mode TEXT NOT NULL DEFAULT 'health',
    audio_file_path TEXT,
    transcript TEXT,
    clinical_facts TEXT,
    memory_state TEXT,
    soap_note TEXT,
    cds_suggestions TEXT,
    cloud_ai_consent INTEGER DEFAULT 0,
    diarized_transcript TEXT,
    user_id TEXT,
    abha_number TEXT,
    pmjay_beneficiary INTEGER DEFAULT 0,
    specialty TEXT,
    clinic_id TEXT,
    patient_phone TEXT,
    patient_age TEXT,
    patient_sex TEXT,
    initiated_by TEXT DEFAULT 'doctor',
    patient_consent_given INTEGER DEFAULT 0,
    patient_consent_timestamp TEXT,
    memory_enabled INTEGER DEFAULT 1,
    signed_at TEXT,
    received_at TEXT,
    delivered_at TEXT,
    hold_for_review INTEGER DEFAULT 0,
    reviewer_id TEXT,
    reviewer_action TEXT,
    reviewer_note TEXT,
    patient_id TEXT
);
"""

PG_CREATE_TOKEN_BLACKLIST_TABLE = """
CREATE TABLE IF NOT EXISTS token_jti_blacklist (
    jti TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    blacklisted_at TEXT NOT NULL
);
"""

PG_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1,
    role TEXT NOT NULL DEFAULT 'doctor',
    nmc_number TEXT,
    specialization TEXT,
    plan TEXT DEFAULT 'trial',
    trial_sessions_used INTEGER DEFAULT 0,
    paid_until TEXT,
    razorpay_payment_id TEXT
);
"""

PG_CREATE_CONSENT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS consent_logs (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    consent_mode TEXT NOT NULL,
    consent_text_version TEXT NOT NULL,
    consent_payload_json TEXT NOT NULL,
    consent_hash TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT
);
"""

PG_CREATE_SOAP_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS soap_feedback (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    original_soap TEXT,
    final_soap TEXT,
    delta TEXT,
    phi_scrubbed_original_soap TEXT,
    phi_scrubbed_final_soap TEXT,
    phi_scrubbed_delta TEXT,
    categories TEXT,
    timestamp TEXT NOT NULL
);
"""

PG_CREATE_DOCTOR_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS doctor_profiles (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    name TEXT,
    mci_number TEXT,
    clinic_name TEXT,
    clinic_address TEXT,
    clinic_phone TEXT,
    updated_at TEXT,
    whatsapp_phone TEXT
);
"""

PG_CREATE_PATIENT_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS patient_memory (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    patient_identifier TEXT,
    memory_key TEXT,
    memory_value TEXT,
    confidence REAL DEFAULT 1.0,
    source_session_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    patient_name TEXT,
    clinic_id TEXT,
    field TEXT,
    med_name TEXT,
    value TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    seen_count INTEGER DEFAULT 1,
    fact_id TEXT,
    review_status TEXT DEFAULT 'confirmed',
    confirmed_by TEXT,
    confirmed_at TEXT,
    superseded INTEGER DEFAULT 0
);
"""

PG_CREATE_EXTRACTION_KNOWLEDGE_TABLE = """
CREATE TABLE IF NOT EXISTS extraction_knowledge (
    id SERIAL PRIMARY KEY,
    alias TEXT,
    canonical TEXT,
    category TEXT,
    knowledge_type TEXT,
    canonical_value TEXT,
    surface_form TEXT,
    field TEXT,
    confidence REAL DEFAULT 0.5,
    weighted_score REAL DEFAULT 0,
    confirmations INTEGER DEFAULT 0,
    rejections INTEGER DEFAULT 0,
    unique_clinics INTEGER DEFAULT 0,
    clinic_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'candidate',
    promotion_status TEXT DEFAULT 'clinic_scoped',
    confirming_users TEXT DEFAULT '[]',
    confirming_clinics TEXT DEFAULT '[]',
    promoted_at TEXT,
    promoted_by TEXT,
    rejected_at TEXT,
    rejected_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

PG_CREATE_FACT_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS fact_corrections (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    action TEXT NOT NULL,
    corrected_at TEXT NOT NULL
);
"""

PG_CREATE_ASSISTANT_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS assistant_tasks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    owner TEXT,
    due TEXT,
    notes TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL
);
"""

PG_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applied_migrations (
    id SERIAL PRIMARY KEY,
    version TEXT UNIQUE NOT NULL,
    applied_at TEXT NOT NULL
);
"""

PG_CREATE_AUDIT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    timestamp TEXT NOT NULL
);
"""

PG_CREATE_CLINICS_TABLE = """
CREATE TABLE IF NOT EXISTS clinics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    plan_name TEXT NOT NULL DEFAULT 'Pilot',
    plan_status TEXT NOT NULL DEFAULT 'trial',
    trial_starts_at TEXT,
    trial_ends_at TEXT,
    session_limit INTEGER DEFAULT 100,
    created_at TEXT NOT NULL
);
"""

PG_CREATE_CLINIC_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS clinic_members (
    clinic_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    PRIMARY KEY (clinic_id, user_id)
);
"""

PG_CREATE_USAGE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS usage_events (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metadata_json TEXT,
    timestamp TEXT NOT NULL
);
"""

PG_CREATE_BILLING_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS billing_records (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    clinic_name TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    amount_inr INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# Per-consultation patient fee, distinct from billing_records (Lipi's own
# SaaS/plan billing). Split from a shared table that had drifted into two
# incompatible schemas across environments.
PG_CREATE_CONSULTATION_BILLING_TABLE = """
CREATE TABLE IF NOT EXISTS consultation_billing (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    amount REAL,
    currency TEXT DEFAULT 'INR',
    notes TEXT,
    clinic_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

SQLITE_CREATE_CONSULTATION_BILLING_TABLE = """
CREATE TABLE IF NOT EXISTS consultation_billing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    amount REAL,
    currency TEXT DEFAULT 'INR',
    notes TEXT,
    clinic_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# Canonical patient identity — sessions carry a denormalized copy of patient
# fields for historical reasons; this table is the single durable identity a
# patient keeps across visits, keyed by phone number since that's what
# WhatsApp delivery and the patient portal already use to find someone.
PG_CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    phone_number TEXT NOT NULL UNIQUE,
    whatsapp_number TEXT,
    name TEXT,
    age TEXT,
    sex TEXT,
    abha_number TEXT,
    pmjay_beneficiary INTEGER DEFAULT 0,
    consent_on_file INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# SQLite tables schema
SQLITE_CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    patient_name TEXT,
    doctor_name TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    mode TEXT NOT NULL DEFAULT 'health',
    audio_file_path TEXT,
    transcript TEXT,
    clinical_facts TEXT,
    memory_state TEXT,
    soap_note TEXT,
    cds_suggestions TEXT,
    cloud_ai_consent INTEGER DEFAULT 0,
    diarized_transcript TEXT,
    user_id TEXT,
    abha_number TEXT,
    pmjay_beneficiary INTEGER DEFAULT 0,
    specialty TEXT,
    clinic_id TEXT
);
"""

SQLITE_CREATE_TOKEN_BLACKLIST_TABLE = """
CREATE TABLE IF NOT EXISTS token_jti_blacklist (
    jti TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    blacklisted_at TEXT NOT NULL
);
"""

SQLITE_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1,
    role TEXT NOT NULL DEFAULT 'doctor'
);
"""

SQLITE_CREATE_CONSENT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS consent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    consent_mode TEXT NOT NULL,
    consent_text_version TEXT NOT NULL,
    consent_payload_json TEXT NOT NULL,
    consent_hash TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT
);
"""

SQLITE_CREATE_SOAP_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS soap_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    original_soap TEXT,
    final_soap TEXT,
    delta TEXT,
    phi_scrubbed_original_soap TEXT,
    phi_scrubbed_final_soap TEXT,
    phi_scrubbed_delta TEXT,
    categories TEXT,
    timestamp TEXT NOT NULL
);
"""

SQLITE_CREATE_DOCTOR_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS doctor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    name TEXT,
    mci_number TEXT,
    clinic_name TEXT,
    clinic_address TEXT,
    clinic_phone TEXT,
    updated_at TEXT
);
"""

SQLITE_CREATE_PATIENT_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS patient_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    patient_identifier TEXT,
    memory_key TEXT,
    memory_value TEXT,
    confidence REAL DEFAULT 1.0,
    source_session_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    patient_name TEXT,
    clinic_id TEXT,
    field TEXT,
    med_name TEXT,
    value TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    seen_count INTEGER DEFAULT 1,
    fact_id TEXT,
    review_status TEXT DEFAULT 'confirmed',
    confirmed_by TEXT,
    confirmed_at TEXT,
    superseded INTEGER DEFAULT 0
);
"""

SQLITE_CREATE_EXTRACTION_KNOWLEDGE_TABLE = """
CREATE TABLE IF NOT EXISTS extraction_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT,
    canonical TEXT,
    category TEXT,
    knowledge_type TEXT,
    canonical_value TEXT,
    surface_form TEXT,
    field TEXT,
    confidence REAL DEFAULT 0.5,
    weighted_score REAL DEFAULT 0,
    confirmations INTEGER DEFAULT 0,
    rejections INTEGER DEFAULT 0,
    unique_clinics INTEGER DEFAULT 0,
    clinic_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'candidate',
    promotion_status TEXT DEFAULT 'clinic_scoped',
    confirming_users TEXT DEFAULT '[]',
    confirming_clinics TEXT DEFAULT '[]',
    promoted_at TEXT,
    promoted_by TEXT,
    rejected_at TEXT,
    rejected_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

SQLITE_CREATE_FACT_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS fact_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    action TEXT NOT NULL,
    corrected_at TEXT NOT NULL
);
"""

SQLITE_CREATE_ASSISTANT_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS assistant_tasks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    owner TEXT,
    due TEXT,
    notes TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL
);
"""

SQLITE_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applied_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    applied_at TEXT NOT NULL
);
"""

SQLITE_CREATE_AUDIT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    timestamp TEXT NOT NULL
);
"""

SQLITE_CREATE_CLINICS_TABLE = """
CREATE TABLE IF NOT EXISTS clinics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    plan_name TEXT NOT NULL DEFAULT 'Pilot',
    plan_status TEXT NOT NULL DEFAULT 'trial',
    trial_starts_at TEXT,
    trial_ends_at TEXT,
    session_limit INTEGER DEFAULT 100,
    created_at TEXT NOT NULL
);
"""

SQLITE_CREATE_CLINIC_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS clinic_members (
    clinic_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    PRIMARY KEY (clinic_id, user_id)
);
"""

SQLITE_CREATE_USAGE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metadata_json TEXT,
    timestamp TEXT NOT NULL
);
"""

SQLITE_CREATE_BILLING_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS billing_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    clinic_name TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    amount_inr INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

SQLITE_CREATE_FOLLOW_UP_REMINDERS_TABLE = """
CREATE TABLE IF NOT EXISTS follow_up_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    patient_name TEXT,
    doctor_name TEXT DEFAULT '',
    scheduled_for TEXT NOT NULL,
    due_at TEXT NOT NULL,
    reminder_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SQLITE_CREATE_PATIENT_INTERACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS patient_interactions (
    id TEXT PRIMARY KEY,
    patient_phone TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    doctor_user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
"""

SQLITE_CREATE_LAB_DISPATCH_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS lab_dispatch_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    tests_json TEXT NOT NULL,
    dispatched_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'sent'
);
"""

SQLITE_CREATE_DHIS_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS dhis_transactions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    abha_id TEXT NOT NULL,
    facility_hfr_id TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Cat2',
    abdm_transaction_id TEXT,
    clinic_amount REAL NOT NULL DEFAULT 7.50,
    dsc_amount REAL NOT NULL DEFAULT 2.50,
    status TEXT NOT NULL DEFAULT 'pending_claim',
    created_at TEXT NOT NULL
);
"""

SQLITE_CREATE_PATIENT_INTAKE_TABLE = """
CREATE TABLE IF NOT EXISTS patient_intake_sessions (
    id TEXT PRIMARY KEY,
    from_phone TEXT NOT NULL,
    clinic_code TEXT,
    clinic_user_id TEXT,
    step TEXT NOT NULL DEFAULT 'awaiting_clinic_code',
    patient_name TEXT,
    patient_age TEXT,
    chief_complaint TEXT,
    current_medications TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
"""

SQLITE_CREATE_PRE_VISIT_FORMS_TABLE = """
CREATE TABLE IF NOT EXISTS pre_visit_forms (
    id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL,
    chief_complaint TEXT,
    current_medications TEXT,
    allergies TEXT,
    additional_notes TEXT,
    submitted_at TEXT NOT NULL
);
"""

SQLITE_CREATE_APPOINTMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    clinic_user_id TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    patient_name TEXT,
    slot_datetime TEXT NOT NULL,
    chief_complaint TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""

SQLITE_CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    phone_number TEXT NOT NULL UNIQUE,
    whatsapp_number TEXT,
    name TEXT,
    age TEXT,
    sex TEXT,
    abha_number TEXT,
    pmjay_beneficiary INTEGER DEFAULT 0,
    consent_on_file INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

SQLITE_CREATE_DOCTOR_AVAILABILITY_TABLE = """
CREATE TABLE IF NOT EXISTS doctor_availability (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    slot_duration_minutes INTEGER NOT NULL DEFAULT 15,
    is_active INTEGER NOT NULL DEFAULT 1
);
"""

SQLITE_MIGRATIONS = [
    "ALTER TABLE sessions ADD COLUMN audio_file_path TEXT",
    "ALTER TABLE sessions ADD COLUMN cloud_ai_consent INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN diarized_transcript TEXT",
    "ALTER TABLE sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'health'",
    "ALTER TABLE sessions ADD COLUMN user_id TEXT",
    "ALTER TABLE sessions ADD COLUMN abha_number TEXT",
    "ALTER TABLE sessions ADD COLUMN pmjay_beneficiary INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN specialty TEXT",
    "ALTER TABLE sessions ADD COLUMN clinic_id TEXT",
    "ALTER TABLE patient_memory ADD COLUMN fact_id TEXT",
    "ALTER TABLE patient_memory ADD COLUMN review_status TEXT DEFAULT 'confirmed'",
    "ALTER TABLE patient_memory ADD COLUMN confirmed_by TEXT",
    "ALTER TABLE patient_memory ADD COLUMN confirmed_at TEXT",
    "ALTER TABLE patient_memory ADD COLUMN superseded INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'doctor'",
    "ALTER TABLE sessions ADD COLUMN patient_phone TEXT",
    "ALTER TABLE sessions ADD COLUMN patient_age TEXT",
    "ALTER TABLE sessions ADD COLUMN patient_sex TEXT",
    "ALTER TABLE sessions ADD COLUMN initiated_by TEXT DEFAULT 'doctor'",
    "ALTER TABLE sessions ADD COLUMN patient_consent_given INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN patient_consent_timestamp TEXT",
    "ALTER TABLE sessions ADD COLUMN memory_enabled INTEGER DEFAULT 1",
    "ALTER TABLE doctor_profiles ADD COLUMN whatsapp_phone TEXT",
    "ALTER TABLE users ADD COLUMN nmc_number TEXT",
    "ALTER TABLE users ADD COLUMN specialization TEXT",
    "ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'trial'",
    "ALTER TABLE users ADD COLUMN trial_sessions_used INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN paid_until TEXT",
    "ALTER TABLE users ADD COLUMN razorpay_payment_id TEXT",
    "ALTER TABLE sessions ADD COLUMN signed_at TEXT",
    "ALTER TABLE sessions ADD COLUMN received_at TEXT",
    "ALTER TABLE sessions ADD COLUMN delivered_at TEXT",
    "ALTER TABLE sessions ADD COLUMN hold_for_review INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN reviewer_id TEXT",
    "ALTER TABLE sessions ADD COLUMN reviewer_action TEXT",
    "ALTER TABLE sessions ADD COLUMN reviewer_note TEXT",
    "ALTER TABLE sessions ADD COLUMN patient_id TEXT",
]

class DBCursor:
    def __init__(self, records=None, lastrowid=None):
        self.records = records or []
        self.index = 0
        self.lastrowid = lastrowid

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.records):
            row = self.records[self.index]
            self.index += 1
            return row
        raise StopAsyncIteration

    async def fetchone(self):
        if self.index < len(self.records):
            row = self.records[self.index]
            self.index += 1
            return row
        return None

    async def fetchall(self):
        return self.records


class ExecuteWrapper:
    def __init__(self, db_conn, query: str, parameters: tuple):
        self.db_conn = db_conn
        self.query = query
        self.parameters = parameters
        self.cursor = None

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        if self.db_conn.is_pg:
            # Replace '?' placeholders with '$1', '$2', ...
            parts = self.query.split('?')
            translated_query = "".join(f"{part}${i+1}" for i, part in enumerate(parts[:-1])) + parts[-1]
            
            # For PostgreSQL, try to return the row ID after INSERT.
            # Skip RETURNING id when ON CONFLICT is present (tables like doctor_profiles
            # use user_id as PK and have no id column).
            if "INSERT INTO" in self.query.upper() and "ON CONFLICT" not in self.query.upper():
                translated_query += " RETURNING id"
                lastrowid = await self.db_conn.conn.fetchval(translated_query, *self.parameters)
                self.cursor = DBCursor([], lastrowid=lastrowid)
            elif "SELECT" in self.query.upper():
                records = await self.db_conn.conn.fetch(translated_query, *self.parameters)
                self.cursor = DBCursor(records)
            else:
                await self.db_conn.conn.execute(translated_query, *self.parameters)
                self.cursor = DBCursor([])
            return self.cursor
        else:
            # SQLite: await the cursor
            self.cursor = await self.db_conn.conn.execute(self.query, self.parameters)
            return self.cursor

    async def __aenter__(self):
        await self._execute()
        return self.cursor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.db_conn.is_pg and self.cursor:
            await self.cursor.close()


class DBConnection:
    def __init__(self, conn, is_pg: bool, pool=None):
        self.conn = conn
        self.is_pg = is_pg
        self.pool = pool
        self.tx = None

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        if not self.is_pg:
            self.conn.row_factory = value

    async def __aenter__(self):
        if self.is_pg:
            self.tx = self.conn.transaction()
            await self.tx.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.is_pg:
            try:
                if exc_type is not None:
                    await self.tx.rollback()
                else:
                    await self.tx.commit()
            finally:
                if self.pool is not None:
                    await self.pool.release(self.conn)
                else:
                    await self.conn.close()
        else:
            # Closed externally for aiosqlite
            pass

    def execute(self, query: str, parameters: tuple = ()):
        return ExecuteWrapper(self, query, parameters)

    async def commit(self):
        if not self.is_pg:
            await self.conn.commit()


@contextlib.asynccontextmanager
async def db_connect():
    if is_postgresql():
        pool = await get_db_pool()
        conn = await pool.acquire()
        db_conn = DBConnection(conn, is_pg=True, pool=pool)
        entered = False
        try:
            await db_conn.__aenter__()
            entered = True
            yield db_conn
        except Exception:
            if entered:
                await db_conn.__aexit__(*sys.exc_info())
            else:
                await pool.release(conn)
            raise
        else:
            await db_conn.__aexit__(None, None, None)
    else:
        conn = await aiosqlite.connect(_DB_PATH)
        db_conn = DBConnection(conn, is_pg=False)
        try:
            yield db_conn
        finally:
            await conn.close()


async def init_db() -> None:
    if is_postgresql():
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            async with conn.transaction():
                await conn.execute(PG_CREATE_SESSIONS_TABLE)
                await conn.execute(PG_CREATE_USERS_TABLE)
                await conn.execute(PG_CREATE_CONSENT_LOGS_TABLE)
                await conn.execute(PG_CREATE_SOAP_FEEDBACK_TABLE)
                await conn.execute(PG_CREATE_DOCTOR_PROFILES_TABLE)
                await conn.execute(PG_CREATE_PATIENT_MEMORY_TABLE)
                await conn.execute(PG_CREATE_EXTRACTION_KNOWLEDGE_TABLE)
                await conn.execute(PG_CREATE_FACT_CORRECTIONS_TABLE)
                await conn.execute(PG_CREATE_ASSISTANT_TASKS_TABLE)
                await conn.execute(PG_CREATE_MIGRATIONS_TABLE)
                await conn.execute(PG_CREATE_AUDIT_LOGS_TABLE)
                await conn.execute(PG_CREATE_CLINICS_TABLE)
                await conn.execute(PG_CREATE_CLINIC_MEMBERS_TABLE)
                await conn.execute(PG_CREATE_USAGE_EVENTS_TABLE)
                await conn.execute(PG_CREATE_BILLING_RECORDS_TABLE)
                await conn.execute(PG_CREATE_CONSULTATION_BILLING_TABLE)
                await conn.execute(PG_CREATE_TOKEN_BLACKLIST_TABLE)
                await conn.execute(PG_CREATE_PATIENTS_TABLE)
                await conn.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS patient_id TEXT")

                # New service-model tables
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS follow_up_reminders (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        patient_phone TEXT NOT NULL,
                        patient_name TEXT,
                        doctor_name TEXT DEFAULT '',
                        scheduled_for TEXT NOT NULL,
                        due_at TEXT NOT NULL,
                        reminder_text TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        error_text TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_interactions (
                        id TEXT PRIMARY KEY,
                        patient_phone TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        reference_id TEXT NOT NULL,
                        doctor_user_id TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending'
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS lab_dispatch_log (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        patient_phone TEXT NOT NULL,
                        tests_json TEXT NOT NULL,
                        dispatched_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'sent'
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS dhis_transactions (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        abha_id TEXT NOT NULL,
                        facility_hfr_id TEXT NOT NULL,
                        category TEXT NOT NULL DEFAULT 'Cat2',
                        abdm_transaction_id TEXT,
                        clinic_amount REAL NOT NULL DEFAULT 7.50,
                        dsc_amount REAL NOT NULL DEFAULT 2.50,
                        status TEXT NOT NULL DEFAULT 'pending_claim',
                        created_at TEXT NOT NULL
                    )
                """)
                # whatsapp_phone column on doctor_profiles (IF NOT EXISTS avoids aborting the transaction)
                await conn.execute("ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS whatsapp_phone TEXT")

                # patient intake, appointment booking, doctor availability
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_intake_sessions (
                        id TEXT PRIMARY KEY,
                        from_phone TEXT NOT NULL,
                        clinic_code TEXT,
                        clinic_user_id TEXT,
                        step TEXT NOT NULL DEFAULT 'awaiting_clinic_code',
                        patient_name TEXT,
                        patient_age TEXT,
                        chief_complaint TEXT,
                        current_medications TEXT,
                        created_at TEXT NOT NULL,
                        completed_at TEXT
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        id TEXT PRIMARY KEY,
                        clinic_user_id TEXT NOT NULL,
                        patient_phone TEXT NOT NULL,
                        patient_name TEXT,
                        slot_datetime TEXT NOT NULL,
                        chief_complaint TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TEXT NOT NULL
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS pre_visit_forms (
                        id TEXT PRIMARY KEY,
                        appointment_id TEXT NOT NULL,
                        chief_complaint TEXT,
                        current_medications TEXT,
                        allergies TEXT,
                        additional_notes TEXT,
                        submitted_at TEXT NOT NULL
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS doctor_availability (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        day_of_week INTEGER NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        slot_duration_minutes INTEGER NOT NULL DEFAULT 15,
                        is_active INTEGER NOT NULL DEFAULT 1
                    )
                """)

                # Admin seeding
                if settings.shruti_admin_user and settings.shruti_admin_password:
                    row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", settings.shruti_admin_user)
                    if not row:
                        from app.utils.security import get_password_hash
                        hashed_pw = get_password_hash(settings.shruti_admin_password)
                        await conn.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name) VALUES ($1, $2, $3, $4)",
                            settings.shruti_admin_user, f"{settings.shruti_admin_user}@example.com", hashed_pw, "Administrator"
                        )
                
                # Demo user seeding (Gated behind SEED_DEMO_USER=true)
                if settings.seed_demo_user and settings.demo_username and settings.demo_password:
                    from app.utils.security import get_password_hash
                    row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", settings.demo_username)
                    if not row:
                        hashed_pw = get_password_hash(settings.demo_password)
                        await conn.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name, role) VALUES ($1, $2, $3, $4, 'doctor')",
                            settings.demo_username, f"{settings.demo_username}@example.com", hashed_pw, settings.demo_full_name
                        )
                    # Assistant demo user — always paired with the doctor demo
                    row = await conn.fetchrow("SELECT id FROM users WHERE username = 'assistant_demo'")
                    if not row:
                        hashed_pw = get_password_hash(settings.demo_password)
                        await conn.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name, role) VALUES ($1, $2, $3, $4, 'assistant')",
                            'assistant_demo', 'assistant_demo@example.com', hashed_pw, 'Meena (Front Desk)'
                        )

                    # Demo clinic — links demo doctor + assistant_demo so assistant skips code entry.
                    # Id avoids 'O'/'0' and 'I'/'1' look-alike chars — its first 6 hex chars become
                    # the spoken/typed clinic invite code (see /api/clinic/invite-code).
                    demo_clinic_id = 'a1b2c3-0000-0000-0000-000000000000'
                    doctor_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", settings.demo_username)
                    assistant_row = await conn.fetchrow("SELECT id FROM users WHERE username = 'assistant_demo'")
                    if doctor_row and assistant_row:
                        doctor_id = str(doctor_row['id'])
                        assistant_id = str(assistant_row['id'])
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc).isoformat()
                        await conn.execute(
                            """INSERT INTO clinics (id, name, owner_user_id, plan_name, plan_status, created_at)
                               VALUES ($1, $2, $3, 'Pilot', 'trial', $4)
                               ON CONFLICT (id) DO NOTHING""",
                            demo_clinic_id, 'Demo Clinic', doctor_id, now
                        )
                        await conn.execute(
                            "INSERT INTO clinic_members (clinic_id, user_id, role) VALUES ($1, $2, 'owner') ON CONFLICT DO NOTHING",
                            demo_clinic_id, doctor_id
                        )
                        await conn.execute(
                            "INSERT INTO clinic_members (clinic_id, user_id, role) VALUES ($1, $2, 'member') ON CONFLICT DO NOTHING",
                            demo_clinic_id, assistant_id
                        )
        finally:
            await pool.release(conn)
    else:
        _DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(SQLITE_CREATE_SESSIONS_TABLE)
            await db.execute(SQLITE_CREATE_USERS_TABLE)
            await db.execute(SQLITE_CREATE_CONSENT_LOGS_TABLE)
            await db.execute(SQLITE_CREATE_SOAP_FEEDBACK_TABLE)
            await db.execute(SQLITE_CREATE_DOCTOR_PROFILES_TABLE)
            await db.execute(SQLITE_CREATE_PATIENT_MEMORY_TABLE)
            await db.execute(SQLITE_CREATE_EXTRACTION_KNOWLEDGE_TABLE)
            await db.execute(SQLITE_CREATE_FACT_CORRECTIONS_TABLE)
            await db.execute(SQLITE_CREATE_ASSISTANT_TASKS_TABLE)
            await db.execute(SQLITE_CREATE_MIGRATIONS_TABLE)
            await db.execute(SQLITE_CREATE_AUDIT_LOGS_TABLE)
            await db.execute(SQLITE_CREATE_CLINICS_TABLE)
            await db.execute(SQLITE_CREATE_CLINIC_MEMBERS_TABLE)
            await db.execute(SQLITE_CREATE_USAGE_EVENTS_TABLE)
            await db.execute(SQLITE_CREATE_BILLING_RECORDS_TABLE)
            await db.execute(SQLITE_CREATE_CONSULTATION_BILLING_TABLE)
            await db.execute(SQLITE_CREATE_TOKEN_BLACKLIST_TABLE)
            await db.execute(SQLITE_CREATE_PATIENTS_TABLE)
            await db.execute(SQLITE_CREATE_FOLLOW_UP_REMINDERS_TABLE)
            await db.execute(SQLITE_CREATE_PATIENT_INTERACTIONS_TABLE)
            await db.execute(SQLITE_CREATE_LAB_DISPATCH_LOG_TABLE)
            await db.execute(SQLITE_CREATE_DHIS_TRANSACTIONS_TABLE)
            await db.execute(SQLITE_CREATE_PATIENT_INTAKE_TABLE)
            await db.execute(SQLITE_CREATE_APPOINTMENTS_TABLE)
            await db.execute(SQLITE_CREATE_PRE_VISIT_FORMS_TABLE)
            await db.execute(SQLITE_CREATE_DOCTOR_AVAILABILITY_TABLE)
            for stmt in SQLITE_MIGRATIONS:
                try:
                    await db.execute(stmt)
                except aiosqlite.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        raise
            
            # Admin seeding
            if settings.shruti_admin_user and settings.shruti_admin_password:
                async with db.execute("SELECT id FROM users WHERE username = ?", (settings.shruti_admin_user,)) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        from app.utils.security import get_password_hash
                        hashed_pw = get_password_hash(settings.shruti_admin_password)
                        await db.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name) VALUES (?, ?, ?, ?)",
                            (settings.shruti_admin_user, f"{settings.shruti_admin_user}@example.com", hashed_pw, "Administrator")
                        )
            
            # Demo user seeding (Gated behind SEED_DEMO_USER=true)
            if settings.seed_demo_user and settings.demo_username and settings.demo_password:
                async with db.execute("SELECT id FROM users WHERE username = ?", (settings.demo_username,)) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        from app.utils.security import get_password_hash
                        hashed_pw = get_password_hash(settings.demo_password)
                        await db.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name, role) VALUES (?, ?, ?, ?, ?)",
                            (settings.demo_username, f"{settings.demo_username}@example.com", hashed_pw, settings.demo_full_name, "doctor")
                        )

            # Demo assistant seeding (always present for demo/dev)
            async with db.execute("SELECT id FROM users WHERE username = ?", ("meena",)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    from app.utils.security import get_password_hash
                    hashed_pw = get_password_hash("1234")
                    await db.execute(
                        "INSERT INTO users (username, email, hashed_password, full_name, role) VALUES (?, ?, ?, ?, ?)",
                        ("meena", "meena@example.com", hashed_pw, "Meena (Assistant)", "assistant")
                    )

            await db.commit()

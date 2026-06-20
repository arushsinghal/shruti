from pathlib import Path
import aiosqlite
import logging
import contextlib
import sys

from app.utils.config import settings

logger = logging.getLogger(__name__)

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
    pmjay_beneficiary INTEGER DEFAULT 0
);
"""

PG_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1
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
    pmjay_beneficiary INTEGER DEFAULT 0
);
"""

SQLITE_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1
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

SQLITE_MIGRATIONS = [
    "ALTER TABLE sessions ADD COLUMN audio_file_path TEXT",
    "ALTER TABLE sessions ADD COLUMN cloud_ai_consent INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN diarized_transcript TEXT",
    "ALTER TABLE sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'health'",
    "ALTER TABLE sessions ADD COLUMN user_id TEXT",
    "ALTER TABLE sessions ADD COLUMN abha_number TEXT",
    "ALTER TABLE sessions ADD COLUMN pmjay_beneficiary INTEGER DEFAULT 0",
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
            
            # For PostgreSQL, check if query is an INSERT to return ID
            if "INSERT INTO" in self.query.upper():
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
    def __init__(self, conn, is_pg: bool):
        self.conn = conn
        self.is_pg = is_pg
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
            if exc_type is not None:
                await self.tx.rollback()
            else:
                await self.tx.commit()
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
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        db_conn = DBConnection(conn, is_pg=True)
        await db_conn.__aenter__()
        try:
            yield db_conn
        except Exception:
            await db_conn.__aexit__(*sys.exc_info())
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
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        try:
            async with conn.transaction():
                await conn.execute(PG_CREATE_SESSIONS_TABLE)
                await conn.execute(PG_CREATE_USERS_TABLE)
                await conn.execute(PG_CREATE_CONSENT_LOGS_TABLE)
                await conn.execute(PG_CREATE_SOAP_FEEDBACK_TABLE)
                
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
                    row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", settings.demo_username)
                    if not row:
                        from app.utils.security import get_password_hash
                        hashed_pw = get_password_hash(settings.demo_password)
                        await conn.execute(
                            "INSERT INTO users (username, email, hashed_password, full_name) VALUES ($1, $2, $3, $4)",
                            settings.demo_username, f"{settings.demo_username}@example.com", hashed_pw, settings.demo_full_name
                        )
        finally:
            await conn.close()
    else:
        _DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.execute(SQLITE_CREATE_SESSIONS_TABLE)
            await db.execute(SQLITE_CREATE_USERS_TABLE)
            await db.execute(SQLITE_CREATE_CONSENT_LOGS_TABLE)
            await db.execute(SQLITE_CREATE_SOAP_FEEDBACK_TABLE)
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
                            "INSERT INTO users (username, email, hashed_password, full_name) VALUES (?, ?, ?, ?)",
                            (settings.demo_username, f"{settings.demo_username}@example.com", hashed_pw, settings.demo_full_name)
                        )
            
            await db.commit()

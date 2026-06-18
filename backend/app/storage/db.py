from pathlib import Path

import aiosqlite

from app.utils.config import settings

# Always resolve relative to the backend/ directory so the path is stable
# regardless of the working directory uvicorn is launched from.
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = Path(settings.data_dir) if settings.data_dir else _BACKEND_DIR
_DB_FILE = Path(settings.sqlite_db) if Path(settings.sqlite_db).is_absolute() else _DATA_DIR / settings.sqlite_db
_DB_PATH = str(_DB_FILE)

CREATE_SESSIONS_TABLE = """
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
    user_id TEXT
);
"""

_MIGRATIONS = [
    "ALTER TABLE sessions ADD COLUMN audio_file_path TEXT",
    "ALTER TABLE sessions ADD COLUMN cloud_ai_consent INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN diarized_transcript TEXT",
    "ALTER TABLE sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'health'",
    "ALTER TABLE sessions ADD COLUMN user_id TEXT",
]


CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1
);
"""

async def init_db() -> None:
    _DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(CREATE_SESSIONS_TABLE)
        await db.execute(CREATE_USERS_TABLE)
        for stmt in _MIGRATIONS:
            try:
                await db.execute(stmt)
            except aiosqlite.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
        await db.commit()


def get_db_path() -> str:
    return _DB_PATH

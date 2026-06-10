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
    audio_file_path TEXT,
    transcript TEXT,
    clinical_facts TEXT,
    memory_state TEXT,
    soap_note TEXT,
    cds_suggestions TEXT,
    cloud_ai_consent INTEGER DEFAULT 0,
    diarized_transcript TEXT
);
"""

_MIGRATIONS = [
    "ALTER TABLE sessions ADD COLUMN audio_file_path TEXT",
    "ALTER TABLE sessions ADD COLUMN cloud_ai_consent INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN diarized_transcript TEXT",
]


async def init_db() -> None:
    _DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(CREATE_SESSIONS_TABLE)
        for stmt in _MIGRATIONS:
            try:
                await db.execute(stmt)
            except Exception:
                pass  # column already exists
        await db.commit()


def get_db_path() -> str:
    return _DB_PATH

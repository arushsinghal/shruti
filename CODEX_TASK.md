# Codex Task — Lipi Backend + Frontend Hardening (47 items)

## Project overview

**Lipi** is an OPD administration service for Indian clinics. It records doctor-patient consultations, transcribes via Sarvam cloud ASR, and extracts clinical facts using a zero-LLM deterministic Python pipeline. It produces SOAP notes, investigation orders, and prescriptions. Stack: FastAPI + aiosqlite + Python 3.11 backend, React + TypeScript + Vite frontend.

Project root: `/Users/arushsinghal/Documents/clinical-decision-support-system/`

---

## CRITICAL CONSTRAINTS — read before touching any file

1. **Never add any LLM or generative model call to the clinical extraction pipeline.** The zero-LLM extraction is the product moat. Do not import `ollama`, `openai`, `anthropic`, or `gemini` into any file that handles transcript → clinical facts → SOAP.
2. **Never modify** `clinical_extractor.py`, `cds_engine.py`, `clinical_pipeline.py`, `soap_generator.py`, `memory_service.py`, `routes_notes.py`, `llm_client.py`. These are off-limits for this task.
3. **Never hardcode secrets.** All credentials must come from `settings` (pydantic-settings via `.env`).
4. **Schema is SQLite + PostgreSQL dual-target.** Every new table must have both a `SQLITE_CREATE_*` and `PG_CREATE_*` variant in `backend/app/storage/db.py`, and must be called in both branches of `init_db()`.
5. **Follow the existing code pattern exactly.** Read the file before editing it. Match the imports, spacing, naming, and async patterns already used.

---

## Already done — do NOT redo these

The following fixes were already applied in a prior session. Do not touch these files for these purposes:

- `backend/app/utils/config.py` — `allow_stub_asr`, `twilio_account_sid`, `twilio_auth_token`, `twilio_whatsapp_number`, `public_rate_limit_max_attempts`, `public_rate_limit_window_seconds` are already added
- `backend/app/services/sarvam_asr.py` — ASR stub gate already added
- `backend/app/services/whatsapp_service.py` — PHI redacted from all logs already
- `backend/app/services/phi_scrubber.py` — `_INDIAN_PHONE_REGEX`, `_AADHAAR_REGEX`, `_ABHA_REGEX` already added
- `backend/app/api/routes_ws.py` — `_MAX_WS_BYTES = 100 * 1024 * 1024` cap already added
- `backend/app/api/routes_audio.py` — UUID filename (path traversal fix) already applied
- `backend/app/api/routes_auth.py` — `is_active` check already added
- `backend/app/api/routes_notes.py` — error message leak already fixed
- `backend/app/storage/repository.py` — `get_doctor_profile()` already added
- `render.yaml` — healthCheckPath already set to `/api/health`
- `Dockerfile` — frontend dist path already fixed

---

## Task list

Work through these in order. Each task specifies the exact file, what to add/change, and any constraints.

---

### BLOCK A — Frontend TypeScript build fixes
*Goal: `cd frontend && npm run build` must exit 0.*

#### A1. `frontend/src/types/clinical.ts` — add missing types

At the end of the file, append:

```typescript
export interface ExtractedFact {
  fact_id: string;
  field: string;
  value: string;
  source_span: string;
  review_status: 'candidate' | 'confirmed' | 'rejected';
  confirmed_by?: string;
  confirmed_at?: string;
}

export interface AuditLogEntry {
  id: number;
  session_id: string;
  user_id: string;
  action: string;
  detail?: string;
  timestamp: string;
}

export interface AssistantTask {
  id: string;
  session_id: string;
  task_type: string;
  title: string;
  status: 'open' | 'in_progress' | 'done' | 'blocked';
  owner?: string;
  due?: string;
  notes?: string;
  completed_at?: string;
}

export interface DoctorProfile {
  name?: string;
  mci_number?: string;
  clinic_name?: string;
  clinic_address?: string;
  clinic_phone?: string;
}
```

Also add `consent_log` field and `extracted_facts` field to existing interfaces:

In `ConsultationSession`, add after `cds_suggestions`:
```typescript
  consent_log?: {
    consent_mode: string;
    consent_text_version: string;
    consent_hash: string;
    timestamp: string;
  };
```

In `ProcessClinicalResponse`, add after `source`:
```typescript
  extracted_facts?: ExtractedFact[];
```

#### A2. `frontend/src/lib/api.ts` — add missing exports

First add the import at the top of the file (after existing type imports):
```typescript
import type {
  AuditLogEntry,
  AssistantTask,
  DoctorProfile,
  ExtractedFact,
} from '../types/clinical';
```

Then append these functions at the end of the file, following the exact same `client.get/post/put/patch` axios pattern already used:

```typescript
// ── Fact review ──────────────────────────────────────────────────────────────

export async function reviewExtractedFact(
  sessionId: string,
  factId: string,
  decision: { action: 'accept' | 'reject' | 'edit'; edited_value?: string }
): Promise<ExtractedFact> {
  const res = await client.put<ExtractedFact>(
    `/sessions/${sessionId}/facts/${factId}`,
    decision
  );
  return res.data;
}

export async function finalizeReviewedFacts(sessionId: string): Promise<{ confirmed: number }> {
  const res = await client.post<{ confirmed: number }>(
    `/sessions/${sessionId}/facts/finalize`
  );
  return res.data;
}

export async function updateFactsAndRegenerate(
  sessionId: string,
  facts: ExtractedFact[]
): Promise<ProcessClinicalResponse> {
  const res = await client.post<ProcessClinicalResponse>(
    `/sessions/${sessionId}/facts/regenerate`,
    { facts }
  );
  return res.data;
}

export async function submitExtractionFeedback(
  sessionId: string,
  feedback: { category: string; detail: string }
): Promise<{ ok: boolean }> {
  const res = await client.post<{ ok: boolean }>(
    `/sessions/${sessionId}/extraction-feedback`,
    feedback
  );
  return res.data;
}

// ── WhatsApp ──────────────────────────────────────────────────────────────────

export async function sharePrescriptionViaWhatsapp(
  sessionId: string,
  data: { phone_number: string; doctor_name: string }
): Promise<{ success: boolean; provider?: string; error?: string }> {
  const res = await client.post(
    `/sessions/${sessionId}/whatsapp`,
    data
  );
  return res.data;
}

export async function sendFollowUpReminder(
  sessionId: string,
  data: { phone_number: string; doctor_name: string; follow_up_text: string }
): Promise<{ success: boolean; error?: string }> {
  const res = await client.post(
    `/sessions/${sessionId}/follow-up`,
    data
  );
  return res.data;
}

// ── Audit logs ────────────────────────────────────────────────────────────────

export async function getAuditLogs(sessionId: string): Promise<AuditLogEntry[]> {
  const res = await client.get<AuditLogEntry[]>(`/sessions/${sessionId}/audit`);
  return res.data;
}

// ── Doctor profile ────────────────────────────────────────────────────────────

export async function getDoctorProfile(): Promise<DoctorProfile> {
  const res = await client.get<DoctorProfile>('/auth/doctor-profile');
  return res.data;
}

export async function updateDoctorProfile(data: DoctorProfile): Promise<DoctorProfile> {
  const res = await client.put<DoctorProfile>('/auth/doctor-profile', data);
  return res.data;
}

export async function completeOnboarding(data: {
  clinic_name: string;
  mci_number?: string;
}): Promise<{ ok: boolean }> {
  const res = await client.post<{ ok: boolean }>('/auth/onboarding/complete', data);
  return res.data;
}

// ── Public prescription portal ────────────────────────────────────────────────

export async function verifyPublicAccess(
  token: string,
  challenge: { initials: string; dob_year?: string }
): Promise<{ verified: boolean; session_id?: string }> {
  const res = await client.post(`/public/verify/${token}`, challenge);
  return res.data;
}

export async function getPublicPrescriptionHtml(token: string): Promise<string> {
  const res = await client.get<string>(`/public/prescription/${token}`, {
    responseType: 'text',
  });
  return res.data;
}

// ── Assistant tasks ───────────────────────────────────────────────────────────

export async function listTasks(filters?: { status?: string }): Promise<AssistantTask[]> {
  const params = filters?.status ? `?status=${filters.status}` : '';
  const res = await client.get<AssistantTask[]>(`/tasks${params}`);
  return res.data;
}

export async function updateTask(
  taskId: string,
  update: { status?: string; notes?: string; owner?: string }
): Promise<AssistantTask> {
  const res = await client.patch<AssistantTask>(`/tasks/${taskId}`, update);
  return res.data;
}
```

Also re-export `ProcessClinicalResponse` type at the bottom for any imports that pull from api.ts:
```typescript
export type { ProcessClinicalResponse } from '../types/clinical';
```

#### A3. `render.yaml` — fix CORS origins

Change:
```yaml
      - key: CORS_ORIGINS
        value: "http://localhost:5173,http://127.0.0.1:5173"
```
To:
```yaml
      - key: CORS_ORIGINS
        value: "http://localhost:5173,http://127.0.0.1:5173,https://lipi.onrender.com"
```

---

### BLOCK B — Database tables
*All new tables go in `backend/app/storage/db.py`. Add both PG and SQLite variants, call both in init_db().*

#### B1. Add `doctor_profiles` table

Add after the existing SOAP feedback table constants:

SQLite:
```python
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
```

PostgreSQL:
```python
PG_CREATE_DOCTOR_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS doctor_profiles (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    name TEXT,
    mci_number TEXT,
    clinic_name TEXT,
    clinic_address TEXT,
    clinic_phone TEXT,
    updated_at TEXT
);
"""
```

Call both in `init_db()` — in the PG branch: `await conn.execute(PG_CREATE_DOCTOR_PROFILES_TABLE)`. In the SQLite branch: `await db.execute(SQLITE_CREATE_DOCTOR_PROFILES_TABLE)`.

#### B2. Add `patient_memory` table

```python
SQLITE_CREATE_PATIENT_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS patient_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    patient_identifier TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, patient_identifier, memory_key)
);
"""

PG_CREATE_PATIENT_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS patient_memory (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    patient_identifier TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, patient_identifier, memory_key)
);
"""
```

Call both in `init_db()`.

#### B3. Add `extraction_knowledge` and `fact_corrections` tables

```python
SQLITE_CREATE_EXTRACTION_KNOWLEDGE_TABLE = """
CREATE TABLE IF NOT EXISTS extraction_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL,
    canonical TEXT NOT NULL,
    category TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    clinic_count INTEGER DEFAULT 1,
    promotion_status TEXT DEFAULT 'clinic_scoped',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(alias, category)
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

PG_CREATE_EXTRACTION_KNOWLEDGE_TABLE = """
CREATE TABLE IF NOT EXISTS extraction_knowledge (
    id SERIAL PRIMARY KEY,
    alias TEXT NOT NULL,
    canonical TEXT NOT NULL,
    category TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    clinic_count INTEGER DEFAULT 1,
    promotion_status TEXT DEFAULT 'clinic_scoped',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(alias, category)
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
```

Call all four in `init_db()`.

#### B4. Add `assistant_tasks` table

```python
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
```

Call both in `init_db()`.

#### B5. Add `applied_migrations` tracking table

```python
SQLITE_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applied_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    applied_at TEXT NOT NULL
);
"""

PG_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applied_migrations (
    id SERIAL PRIMARY KEY,
    version TEXT UNIQUE NOT NULL,
    applied_at TEXT NOT NULL
);
"""
```

Call both in `init_db()`.

---

### BLOCK C — Backend repository methods
*File: `backend/app/storage/repository.py`*

Read the file first. All new methods go inside the `SessionRepository` class, following the exact same `async with db_connect() as db` pattern.

#### C1. Add `log_usage_event` and `log_audit` methods

```python
async def log_usage_event(self, user_id: str, event_type: str, detail: Optional[str] = None) -> None:
    async with db_connect() as db:
        try:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "INSERT INTO audit_logs (session_id, user_id, action, detail, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("", user_id, event_type, detail or "", now),
            )
            await db.commit()
        except Exception:
            pass

async def log_audit(self, session_id: str, user_id: str, action: str, detail: Optional[str] = None) -> None:
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
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
            return [
                {"id": r[0], "session_id": r[1], "user_id": r[2], "action": r[3], "detail": r[4], "timestamp": r[5]}
                for r in rows
            ]
        except Exception:
            return []
```

Also add an `audit_logs` table to db.py:

```python
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
```

Call in `init_db()`.

#### C2. Add clinic repository methods

```python
async def ensure_default_clinic(self, user_id: str) -> dict:
    async with db_connect() as db:
        try:
            async with db.execute(
                "SELECT id, name FROM clinics WHERE owner_user_id = ? LIMIT 1", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1]}
            clinic_id = str(__import__("uuid").uuid4())
            now = __import__("datetime").datetime.utcnow().isoformat()
            await db.execute(
                "INSERT INTO clinics (id, name, owner_user_id, created_at) VALUES (?, ?, ?, ?)",
                (clinic_id, "My Clinic", user_id, now),
            )
            await db.commit()
            return {"id": clinic_id, "name": "My Clinic"}
        except Exception:
            return {"id": "", "name": ""}

async def get_clinic_members(self, clinic_id: str) -> list[dict]:
    async with db_connect() as db:
        try:
            async with db.execute(
                "SELECT user_id, role FROM clinic_members WHERE clinic_id = ?", (clinic_id,)
            ) as cursor:
                rows = await cursor.fetchall()
            return [{"user_id": r[0], "role": r[1]} for r in rows]
        except Exception:
            return []

async def update_clinic(self, clinic_id: str, user_id: str, name: str) -> dict:
    async with db_connect() as db:
        try:
            await db.execute(
                "UPDATE clinics SET name = ? WHERE id = ? AND owner_user_id = ?",
                (name, clinic_id, user_id),
            )
            await db.commit()
            return {"id": clinic_id, "name": name}
        except Exception:
            return {}

async def add_clinic_member(self, clinic_id: str, member_user_id: str, role: str = "member") -> bool:
    async with db_connect() as db:
        try:
            await db.execute(
                "INSERT OR REPLACE INTO clinic_members (clinic_id, user_id, role) VALUES (?, ?, ?)",
                (clinic_id, member_user_id, role),
            )
            await db.commit()
            return True
        except Exception:
            return False
```

Also add `clinics` and `clinic_members` tables to db.py:

```python
SQLITE_CREATE_CLINICS_TABLE = """
CREATE TABLE IF NOT EXISTS clinics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
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

PG_CREATE_CLINICS_TABLE = """
CREATE TABLE IF NOT EXISTS clinics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
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
```

Call all four in `init_db()`.

---

### BLOCK D — New API routes

#### D1. `backend/app/api/routes_tasks.py` — create new file

```python
"""Assistant task queue routes."""
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect

logger = logging.getLogger(__name__)
router = APIRouter()


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    owner: Optional[str] = None


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])
    async with db_connect() as db:
        if status:
            async with db.execute(
                "SELECT id, session_id, user_id, task_type, title, status, owner, due, notes, completed_at, created_at FROM assistant_tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status),
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT id, session_id, user_id, task_type, title, status, owner, due, notes, completed_at, created_at FROM assistant_tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
    return [
        {
            "id": r[0], "session_id": r[1], "user_id": r[2],
            "task_type": r[3], "title": r[4], "status": r[5],
            "owner": r[6], "due": r[7], "notes": r[8],
            "completed_at": r[9], "created_at": r[10],
        }
        for r in rows
    ]


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        async with db.execute(
            "SELECT id FROM assistant_tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        if update.status:
            completed_at = now if update.status == "done" else None
            await db.execute(
                "UPDATE assistant_tasks SET status = ?, completed_at = ? WHERE id = ?",
                (update.status, completed_at, task_id),
            )
        if update.notes is not None:
            await db.execute("UPDATE assistant_tasks SET notes = ? WHERE id = ?", (update.notes, task_id))
        if update.owner is not None:
            await db.execute("UPDATE assistant_tasks SET owner = ? WHERE id = ?", (update.owner, task_id))
        await db.commit()

        async with db.execute(
            "SELECT id, session_id, user_id, task_type, title, status, owner, due, notes, completed_at, created_at FROM assistant_tasks WHERE id = ?",
            (task_id,),
        ) as cursor:
            r = await cursor.fetchone()
    return {
        "id": r[0], "session_id": r[1], "user_id": r[2],
        "task_type": r[3], "title": r[4], "status": r[5],
        "owner": r[6], "due": r[7], "notes": r[8],
        "completed_at": r[9], "created_at": r[10],
    }
```

#### D2. `backend/app/api/routes_profile.py` — create new file

```python
"""Doctor profile routes."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.routes_auth import get_current_user
from app.storage.db import db_connect

logger = logging.getLogger(__name__)
router = APIRouter()


class DoctorProfileUpdate(BaseModel):
    name: Optional[str] = None
    mci_number: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None


@router.get("/auth/doctor-profile")
async def get_doctor_profile(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    async with db_connect() as db:
        try:
            async with db.execute(
                "SELECT name, mci_number, clinic_name, clinic_address, clinic_phone FROM doctor_profiles WHERE user_id = ?",
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
    }


@router.put("/auth/doctor-profile")
async def update_doctor_profile(
    data: DoctorProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["id"])
    now = datetime.utcnow().isoformat()
    async with db_connect() as db:
        await db.execute(
            """
            INSERT INTO doctor_profiles (user_id, name, mci_number, clinic_name, clinic_address, clinic_phone, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                mci_number = excluded.mci_number,
                clinic_name = excluded.clinic_name,
                clinic_address = excluded.clinic_address,
                clinic_phone = excluded.clinic_phone,
                updated_at = excluded.updated_at
            """,
            (user_id, data.name, data.mci_number, data.clinic_name, data.clinic_address, data.clinic_phone, now),
        )
        await db.commit()
    return {"ok": True}


@router.post("/auth/onboarding/complete")
async def complete_onboarding(
    data: DoctorProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    return await update_doctor_profile(data, current_user)
```

#### D3. `backend/app/api/routes_audit.py` — create new file

```python
"""Session audit log routes."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes_auth import get_current_user
from app.storage.repository import SessionRepository

logger = logging.getLogger(__name__)
router = APIRouter()
repo = SessionRepository()


@router.get("/sessions/{session_id}/audit")
async def get_session_audit(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await repo.get_session(session_id, str(current_user["id"]))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await repo.get_audit_logs(session_id)
```

#### D4. Mount new routers in `backend/app/main.py`

Read `main.py` first. Then import and mount the three new routers and also mount `routes_public` and `routes_clinics` (which already exist but aren't mounted). Add after the existing router includes:

```python
from app.api.routes_tasks import router as tasks_router
from app.api.routes_profile import router as profile_router
from app.api.routes_audit import router as audit_router
from app.api.routes_public import router as public_router
from app.api.routes_clinics import router as clinics_router

app.include_router(tasks_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(clinics_router, prefix="/api")
```

---

### BLOCK E — Security hardening

#### E1. Rate limiting — `backend/app/main.py` + affected route files

Add slowapi rate limiting. First check if `slowapi` is already in `pyproject.toml`. If not, add it.

In `main.py`, add:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

In `backend/app/api/routes_auth.py`, add `from slowapi import Limiter` and decorate the login and register endpoints:
```python
@router.post("/auth/token")
@limiter.limit("10/minute")
async def login(..., request: Request):
    ...

@router.post("/auth/register")  
@limiter.limit("5/minute")
async def register(..., request: Request):
    ...
```

Add `Request` to the function signatures where needed (import from `fastapi`).

In `backend/app/api/routes_audio.py`, decorate transcribe:
```python
@router.post("/sessions/{session_id}/transcribe", ...)
@limiter.limit("30/minute")
async def transcribe_audio(..., request: Request):
```

#### E2. WebSocket inactivity timeout — `backend/app/api/routes_ws.py`

The file already has `_MAX_WS_BYTES`. Add an inactivity timeout. In the `while True` receive loop, replace the bare `await websocket.receive()` with:

```python
import asyncio
try:
    message = await asyncio.wait_for(websocket.receive(), timeout=120.0)
except asyncio.TimeoutError:
    await websocket.send_json({"status": "error", "detail": "Stream timeout after 120s inactivity"})
    await websocket.close(code=4008)
    break
```

#### E3. Upload: stream to disk instead of full read into memory — `backend/app/api/routes_audio.py`

Currently the upload does `contents = await file.read()` followed by a size check. Replace with chunked streaming:

```python
dest_dir = _UPLOADS_DIR / session_id
dest_dir.mkdir(parents=True, exist_ok=True)
import uuid as _uuid
dest_path = dest_dir / f"{_uuid.uuid4().hex}{suffix}"

total = 0
with open(dest_path, "wb") as out:
    while chunk := await file.read(65536):
        total += len(chunk)
        if total > _MAX_UPLOAD_BYTES:
            out.close()
            dest_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Maximum is {_MAX_UPLOAD_BYTES // (1024*1024)} MB.",
            )
        out.write(chunk)
```

Remove the old `contents = await file.read()` and `dest_path.write_bytes(contents)` lines.

#### E4. Upload: MIME magic bytes validation — `backend/app/api/routes_audio.py`

After the suffix check, before writing the file, add:

```python
MAGIC_BYTES: dict[str, list[bytes]] = {
    ".mp3":  [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    ".wav":  [b"RIFF"],
    ".m4a":  [b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftyp"],
    ".webm": [b"\x1a\x45\xdf\xa3"],
}

header = await file.read(16)
await file.seek(0)
valid = False
for magic in MAGIC_BYTES.get(suffix, []):
    if header[:len(magic)] == magic:
        valid = True
        break
if not valid and suffix in MAGIC_BYTES:
    raise HTTPException(status_code=400, detail=f"File content does not match declared type '{suffix}'.")
```

Note: this requires `file.seek(0)` — check if `UploadFile` supports seek (it does via `file.file.seek(0)` on SpooledTemporaryFile). Use `await file.seek(0)` if the async interface is available, else `file.file.seek(0)`.

#### E5. Fix env mismatch — `render.yaml`

Change:
```yaml
      - key: LIPI_ADMIN_USER
        value: demo
      - key: LIPI_ADMIN_PASSWORD
        sync: false
```
To:
```yaml
      - key: SHRUTI_ADMIN_USER
        value: demo
      - key: SHRUTI_ADMIN_PASSWORD
        sync: false
```

Also check `backend/app/utils/config.py` — the settings field is already `shruti_admin_user`. The render.yaml env var key must match the pydantic-settings convention: `SHRUTI_ADMIN_USER` maps to `shruti_admin_user`.

#### E6. Fix `unique_clinics` counter — `backend/app/services/learning_service.py`

Read `learning_service.py`. Find where `unique_clinics` is tracked. If it's an integer being incremented, change it to store a set of clinic IDs as a JSON list and compute `len(set)` for the count. The goal is to never double-count the same clinic.

#### E7. Audio cleanup sweeper — `backend/app/main.py`

In the `lifespan` startup block (or wherever `init_db()` is called), add a background cleanup:

```python
import asyncio
from pathlib import Path

async def _cleanup_stale_audio():
    import time
    data_dir = Path(settings.data_dir) if settings.data_dir else Path(".")
    audio_dir = data_dir / "audio_uploads"
    cutoff = time.time() - 48 * 3600
    if audio_dir.exists():
        for f in audio_dir.glob("*_live.webm"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except Exception:
                pass
```

Call `asyncio.create_task(_cleanup_stale_audio())` in the lifespan startup.

---

### BLOCK F — CDS interactions
*File: `backend/app/services/cds_engine.py`*

Read the file. Find the drug-drug interaction table (search for `_DDI` or `drug_drug` or the dict where pairs like `("warfarin", "aspirin")` are defined). Add these three entries following the exact same format already used:

```python
# Warfarin + Metronidazole — INR elevation, major bleeding risk
("warfarin", "metronidazole"): {
    "severity": "high",
    "effect": "Metronidazole inhibits CYP2C9, significantly raising warfarin levels and bleeding risk.",
    "recommendation": "Monitor INR closely. Reduce warfarin dose by 25–50% if co-prescribing.",
},

# Metformin + Contrast CT — Lactic acidosis risk
("metformin", "contrast"): {
    "severity": "medium",
    "effect": "Iodinated contrast can cause acute kidney injury, impairing metformin clearance and raising lactic acidosis risk.",
    "recommendation": "Hold metformin 48h before contrast administration. Resume only after confirming renal function is stable.",
},

# Sildenafil + Nitroglycerin — Severe hypotension, absolute contraindication
("sildenafil", "nitroglycerin"): {
    "severity": "critical",
    "effect": "Both agents reduce preload. Combination causes profound, potentially fatal hypotension.",
    "recommendation": "ABSOLUTE CONTRAINDICATION. Do not co-prescribe. If patient takes nitrates in any form, sildenafil is contraindicated.",
},
```

If the table uses a different structure (e.g., list of dicts instead of dict of tuples), match whatever structure is already there.

---

### BLOCK G — FHIR improvements
*File: `backend/app/services/fhir_mapper.py`*

Read the file first.

#### G1. Add Composition resource

A FHIR Bundle of type `document` requires a Composition resource as the first entry. Find where the Bundle entries are assembled and prepend a Composition:

```python
composition = {
    "resourceType": "Composition",
    "id": f"comp-{session.id}",
    "status": "final",
    "type": {
        "coding": [{"system": "http://loinc.org", "code": "34133-9", "display": "Summary of episode note"}]
    },
    "subject": {"reference": f"Patient/{session.id}"},
    "date": session.created_at.isoformat() if hasattr(session.created_at, 'isoformat') else session.created_at,
    "author": [{"display": session.doctor_name or "Unknown Physician"}],
    "title": "OPD Consultation Note",
    "section": [{"title": "Clinical Note", "text": {"status": "generated", "div": "<div>See structured data</div>"}}],
}
```

Add it as the first entry in the Bundle's `entry` list:
```python
{"fullUrl": f"urn:uuid:comp-{session.id}", "resource": composition}
```

#### G2. Add proper LOINC/SNOMED coding

When building `Observation` resources for vitals, add a `code` field with LOINC codes:

Common vitals:
- Blood pressure: `{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}`
- Temperature: `{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}`
- Heart rate: `{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}`
- SpO2: `{"system": "http://loinc.org", "code": "59408-5", "display": "Oxygen saturation"}`
- Weight: `{"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"}`
- Height: `{"system": "http://loinc.org", "code": "8302-2", "display": "Body height"}`

For `Condition` resources (diagnoses), add:
```python
"code": {
    "coding": [{"system": "http://snomed.info/sct", "display": condition_text}],
    "text": condition_text,
}
```

For `AllergyIntolerance` resources, add:
```python
"code": {
    "coding": [{"system": "http://snomed.info/sct", "display": allergy_text}],
    "text": allergy_text,
}
```

---

### BLOCK H — Prescription renderer improvements
*File: `backend/app/services/prescription_renderer.py`*

Read the file. Make these additive changes:

#### H1. Schedule H/H1 indicator

Add a helper that classifies a medication name as Schedule H or H1:

```python
_SCHEDULE_H1_DRUGS = {
    "tramadol", "codeine", "buprenorphine", "fentanyl", "morphine",
    "oxycodone", "hydrocodone", "alprazolam", "diazepam", "clonazepam",
    "lorazepam", "zolpidem", "nitrazepam",
}
_SCHEDULE_H_KEYWORDS = {
    "antibiotic", "amoxicillin", "azithromycin", "ciprofloxacin",
    "metronidazole", "cefixime", "doxycycline", "cetirizine",
    "omeprazole", "pantoprazole", "metformin", "amlodipine",
    "atenolol", "atorvastatin", "losartan", "telmisartan",
}

def _schedule_label(med_name: str) -> str:
    name_lower = med_name.lower()
    if any(d in name_lower for d in _SCHEDULE_H1_DRUGS):
        return "Sch. H1"
    if any(d in name_lower for d in _SCHEDULE_H_KEYWORDS):
        return "Sch. H"
    return ""
```

In the HTML template for each medication line, append the schedule label after the drug name if non-empty.

#### H2. NMC registration display

In the doctor header section of the prescription HTML, add the MCI/NMC number if present in the doctor profile:
```html
<span class="mci">Reg. No.: {mci_number}</span>
```

#### H3. General professional polish

Add to the prescription HTML template:
- A legal disclaimer line at the bottom: `"This prescription is valid for 30 days from date of issue. For Schedule H/H1 drugs, valid for use in the state of issue only."`
- Ensure font is `Arial, sans-serif`, font-size `11pt`, margins `1cm` on all sides for print
- Add `@media print { body { margin: 1cm; } }` to the `<style>` block if not present

---

### BLOCK I — Investigation order HTML fix
*File: `backend/app/services/investigation_order_renderer.py`*

Read the file. Find any malformed HTML: unclosed tags, mismatched `<div>`, `<td>`, `<tr>` tags, or bare `&` characters not escaped as `&amp;`. Fix all of them. If a `<table>` exists without `<tbody>`, add it. Ensure every `<tr>` is inside a `<tbody>` or `<thead>`.

---

### BLOCK J — PHI scrubber additions
*File: `backend/app/services/phi_scrubber.py`*

Read the file first. `_INDIAN_PHONE_REGEX`, `_AADHAAR_REGEX`, and `_ABHA_REGEX` are already there. Add:

```python
_UHID_MRN_REGEX = re.compile(r'\b(?:UHID|MRN|UID|HN|PID)[:\s#-]*\d{4,12}\b', re.IGNORECASE)
_PIN_CODE_REGEX = re.compile(r'\b[1-9]\d{5}\b')
```

In `scrub()`, add after the existing redactions:
```python
text = _UHID_MRN_REGEX.sub("[REDACTED_ID]", text)
# PIN codes are contextual — only redact when preceded by an address keyword
text = re.sub(r'(?i)(?:pin\s*(?:code)?|pincode)[:\s]*([1-9]\d{5})', '[REDACTED_PIN]', text)
```

Do NOT add a broad 6-digit regex that would catch clinical values like dosages or CBC counts.

---

### BLOCK K — Copy and positioning fixes

#### K1. `frontend/src/pages/Landing.tsx` (or wherever the landing copy lives)

Find and change:
- Any text saying "no audio or document content transmitted to third-party cloud" → change to: "Audio is processed via Sarvam AI (India) cloud speech recognition with your explicit consent. Raw audio is deleted immediately after transcription."
- Any instance of "AI scribe" → "OPD administration service"

#### K2. Across all frontend `.tsx` files

Find all remaining instances of "AI scribe" and replace with "OPD administration service".
Find references to "government mode", "FIR report", "legal mode", "legal document" in navigation menus or dashboard landing UI — remove them from visible navigation but do not delete the underlying route files.

#### K3. Privacy/dashboard copy

Find where the app claims audio files are deleted after processing. Update to accurately reflect: "Raw audio is deleted after successful transcription. Files from incomplete or failed sessions may be retained up to 48 hours."

#### K4. README.md

Find any mention of "Ollama" as a feature or requirement. Remove it or note it as "removed — zero-LLM pipeline only." Find any claim that no data is sent to external services and update to accurately describe Sarvam cloud ASR.

#### K5. Add demotion API — `backend/app/api/routes_tasks.py` (add to the file created in D1) or create `backend/app/api/routes_learning.py`

```python
@router.delete("/learning/aliases/{alias_id}")
async def revoke_alias(
    alias_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Admin: revoke a promoted alias by setting its status to 'revoked'."""
    async with db_connect() as db:
        await db.execute(
            "UPDATE extraction_knowledge SET promotion_status = 'revoked' WHERE id = ?",
            (alias_id,),
        )
        await db.commit()
    return {"ok": True, "alias_id": alias_id}
```

Add this to `main.py` imports and mounts.

#### K6. WhatsApp Business API onboarding doc — `docs/whatsapp_setup.md`

Create a markdown file with:
- Step 1: Create a Twilio account at twilio.com
- Step 2: Activate the WhatsApp Sandbox (for demo/pilot)
- Step 3: Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` in `.env`
- Step 4: For production (post-YC), apply for WhatsApp Business API approval through Twilio
- Step 5: The sender number must be `whatsapp:+1415XXXXXXX` format (Twilio adds the prefix if missing)
- Note: In demo mode with no Twilio keys, the system logs "MOCK WHATSAPP" without sending anything

---

## Verification checklist

After all changes, run these in order:

```bash
# 1. Backend: check imports and startup
cd /Users/arushsinghal/Documents/clinical-decision-support-system/backend
python -m py_compile app/storage/db.py
python -m py_compile app/storage/repository.py
python -m py_compile app/api/routes_tasks.py
python -m py_compile app/api/routes_profile.py
python -m py_compile app/api/routes_audit.py
python -m py_compile app/main.py

# 2. Frontend: TypeScript build must exit 0
cd /Users/arushsinghal/Documents/clinical-decision-support-system/frontend
npm run build

# 3. Backend tests (ignore pre-existing failures in test_extraction_reliability.py)
cd /Users/arushsinghal/Documents/clinical-decision-support-system/backend
python -m pytest tests/ --ignore=tests/test_extraction_reliability.py -x -q 2>&1 | tail -20
```

If `npm run build` still fails, read the error output carefully — it will name the exact missing type or export. Fix only what the error names.

If a pytest test fails that was previously passing, investigate before moving on. Do not mask test failures by deleting tests.

---

## What NOT to do

- Do not modify `clinical_extractor.py`, `cds_engine.py`, `clinical_pipeline.py`, `soap_generator.py`, `memory_service.py`, `routes_notes.py`, `llm_client.py`, `ollama_extractor.py`
- Do not add any `import openai`, `import anthropic`, `import ollama`, `import google.generativeai` to any file
- Do not change the authentication logic in `routes_auth.py` beyond adding rate limiting decorators
- Do not delete any existing tests
- Do not change the SQLite WAL mode settings or connection pooling
- Do not change how `_row_to_session` maps DB rows — add columns only at the end of `_SELECT` and `_row_to_session`

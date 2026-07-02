"""
Lipi - Multilingual Clinical Documentation 
Research Prototype

Developed to study computational challenges in 
low-resource, multilingual clinical settings in India.

Research context: Rural India doctor:patient ratio 
crisis (1:1,457), Hindi/Hinglish clinical NLP, 
offline-first edge deployment.

NOT a certified medical device. Research use only.
"""

import asyncio
import logging
import logging.config
import os
import base64
import secrets
import time
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import FastAPI, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes_auth import router as auth_router
from app.api.routes_auth import get_current_user
from app.api.routes_audio import router as audio_router
from app.api.routes_health import router as health_router
from app.api.routes_sessions import router as sessions_router
from app.api.routes_notes import router as notes_router
from app.api.routes_fact_review import router as fact_review_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_ws import router as ws_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_profile import router as profile_router
from app.api.routes_audit import router as audit_router
from app.api.routes_public import router as public_router
from app.api.routes_clinics import router as clinics_router
from app.api.routes_learning import router as learning_router
from app.api.routes_whatsapp import router as whatsapp_router
from app.api.routes_documents import router as documents_router
from app.api.routes_billing import router as billing_router
from app.api.routes_reviewer import router as reviewer_router
from app.api.routes_tpa import router as tpa_router
from app.storage.db import init_db
from app.utils.config import settings
from app.utils.rate_limit import SLOWAPI_AVAILABLE, RateLimitExceeded, _rate_limit_exceeded_handler, limiter

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s - %(message)s")
logger = logging.getLogger(__name__)


async def _retention_loop() -> None:
    """Task 40: Create follow-up assistant_tasks at day 30 and day 90 after consultation."""
    import uuid as _uuid_mod
    from datetime import timedelta
    from app.storage.db import db_connect
    while True:
        await asyncio.sleep(86400)
        try:
            now = datetime.utcnow()
            async with db_connect() as db:
                for days in (30, 90):
                    window_start = (now - timedelta(days=days, hours=12)).isoformat()
                    window_end = (now - timedelta(days=days - 1)).isoformat()
                    async with db.execute(
                        "SELECT id, user_id FROM sessions WHERE status = 'complete' "
                        "AND created_at >= ? AND created_at <= ?",
                        (window_start, window_end),
                    ) as cur:
                        sessions_due = await cur.fetchall()
                    for s_row in sessions_due:
                        s_id, u_id = s_row[0], str(s_row[1])
                        task_type = f"retention_followup_{days}d"
                        async with db.execute(
                            "SELECT 1 FROM assistant_tasks WHERE session_id = ? AND task_type = ?",
                            (s_id, task_type),
                        ) as chk:
                            if await chk.fetchone():
                                continue
                        await db.execute(
                            "INSERT INTO assistant_tasks (id, session_id, user_id, task_type, title, status, created_at) "
                            "VALUES (?, ?, ?, ?, ?, 'open', ?)",
                            (
                                str(_uuid_mod.uuid4()), s_id, u_id, task_type,
                                f"Day-{days} follow-up check for patient",
                                now.isoformat(),
                            ),
                        )
                await db.commit()
            logger.info("Retention loop: created day-30/90 follow-up tasks")
        except Exception as exc:
            logger.warning("Retention loop error (non-fatal): %s", exc)


async def _cleanup_stale_audio() -> None:
    data_dir = Path(settings.data_dir) if settings.data_dir else Path(".")
    audio_dir = data_dir / "audio_uploads"
    cutoff = time.time() - 48 * 3600
    if not audio_dir.exists():
        return
    for file_path in audio_dir.glob("*_live.webm"):
        try:
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.services.clinical_extractor import async_reload_knowledge
    from app.services.follow_up_scheduler import follow_up_reminder_loop
    from app.services.monthly_report import monthly_report_loop
    await async_reload_knowledge()
    asyncio.create_task(_cleanup_stale_audio())
    asyncio.create_task(_retention_loop())
    asyncio.create_task(follow_up_reminder_loop())
    asyncio.create_task(monthly_report_loop())
    logger.info("ASR configuration verified. Key loaded: %s", "yes" if settings.sarvam_api_key else "NO")
    yield


app = FastAPI(title="Lipi - Multilingual Clinical Documentation Platform", version="0.1.0", lifespan=lifespan)

if SLOWAPI_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = settings.allowed_origins or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.ngrok.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

# Protected Routes
protected_dependencies = [Depends(get_current_user)]
app.include_router(sessions_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(audio_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(fact_review_router, prefix="/api")
app.include_router(notes_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(analytics_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(ws_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(tasks_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(clinics_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
# WhatsApp inbound webhook — no JWT auth (Twilio calls this directly)
app.include_router(whatsapp_router, prefix="/api")
app.include_router(documents_router, prefix="/api", dependencies=protected_dependencies)
# Billing: status + webhook (webhook is public — Razorpay calls it directly)
app.include_router(billing_router, prefix="/api")
app.include_router(reviewer_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(tpa_router, prefix="/api", dependencies=protected_dependencies)

# Serve the built React frontend from backend/dist/
_DIST = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(os.path.join(_DIST, "favicon.svg"))

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """Catch-all: serve index.html for any non-API route (SPA client-side routing)."""
        index = os.path.join(_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return Response(content="Frontend not built. Run: cd frontend && npm run build", status_code=503)
else:
    logger.warning("Frontend dist not found at %s — run 'cd frontend && npm run build'", _DIST)

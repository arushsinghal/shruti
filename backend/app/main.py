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

import logging
import logging.config
import os
import base64
import secrets
from contextlib import asynccontextmanager
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
from app.api.routes_analytics import router as analytics_router
from app.api.routes_ws import router as ws_router
from app.storage.db import init_db
from app.utils.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("ASR configuration verified. Key loaded: %s", "yes" if settings.sarvam_api_key else "NO")
    yield


app = FastAPI(title="Lipi - Multilingual Clinical Documentation Platform", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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
app.include_router(notes_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(analytics_router, prefix="/api", dependencies=protected_dependencies)
app.include_router(ws_router, prefix="/api", dependencies=protected_dependencies)

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

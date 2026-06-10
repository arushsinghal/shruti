"""
SHRUTI - Multilingual Clinical Documentation 
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

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
    logger.info("Language model configuration verified. Key loaded: %s", "yes" if settings.gemini_api_key else "NO")
    yield


app = FastAPI(title="SHRUTI - Multilingual Clinical Documentation Platform", version="0.1.0", lifespan=lifespan)


_PUBLIC_EXACT_PATHS = {
    "/",
    "/about",
    "/health",
    "/favicon.svg",
    "/icons.svg",
    "/rural_doctor_hero.png",
    "/shruti_app_mockup.png",
}
_PUBLIC_PREFIXES = ("/assets/",)
_PROTECTED_PREFIXES = (
    "/analytics",
    "/consultation",
    "/dashboard",
    "/review",
    "/sessions",
)


def _auth_required(path: str) -> bool:
    if not settings.shruti_admin_password:
        return False
    if path in _PUBLIC_EXACT_PATHS:
        return False
    if any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def _unauthorized() -> Response:
    return Response(
        "Authentication required",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="SHRUTI Demo"'},
    )


def _has_valid_basic_auth(header: str | None) -> bool:
    if not header or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header.removeprefix("Basic ").strip()).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return False

    return secrets.compare_digest(username, settings.shruti_admin_user) and secrets.compare_digest(
        password,
        settings.shruti_admin_password,
    )


@app.middleware("http")
async def protect_demo_console(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    if request.method == "OPTIONS" or not _auth_required(request.url.path):
        return await call_next(request)

    if not _has_valid_basic_auth(request.headers.get("authorization")):
        return _unauthorized()

    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(audio_router)
app.include_router(notes_router)
app.include_router(analytics_router)
app.include_router(ws_router)

# Serve static files and fallback to index.html for Single Page App routing
dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist")
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Ignore websocket paths or API base paths if they fall through
        if catchall.startswith("ws/") or catchall.startswith("api/"):
            return Response(status_code=404, content="Not Found")
            
        file_path = os.path.join(dist_dir, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return Response(status_code=404, content="Not Found")

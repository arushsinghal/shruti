from datetime import datetime, timezone

from fastapi import APIRouter

from app.utils.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Returns health check status for system uptime monitoring. Research prototype only — output requires physician review."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

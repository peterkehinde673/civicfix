from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """System health check and runtime capabilities status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "demo_mode": settings.DEMO_MODE,
        "mock_firestore": settings.MOCK_FIRESTORE,
        "gemini_model": settings.GEMINI_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

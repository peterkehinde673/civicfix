from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.api.orchestrator import router as orchestrator_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_SUBTITLE,
    version="0.3.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# Static files and templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")

# Include Routers
app.include_router(health_router)
app.include_router(cases_router)
app.include_router(orchestrator_router)


@app.get("/", tags=["Frontend"])
async def render_dashboard(request: Request):
    """Render the main CivicFix dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "app_subtitle": settings.APP_SUBTITLE,
        },
    )

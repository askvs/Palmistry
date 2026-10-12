from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(db: Session = Depends(get_db)) -> HealthResponse:
    # Run real DB and AI provider checks.
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    ai_provider = "configured" if settings.GROQ_API_KEY else "not_configured"
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        database=database,
        ai_provider=ai_provider,
    )

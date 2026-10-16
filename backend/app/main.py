from contextlib import asynccontextmanager

try:
    import matplotlib

    matplotlib.use("Agg")
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.auth.errors import AuthError
from app.config import settings
from app.middleware.monitoring import ErrorMonitoringMiddleware
from app.middleware.request_context import RequestContextMiddleware, get_request_id
from app.services.admin.service import AdminError
from app.services.assistant import AssistantError
from app.services.notifications.scheduler import start_scheduler
from app.services.booking.errors import BookingError
from app.services.booking.scheduler import start_booking_scheduler
from app.services.consultation.service import ConsultationError
from app.services.interpretation.engine import InterpretationError
from app.services.palm_analysis.preprocessor import PalmValidationError
from app.services.personality.service import PersonalityError
from app.services.profile.errors import ProfileError
from app.services.recommendations.engine import RecommendationEngineError
from app.services.recommendations.service import RecommendationServiceError
from app.services.reading.service import ReadingError
from app.services.tarot.interpretation import TarotInterpretationError
from app.services.tarot.custom_spreads import CustomSpreadError
from app.utils.logging import configure_logging, logger

# Shared handler for all domain errors.
DOMAIN_ERRORS = (
    AuthError,
    ProfileError,
    ReadingError,
    TarotInterpretationError,
    CustomSpreadError,
    PalmValidationError,
    InterpretationError,
    ConsultationError,
    AdminError,
    PersonalityError,
    RecommendationEngineError,
    RecommendationServiceError,
    AssistantError,
    BookingError,
)


async def domain_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": get_request_id(),
        },
    )


def _error_cors_headers(request: Request) -> dict:
    """CORS headers for error responses sent outside CORSMiddleware."""
    origin = request.headers.get("origin")
    if origin and origin in settings.CORS_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Expose-Headers": "X-Request-ID",
        }
    return {}


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled exception request_id=%s", get_request_id())
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": get_request_id(),
        },
        headers=_error_cors_headers(request),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("startup environment=%s version=%s", settings.ENVIRONMENT, settings.APP_VERSION)

    # Start background schedulers (lifespan takes precedence over on_event).
    from app.db.session import get_db

    db = next(get_db())
    try:
        start_scheduler(db)
        # Booking reminders, slot rollout, and session auto-completion.
        start_booking_scheduler(db)
    finally:
        db.close()

    yield

    logger.info("shutdown")

    # Persist any API latency samples still buffered in the monitoring middleware.
    from app.middleware.monitoring import flush_samples

    flush_samples()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    # Outermost user middleware so it also sees failures from inner layers.
    app.add_middleware(ErrorMonitoringMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "request_id": get_request_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "request_id": get_request_id(),
                "fields": [
                    {"loc": list(err.get("loc", [])), "msg": err.get("msg", "")}
                    for err in exc.errors()
                ],
            },
        )

    for error_cls in DOMAIN_ERRORS:
        app.add_exception_handler(error_cls, domain_error_handler)

    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", include_in_schema=False)
    async def root_health():
        return {"status": "ok"}

    return app


app = create_app()

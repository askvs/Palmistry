from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    assistant,
    auth,
    booking,
    consultations,
    health,
    interpretation,
    life_trends,
    notifications,
    palm,
    personality,
    portals,
    profile,
    reader,
    readings,
    recommendations,
    reports,
    tarot,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(notifications.router, tags=["notifications"])
api_router.include_router(portals.router, tags=["auth"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(palm.router, tags=["palm"])
api_router.include_router(tarot.router, tags=["tarot"])
api_router.include_router(readings.router, tags=["readings"])
api_router.include_router(readings.reader_router, tags=["reader"])
api_router.include_router(reader.reader_router, tags=["reader"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(consultations.router, tags=["consultations"])
api_router.include_router(consultations.consultant_router, tags=["consultant"])
api_router.include_router(admin.admin_router, tags=["admin"])
api_router.include_router(interpretation.router, tags=["interpretation"])
api_router.include_router(personality.router, tags=["personality"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(life_trends.router, tags=["life-trends"])
api_router.include_router(assistant.router, tags=["assistant"])
# Live consultation & booking module (independent of the palm/tarot flows).
api_router.include_router(booking.consultants, tags=["consultants"])
api_router.include_router(booking.consultant, tags=["consultant-studio"])
api_router.include_router(booking.bookings, tags=["bookings"])

"""Admin endpoints (FR-007)."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminReadingListOut,
    AdminUserListOut,
    AdminUserOut,
    AdminUserUpdate,
    AuditLogListOut,
    AuditLogOut,
    AuthSettingsOut,
    ErrorLogListOut,
    ErrorLogOut,
    ErrorStatsOut,
    PerformanceSummaryOut,
    PermissionMatrixOut,
    PlatformAnalytics,
    ReadingStatistics,
    SessionOversight,
    SystemConfigOut,
    SystemReportOut,
)
from app.schemas.consultation import ConsultationListOut, ConsultationOut
from app.services import admin as admin_service
from app.services import consultation as consultation_service

admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_admin)],
)


# User management


@admin_router.get("/users", response_model=AdminUserListOut)
async def list_users(
    role: UserRole | None = None,
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = admin_service.list_users(db, role=role, search=search, limit=limit, offset=offset)
    return AdminUserListOut(items=[AdminUserOut.model_validate(u) for u in items], total=total)


@admin_router.get("/users/{user_id}", response_model=AdminUserOut)
async def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return AdminUserOut.model_validate(admin_service.get_user(db, user_id))


@admin_router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    target = admin_service.get_user(db, user_id)
    updated = admin_service.update_user(
        db, target, payload.model_dump(exclude_unset=True), actor=admin
    )
    return AdminUserOut.model_validate(updated)


# Platform analytics & statistics

@admin_router.get("/readings", response_model=AdminReadingListOut)
async def platform_readings(
    type: str | None = Query(default=None, max_length=50),
    status: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Reading oversight: every platform reading with its owner, newest first (FR-007)."""
    items, total = admin_service.list_all_readings(
        db, type_filter=type, status_filter=status, limit=limit, offset=offset
    )
    return AdminReadingListOut(items=items, total=total)


@admin_router.get("/analytics/platform", response_model=PlatformAnalytics)
async def platform_analytics(
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return PlatformAnalytics(**admin_service.platform_analytics(db, days=days))


@admin_router.get("/analytics/readings", response_model=ReadingStatistics)
async def reading_statistics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return ReadingStatistics(**admin_service.reading_statistics(db, days=days))


@admin_router.get("/consultations", response_model=ConsultationListOut)
async def all_consultations(db: Session = Depends(get_db)):
    items, total = consultation_service.list_queue(db)
    return ConsultationListOut(
        items=[ConsultationOut.model_validate(c) for c in items],
        total=total,
    )


# Reports & audit


@admin_router.post("/reports/system", response_model=SystemReportOut, status_code=201)
async def generate_system_report(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    return SystemReportOut(**admin_service.system_report(db, admin))


@admin_router.get("/audit-logs", response_model=AuditLogListOut)
async def audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = admin_service.list_audit_logs(db, limit=limit, offset=offset)
    return AuditLogListOut(
        items=[AuditLogOut.model_validate(a) for a in items],
        total=total,
    )


# Session oversight (read-only)


@admin_router.get("/analytics/sessions", response_model=SessionOversight)
async def session_oversight(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Read-only session statistics: how many sessions are scheduled and what."""
    return SessionOversight(**admin_service.session_oversight(db, days=days))


# Access & permissions


@admin_router.get("/permissions", response_model=PermissionMatrixOut)
async def permissions():
    """The live RBAC matrix (§49.3) explained for the console."""
    return PermissionMatrixOut(**admin_service.permission_matrix())


# Authentication & system configuration


@admin_router.get("/settings/auth", response_model=AuthSettingsOut)
async def authentication_settings():
    """Authentication posture (token policy, cookies, OAuth, rate limits)."""
    return AuthSettingsOut(**admin_service.auth_settings())


@admin_router.get("/settings/system", response_model=SystemConfigOut)
async def system_configuration(db: Session = Depends(get_db)):
    """Deployment-shaped view of the running configuration and release."""
    return SystemConfigOut(**admin_service.system_config(db))


# Errors, security events & performance


@admin_router.get("/errors", response_model=ErrorLogListOut)
async def list_errors(
    level: str | None = Query(default=None, pattern="^(error|security)$"),
    kind: str | None = Query(default=None, max_length=40),
    unresolved_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = admin_service.list_errors(
        db,
        level=level,
        kind=kind,
        unresolved_only=unresolved_only,
        limit=limit,
        offset=offset,
    )
    unresolved = sum(1 for i in items if i["acknowledged_at"] is None)
    return ErrorLogListOut(
        items=[ErrorLogOut.model_validate(i) for i in items],
        total=total,
        unresolved=unresolved,
    )


@admin_router.get("/errors/stats", response_model=ErrorStatsOut)
async def error_statistics(
    hours: int = Query(default=24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    return ErrorStatsOut(**admin_service.error_stats(db, hours=hours))


@admin_router.post("/errors/{error_id}/acknowledge", status_code=204)
async def acknowledge_error(
    error_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    admin_service.acknowledge_error(db, error_id, actor=admin)
    return None


@admin_router.get("/system/performance", response_model=PerformanceSummaryOut)
async def performance_summary():
    return PerformanceSummaryOut(**admin_service.performance_summary())

"""Admin service: user management, platform analytics, reports, audit (FR-007)."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.consultation import AuditLog, Consultation
from app.models.reading import Reading
from app.models.user import User, UserRole

# Refresh token cookie name.
REFRESH_COOKIE_NAME = "palmistry_refresh"


class AdminError(Exception):
    code = "ADMIN_ERROR"
    status_code = 400

    def __init__(self, message: str = "Admin operation failed"):
        self.message = message
        super().__init__(message)


class UserNotFound(AdminError):
    code = "USER_NOT_FOUND"
    status_code = 404


class LastAdminError(AdminError):
    code = "LAST_ADMIN"
    status_code = 409


class ErrorEntryNotFound(AdminError):
    code = "ERROR_NOT_FOUND"
    status_code = 404


def list_users(
    db: Session, *, role: UserRole | None = None, search: str | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[User], int]:
    conditions = []
    if role is not None:
        conditions.append(User.role == role)
    if search:
        like = f"%{search.lower()}%"
        conditions.append(func.lower(User.email).like(like) | func.lower(User.full_name).like(like))
    base = select(User).where(*conditions)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(base.order_by(User.created_at.desc()).limit(limit).offset(offset)).all()
    return list(items), int(total)


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFound("User not found")
    return user


def update_user(db: Session, target: User, updates: dict, actor: User) -> User:
    if updates.get("role") is not None and updates["role"] != target.role:
        _ensure_not_last_admin(db, target, demoting=(updates["role"] != UserRole.admin))
    for field, value in updates.items():
        if value is not None:
            setattr(target, field, value)
    log_action(db, actor, "user.update", str(target.id), f"updates={list(updates.keys())}")
    db.commit()
    db.refresh(target)
    return target


def _ensure_not_last_admin(db: Session, target: User, *, demoting: bool) -> None:
    if not demoting or target.role != UserRole.admin:
        return
    admins = db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.admin, User.is_active.is_(True))
    ) or 0
    if admins <= 1:
        raise LastAdminError("Cannot demote the last active administrator")


def log_action(db: Session, actor: User | None, action: str, target: str, detail: str | None = None) -> None:
    db.add(AuditLog(actor_id=actor.id if actor else None, action=action, target=target, detail=detail))


def platform_analytics(db: Session, *, days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)
    previous_start = period_start - timedelta(days=days)

    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    users_active = db.scalar(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    ) or 0
    by_role_rows = db.execute(select(User.role, func.count()).group_by(User.role)).all()
    readings_total = db.scalar(select(func.count()).select_from(Reading)) or 0
    consultations_total = db.scalar(select(func.count()).select_from(Consultation)) or 0
    signups_rows = db.execute(
        select(
            func.date_trunc("day", User.created_at).label("day"),
            func.count().label("count"),
        )
        .where(User.created_at >= period_start)
        .group_by("day")
        .order_by("day")
    ).all()

    # Period-over-period deltas for the executive summary cards.
    signups_in_period = (
        db.scalar(select(func.count()).select_from(User).where(User.created_at >= period_start)) or 0
    )
    signups_previous = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= previous_start, User.created_at < period_start)
        )
        or 0
    )
    readings_in_period = (
        db.scalar(select(func.count()).select_from(Reading).where(Reading.created_at >= period_start))
        or 0
    )
    readings_previous = (
        db.scalar(
            select(func.count())
            .select_from(Reading)
            .where(Reading.created_at >= previous_start, Reading.created_at < period_start)
        )
        or 0
    )

    # Engagement, derived from existing tables — no session tracking exists,
    users_with_readings = db.scalar(
        select(func.count(func.distinct(Reading.user_id)))
    ) or 0
    multi_readings_subq = (
        select(Reading.user_id)
        .group_by(Reading.user_id)
        .having(func.count() >= 2)
        .subquery()
    )
    users_with_multiple_readings = db.scalar(
        select(func.count()).select_from(multi_readings_subq)
    ) or 0

    return {
        "days": days,
        "users_total": int(users_total),
        "users_active": int(users_active),
        "users_by_role": [{"role": row[0].value, "count": row[1]} for row in by_role_rows],
        "readings_total": int(readings_total),
        "consultations_total": int(consultations_total),
        "signups_per_day": [
            {"day": row[0].strftime("%Y-%m-%d"), "count": row[1]} for row in signups_rows
        ],
        "signups_in_period": int(signups_in_period),
        "signups_previous_period": int(signups_previous),
        "readings_in_period": int(readings_in_period),
        "readings_previous_period": int(readings_previous),
        "engagement": {
            "users_with_readings": int(users_with_readings),
            "users_with_multiple_readings": int(users_with_multiple_readings),
        },
    }


def reading_statistics(db: Session, *, days: int = 30) -> dict:
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    total = db.scalar(select(func.count()).select_from(Reading)) or 0
    reviewed = db.scalar(
        select(func.count()).select_from(Reading).where(Reading.reviewed_by.is_not(None))
    ) or 0
    by_type_rows = db.execute(select(Reading.type, func.count()).group_by(Reading.type)).all()
    by_status_rows = db.execute(select(Reading.status, func.count()).group_by(Reading.status)).all()
    per_day_rows = db.execute(
        select(
            func.date_trunc("day", Reading.created_at).label("day"),
            func.count().label("count"),
        )
        .where(Reading.created_at >= period_start)
        .group_by("day")
        .order_by("day")
    ).all()
    per_day_type_rows = db.execute(
        select(
            func.date_trunc("day", Reading.created_at).label("day"),
            Reading.type,
            func.count().label("count"),
        )
        .where(Reading.created_at >= period_start)
        .group_by("day", Reading.type)
        .order_by("day")
    ).all()
    return {
        "days": days,
        "total": int(total),
        "reviewed_total": int(reviewed),
        "by_type": [{"type": row[0].value, "count": row[1]} for row in by_type_rows],
        "by_status": [{"status": row[0].value, "count": row[1]} for row in by_status_rows],
        "per_day": [{"day": row[0].strftime("%Y-%m-%d"), "count": row[1]} for row in per_day_rows],
        "per_day_by_type": [
            {"day": row[0].strftime("%Y-%m-%d"), "type": row[1].value, "count": row[2]}
            for row in per_day_type_rows
        ],
    }


def list_all_readings(
    db: Session,
    *,
    type_filter: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Platform-wide reading oversight rows (reading + owner email), newest first."""
    conditions = []
    if type_filter:
        conditions.append(Reading.type == type_filter)
    if status_filter:
        conditions.append(Reading.status == status_filter)
    base = select(Reading, User.email).join(User, Reading.user_id == User.id, isouter=True).where(*conditions)
    total = db.scalar(select(func.count()).select_from(Reading).where(*conditions)) or 0
    rows = db.execute(base.order_by(Reading.created_at.desc()).limit(limit).offset(offset)).all()
    items = [
        {
            "id": reading.id,
            "user_id": reading.user_id,
            "owner_email": email,
            "type": reading.type.value if hasattr(reading.type, "value") else reading.type,
            "status": reading.status.value if hasattr(reading.status, "value") else reading.status,
            "title": reading.title,
            "summary": reading.summary,
            "reviewed_by": reading.reviewed_by,
            "created_at": reading.created_at,
        }
        for reading, email in rows
    ]
    return items, int(total)


def system_report(db: Session, actor: User) -> dict:
    payload = {
        "platform": platform_analytics(db),
        "readings": reading_statistics(db),
    }
    report = {
        "generated_at": datetime.now(timezone.utc),
        "generated_by": actor.id,
        "payload": payload,
    }
    log_action(db, actor, "report.generate", "system", "Generated system report")
    db.commit()
    return report


def list_audit_logs(db: Session, *, limit: int = 100, offset: int = 0) -> tuple[list[dict], int]:
    """Audit trail with the acting account's email resolved for display."""
    base = select(AuditLog, User.email).join(User, AuditLog.actor_id == User.id, isouter=True)
    total = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    rows = db.execute(base.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)).all()
    items = [
        {
            "id": log.id,
            "actor_id": log.actor_id,
            "actor_email": email,
            "action": log.action,
            "target": log.target,
            "detail": log.detail,
            "created_at": log.created_at,
        }
        for log, email in rows
    ]
    return items, int(total)


# Session oversight (read-only)


def session_oversight(db: Session, *, days: int = 30, upcoming_limit: int = 8) -> dict:
    """Read-only session statistics for the admin console."""
    from app.models.booking import Booking, BookingStatus, ConsultantProfile

    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    total = db.scalar(select(func.count()).select_from(Booking)) or 0
    by_status_rows = db.execute(
        select(Booking.status, func.count()).group_by(Booking.status)
    ).all()
    by_status = [
        {"status": status.value if hasattr(status, "value") else status, "count": count}
        for status, count in by_status_rows
    ]
    status_counts = {row["status"]: row["count"] for row in by_status}

    upcoming = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.status == BookingStatus.accepted,
            Booking.start_time >= now,
        )
    ) or 0
    pending_requests = status_counts.get(BookingStatus.pending.value, 0)

    per_day_rows = db.execute(
        select(
            func.date_trunc("day", Booking.start_time).label("day"),
            func.count().label("count"),
        )
        .where(Booking.start_time >= period_start)
        .group_by("day")
        .order_by("day")
    ).all()

    consultants_total = (
        db.scalar(select(func.count()).select_from(ConsultantProfile)) or 0
    )
    consultants_accepting = db.scalar(
        select(func.count())
        .select_from(ConsultantProfile)
        .where(ConsultantProfile.is_accepting_bookings.is_(True))
    ) or 0

    rating_row = db.scalar(
        select(func.avg(ConsultantProfile.avg_rating)).where(
            ConsultantProfile.review_count > 0
        )
    )
    review_count = db.scalar(
        select(func.coalesce(func.sum(ConsultantProfile.review_count), 0))
    ) or 0
    unique_seekers = db.scalar(
        select(func.count(func.distinct(Booking.user_id)))
    ) or 0

    upcoming_rows = db.execute(
        select(Booking, ConsultantProfile, User.email)
        .join(ConsultantProfile, Booking.consultant_id == ConsultantProfile.id)
        .join(User, Booking.user_id == User.id, isouter=True)
        .where(Booking.start_time >= now)
        .where(Booking.status.in_((BookingStatus.pending, BookingStatus.accepted, BookingStatus.countered)))
        .order_by(Booking.start_time.asc())
        .limit(upcoming_limit)
    ).all()

    def _session_row(booking, profile, seeker_email):
        return {
            "id": booking.id,
            "subject": booking.subject,
            "status": booking.status.value if hasattr(booking.status, "value") else booking.status,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "duration_minutes": booking.duration_minutes,
            "consultant_name": profile.user.full_name if profile.user is not None else None,
            "seeker_email": seeker_email,
            "meet_link_booked": bool(booking.meet_link),
        }

    return {
        "days": days,
        "total": int(total),
        "by_status": by_status,
        "upcoming": int(upcoming),
        "pending_requests": int(pending_requests),
        "sessions_per_day": [
            {"day": row[0].strftime("%Y-%m-%d"), "count": row[1]} for row in per_day_rows
        ],
        "consultants_total": int(consultants_total),
        "consultants_accepting": int(consultants_accepting),
        "avg_rating": round(float(rating_row), 2) if rating_row is not None else None,
        "review_count": int(review_count),
        "unique_seekers": int(unique_seekers),
        "upcoming_sessions": [
            _session_row(booking, profile, email)
            for booking, profile, email in upcoming_rows
        ],
    }


# Access & permissions

# Permission rule descriptions.
PERMISSION_RULES: list[dict] = [
    {
        "name": "require_user",
        "allowed": ["user", "tarot_reader", "spiritual_consultant", "admin"],
        "surfaces": [
            "own profile, readings, reports, notifications and recommendations",
        ],
    },
    {
        "name": "require_tarot_reader",
        "allowed": ["tarot_reader", "admin"],
        "surfaces": [
            "reader workspace: every platform reading, reading analytics, reading review",
        ],
    },
    {
        "name": "require_spiritual_consultant",
        "allowed": ["spiritual_consultant", "admin"],
        "surfaces": [
            "consultant workspace: guidance queue, guidance dispatch, insight analytics",
        ],
    },
    {
        "name": "require_admin",
        "allowed": ["admin"],
        "surfaces": [
            "user management and role assignment",
            "platform analytics and reading statistics",
            "system reports and audit logs",
            "access permissions, authentication settings and system configuration",
            "error, security and performance monitoring",
        ],
    },
    {
        "name": "require_consultant_role",
        "allowed": ["tarot_reader", "spiritual_consultant"],
        "surfaces": [
            "consultant studio: availability, booking requests, session notes",
        ],
    },
    {
        "name": "require_session_role",
        "allowed": ["user", "tarot_reader", "spiritual_consultant"],
        "surfaces": ["booking as a seeker: reserves, proposals, cancellations"],
    },
]


def permission_matrix() -> dict:
    """Explain the live RBAC matrix (§49.3) with each rule's allowed roles."""
    return {
        "roles": [role.value for role in UserRole],
        "rules": PERMISSION_RULES,
        "notes": [
            "Backend enforcement is authoritative; this matrix describes it.",
            "Administrators govern the platform and never take part in sessions.",
        ],
    }


def verify_permission_matrix() -> list[str]:
    """Names of declared rules whose bundle no longer exists (drift detection)."""
    from app.api.v1.endpoints import booking as booking_endpoints
    from app.auth import rbac

    declared = {rule["name"] for rule in PERMISSION_RULES}
    live = {name for name in dir(rbac) if name.startswith("require_")}
    live |= {name for name in dir(booking_endpoints) if name.startswith("require_")}
    return sorted(declared - live)


# Authentication & security settings


def auth_settings() -> dict:
    """Authentication posture. Secrets are reported as presence flags only."""
    from app.auth import tokens

    oauth_providers = []
    oauth_configured = []
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        oauth_providers.append("google")
        oauth_configured.append("google")
    elif settings.GOOGLE_CLIENT_ID:
        oauth_providers.append("google")

    return {
        "jwt_algorithm": tokens.JWT_ALGORITHM,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
        "refresh_cookie_name": REFRESH_COOKIE_NAME,
        "refresh_cookie_secure": settings.REFRESH_COOKIE_SECURE,
        "refresh_cookie_samesite": "none" if settings.REFRESH_COOKIE_SECURE else "lax",
        "refresh_cookie_path": "/api/v1/auth",
        "password_hashing": "argon2id",
        "oauth_providers": oauth_providers,
        "oauth_configured": oauth_configured,
        "admin_signup_requires_invite_code": bool(settings.ADMIN_SIGNUP_CODE),
        "rate_limits": {
            "auth_requests_per_minute": settings.AUTH_RATE_LIMIT_PER_MINUTE,
        },
        "cors_origins": list(settings.CORS_ORIGINS),
        "notes": [
            "Access tokens are short-lived and stateless; refresh tokens rotate and "
            "are stored hashed with reuse detection.",
            "Secrets are never returned by the API — only whether they are set.",
        ],
    }


# System configuration & release


def _database_target() -> str:
    """Host/database only — never credentials."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL)
        return f"{parsed.hostname or 'localhost'}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"
    except Exception:  # pragma: no cover - defensive
        return "unknown"


def _migration_revision(db: Session) -> str | None:
    try:
        from sqlalchemy import text

        row = db.execute(text("SELECT version_num FROM alembic_version")).first()
        return row[0] if row else None
    except Exception:  # pragma: no cover - defensive
        return None


def _ai_provider() -> tuple[str, str, bool]:
    if settings.LLM_PROVIDER:
        provider = settings.LLM_PROVIDER
        model = settings.OPENAI_MODEL if provider == "openai" else settings.GROQ_MODEL
        configured = bool(
            settings.OPENAI_API_KEY if provider == "openai" else settings.GROQ_API_KEY
        )
        return provider, model, configured
    if settings.GROQ_API_KEY:
        return "groq", settings.GROQ_MODEL, True
    if settings.OPENAI_API_KEY:
        return "openai", settings.OPENAI_MODEL, True
    return "none", "rule-based fallback", False


def system_config(db: Session) -> dict:
    """Deployment-shaped view of the running configuration."""
    from app.middleware import monitoring
    from app.services.booking import scheduler as booking_scheduler
    from app.services.notifications import scheduler as notification_scheduler

    provider, model, ai_configured = _ai_provider()

    schedulers = []
    for name, sched, jobs in (
        (
            "notifications",
            notification_scheduler.scheduler,
            ["daily_guidance", "reading_reminder"],
        ),
        (
            "booking",
            booking_scheduler.scheduler,
            ["booking_reminders", "booking_availability_rollout", "booking_autocomplete"],
        ),
    ):
        registered = {job.id for job in sched.get_jobs()} if sched.running else set()
        schedulers.append(
            {
                "name": name,
                "running": bool(sched.running),
                "jobs": [
                    {"id": job_id, "registered": job_id in registered} for job_id in jobs
                ],
            }
        )

    return {
        "environment": settings.ENVIRONMENT,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_prefix": settings.API_V1_PREFIX,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "database_target": _database_target(),
        "migration_revision": _migration_revision(db),
        "ai_provider": provider,
        "ai_model": model,
        "ai_configured": ai_configured,
        "email_configured": bool(settings.EMAIL_SMTP_HOST),
        "sms_configured": False,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "allowed_image_types": ["jpg", "jpeg", "png", "webp"],
        "schedulers": schedulers,
        "uptime_seconds": monitoring.uptime_seconds(),
        "started_at": monitoring.started_at(),
        "timezone": "UTC",
        "notes": [
            "Configuration is read from the environment and is read-only from the console.",
            "SMS delivery is not configured; notifications use in-app and email channels.",
        ],
    }


# Errors, security events & performance


def list_errors(
    db: Session,
    *,
    level: str | None = None,
    kind: str | None = None,
    unresolved_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Deduplicated operational error rows, newest activity first."""
    from app.models.error_log import ErrorLog

    conditions = []
    if level:
        conditions.append(ErrorLog.level == level)
    if kind:
        conditions.append(ErrorLog.kind == kind)
    if unresolved_only:
        conditions.append(ErrorLog.acknowledged_at.is_(None))
    base = select(ErrorLog, User.email).outerjoin(User, ErrorLog.actor_id == User.id)
    if conditions:
        base = base.where(*conditions)
    total = db.scalar(
        select(func.count()).select_from(ErrorLog).where(*conditions)
    ) or 0
    rows = db.execute(
        base.order_by(ErrorLog.last_seen_at.desc()).limit(limit).offset(offset)
    ).all()
    items = [
        {
            "id": log.id,
            "level": log.level.value if hasattr(log.level, "value") else log.level,
            "kind": log.kind.value if hasattr(log.kind, "value") else log.kind,
            "status_code": log.status_code,
            "method": log.method,
            "path": log.path,
            "request_id": log.request_id,
            "message": log.message,
            "actor_id": log.actor_id,
            "actor_email": email,
            "occurrences": log.occurrences,
            "created_at": log.created_at,
            "last_seen_at": log.last_seen_at,
            "acknowledged_at": log.acknowledged_at,
            "acknowledged_by": log.acknowledged_by,
        }
        for log, email in rows
    ]
    return items, int(total)


def error_stats(db: Session, *, hours: int = 24) -> dict:
    """Counts for the console's header chips."""
    from app.models.error_log import ErrorKind, ErrorLevel, ErrorLog

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    total = db.scalar(select(func.count()).select_from(ErrorLog)) or 0
    unresolved = db.scalar(
        select(func.count())
        .select_from(ErrorLog)
        .where(ErrorLog.acknowledged_at.is_(None))
    ) or 0
    last_24h = db.scalar(
        select(func.count()).select_from(ErrorLog).where(ErrorLog.last_seen_at >= since)
    ) or 0
    by_kind_rows = db.execute(
        select(ErrorLog.kind, func.count()).group_by(ErrorLog.kind)
    ).all()
    by_status_rows = db.execute(
        select(ErrorLog.status_code, func.count()).group_by(ErrorLog.status_code)
    ).all()

    def _recent(kind: ErrorKind) -> int:
        return (
            db.scalar(
                select(func.count())
                .select_from(ErrorLog)
                .where(ErrorLog.kind == kind, ErrorLog.last_seen_at >= since)
            )
            or 0
        )

    return {
        "total": int(total),
        "unresolved": int(unresolved),
        "last_24h": int(last_24h),
        "by_kind": [
            {"kind": k.value if hasattr(k, "value") else k, "count": c}
            for k, c in by_kind_rows
        ],
        "by_status": [
            {"status_code": s, "count": c} for s, c in by_status_rows
        ],
        "server_errors_24h": int(_recent(ErrorKind.server_error)),
        "auth_failures_24h": int(_recent(ErrorKind.auth_failure)),
    }


def acknowledge_error(db: Session, error_id: uuid.UUID, actor: User) -> None:
    """Mark one error row as triaged (idempotent)."""
    from app.models.error_log import ErrorLog

    row = db.get(ErrorLog, error_id)
    if row is None:
        raise ErrorEntryNotFound("Error entry not found")
    if row.acknowledged_at is None:
        row.acknowledged_at = datetime.now(timezone.utc)
        row.acknowledged_by = actor.id
        log_action(
            db, actor, "error.acknowledge", str(row.id), f"{row.kind} {row.method} {row.path}"
        )
        db.commit()


def performance_summary() -> dict:
    """In-process latency aggregates (resets on restart, by design)."""
    from app.middleware import monitoring

    snapshot = monitoring.performance_snapshot()
    snapshot["notes"] = [
        "Metrics are collected in the current process only and reset on restart.",
        "Health probes and API docs are excluded from latency accounting.",
    ]
    return snapshot

"""Admin schemas (FR-007)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Plain string field for admin listings.
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserListOut(BaseModel):
    items: list[AdminUserOut]
    total: int


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)


class EngagementAnalytics(BaseModel):
    # Derived from existing tables (no session tracking exists): "activated"
    users_with_readings: int
    users_with_multiple_readings: int


class PlatformAnalytics(BaseModel):
    days: int = 7
    users_total: int
    users_active: int
    users_by_role: list[dict]
    readings_total: int
    consultations_total: int
    signups_per_day: list[dict]
    signups_in_period: int = 0
    signups_previous_period: int = 0
    readings_in_period: int = 0
    readings_previous_period: int = 0
    engagement: EngagementAnalytics


class ReadingStatistics(BaseModel):
    days: int = 30
    total: int
    by_type: list[dict]
    by_status: list[dict]
    per_day: list[dict]
    per_day_by_type: list[dict] = []
    reviewed_total: int


class AdminReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    owner_email: str | None
    type: str
    status: str
    title: str
    summary: str
    reviewed_by: uuid.UUID | None
    created_at: datetime


class AdminReadingListOut(BaseModel):
    items: list[AdminReadingOut]
    total: int


class SystemReportOut(BaseModel):
    generated_at: datetime
    generated_by: uuid.UUID | None
    payload: dict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_email: str | None = None
    action: str
    target: str
    detail: str | None
    created_at: datetime


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int


class SessionStatusCount(BaseModel):
    status: str
    count: int


class SessionDayCount(BaseModel):
    day: str
    count: int


class SessionOversightRow(BaseModel):
    id: uuid.UUID
    subject: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    consultant_name: str | None = None
    seeker_email: str | None = None
    meet_link_booked: bool = False


class SessionOversight(BaseModel):
    """Read-only session statistics for the admin console (FR-036 governance)."""

    days: int
    total: int
    by_status: list[SessionStatusCount]
    upcoming: int
    pending_requests: int
    sessions_per_day: list[SessionDayCount]
    consultants_total: int
    consultants_accepting: int
    avg_rating: float | None = None
    review_count: int
    unique_seekers: int
    upcoming_sessions: list[SessionOversightRow]


# Access & permissions


class PermissionRuleOut(BaseModel):
    name: str
    allowed: list[str]
    surfaces: list[str]


class PermissionMatrixOut(BaseModel):
    roles: list[str]
    rules: list[PermissionRuleOut]
    notes: list[str]


# Authentication & security settings


class AuthSettingsOut(BaseModel):
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    refresh_cookie_name: str
    refresh_cookie_secure: bool
    refresh_cookie_samesite: str
    refresh_cookie_path: str
    password_hashing: str
    oauth_providers: list[str]
    oauth_configured: list[str]
    admin_signup_requires_invite_code: bool
    rate_limits: dict[str, int]
    cors_origins: list[str]
    notes: list[str]


# System configuration & release


class SystemConfigOut(BaseModel):
    environment: str
    app_name: str
    version: str
    api_prefix: str
    docs_url: str
    database_target: str
    migration_revision: str | None
    ai_provider: str
    ai_model: str
    ai_configured: bool
    email_configured: bool
    sms_configured: bool
    max_upload_size_mb: int
    allowed_image_types: list[str]
    schedulers: list[dict]
    uptime_seconds: int
    started_at: datetime
    timezone: str
    notes: list[str]


# Errors, security events & performance


class ErrorLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    level: str
    kind: str
    status_code: int
    method: str
    path: str
    request_id: str | None
    message: str
    actor_id: uuid.UUID | None = None
    actor_email: str | None = None
    occurrences: int
    created_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: uuid.UUID | None = None


class ErrorLogListOut(BaseModel):
    items: list[ErrorLogOut]
    total: int
    unresolved: int


class ErrorStatsOut(BaseModel):
    total: int
    unresolved: int
    last_24h: int
    by_kind: list[dict]
    by_status: list[dict]
    server_errors_24h: int
    auth_failures_24h: int


class PerformanceSummaryOut(BaseModel):
    uptime_seconds: int
    requests_total: int
    requests_per_minute: float
    error_rate: float
    latency_ms: dict[str, float]
    slowest_routes: list[dict]
    window_requests: int
    notes: list[str]


# System reports (overview, health, errors, performance)


class ReportUserCounts(BaseModel):
    total: int
    new_in_period: int


class ReportAnalysisCounts(BaseModel):
    successful: int
    failed: int
    total: int
    successful_all_time: int
    failed_all_time: int
    total_all_time: int
    success_by_type: list[dict]
    failed_by_type: list[dict]
    failed_tracking_since: datetime | None = None


class SystemOverviewOut(BaseModel):
    days: int
    generated_at: datetime
    users: ReportUserCounts
    analyses: ReportAnalysisCounts


class ServiceStatusOut(BaseModel):
    status: str
    detail: str
    latency_ms: float | None = None


class SystemHealthOut(BaseModel):
    generated_at: datetime
    backend: ServiceStatusOut
    database: ServiceStatusOut
    ai_service: ServiceStatusOut
    ai_provider: str
    ai_model: str
    environment: str
    version: str
    uptime_seconds: int
    started_at: datetime
    notes: list[str]


class ErrorReportItemOut(BaseModel):
    id: uuid.UUID
    category: str
    description: str
    method: str
    path: str
    status_code: int
    occurrences: int
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None = None


class ErrorReportCountsOut(BaseModel):
    rows: int
    total: int
    failed_analyses: int
    server_errors: int
    by_category: list[dict]


class ErrorReportOut(BaseModel):
    days: int
    generated_at: datetime
    counts: ErrorReportCountsOut
    items: list[ErrorReportItemOut]
    notes: list[str]


class ApiPerformanceOut(BaseModel):
    status: str
    requests: int
    avg_ms: float | None = None
    p50_ms: float | None = None
    p95_ms: float | None = None
    max_ms: float | None = None
    error_rate: float | None = None
    first_sample_at: datetime | None = None
    last_sample_at: datetime | None = None


class AnalysisPerformanceOut(BaseModel):
    status: str
    samples: int
    avg_ms: float | None = None
    p95_ms: float | None = None
    max_ms: float | None = None
    by_type: list[dict]


class PerformanceReportOut(BaseModel):
    days: int
    generated_at: datetime
    api: ApiPerformanceOut
    analysis_generation: AnalysisPerformanceOut
    notes: list[str]

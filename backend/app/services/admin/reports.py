"""System reports for the admin console: overview, health, errors, performance."""
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.error_log import ErrorKind, ErrorLog
from app.models.reading import Reading, ReadingType
from app.models.user import User
from app.services.admin.service import _ai_provider

# Failed-analysis descriptions are trimmed to this length.
_DESCRIPTION_LIMIT = 200


def _analysis_type_from_path(path: str | None) -> str | None:
    # Failed-analysis rows carry the reading type as their last path segment.
    tail = (path or "").rstrip("/").rsplit("/", 1)[-1].lower()
    return tail if tail in {item.value for item in ReadingType} else None


def system_overview(db: Session, *, days: int = 7) -> dict:
    """Registered users and analysis totals (all-time plus the selected period)."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    users_new = (
        db.scalar(
            select(func.count()).select_from(User).where(User.created_at >= period_start)
        )
        or 0
    )

    # A reading row exists only for a successful analysis.
    successful = (
        db.scalar(
            select(func.count())
            .select_from(Reading)
            .where(Reading.created_at >= period_start)
        )
        or 0
    )
    successful_all = db.scalar(select(func.count()).select_from(Reading)) or 0

    success_rows = db.execute(
        select(Reading.type, func.count())
        .where(Reading.created_at >= period_start)
        .group_by(Reading.type)
    ).all()
    success_counts = {item.value: 0 for item in ReadingType}
    for reading_type, count in success_rows:
        success_counts[reading_type.value] = int(count)

    failed_base = select(func.coalesce(func.sum(ErrorLog.occurrences), 0)).where(
        ErrorLog.kind == ErrorKind.analysis_failed
    )
    failed = db.scalar(failed_base.where(ErrorLog.last_seen_at >= period_start)) or 0
    failed_all = db.scalar(failed_base) or 0

    failed_rows = db.execute(
        select(ErrorLog.path, func.sum(ErrorLog.occurrences))
        .where(
            ErrorLog.kind == ErrorKind.analysis_failed,
            ErrorLog.last_seen_at >= period_start,
        )
        .group_by(ErrorLog.path)
    ).all()
    failed_counts = {item.value: 0 for item in ReadingType}
    for path, count in failed_rows:
        analysis_type = _analysis_type_from_path(path)
        if analysis_type:
            failed_counts[analysis_type] += int(count)

    tracking_since = db.scalar(
        select(func.min(ErrorLog.created_at)).where(
            ErrorLog.kind == ErrorKind.analysis_failed
        )
    )

    return {
        "days": days,
        "generated_at": now,
        "users": {
            "total": int(users_total),
            "new_in_period": int(users_new),
        },
        "analyses": {
            "successful": int(successful),
            "failed": int(failed),
            "total": int(successful) + int(failed),
            "successful_all_time": int(successful_all),
            "failed_all_time": int(failed_all),
            "total_all_time": int(successful_all) + int(failed_all),
            "success_by_type": [
                {"type": item.value, "count": success_counts[item.value]}
                for item in ReadingType
            ],
            "failed_by_type": [
                {"type": item.value, "count": failed_counts[item.value]}
                for item in ReadingType
            ],
            "failed_tracking_since": tracking_since,
        },
    }


def system_health(db: Session) -> dict:
    """Backend status, database connectivity, and AI service availability."""
    now = datetime.now(timezone.utc)

    started = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
        database_detail = "SELECT 1 succeeded"
    except Exception:
        database_status = "unavailable"
        database_detail = "database check failed"
    database_latency = round((time.perf_counter() - started) * 1000, 1)

    provider, model, ai_configured = _ai_provider()
    if ai_configured:
        ai_status = "configured"
        ai_detail = f"{provider} configured for model {model}"
    else:
        ai_status = "not_configured"
        ai_detail = "no LLM API key configured; readings use the rule-based fallback"

    from app.middleware import monitoring

    return {
        "generated_at": now,
        "backend": {
            "status": "ok",
            "detail": f"{settings.APP_NAME} v{settings.APP_VERSION}",
            "latency_ms": None,
        },
        "database": {
            "status": database_status,
            "detail": database_detail,
            "latency_ms": database_latency,
        },
        "ai_service": {
            "status": ai_status,
            "detail": ai_detail,
            "latency_ms": None,
        },
        "ai_provider": provider,
        "ai_model": model,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "uptime_seconds": monitoring.uptime_seconds(),
        "started_at": monitoring.started_at(),
        "notes": [
            "Backend and database statuses come from live checks on this request.",
            "AI availability is a configuration check only; no live upstream ping exists.",
            "Generations that fail before completing are recorded as failed analyses.",
        ],
    }


def error_report(db: Session, *, days: int = 7, limit: int = 50) -> dict:
    """Recent system errors and failed analyses, newest activity first."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)
    in_period = ErrorLog.last_seen_at >= period_start

    rows_in_period = (
        db.scalar(select(func.count()).select_from(ErrorLog).where(in_period)) or 0
    )
    total_occurrences = (
        db.scalar(
            select(func.coalesce(func.sum(ErrorLog.occurrences), 0)).where(in_period)
        )
        or 0
    )
    category_rows = db.execute(
        select(ErrorLog.kind, func.coalesce(func.sum(ErrorLog.occurrences), 0))
        .where(in_period)
        .group_by(ErrorLog.kind)
        .order_by(func.coalesce(func.sum(ErrorLog.occurrences), 0).desc())
    ).all()
    by_category = [
        {
            "category": kind.value if hasattr(kind, "value") else str(kind),
            "occurrences": int(count),
        }
        for kind, count in category_rows
    ]
    category_counts = {row["category"]: row["occurrences"] for row in by_category}

    logs = db.scalars(
        select(ErrorLog)
        .where(in_period)
        .order_by(ErrorLog.last_seen_at.desc())
        .limit(limit)
    ).all()

    items = [
        {
            "id": log.id,
            "category": log.kind.value if hasattr(log.kind, "value") else str(log.kind),
            "description": " ".join((log.message or "").split())[:_DESCRIPTION_LIMIT],
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "occurrences": log.occurrences,
            "first_seen_at": log.created_at,
            "last_seen_at": log.last_seen_at,
            "acknowledged_at": log.acknowledged_at,
        }
        for log in logs
    ]

    tracking_since = db.scalar(
        select(func.min(ErrorLog.created_at)).where(
            ErrorLog.kind == ErrorKind.analysis_failed
        )
    )
    notes = [
        "Descriptions are whitespace-collapsed and trimmed to keep rows short.",
        "Acknowledged rows stay listed; acknowledged_at shows their triage state.",
    ]
    if tracking_since is None:
        notes.append("No failed analyses have been recorded yet.")
    else:
        notes.append(f"Failed analyses are tracked since {tracking_since.isoformat()}.")

    return {
        "days": days,
        "generated_at": now,
        "counts": {
            "rows": int(rows_in_period),
            "total": int(total_occurrences),
            "failed_analyses": category_counts.get(ErrorKind.analysis_failed.value, 0),
            "server_errors": category_counts.get(ErrorKind.server_error.value, 0),
            "by_category": by_category,
        },
        "items": items,
        "notes": notes,
    }


def performance_report(db: Session, *, days: int = 7) -> dict:
    """API response times and analysis-generation times for the period."""
    from app.middleware import monitoring
    from app.models.performance_sample import PerformanceSample

    # Persist anything still buffered so the report always reads fresh data.
    monitoring.flush_samples()

    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    sample_rows = db.execute(
        select(
            func.count(),
            func.coalesce(func.avg(PerformanceSample.duration_ms), 0.0),
            func.coalesce(func.max(PerformanceSample.duration_ms), 0.0),
            func.min(PerformanceSample.sampled_at),
            func.max(PerformanceSample.sampled_at),
        ).where(PerformanceSample.sampled_at >= period_start)
    ).one()
    requests = int(sample_rows[0] or 0)
    errors = (
        db.scalar(
            select(func.count())
            .select_from(PerformanceSample)
            .where(
                PerformanceSample.sampled_at >= period_start,
                PerformanceSample.status_code >= 500,
            )
        )
        or 0
    )

    if requests:
        # Reuse the middleware percentile so both surfaces report identical math.
        durations = [
            float(value)
            for (value,) in db.execute(
                select(PerformanceSample.duration_ms).where(
                    PerformanceSample.sampled_at >= period_start
                )
            ).all()
        ]
        api = {
            "status": "ok",
            "requests": requests,
            "avg_ms": round(float(sample_rows[1]), 1),
            "p50_ms": monitoring._percentile(durations, 50),
            "p95_ms": monitoring._percentile(durations, 95),
            "max_ms": round(float(sample_rows[2]), 1),
            "error_rate": round(int(errors) / requests, 4),
            "first_sample_at": sample_rows[3],
            "last_sample_at": sample_rows[4],
        }
    else:
        # Honest "no data" — never a misleading zero.
        api = {
            "status": "no_data",
            "requests": 0,
            "avg_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "max_ms": None,
            "error_rate": None,
            "first_sample_at": None,
            "last_sample_at": None,
        }

    # Analysis-generation timing comes from measured per-reading durations.
    analysis_rows = db.execute(
        select(
            Reading.type,
            func.count(),
            func.coalesce(func.avg(Reading.duration_ms), 0.0),
        )
        .where(Reading.created_at >= period_start, Reading.duration_ms.is_not(None))
        .group_by(Reading.type)
    ).all()
    analysis_samples = sum(int(count) for _type, count, _avg in analysis_rows)
    if analysis_samples:
        durations = [
            float(value)
            for (value,) in db.execute(
                select(Reading.duration_ms).where(
                    Reading.created_at >= period_start,
                    Reading.duration_ms.is_not(None),
                )
            ).all()
        ]
        analysis = {
            "status": "ok",
            "samples": analysis_samples,
            "avg_ms": round(sum(durations) / len(durations), 1),
            "p95_ms": monitoring._percentile(durations, 95),
            "max_ms": round(max(durations), 1),
            "by_type": [
                {
                    "type": (
                        reading_type.value
                        if hasattr(reading_type, "value")
                        else str(reading_type)
                    ),
                    "samples": int(count),
                    "avg_ms": round(float(avg), 1),
                }
                for reading_type, count, avg in sorted(
                    analysis_rows, key=lambda row: str(row[0])
                )
            ],
        }
    else:
        analysis = {
            "status": "no_data",
            "samples": 0,
            "avg_ms": None,
            "p95_ms": None,
            "max_ms": None,
            "by_type": [],
        }

    return {
        "days": days,
        "generated_at": now,
        "api": api,
        "analysis_generation": analysis,
        "notes": [
            "API metrics come from latency samples persisted by the monitoring "
            "middleware; buffered samples are flushed when this report is read.",
            "Analysis timing is measured per generated reading; failed generations have no duration.",
            "Samples older than 90 days are pruned automatically.",
        ],
    }


__all__ = [
    "error_report",
    "performance_report",
    "system_health",
    "system_overview",
]

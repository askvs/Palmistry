# Monitoring middleware: error/security log plus latency tracking.
import json
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.utils.logging import logger

# Fixed-size buffers to keep memory use bounded.
_MAX_LATENCY_SAMPLES = 2000
_MAX_ROUTE_KEYS = 200

# Buffered API samples awaiting a flush into the `performance_samples` table.
_MAX_PENDING_SAMPLES = 2000
_SAMPLE_RETENTION_DAYS = 90

# Paths skipped in latency stats.
_NOISY_PATHS = ("/health", "/api/docs", "/api/openapi.json", "/favicon.ico")

_STARTED_AT = datetime.now(timezone.utc)
_START_MONOTONIC = time.monotonic()

_lock = threading.Lock()
_latency: deque[tuple[float, int]] = deque(maxlen=_MAX_LATENCY_SAMPLES)
_pending_samples: deque[tuple[str, str, int, float, datetime]] = deque(
    maxlen=_MAX_PENDING_SAMPLES
)
_routes: dict[str, dict[str, float]] = {}
_requests_since_start = 0
_errors_since_start = 0


def started_at() -> datetime:
    # Process start time for uptime reporting.
    return _STARTED_AT


def uptime_seconds() -> int:
    return int(time.monotonic() - _START_MONOTONIC)


def reset_metrics() -> None:
    # Clear collected samples (test helper).
    global _requests_since_start, _errors_since_start
    with _lock:
        _latency.clear()
        _pending_samples.clear()
        _routes.clear()
        _requests_since_start = 0
        _errors_since_start = 0


def _record_latency(path: str, status: int, duration_ms: float, method: str = "GET") -> None:
    global _requests_since_start, _errors_since_start
    if any(path.startswith(prefix) for prefix in _NOISY_PATHS):
        return
    with _lock:
        _requests_since_start += 1
        if status >= 500:
            _errors_since_start += 1
        _latency.append((duration_ms, status))
        _pending_samples.append(
            (
                method[:10],
                path[:500],
                status,
                round(duration_ms, 1),
                datetime.now(timezone.utc),
            )
        )
        stats = _routes.get(path)
        if stats is None:
            if len(_routes) >= _MAX_ROUTE_KEYS:
                return
            stats = {"count": 0.0, "total_ms": 0.0, "max_ms": 0.0, "errors": 0.0}
            _routes[path] = stats
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        if status >= 500:
            stats["errors"] += 1


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1)))))
    return round(ordered[index], 1)


def _actor_id(request: Request):
    # Best-effort caller identity from bearer token.
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return None
    try:
        from app.auth import tokens

        payload = tokens.decode_access_token(header[7:])
        return uuid.UUID(str(payload.get("sub")))
    except Exception:
        return None


def _classify(status_code: int) -> tuple[str, str] | None:
    # Map status code to (level, kind), else None.
    if status_code >= 500:
        return "error", "server_error"
    if status_code == 401:
        return "security", "auth_failure"
    if status_code == 403:
        return "security", "forbidden"
    if status_code == 429:
        return "security", "rate_limited"
    return None


def _read_error_message(response: Response) -> tuple[str, str | None]:
    # Extract message and request_id from JSON error response.
    message = f"HTTP {response.status_code}"
    request_id = response.headers.get("X-Request-ID")
    body = getattr(response, "body", None)
    if isinstance(response, JSONResponse) and body:
        try:
            payload = json.loads(bytes(body).decode("utf-8"))
            message = str(payload.get("message") or message)
            request_id = payload.get("request_id") or request_id
        except Exception:  # pragma: no cover - defensive
            pass
    return message[:2000], request_id


def _upsert_error_row(
    *,
    level: str,
    kind: str,
    status_code: int,
    method: str,
    path: str,
    message: str,
    request_id: str | None = None,
    actor_id=None,
) -> None:
    # Deduplicated insert/update of one error row. Callers guard exceptions.
    from sqlalchemy.orm import sessionmaker

    from app.db.session import get_engine
    from app.models.error_log import ErrorKind, ErrorLevel, ErrorLog

    now = datetime.now(timezone.utc)
    safe_message = (message or "")[:2000]
    session_factory = sessionmaker(bind=get_engine(), autoflush=False)
    db = session_factory()
    try:
        existing = (
            db.query(ErrorLog)
            .filter(
                ErrorLog.kind == kind,
                ErrorLog.method == method[:10],
                ErrorLog.path == path[:500],
                ErrorLog.status_code == status_code,
                ErrorLog.message == safe_message,
                ErrorLog.acknowledged_at.is_(None),
            )
            .first()
        )
        if existing is not None:
            existing.occurrences += 1
            existing.last_seen_at = now
            if request_id:
                existing.request_id = request_id
        else:
            db.add(
                ErrorLog(
                    level=ErrorLevel(level),
                    kind=ErrorKind(kind),
                    status_code=status_code,
                    method=method[:10],
                    path=path[:500],
                    request_id=request_id,
                    message=safe_message,
                    actor_id=actor_id,
                    last_seen_at=now,
                )
            )
        db.commit()
    finally:
        db.close()


def _record_error(
    *,
    status_code: int,
    method: str,
    path: str,
    message: str,
    request_id: str | None,
    actor_id=None,
) -> None:
    # Save one deduplicated error row; never raises.
    try:
        classification = _classify(status_code)
        if classification is None:
            return
        level, kind = classification
        _upsert_error_row(
            level=level,
            kind=kind,
            status_code=status_code,
            method=method,
            path=path,
            message=message,
            request_id=request_id,
            actor_id=actor_id,
        )
    except Exception:  # pragma: no cover - defensive
        logger.warning("could not record operational error row", exc_info=True)


def record_analysis_failure(
    *,
    analysis_type: str,
    path: str,
    exc: BaseException,
    method: str = "POST",
    status_code: int = 500,
    actor_id=None,
) -> None:
    # Save one deduplicated failed-analysis row; never raises.
    try:
        message = f"{analysis_type} analysis failed: {type(exc).__name__}: {exc}"
        _upsert_error_row(
            level="error",
            kind="analysis_failed",
            status_code=status_code,
            method=method,
            path=path,
            message=message,
            actor_id=actor_id,
        )
    except Exception:  # pragma: no cover - defensive
        logger.warning("could not record analysis failure", exc_info=True)


def flush_samples() -> int:
    # Persist buffered API samples into the database; never raises.
    # Returns the number of rows written (0 when the buffer is empty or the write fails).
    with _lock:
        pending = list(_pending_samples)
        _pending_samples.clear()
    if not pending:
        return 0

    try:
        from sqlalchemy import delete
        from sqlalchemy.orm import sessionmaker

        from app.db.session import get_engine
        from app.models.performance_sample import PerformanceSample

        session_factory = sessionmaker(bind=get_engine(), autoflush=False)
        db = session_factory()
        try:
            db.add_all(
                [
                    PerformanceSample(
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        sampled_at=sampled_at,
                    )
                    for method, path, status_code, duration_ms, sampled_at in pending
                ]
            )
            # Keep the table bounded: prune samples past the retention window.
            cutoff = datetime.now(timezone.utc) - timedelta(days=_SAMPLE_RETENTION_DAYS)
            db.execute(
                delete(PerformanceSample).where(PerformanceSample.sampled_at < cutoff)
            )
            db.commit()
            return len(pending)
        finally:
            db.close()
    except Exception:
        logger.warning("could not flush performance samples", exc_info=True)
        # Put the samples back so a later flush can retry them.
        with _lock:
            _pending_samples.extend(pending)
        return 0


class ErrorMonitoringMiddleware(BaseHTTPMiddleware):
    # Record failing responses and request latency.
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        start = time.perf_counter()
        status_code = 500
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            # Unhandled error: record generic 500 entry (latency is recorded in finally).
            _record_error(
                status_code=500,
                method=method,
                path=path,
                message="Unhandled exception",
                request_id=request.headers.get("X-Request-ID"),
                actor_id=_actor_id(request),
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            _record_latency(path, status_code, duration_ms, method)
            if status_code >= 400 and response is not None:
                # Record error details from response body.
                message, request_id = _read_error_message(response)
                _record_error(
                    status_code=status_code,
                    method=method,
                    path=path,
                    message=message,
                    request_id=request_id,
                    actor_id=_actor_id(request),
                )


def performance_snapshot(*, window_requests: int = 500) -> dict:
    # Aggregate latency buffer into summary stats.
    with _lock:
        samples = list(_latency)[-window_requests:]
        routes = {path: dict(stats) for path, stats in _routes.items()}
        requests_since_start = _requests_since_start
        errors_since_start = _errors_since_start

    durations = [duration for duration, _status in samples]
    errors = sum(1 for _duration, status in samples if status >= 500)
    total = len(samples)
    minutes = max(uptime_seconds() / 60, 1 / 60)

    slowest = sorted(
        (
            {
                "path": path,
                "count": int(stats["count"]),
                "avg_ms": round(stats["total_ms"] / stats["count"], 1) if stats["count"] else 0.0,
                "max_ms": round(stats["max_ms"], 1),
                "error_rate": round(stats["errors"] / stats["count"], 4) if stats["count"] else 0.0,
            }
            for path, stats in routes.items()
        ),
        key=lambda row: row["avg_ms"],
        reverse=True,
    )[:8]

    return {
        "uptime_seconds": uptime_seconds(),
        "requests_total": requests_since_start,
        "requests_per_minute": round(requests_since_start / minutes, 2),
        "error_rate": (
            round(errors_since_start / requests_since_start, 4)
            if requests_since_start
            else 0.0
        ),
        "latency_ms": {
            "p50": _percentile(durations, 50),
            "p95": _percentile(durations, 95),
            "max": round(max(durations), 1) if durations else 0.0,
            "avg": round(sum(durations) / total, 1) if total else 0.0,
        },
        "slowest_routes": slowest,
        "window_requests": window_requests,
    }


__all__ = [
    "ErrorMonitoringMiddleware",
    "flush_samples",
    "performance_snapshot",
    "record_analysis_failure",
    "reset_metrics",
    "started_at",
    "uptime_seconds",
]

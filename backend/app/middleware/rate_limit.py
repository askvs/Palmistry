# Fixed-window in-process rate limiter for auth endpoints.
import time

from fastapi import HTTPException, Request, status

from app.config import settings

_buckets: dict[str, tuple[float, int]] = {}

RATE_LIMIT_CODE = "RATE_LIMITED"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, per_minute: int | None = None):
    # Limit requests per IP within scope.
    def _check(request: Request) -> None:
        limit = per_minute if per_minute is not None else settings.AUTH_RATE_LIMIT_PER_MINUTE
        key = f"{scope}:{_client_ip(request)}"
        now = time.monotonic()
        window_start, count = _buckets.get(key, (now, 0))
        if now - window_start >= 60.0:
            window_start, count = now, 0
        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a moment and try again.",
            )
        _buckets[key] = (window_start, count + 1)

    return _check

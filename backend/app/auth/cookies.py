"""Refresh-cookie policy shared by the auth endpoints and the role portals.

SameSite=None (required when the frontend is on a different site, e.g.
Vercel -> Render) is only accepted by browsers together with Secure. An
HTTPS frontend (either the request Origin, or the configured FRONTEND_URL,
which covers OAuth callback navigations that carry no Origin header)
implies exactly that split deployment, so both flags are derived
accordingly: HTTPS gets Secure + SameSite=None. Plain-HTTP local
development keeps Lax (and no Secure). Setting REFRESH_COOKIE_SECURE=true
forces the strict combination regardless, which also covers non-browser
clients that send no Origin header.
"""
from fastapi import Request, Response

from app.config import settings

REFRESH_COOKIE = "palmistry_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def refresh_cookie_flags(request: Request | None) -> tuple[bool, str]:
    """Return (secure, samesite) for the refresh cookie on this request."""
    origin = (request.headers.get("origin") or "").lower() if request is not None else ""
    secure = (
        settings.REFRESH_COOKIE_SECURE
        or origin.startswith("https://")
        # OAuth callbacks are top-level navigations without an Origin header;
        # an HTTPS frontend URL still means the split deployment needs None.
        or settings.FRONTEND_URL.startswith("https://")
    )
    return secure, "none" if secure else "lax"


def set_refresh_cookie(response: Response, raw_token: str, request: Request | None = None) -> None:
    secure, samesite = refresh_cookie_flags(request)
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)

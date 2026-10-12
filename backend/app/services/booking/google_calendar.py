"""Google Calendar integration for the booking module (FR-BOOK-004)."""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx
import jwt

from app.config import settings

logger = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# Scopes needed to create events with conference data on someone's calendar.
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
CALENDAR_SCOPES = (CALENDAR_EVENTS_SCOPE, CALENDAR_SCOPE)

_SERVICE_ACCOUNT_CACHE: dict[str, Any] = {}


class CalendarApiError(RuntimeError):
    """Google Calendar/authorisation endpoint returned an error."""


@dataclass(frozen=True)
class CalendarEventResult:
    """The parts of a Google Calendar event we persist."""

    event_id: str
    html_link: str | None
    meet_link: str | None
    meet_code: str | None
    calendar_id: str
    raw: dict


# Token exchange helpers


def _post_form(url: str, data: dict[str, str], *, timeout: int | None = None) -> dict:
    try:
        response = httpx.post(
            url,
            data=data,
            timeout=timeout or settings.GOOGLE_OAUTH_TIMEOUT_SECONDS,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except httpx.HTTPError as exc:
        raise CalendarApiError(f"Could not reach Google: {exc}") from exc

    if response.status_code >= 400:
        raise CalendarApiError(
            f"Google token endpoint returned {response.status_code}: {response.text[:500]}"
        )
    payload = response.json()
    if not isinstance(payload, dict) or "access_token" not in payload:
        raise CalendarApiError("Google token endpoint response had no access_token")
    return payload


def exchange_authorization_code(code: str, *, redirect_uri: str) -> dict:
    """Exchange an OAuth2 authorization code for tokens."""
    return _post_form(
        TOKEN_URL,
        {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )


def refresh_access_token(refresh_token: str, *, client_id: str = "", client_secret: str = "") -> dict:
    """Mint a fresh access token from a stored refresh token."""
    return _post_form(
        TOKEN_URL,
        {
            "refresh_token": refresh_token,
            "client_id": client_id or settings.GOOGLE_CLIENT_ID,
            "client_secret": client_secret or settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        },
    )


def _load_service_account_info() -> dict:
    """Read the service-account key from a path or an inline JSON string."""
    raw = settings.GOOGLE_SERVICE_ACCOUNT_FILE
    if not raw:
        return {}
    cached = _SERVICE_ACCOUNT_CACHE.get(raw)
    if cached is not None:
        return cached
    path = Path(raw)
    info: Any = None
    try:
        if path.exists():
            info = json.loads(path.read_text(encoding="utf-8"))
        else:
            info = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CalendarApiError(f"Invalid GOOGLE_SERVICE_ACCOUNT_FILE: {exc}") from exc
    if not isinstance(info, dict) or "client_email" not in info:
        raise CalendarApiError("Service account key is missing client_email")
    _SERVICE_ACCOUNT_CACHE[raw] = info
    return info


def service_account_access_token() -> tuple[str, datetime]:
    """JWT-bearer assertion for the configured service account."""
    info = _load_service_account_info()
    now = datetime.now(timezone.utc)
    claims = {
        "iss": info["client_email"],
        "scope": " ".join(CALENDAR_SCOPES),
        "aud": TOKEN_URL,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    try:
        assertion = jwt.encode(
            claims, info["private_key"], algorithm="RS256"
        )
    except Exception as exc:  # pragma: no cover - malformed key
        raise CalendarApiError(f"Could not sign the service-account assertion: {exc}") from exc

    payload = _post_form(
        TOKEN_URL,
        {
            "assertion": assertion,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        },
    )
    expires_in = int(payload.get("expires_in", 3600))
    return payload["access_token"], now + timedelta(seconds=expires_in - 60)


def is_service_account_configured() -> bool:
    return bool(
        settings.GOOGLE_CALENDAR_ENABLED and settings.GOOGLE_SERVICE_ACCOUNT_FILE
    )


def is_calendar_enabled() -> bool:
    return bool(settings.GOOGLE_CALENDAR_ENABLED)


# OAuth2 consent helpers (used by the "connect my calendar" flow)


def build_authorization_url(*, redirect_uri: str, state: str, login_hint: str = "") -> str:
    """Google consent URL for the calendar scope."""
    from urllib.parse import urlencode

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    if login_hint:
        params["login_hint"] = login_hint
    return f"{AUTH_URL}?{urlencode(params)}"


def is_oauth_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


# Calendar client


class GoogleCalendarClient:
    """Minimal Calendar v3 client scoped to the events the module needs."""

    def __init__(
        self,
        *,
        access_token: str,
        calendar_id: str = "primary",
        on_token_refreshed=None,
    ) -> None:
        self._access_token = access_token
        self.calendar_id = calendar_id
        self._on_token_refreshed = on_token_refreshed

    @classmethod
    def from_service_account(cls, calendar_id: str | None = None) -> "GoogleCalendarClient":
        token, _expires = service_account_access_token()
        return cls(
            access_token=token,
            calendar_id=calendar_id or settings.GOOGLE_CALENDAR_ID or "primary",
        )

    @classmethod
    def from_refresh_token(
        cls,
        refresh_token: str,
        *,
        calendar_id: str = "primary",
        on_token_refreshed=None,
    ) -> "GoogleCalendarClient":
        payload = refresh_access_token(refresh_token)
        expires_in = int(payload.get("expires_in", 3600))
        if on_token_refreshed is not None:
            on_token_refreshed(
                access_token=payload["access_token"],
                expires_at=datetime.now(timezone.utc)
                + timedelta(seconds=max(expires_in - 60, 30)),
            )
        return cls(access_token=payload["access_token"], calendar_id=calendar_id)

    # HTTP
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _url(self, event_id: str | None = None, *, action: str = "") -> str:
        base = f"{CALENDAR_API}/calendars/{self.calendar_id}/events"
        if event_id:
            base = f"{base}/{event_id}"
        return f"{base}{action}" if action else base

    def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        try:
            response = httpx.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
                params=params,
                timeout=settings.GOOGLE_OAUTH_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            raise CalendarApiError(f"Google Calendar request failed: {exc}") from exc

        if response.status_code >= 400:
            raise CalendarApiError(
                f"Google Calendar returned {response.status_code}: {response.text[:500]}"
            )
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    # Events
    def create_event(
        self,
        *,
        summary: str,
        description: str = "",
        start: datetime,
        end: datetime,
        timezone_name: str = "UTC",
        attendees: Iterable[str] = (),
        location: str = "",
        create_meet: bool = True,
        conference_request_id: str | None = None,
    ) -> CalendarEventResult:
        body = self._event_body(
            summary=summary,
            description=description,
            start=start,
            end=end,
            timezone_name=timezone_name,
            attendees=attendees,
            location=location,
            create_meet=create_meet,
            conference_request_id=conference_request_id or uuid.uuid4().hex,
        )
        params = {"conferenceDataVersion": "1"} if create_meet else None
        payload = self._request("POST", self._url(), json_body=body, params=params)
        return self._to_result(payload)

    def update_event(
        self,
        event_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        timezone_name: str = "UTC",
        attendees: Iterable[str] | None = None,
        create_meet: bool = False,
        conference_request_id: str | None = None,
    ) -> CalendarEventResult:
        body = self._event_body(
            summary=summary or "",
            description=description or "",
            start=start,
            end=end,
            timezone_name=timezone_name,
            attendees=attendees or (),
            create_meet=create_meet,
            conference_request_id=conference_request_id or uuid.uuid4().hex,
        )
        params = {"conferenceDataVersion": "1"} if create_meet else None
        payload = self._request(
            "PATCH", self._url(event_id), json_body=body, params=params
        )
        return self._to_result(payload)

    def cancel_event(self, event_id: str) -> bool:
        self._request("DELETE", self._url(event_id))
        return True

    def get_event(self, event_id: str) -> dict:
        return self._request("GET", self._url(event_id))

    # (De)serialisation
    @staticmethod
    def _event_payload(
        *,
        summary: str,
        description: str,
        start: datetime,
        end: datetime,
        timezone_name: str,
        attendees: Iterable[str],
    ) -> dict:
        payload: dict[str, Any] = {
            "summary": summary[:900],
            "description": (description or "")[:8000],
            "start": {"dateTime": _rfc3339(start), "timeZone": timezone_name},
            "end": {"dateTime": _rfc3339(end), "timeZone": timezone_name},
            "guestsCanSeeOtherGuests": False,
            "guestsCanModify": False,
        }
        emails = [email for email in dict.fromkeys(attendees) if email]
        if emails:
            payload["attendees"] = [{"email": email} for email in emails]
        return payload

    def _event_body(
        self,
        *,
        summary: str,
        description: str,
        start: datetime | None,
        end: datetime | None,
        timezone_name: str,
        attendees: Iterable[str],
        create_meet: bool,
        conference_request_id: str,
    ) -> dict:
        if start is None or end is None:
            raise CalendarApiError("start and end are required to build an event")
        body = self._event_payload(
            summary=summary,
            description=description,
            start=start,
            end=end,
            timezone_name=timezone_name,
            attendees=attendees,
        )
        if create_meet:
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": conference_request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        return body

    def _to_result(self, payload: dict) -> CalendarEventResult:
        conference = payload.get("conferenceData") or {}
        entry_points = conference.get("entryPoints") or []
        meet_link = None
        meet_code = None
        for entry in entry_points:
            if entry.get("entryPointType") == "video":
                meet_link = entry.get("uri") or entry.get("label")
                meet_code = (meet_link or "").rstrip("/").rsplit("/", 1)[-1] or None
                break
        if not meet_link:
            # Older API responses (and some updates) keep the plain field.
            meet_link = payload.get("hangoutLink")
            meet_code = (meet_link or "").rstrip("/").rsplit("/", 1)[-1] or None
        return CalendarEventResult(
            event_id=str(payload.get("id") or ""),
            html_link=payload.get("htmlLink"),
            meet_link=meet_link,
            meet_code=meet_code,
            calendar_id=self.calendar_id,
            raw=payload,
        )


def _rfc3339(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "CALENDAR_SCOPES",
    "CalendarApiError",
    "CalendarEventResult",
    "GoogleCalendarClient",
    "build_authorization_url",
    "exchange_authorization_code",
    "is_calendar_enabled",
    "is_oauth_configured",
    "is_service_account_configured",
    "refresh_access_token",
    "service_account_access_token",
]

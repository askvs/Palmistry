"""Bridge between bookings and Google Calendar (FR-BOOK-004 / FR-BOOK-005)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.booking import (
    Booking,
    CalendarSyncStatus,
    ConsultantCalendarConnection,
    ConsultantProfile,
)
from app.services.booking import google_calendar as gcal
from app.services.booking.errors import CalendarError

logger = logging.getLogger(__name__)

_PLATFORM_CALENDAR_NOTE = "platform"


def _service_account_client() -> gcal.GoogleCalendarClient | None:
    if not (settings.GOOGLE_CALENDAR_ENABLED and settings.GOOGLE_SERVICE_ACCOUNT_FILE):
        return None
    try:
        return gcal.GoogleCalendarClient.from_service_account()
    except gcal.CalendarApiError as exc:
        logger.error("service account calendar client unavailable: %s", exc)
        return None


def _consultant_client(
    db: Session, consultant: ConsultantProfile
) -> tuple[gcal.GoogleCalendarClient | None, bool]:
    """Return (client, is_consultant_calendar)."""
    connection = consultant.calendar_connection
    if connection is None or not connection.is_active or not connection.refresh_token:
        connection = db.scalar(
            _select_connection(consultant.id)
        )
    if connection is not None and connection.is_active and connection.refresh_token:
        try:
            client = gcal.GoogleCalendarClient.from_refresh_token(
                connection.refresh_token,
                calendar_id=connection.calendar_id or "primary",
                on_token_refreshed=lambda **kw: _persist_refreshed_token(
                    db, connection, **kw
                ),
            )
            connection.last_error = None
            return client, True
        except gcal.CalendarApiError as exc:
            connection.last_error = str(exc)[:1000]
            db.commit()
            logger.warning(
                "consultant calendar connection %s failed: %s", connection.id, exc
            )
    return _service_account_client(), False


def _select_connection(consultant_id):
    from sqlalchemy import select

    return select(ConsultantCalendarConnection).where(
        ConsultantCalendarConnection.consultant_id == consultant_id
    )


def _persist_refreshed_token(
    db: Session,
    connection: ConsultantCalendarConnection,
    *,
    access_token: str,
    expires_at: datetime,
) -> None:
    # Cache token expiry on the connection.
    connection.access_token_expires_at = expires_at
    try:
        db.commit()
    except Exception:  # pragma: no cover - booking must not depend on this
        db.rollback()


def _attendees(booking: Booking, consultant: ConsultantProfile) -> list[str]:
    emails: list[str] = []
    if booking.user is not None:
        emails.append(booking.user.email)
    if consultant.user is not None:
        emails.append(consultant.user.email)
    return [email for email in emails if email]


def _event_title(booking: Booking, consultant: ConsultantProfile) -> str:
    consultant_name = consultant.user.full_name if consultant.user is not None else "your consultant"
    return f"MysticLens session · {consultant_name} · {booking.subject}"[:900]


def _event_description(booking: Booking, consultant: ConsultantProfile) -> str:
    consultant_name = consultant.user.full_name if consultant.user is not None else "Consultant"
    seeker_name = booking.user.full_name if booking.user is not None else "Seeker"
    lines = [
        f"Live consultation booked on MysticLens (booking {booking.id}).",
        "",
        f"Consultant: {consultant_name}",
        f"Seeker: {seeker_name}",
        f"Focus: {booking.subject}",
        f"Starts: {booking.start_time.isoformat()}",
        f"Duration: {booking.duration_minutes} minutes",
    ]
    if booking.notes:
        lines += ["", "Seeker's notes:", booking.notes]
    return "\n".join(lines)


def create_calendar_event(db: Session, booking: Booking) -> CalendarSyncStatus:
    """Create the Google Calendar event + Meet link for an accepted booking."""
    if not settings.GOOGLE_CALENDAR_ENABLED:
        booking.calendar_sync_status = CalendarSyncStatus.disabled
        booking.calendar_error = None
        db.commit()
        return booking.calendar_sync_status

    consultant = booking.consultant
    client, is_consultant_calendar = _consultant_client(db, consultant)
    if client is None:
        booking.calendar_sync_status = CalendarSyncStatus.not_created
        booking.calendar_error = (
            "No Google Calendar is configured for this consultant. Connect a "
            "calendar in Consultant Studio to generate a Meet link."
        )
        db.commit()
        logger.info(
            "booking %s has no calendar client; skipping event creation",
            booking.id,
        )
        return booking.calendar_sync_status

    try:
        result = client.create_event(
            summary=_event_title(booking, consultant),
            description=_event_description(booking, consultant),
            start=booking.start_time,
            end=booking.end_time,
            timezone_name=booking.timezone or "UTC",
            attendees=_attendees(booking, consultant),
            create_meet=settings.GOOGLE_CALENDAR_CREATE_MEET,
            conference_request_id=str(booking.id),
        )
    except gcal.CalendarApiError as exc:
        booking.calendar_sync_status = CalendarSyncStatus.failed
        booking.calendar_error = str(exc)[:2000]
        db.commit()
        logger.error("calendar event creation failed for booking %s: %s", booking.id, exc)
        return booking.calendar_sync_status

    booking.google_event_id = result.event_id or None
    booking.google_calendar_id = result.calendar_id
    # Prefer the Google Meet link when available.
    booking.meet_link = result.meet_link or booking.meet_link
    booking.meet_code = result.meet_code
    booking.calendar_sync_status = CalendarSyncStatus.created
    booking.calendar_synced_at = datetime.now(timezone.utc)
    booking.calendar_error = None
    db.commit()
    logger.info(
        "calendar event %s created for booking %s (meet=%s)",
        result.event_id,
        booking.id,
        bool(result.meet_link),
    )
    return booking.calendar_sync_status


def cancel_calendar_event(db: Session, booking: Booking) -> CalendarSyncStatus:
    """Delete the backing Google Calendar event. Never raises."""
    if not booking.google_event_id:
        return booking.calendar_sync_status
    if not settings.GOOGLE_CALENDAR_ENABLED:
        return booking.calendar_sync_status

    client, _ = _consultant_client(db, booking.consultant)
    if client is None:
        booking.calendar_error = "Calendar is unavailable; the remote event was left untouched."
        db.commit()
        return booking.calendar_sync_status

    try:
        client.cancel_event(booking.google_event_id)
    except gcal.CalendarApiError as exc:
        booking.calendar_error = str(exc)[:2000]
        db.commit()
        logger.error("calendar event cancel failed for booking %s: %s", booking.id, exc)
        return booking.calendar_sync_status

    booking.calendar_sync_status = CalendarSyncStatus.cancelled
    db.commit()
    logger.info("calendar event %s cancelled for booking %s", booking.google_event_id, booking.id)
    return booking.calendar_sync_status


def retry_calendar_event(db: Session, booking: Booking) -> CalendarSyncStatus:
    """Re-attempt event creation, patching the existing event if there is one."""
    if not settings.GOOGLE_CALENDAR_ENABLED:
        raise CalendarError("Google Calendar integration is disabled on this server")

    if booking.google_event_id:
        client, _ = _consultant_client(db, booking.consultant)
        if client is None:
            raise CalendarError("No Google Calendar is available for this consultant")
        try:
            result = client.get_event(booking.google_event_id)
        except gcal.CalendarApiError as exc:
            raise CalendarError(str(exc)) from exc
        meet_link = _extract_meet(result)
        booking.calendar_sync_status = CalendarSyncStatus.created
        booking.calendar_synced_at = datetime.now(timezone.utc)
        booking.calendar_error = None
        booking.meet_link = meet_link or booking.meet_link
        db.commit()
        return booking.calendar_sync_status

    return create_calendar_event(db, booking)


def _extract_meet(payload: dict) -> str | None:
    for entry in (payload.get("conferenceData") or {}).get("entryPoints") or []:
        if entry.get("entryPointType") == "video":
            return entry.get("uri")
    return payload.get("hangoutLink")


__all__ = [
    "cancel_calendar_event",
    "create_calendar_event",
    "retry_calendar_event",
]

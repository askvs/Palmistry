"""Booking notifications, delivered through the existing in-app channel."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.notification import NotificationPriority, NotificationType
from app.services.notifications.service import create_notification

logger = logging.getLogger(__name__)

# Where each role lands when it clicks through the notification.
SEEKER_ACTION_URL = "/sessions"
CONSULTANT_ACTION_URL = "/consultant-studio"

_TYPE_BY_STATUS = {
    BookingStatus.accepted: NotificationType.booking_accepted,
    BookingStatus.rejected: NotificationType.booking_rejected,
    BookingStatus.cancelled: NotificationType.booking_cancelled,
    BookingStatus.completed: NotificationType.booking_completed,
}

_COPY_BY_STATUS = {
    BookingStatus.accepted: ("Session confirmed", "Your session is confirmed and the Google Meet link is ready."),
    BookingStatus.rejected: ("Session declined", "The consultant could not take this session."),
    BookingStatus.cancelled: ("Session cancelled", "This session has been cancelled."),
    BookingStatus.completed: ("Session completed", "This session has been marked complete."),
}


def _when(booking: Booking) -> str:
    return booking.start_time.strftime("%a %d %b %Y, %H:%M UTC")


def _names(booking: Booking) -> tuple[str, str]:
    seeker = booking.user.full_name if booking.user is not None else "The seeker"
    consultant = (
        booking.consultant.user.full_name
        if booking.consultant is not None and booking.consultant.user is not None
        else "your consultant"
    )
    return seeker, consultant


def notify_booking_requested(db: Session, booking: Booking) -> None:
    """Pending booking: alert the consultant."""
    seeker, consultant_name = _names(booking)
    _safe(
        db,
        recipient=booking.consultant.user_id if booking.consultant else None,
        notification_type=NotificationType.booking_requested,
        title="New booking request",
        message=(
            f"{seeker} requested a session with you on {_when(booking)} "
            f"({booking.duration_minutes} min)."
        ),
        priority=NotificationPriority.high,
        action_url=CONSULTANT_ACTION_URL,
        metadata={"booking_id": str(booking.id), "subject": booking.subject},
        idempotency_key=f"booking_requested_{booking.id}",
    )
    logger.info("booking %s request notification queued", booking.id)


def notify_status_changed(
    db: Session,
    booking: Booking,
    *,
    status: BookingStatus,
    actor_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> None:
    """Tell the *other* party about an accept/reject/cancel/complete."""
    notification_type = _TYPE_BY_STATUS.get(status)
    if notification_type is None:
        return
    title, default_message = _COPY_BY_STATUS[status]
    seeker, consultant_name = _names(booking)

    actor_is_consultant = bool(
        actor_id and booking.consultant and actor_id == booking.consultant.user_id
    )

    if actor_is_consultant:
        # Consultant acted → notify the seeker.
        recipient = booking.user_id
        message = (
            f"{consultant_name} responded to your session on {_when(booking)}. "
            f"{default_message}"
        )
        if reason and status in (BookingStatus.rejected, BookingStatus.cancelled):
            message += f" Reason: {reason}"
    else:
        # Seeker acted (cancelled) → notify the consultant.
        recipient = booking.consultant.user_id if booking.consultant else None
        message = f"{seeker} cancelled the session on {_when(booking)}."
        if reason:
            message += f" Reason: {reason}"
        if status == BookingStatus.cancelled:
            title = "Session cancelled by seeker"

    _safe(
        db,
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=NotificationPriority.high
        if status in (BookingStatus.accepted, BookingStatus.cancelled)
        else NotificationPriority.normal,
        action_url=CONSULTANT_ACTION_URL if recipient == (booking.consultant.user_id if booking.consultant else None) else SEEKER_ACTION_URL,
        metadata={"booking_id": str(booking.id), "status": status.value},
        idempotency_key=f"booking_{status.value}_{booking.id}",
    )


def notify_booking_countered(db: Session, booking: Booking, *, awaiting: str) -> None:
    """A party proposed/changed the time; alert whoever now needs to respond."""
    seeker, consultant_name = _names(booking)
    if awaiting == "consultant":
        recipient = booking.consultant.user_id if booking.consultant else None
        action_url = CONSULTANT_ACTION_URL
        title = "New time proposed"
        message = (
            f"{seeker} proposed a new time for your session: "
            f"{_when(booking)} ({booking.duration_minutes} min)."
        )
    else:  # awaiting the seeker
        recipient = booking.user_id
        action_url = SEEKER_ACTION_URL
        title = "Consultant proposed a new time"
        message = (
            f"{consultant_name} proposed {_when(booking)} "
            f"({booking.duration_minutes} min). Confirm it or suggest another time."
        )
    _safe(
        db,
        recipient=recipient,
        notification_type=NotificationType.booking_requested,
        title=title,
        message=message,
        priority=NotificationPriority.high,
        action_url=action_url,
        metadata={"booking_id": str(booking.id), "awaiting": awaiting},
        idempotency_key=f"booking_countered_{booking.id}_{int(_now().timestamp())}",
    )


def notify_reminder(db: Session, booking: Booking, *, minutes_ahead: int) -> bool:
    """Send (or skip, when already sent) a session reminder to both parties."""
    horizon = f"{minutes_ahead}m"
    created = 0
    for recipient, role_label in (
        (booking.user_id, "seeker"),
        (booking.consultant.user_id if booking.consultant else None, "consultant"),
    ):
        if recipient is None:
            continue
        notification = _safe(
            db,
            recipient=recipient,
            notification_type=NotificationType.booking_reminder,
            title="Session reminder",
            message=(
                f"Your live consultation starts in {_humanise(minutes_ahead)} "
                f"({_when(booking)})."
            ),
            priority=NotificationPriority.high
            if minutes_ahead <= 60
            else NotificationPriority.normal,
            action_url=CONSULTANT_ACTION_URL if role_label == "consultant" else SEEKER_ACTION_URL,
            metadata={
                "booking_id": str(booking.id),
                "lead_minutes": minutes_ahead,
                "meet_link": booking.meet_link,
            },
            idempotency_key=f"booking_reminder_{horizon}_{booking.id}_{recipient}",
        )
        if notification is not None and notification.created_at is not None:
            created += 1
    return created > 0


def _humanise(minutes: int) -> str:
    if minutes >= 1440 and minutes % 1440 == 0:
        days = minutes // 1440
        return f"{days} day{'s' if days > 1 else ''}"
    if minutes >= 60 and minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours} hour{'s' if hours > 1 else ''}"
    return f"{minutes} minutes"


def _safe(
    db: Session,
    *,
    recipient: uuid.UUID | None,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority,
    action_url: str,
    metadata: dict,
    idempotency_key: str,
):
    """Wrap create_notification so a failure never breaks the caller."""
    if recipient is None:
        return None
    try:
        return create_notification(
            db=db,
            user_id=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("failed to create notification %s", idempotency_key)
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "notify_booking_requested",
    "notify_booking_countered",
    "notify_reminder",
    "notify_status_changed",
]

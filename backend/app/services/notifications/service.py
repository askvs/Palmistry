"""Notification service for creating, managing, and delivering notifications."""
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.models.profile import Profile
from app.models.user import User, UserRole
from app.services.notifications.schemas import (
    NotificationCreate,
    NotificationPreferenceUpdate,
)

if TYPE_CHECKING:
    from app.models.notification import Notification

logger = logging.getLogger(__name__)

# Default daily guidance time (8am in user's local timezone)
DAILY_GUIDANCE_HOUR = 8


class NotificationServiceError(Exception):
    """Base notification service error."""


class NotificationNotFoundError(NotificationServiceError):
    """Notification not found error."""


class ProfileNotFoundError(NotificationServiceError):
    """Profile not found error."""


def get_or_create_profile(db: Session, user_id: uuid.UUID) -> Profile:
    """Get or create a profile for a user."""
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info("Created profile for user_id=%s", user_id)
    return profile


def get_notification_preferences(db: Session, user_id: uuid.UUID) -> dict:
    """Get notification preferences for a user (in-app only)."""
    profile = get_or_create_profile(db, user_id)

    # In-app is always on; toggles map to profile flags.
    return {
        "in_app_notifications": True,
        "daily_guidance": bool(profile.notify_daily_guidance),
        "reading_reminders": bool(profile.notify_reminders),
        "insight_updates": bool(profile.notify_insights),
        "spiritual_growth": bool(profile.notify_growth),
        "platform_announcements": bool(profile.notify_announcements),
    }


def update_notification_preferences(
    db: Session, user_id: uuid.UUID, prefs: NotificationPreferenceUpdate
) -> dict:
    """Update notification preferences for a user (in-app only)."""
    profile = get_or_create_profile(db, user_id)

    # Map each in-app preference onto its persisted profile flag.
    _to_flag = {
        "daily_guidance": "notify_daily_guidance",
        "reading_reminders": "notify_reminders",
        "insight_updates": "notify_insights",
        "spiritual_growth": "notify_growth",
        "platform_announcements": "notify_announcements",
    }
    for pref_key, flag in _to_flag.items():
        value = getattr(prefs, pref_key, None)
        if value is not None:
            setattr(profile, flag, value)

    db.commit()
    db.refresh(profile)

    return get_notification_preferences(db, user_id)


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.normal,
    action_url: str | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> Notification:
    """Create a new notification."""
    # Check for duplicate using idempotency key
    if idempotency_key:
        existing = db.scalar(
            select(Notification).where(
                Notification.idempotency_key == idempotency_key
            )
        )
        if existing:
            logger.info(
                "Duplicate notification with idempotency_key=%s, returning existing",
                idempotency_key,
            )
            return existing

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action_url=action_url,
        metadata=metadata or {},
        idempotency_key=idempotency_key,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    logger.info(
        "Created notification id=%s type=%s for user_id=%s",
        notification.id,
        notification_type.value,
        user_id,
    )

    return notification


def get_user_notifications(
    db: Session,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    include_read: bool = True,
    notification_type: NotificationType | None = None,
) -> tuple[list[Notification], int]:
    """Get paginated notifications for a user."""
    query = select(Notification).where(Notification.user_id == user_id)

    if not include_read:
        query = query.where(Notification.is_read == False)  # noqa: E712

    if notification_type:
        query = query.where(Notification.type == notification_type)

    query = query.order_by(Notification.created_at.desc())

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    notifications = db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return notifications, total or 0


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    """Get unread notification count."""
    count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return count or 0


def mark_notification_read(db: Session, notification_id: uuid.UUID) -> bool:
    """Mark a single notification as read."""
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id)
    )
    if notification is None:
        raise NotificationNotFoundError(f"Notification {notification_id} not found")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)

    logger.info(
        "Marked notification id=%s as read", notification_id,
    )
    return True


def mark_all_notifications_read(db: Session, user_id: uuid.UUID) -> int:
    """Mark all notifications as read for a user."""
    result = db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    db.commit()

    logger.info(
        "Marked %s notifications as read for user_id=%s", result.rowcount, user_id
    )
    return result.rowcount or 0


def delete_notification(db: Session, notification_id: uuid.UUID) -> bool:
    """Delete a notification."""
    result = db.execute(
        delete(Notification).where(Notification.id == notification_id)
    )
    db.commit()

    if result.rowcount == 0:
        return False

    logger.info("Deleted notification id=%s", notification_id)
    return True


def trigger_notification(
    db: Session,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.normal,
    action_url: str | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> Notification:
    """Create an in-app notification for a user."""
    return create_notification(
        db=db,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action_url=action_url,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )


# Event-driven delivery
# In-app notifications are the only channel.


def _safe_create_notification(db: Session, *, user_id, **fields) -> bool:
    """Create a notification, swallowing and rolling back any error."""
    try:
        create_notification(db=db, user_id=user_id, **fields)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "Failed to create notification user_id=%s type=%s: %s",
            user_id,
            fields.get("notification_type"),
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return False


def _recipient_ids_by_roles(db: Session, roles: list[UserRole]) -> list[uuid.UUID]:
    return list(
        db.scalars(
            select(User.id).where(User.role.in_(list(roles)), User.is_active.is_(True))
        ).all()
    )


def notify_user(
    db: Session,
    user_id,
    *,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.normal,
    action_url: str | None = None,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
) -> bool:
    """Create an in-app notification for a single user (never raises)."""
    if user_id is None:
        return False
    return _safe_create_notification(
        db,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action_url=action_url,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )


def notify_roles(
    db: Session,
    roles: list[UserRole],
    *,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.normal,
    action_url: str | None = None,
    idempotency_prefix: str | None = None,
    metadata: dict | None = None,
    exclude_user_ids: list | None = None,
) -> int:
    """Create an in-app notification for every active user in `roles`."""
    try:
        recipient_ids = _recipient_ids_by_roles(db, roles)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to resolve recipients for roles=%s: %s", roles, exc)
        return 0

    exclude = set(exclude_user_ids or ())
    count = 0
    for uid in recipient_ids:
        if uid in exclude:
            continue
        key = f"{idempotency_prefix}:{uid}" if idempotency_prefix else None
        if _safe_create_notification(
            db,
            user_id=uid,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            idempotency_key=key,
            metadata=metadata,
        ):
            count += 1
    return count


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


@contextmanager
def _session_scope():
    """Yield a short-lived session isolated from the caller's."""
    from app.db import session as db_session_mod

    db_session_mod.get_engine()
    db = db_session_mod._SessionLocal()
    try:
        yield db
    finally:
        db.close()


def notify_new_user(*, new_user_id, new_user_email, new_user_role) -> int:
    """Tell administrators that a new account was created."""
    try:
        with _session_scope() as db:
            return notify_roles(
                db,
                [UserRole.admin],
                notification_type=NotificationType.new_user,
                title="New user joined",
                message=f"{new_user_email} just created an account.",
                action_url="/dashboard",
                idempotency_prefix=f"new_user_{new_user_id}",
                metadata={"role": _enum_value(new_user_role)},
                exclude_user_ids=[new_user_id],
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("notify_new_user failed for user %s: %s", new_user_id, exc)
        return 0


def notify_new_reading(*, reading_id, owner_id, reading_type) -> None:
    """Confirm the reading with its owner and alert reviewing staff."""
    reading_type_s = _enum_value(reading_type)
    try:
        with _session_scope() as db:
            notify_user(
                db,
                owner_id,
                notification_type=NotificationType.reading_completed,
                title="Your reading is ready",
                message="Your new reading has been generated. Open it to explore your insights.",
                action_url=f"/readings/{reading_id}",
                idempotency_key=f"reading_completed_{reading_id}",
                metadata={"reading_type": reading_type_s},
            )
            notify_roles(
                db,
                [UserRole.tarot_reader, UserRole.spiritual_consultant],
                notification_type=NotificationType.new_reading,
                title="New reading to review",
                message=f"A new {reading_type_s} reading was submitted by a seeker.",
                action_url="/dashboard",
                idempotency_prefix=f"new_reading_{reading_id}",
                metadata={"reading_type": reading_type_s},
                exclude_user_ids=[owner_id],
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("notify_new_reading failed for reading %s: %s", reading_id, exc)


def notify_new_question(*, consultation_id, asker_id, asker_name, topic) -> int:
    """Alert consultants that a seeker submitted a consultation request."""
    try:
        with _session_scope() as db:
            return notify_roles(
                db,
                [UserRole.spiritual_consultant],
                notification_type=NotificationType.new_question,
                title="New consultation request",
                message=f"{asker_name} asked about: {topic}",
                action_url="/dashboard",
                idempotency_prefix=f"new_question_{consultation_id}",
                metadata={"consultation_id": str(consultation_id)},
                exclude_user_ids=[asker_id],
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("notify_new_question failed for consultation %s: %s", consultation_id, exc)
        return 0


def notify_consultation_message(
    *,
    message_id,
    consultation_id,
    owner_id,
    sender_is_staff: bool,
    sender_id,
    sender_name,
    body_snippet: str,
) -> None:
    """Route a consultation message to the other side of the thread."""
    try:
        with _session_scope() as db:
            if sender_is_staff:
                notify_user(
                    db,
                    owner_id,
                    notification_type=NotificationType.insight_update,
                    title="New reply on your consultation",
                    message="A consultant replied to your question.",
                    action_url=f"/consultations/{consultation_id}",
                    idempotency_key=f"consult_reply_{message_id}",
                )
            else:
                notify_roles(
                    db,
                    [UserRole.spiritual_consultant],
                    notification_type=NotificationType.new_question,
                    title="New message on a consultation",
                    message=f"{sender_name}: {body_snippet}",
                    action_url="/dashboard",
                    idempotency_prefix=f"consult_msg_{message_id}",
                    exclude_user_ids=[sender_id],
                )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("notify_consultation_message failed for message %s: %s", message_id, exc)

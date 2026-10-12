"""Notification API endpoints."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.rbac import get_current_user, require_admin
from app.config import settings
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.notifications import (
    NotificationOut,
    NotificationPreferenceOut,
    NotificationCountOut,
    NotificationPreferenceUpdate,
)
from app.services.notifications.service import (
    get_notification_preferences,
    update_notification_preferences,
    get_user_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
    create_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[NotificationOut])
async def get_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    include_read: bool = True,
    notification_type: str | None = None,
) -> Any:
    """Get notifications for the current user."""
    type_enum = None
    if notification_type:
        try:
            type_enum = NotificationType(notification_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification type. Valid types: {[t.value for t in NotificationType]}",
            )

    notifications, total = get_user_notifications(
        db=db,
        user_id=user.id,
        page=1,
        page_size=100,
        include_read=include_read,
        notification_type=type_enum,
    )

    return notifications


@router.get("/unread-count", response_model=NotificationCountOut)
async def get_unread_count_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Get unread notification count."""
    count = get_unread_count(db=db, user_id=user.id)
    return NotificationCountOut(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Mark a single notification as read."""
    try:
        notif_id = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification ID format",
        )

    # Verify ownership
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == user.id,
        )
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    mark_notification_read(db=db, notification_id=notif_id)
    db.refresh(notification)
    return notification


@router.patch("/read-all", response_model=NotificationCountOut)
async def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Mark all notifications as read."""
    mark_all_notifications_read(db=db, user_id=user.id)
    new_count = get_unread_count(db=db, user_id=user.id)
    return NotificationCountOut(unread_count=new_count)


@router.get("/preferences", response_model=NotificationPreferenceOut)
async def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Get notification preferences."""
    prefs = get_notification_preferences(db=db, user_id=user.id)
    return NotificationPreferenceOut(**prefs)


@router.put("/preferences", response_model=NotificationPreferenceOut)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    """Update notification preferences."""
    update_notification_preferences(db=db, user_id=user.id, prefs=payload)
    return await get_preferences(db=db, user=user)


# Admin endpoints

@router.post("/admin/announcements", tags=["admin"])
async def create_announcement(
    title: str,
    message: str,
    audience: str = "all",
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> Any:
    """Admin creates an announcement."""
    if audience == "all":
        users = db.scalars(select(User)).all()
        sent = 0
        for u in users:
            try:
                create_notification(
                    db=db,
                    user_id=u.id,
                    notification_type=NotificationType.platform_announcement,
                    title=title,
                    message=message,
                    priority="normal",
                    action_url="/announcements",
                    idempotency_key=f"announcement_{u.id}_{datetime.now(timezone.utc).timestamp()}",
                )
                sent += 1
            except Exception as e:
                logger.error(
                    "Failed to create announcement for user %s: %s", u.id, e,
                )
        return {"message": f"Announcement created for {sent} users"}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Audience 'all' only available currently",
    )


@router.get("/admin/announcements", tags=["admin"])
async def list_announcements(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> Any:
    """List announcements."""
    announcements = db.scalars(
        select(Notification).where(Notification.type == NotificationType.platform_announcement)
    ).all()
    return announcements

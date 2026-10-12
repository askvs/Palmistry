"""Notification service schemas."""
import uuid
from typing import Any

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationCreate(BaseModel):
    """Request to create a notification."""
    user_id: uuid.UUID
    notification_type: NotificationType
    title: str
    message: str
    priority: str = "normal"
    action_url: str | None = None
    metadata: dict[str, Any] = {}
    idempotency_key: str | None = None


class NotificationPreferenceUpdate(BaseModel):
    """Request to update notification preferences."""
    daily_guidance: bool | None = None
    reading_reminders: bool | None = None
    insight_updates: bool | None = None
    spiritual_growth: bool | None = None
    platform_announcements: bool | None = None
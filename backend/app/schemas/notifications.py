"""Notification schemas."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


# Request Schemas

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


# Response Schemas

class NotificationOut(BaseModel):
    """Notification response."""
    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    priority: str
    is_read: bool
    read_at: datetime | None
    action_url: str | None
    notification_metadata: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceOut(BaseModel):
    """Notification preferences response."""
    in_app_notifications: bool
    daily_guidance: bool
    reading_reminders: bool
    insight_updates: bool
    spiritual_growth: bool
    platform_announcements: bool

    model_config = ConfigDict(from_attributes=True)


class NotificationCountOut(BaseModel):
    """Unread notification count response."""
    unread_count: int

    model_config = ConfigDict(from_attributes=True)

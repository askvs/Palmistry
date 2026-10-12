"""Notification service package."""

from app.services.notifications.service import (
    create_notification,
    get_user_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
    get_notification_preferences,
    update_notification_preferences,
    trigger_notification,
    notify_user,
    notify_roles,
    notify_new_user,
    notify_new_reading,
    notify_new_question,
    notify_consultation_message,
)

__all__ = [
    "create_notification",
    "get_user_notifications",
    "get_unread_count",
    "mark_notification_read",
    "mark_all_notifications_read",
    "get_notification_preferences",
    "update_notification_preferences",
    "trigger_notification",
    "notify_user",
    "notify_roles",
    "notify_new_user",
    "notify_new_reading",
    "notify_new_question",
    "notify_consultation_message",
]

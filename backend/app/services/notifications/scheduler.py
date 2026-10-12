"""Notification scheduler implementation."""
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import NotificationType
from app.models.profile import Profile
from app.services.notifications.service import create_notification

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def _ensure_started() -> None:
    """Start the scheduler once per process."""
    if scheduler.running:
        return
    scheduler.start()
    logger.info("Notification scheduler started")

def start_scheduler(db: Session):
    """Start the notification scheduler."""
    scheduler.add_job(
        run_daily_guidance_scheduler,
        'cron',
        hour=settings.DAILY_GUIDANCE_HOUR,
        minute=0,
        args=[db],
        id='daily_guidance',
        replace_existing=True,
    )

    scheduler.add_job(
        run_reading_reminder_scheduler,
        'interval',
        hours=24,
        minutes=0,
        args=[db],
        id='reading_reminder',
        replace_existing=True,
    )

    _ensure_started()

def run_daily_guidance_scheduler(db: Session) -> int:
    """Run daily guidance notification scheduler."""
    count = 0

    # Get all users with daily_guidance enabled
    profiles = db.scalars(
        select(Profile).where(Profile.notify_daily_guidance == True)  # noqa: E712
    ).all()

    for profile in profiles:
        try:
            # Skip users without a profile
            if not profile.user_id:
                continue

            # Create notification
            create_notification(
                db=db,
                user_id=profile.user_id,
                notification_type=NotificationType.daily_guidance,
                title="Your daily guidance",
                message="Your personalized guidance for today is ready. Take a moment to reflect.",
                priority="normal",
                action_url="/dashboard",
                idempotency_key=f"daily_guidance_{profile.user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            )
            count += 1

        except Exception as e:
            logger.error(
                "Failed to send daily guidance for user_id=%s: %s",
                profile.user_id,
                e,
            )

    logger.info("Daily guidance scheduler completed: %s notifications sent", count)
    return count


def run_reading_reminder_scheduler(db: Session) -> int:
    """Run reading reminder scheduler."""
    count = 0

    # Get all users with reminders enabled
    profiles = db.scalars(
        select(Profile).where(Profile.notify_reminders == True)  # noqa: E712
    ).all()

    for profile in profiles:
        try:
            # Skip users without a profile
            if not profile.user_id:
                continue

            # Create a reminder notification
            create_notification(
                db=db,
                user_id=profile.user_id,
                notification_type=NotificationType.reading_reminder,
                title="Your reading reminder",
                message="You planned to continue your reading journey. Your next reading session is ready.",
                priority="normal",
                action_url="/readings",
                idempotency_key=f"reading_reminder_{profile.user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            )
            count += 1

        except Exception as e:
            logger.error(
                "Failed to send reading reminder for user_id=%s: %s",
                profile.user_id,
                e,
            )

    logger.info("Reading reminder scheduler completed: %s notifications sent", count)
    return count

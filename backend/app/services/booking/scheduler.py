"""APScheduler jobs for the booking module."""
from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.booking import Booking, BookingStatus, ConsultantProfile
from app.services.booking import availability as avail
from app.services.booking import notifications as booking_notifications

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_booking_scheduler(db: Session) -> None:
    """Register the booking jobs (idempotent; safe to call on every startup)."""
    scheduler.add_job(
        run_session_reminders,
        "interval",
        minutes=1,
        args=[db],
        id="booking_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_availability_rollout,
        "cron",
        hour=settings.BOOKING_ROLLOUT_HOUR,
        minute=0,
        args=[db],
        id="booking_availability_rollout",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_booking_autocomplete,
        "interval",
        minutes=5,
        args=[db],
        id="booking_autocomplete",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Booking scheduler started")


# Jobs


def _upcoming_accepted(db: Session) -> list[Booking]:
    now = avail.now_utc()
    horizon = now + timedelta(minutes=settings.BOOKING_REMINDER_LEAD_MINUTES)
    return list(
        db.scalars(
            select(Booking)
            .where(
                Booking.status == BookingStatus.accepted,
                Booking.start_time > now,
                Booking.start_time <= horizon,
            )
            .options(
                joinedload(Booking.user),
                joinedload(Booking.consultant).joinedload(ConsultantProfile.user),
            )
        ).unique().all()
    )


def run_session_reminders(db: Session) -> int:
    """Send the long- and short-lead reminders for upcoming sessions."""
    sent = 0
    for booking in _upcoming_accepted(db):
        try:
            minutes_until = int(
                (avail.as_utc(booking.start_time) - avail.now_utc()).total_seconds() // 60
            )
            # Short reminder fires only inside its window.
            if (
                booking.short_reminder_sent_at is None
                and minutes_until <= settings.BOOKING_SHORT_REMINDER_LEAD_MINUTES + 1
            ):
                booking_notifications.notify_reminder(
                    db, booking, minutes_ahead=settings.BOOKING_SHORT_REMINDER_LEAD_MINUTES
                )
                booking.short_reminder_sent_at = avail.now_utc()
                db.commit()
                sent += 1
                continue

            if (
                booking.reminder_sent_at is None
                and minutes_until > settings.BOOKING_SHORT_REMINDER_LEAD_MINUTES
            ):
                booking_notifications.notify_reminder(
                    db, booking, minutes_ahead=settings.BOOKING_REMINDER_LEAD_MINUTES
                )
                booking.reminder_sent_at = avail.now_utc()
                db.commit()
                sent += 1
        except Exception:  # pragma: no cover - defensive
            logger.exception("reminder dispatch failed for booking %s", booking.id)
    logger.info("booking reminders: %s messages sent", sent)
    return sent


def run_availability_rollout(db: Session) -> dict:
    """Roll every active consultant's slots forward to the booking horizon."""
    try:
        return avail.rollout_horizon(db)
    except Exception:  # pragma: no cover - defensive
        logger.exception("availability rollout failed")
        return {"created": 0, "consultants": 0}


def run_booking_autocomplete(db: Session) -> int:
    """Mark accepted sessions that have already ended as completed."""
    now = avail.now_utc()
    stale = list(
        db.scalars(
            select(Booking)
            .where(
                Booking.status == BookingStatus.accepted,
                Booking.end_time <= now,
            )
            .options(
                joinedload(Booking.user),
                joinedload(Booking.consultant),
            )
        ).unique().all()
    )

    completed = 0
    for booking in stale:
        try:
            booking.status = BookingStatus.completed
            booking.completed_at = now
            if booking.consultant is not None:
                booking.consultant.total_sessions = int(booking.consultant.total_sessions or 0) + 1
            booking_notifications.notify_status_changed(
                db, booking, status=BookingStatus.completed
            )
            db.commit()
            completed += 1
        except Exception:  # pragma: no cover - defensive
            db.rollback()
            logger.exception("autocomplete failed for booking %s", booking.id)
    if completed:
        logger.info("autocompleted %s sessions", completed)
    return completed


__all__ = [
    "run_availability_rollout",
    "run_booking_autocomplete",
    "run_session_reminders",
    "start_booking_scheduler",
]

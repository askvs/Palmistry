"""Availability management for the booking module."""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.booking import AvailabilityRule, AvailabilitySlot, SlotStatus
from app.services.booking.errors import AvailabilityWindowInvalid

logger = logging.getLogger(__name__)

ONE_DAY = timedelta(days=1)
WEEKDAYS = range(7)

# Hard ceiling so a misconfigured rule can never request millions of rows.
MAX_SLOTS_PER_RULE = 500


def safe_zone(name: str | None) -> ZoneInfo:
    """Resolve a timezone name, falling back to UTC for unknown values."""
    try:
        return ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        logger.warning("unknown timezone %r, falling back to UTC", name)
        return ZoneInfo("UTC")


def as_utc(value: datetime) -> datetime:
    """Coerce any datetime to an aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _rule_window_on(rule: AvailabilityRule, day: date) -> tuple[datetime, datetime]:
    """Absolute start/end of a rule on a given local date."""
    zone = safe_zone(rule.timezone)
    start_local = datetime.combine(day, rule.start_time, tzinfo=zone)
    end_local = datetime.combine(day, rule.end_time, tzinfo=zone)
    return as_utc(start_local), as_utc(end_local)


def _rule_dates(rule: AvailabilityRule, horizon_end: date) -> list[date]:
    start_day = max(rule.effective_from, date.today())
    until = rule.effective_until or horizon_end
    until = min(until, horizon_end)
    if until < start_day:
        return []
    return [start_day + timedelta(days=i) for i in range((until - start_day).days + 1)]


def _existing_starts(db: Session, consultant_id: uuid.UUID) -> set[datetime]:
    rows = db.scalars(
        select(AvailabilitySlot.start_time).where(
            AvailabilitySlot.consultant_id == consultant_id,
            AvailabilitySlot.status != SlotStatus.cancelled,
        )
    ).all()
    return {as_utc(row) for row in rows}


def materialise_rule(
    db: Session,
    rule: AvailabilityRule,
) -> int:
    """Create the concrete slots a rule implies."""
    duration = int(rule.slot_duration_minutes or 0)
    if duration <= 0:
        raise AvailabilityWindowInvalid("Slot duration must be a positive number of minutes")
    if rule.end_time <= rule.start_time:
        raise AvailabilityWindowInvalid("The availability window must end after it starts")

    horizon_end = date.today() + timedelta(days=settings.BOOKING_SLOT_HORIZON_DAYS)
    step = timedelta(minutes=duration + int(rule.buffer_minutes or 0))
    existing = _existing_starts(db, rule.consultant_id)
    cutoff = now_utc()

    created = 0
    for day in _rule_dates(rule, horizon_end):
        if day.weekday() != rule.weekday:
            continue
        window_start, window_end = _rule_window_on(rule, day)
        cursor = window_start
        while cursor + timedelta(minutes=duration) <= window_end:
            slot_start = cursor
            slot_end = cursor + timedelta(minutes=duration)
            cursor += step
            if slot_start <= cutoff:
                # Skip past slots within the lead time.
                continue
            if slot_start in existing:
                continue
            db.add(
                AvailabilitySlot(
                    consultant_id=rule.consultant_id,
                    rule_id=rule.id,
                    start_time=slot_start,
                    end_time=slot_end,
                    timezone=rule.timezone,
                    status=SlotStatus.available,
                )
            )
            existing.add(slot_start)
            created += 1
            if created >= MAX_SLOTS_PER_RULE:
                logger.warning(
                    "rule %s hit the %s slot ceiling; raise the horizon or shorten the window",
                    rule.id,
                    MAX_SLOTS_PER_RULE,
                )
                db.flush()
                return created

    db.flush()
    logger.info(
        "materialised %s slots for availability rule %s (consultant_id=%s)",
        created,
        rule.id,
        rule.consultant_id,
    )
    return created


def extend_horizon_for_consultant(db: Session, consultant_id: uuid.UUID) -> int:
    """Roll every active rule of one consultant forward to the horizon."""
    rules = db.scalars(
        select(AvailabilityRule).where(
            AvailabilityRule.consultant_id == consultant_id,
            AvailabilityRule.is_active == True,  # noqa: E712
        )
    ).all()
    return sum(materialise_rule(db, rule) for rule in rules)


def rollout_horizon(db: Session) -> dict:
    """Scheduler entry point: keep every consultant's slots ahead of the horizon."""
    consultant_ids = db.scalars(
        select(AvailabilityRule.consultant_id)
        .where(AvailabilityRule.is_active == True)  # noqa: E712
        .distinct()
    ).all()
    created = 0
    for consultant_id in consultant_ids:
        try:
            created += extend_horizon_for_consultant(db, consultant_id)
        except Exception:  # pragma: no cover - defensive, one bad rule must not
            # stop the rollout for everyone else.
            logger.exception("availability rollout failed for consultant_id=%s", consultant_id)
    db.commit()
    logger.info("availability rollout created %s slots across %s consultants", created, len(consultant_ids))
    return {"created": created, "consultants": len(consultant_ids)}


def slots_overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    """Half-open overlap test on aware datetimes."""
    return start_a < end_b and start_b < end_a


def local_day_bounds(day: date, zone_name: str | None) -> tuple[datetime, datetime]:
    """UTC bounds of a local calendar day."""
    zone = safe_zone(zone_name)
    start = datetime.combine(day, time.min, tzinfo=zone)
    return as_utc(start), as_utc(start + ONE_DAY)


def coerce_time(value: time | str) -> time:
    """Accept `HH:MM`, `HH:MM:SS` or a `datetime.time`."""
    if isinstance(value, time):
        return value
    text = str(value).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise AvailabilityWindowInvalid(f"{value!r} is not a valid HH:MM time")


def coerce_date(value: date | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise AvailabilityWindowInvalid(
            f"{value!r} is not a valid YYYY-MM-DD date"
        ) from exc


__all__ = [
    "ONE_DAY",
    "WEEKDAYS",
    "as_utc",
    "coerce_date",
    "coerce_time",
    "extend_horizon_for_consultant",
    "local_day_bounds",
    "materialise_rule",
    "now_utc",
    "rollout_horizon",
    "safe_zone",
    "slots_overlap",
]

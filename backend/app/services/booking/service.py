"""Live consultation & booking service layer."""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Select, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.booking import (
    ConsultantCalendarConnection,
    ConsultantProfile,
    AvailabilityRule,
    AvailabilitySlot,
    Booking,
    BookingEvent,
    BookingMessage,
    BookingOrigin,
    BookingStatus,
    NoteVisibility,
    SessionFeedback,
    SessionNote,
    SlotStatus,
)
from app.models.user import User, UserRole
from app.services.booking import availability as avail
from app.services.booking import notifications as booking_notifications
from app.services.booking.calendar import (
    cancel_calendar_event,
    create_calendar_event,
)
from app.services.booking.errors import (
    AvailabilityRuleNotFound,
    AvailabilityRuleOverlap,
    AvailabilityWindowInvalid,
    BookingCancellationClosed,
    BookingNotFound,
    BookingNotAllowed,
    BookingTooFar,
    BookingTooSoon,
    ConsultantProfileIncomplete,
    ConsultantProfileNotFound,
    FeedbackExists,
    FeedbackNotAllowed,
    GoogleOAuthUnavailable,
    InvalidBookingTransition,
    NotAnConsultant,
    SessionNoteNotFound,
    SlotNotBookable,
    SlotNotFound,
)
from app.services.booking.google_calendar import (
    CALENDAR_SCOPES,
    CalendarApiError,
    build_authorization_url,
    exchange_authorization_code,
)

logger = logging.getLogger(__name__)

CONSULTANT_ROLES = (UserRole.tarot_reader, UserRole.spiritual_consultant)

# Statuses that still occupy a slot / count as an open session.
LIVE_STATUSES = (
    BookingStatus.pending,
    BookingStatus.countered,
    BookingStatus.accepted,
)

# Closed statuses belong in the past view.
CLOSED_STATUSES = (
    BookingStatus.completed,
    BookingStatus.cancelled,
    BookingStatus.rejected,
)

# Legal transitions.
ALLOWED_TRANSITIONS: dict[BookingStatus, tuple[BookingStatus, ...]] = {
    BookingStatus.pending: (
        BookingStatus.accepted,
        BookingStatus.rejected,
        BookingStatus.cancelled,
        BookingStatus.countered,
    ),
    BookingStatus.countered: (
        BookingStatus.accepted,
        BookingStatus.rejected,
        BookingStatus.cancelled,
        BookingStatus.pending,
    ),
    BookingStatus.accepted: (BookingStatus.completed, BookingStatus.cancelled),
}

# Statuses from which a booking is still being negotiated (no agreed time yet).
NEGOTIATING_STATUSES = (BookingStatus.pending, BookingStatus.countered)


def awaiting_party(booking: Booking) -> str | None:
    """Who the booking is currently waiting on, for UI badges."""
    if booking.status == BookingStatus.pending:
        return "consultant"
    if booking.status == BookingStatus.countered:
        return "seeker"
    return None


# Helpers


def is_consultant(user: User) -> bool:
    return user.role in CONSULTANT_ROLES


def require_consultant(user: User) -> None:
    if not is_consultant(user):
        raise NotAnConsultant()


def _now() -> datetime:
    return avail.now_utc()


def _release_slot(db: Session, booking: Booking) -> None:
    """Return a booking's slot to the pool."""
    slot = db.get(AvailabilitySlot, booking.slot_id)
    if slot is not None:
        slot.status = SlotStatus.available
        slot.booking_id = None
        db.flush()


def _occupy_slot(db: Session, slot: AvailabilitySlot, booking: Booking) -> None:
    slot.status = SlotStatus.booked
    slot.booking_id = booking.id
    db.flush()


def _record_event(
    db: Session,
    booking: Booking,
    *,
    event_type: str,
    actor: User | None,
    from_status: BookingStatus | None = None,
    to_status: BookingStatus | None = None,
    message: str | None = None,
    metadata: dict | None = None,
) -> BookingEvent:
    event = BookingEvent(
        booking_id=booking.id,
        actor_id=actor.id if actor is not None else None,
        event_type=event_type,
        from_status=from_status.value if isinstance(from_status, BookingStatus) else from_status,
        to_status=to_status.value if isinstance(to_status, BookingStatus) else to_status,
        message=message,
        booking_metadata=metadata or {},
    )
    db.add(event)
    db.flush()
    return event


def _load_booking(db: Session, booking_id: uuid.UUID) -> Booking | None:
    return db.scalar(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            joinedload(Booking.slot),
            joinedload(Booking.user),
            joinedload(Booking.consultant).joinedload(ConsultantProfile.user),
        )
    )


def _base_booking_query() -> Select:
    return select(Booking).options(
        joinedload(Booking.slot),
        joinedload(Booking.user),
        joinedload(Booking.consultant).joinedload(ConsultantProfile.user),
    )


# Consultant profiles


def get_consultant_profile(db: Session, consultant_id: uuid.UUID) -> ConsultantProfile:
    consultant = db.scalar(
        select(ConsultantProfile)
        .where(ConsultantProfile.id == consultant_id)
        .options(joinedload(ConsultantProfile.user))
    )
    if consultant is None:
        raise ConsultantProfileNotFound()
    return consultant


def get_my_consultant_profile(db: Session, user: User) -> ConsultantProfile:
    require_consultant(user)
    consultant = db.scalar(
        select(ConsultantProfile)
        .where(ConsultantProfile.user_id == user.id)
        .options(joinedload(ConsultantProfile.user))
    )
    if consultant is None:
        raise ConsultantProfileNotFound()
    return consultant


def create_or_update_my_consultant_profile(
    db: Session, user: User, *, payload: dict
) -> ConsultantProfile:
    """Create or patch the signed-in consultant's public profile."""
    require_consultant(user)
    consultant = db.scalar(select(ConsultantProfile).where(ConsultantProfile.user_id == user.id))
    if consultant is None:
        if not payload.get("headline"):
            raise ConsultantProfileIncomplete("A headline is required to open your consultant profile")
        consultant = ConsultantProfile(user_id=user.id)
        db.add(consultant)

    for field in (
        "headline",
        "bio",
        "specializations",
        "modalities",
        "languages",
        "years_experience",
        "session_rate",
        "currency",
        "session_duration_minutes",
        "buffer_minutes",
        "timezone",
        "is_accepting_bookings",
    ):
        if field in payload and payload[field] is not None:
            setattr(consultant, field, payload[field])

    if not consultant.headline:
        raise ConsultantProfileIncomplete("A headline is required to open your consultant profile")

    db.commit()
    db.refresh(consultant)
    logger.info("consultant profile saved user_id=%s profile_id=%s", user.id, consultant.id)
    return consultant


def set_accepting_bookings(
    db: Session, user: User, *, is_accepting: bool
) -> ConsultantProfile:
    consultant = get_my_consultant_profile(db, user)
    consultant.is_accepting_bookings = bool(is_accepting)
    db.commit()
    db.refresh(consultant)
    logger.info("consultant %s accepting_bookings=%s", consultant.id, consultant.is_accepting_bookings)
    return consultant


_MIN_SEARCH_LEN = 2


def list_consultants(
    db: Session,
    *,
    search: str | None = None,
    specialization: str | None = None,
    language: str | None = None,
    max_rate: float | None = None,
    available_from: datetime | None = None,
    available_to: datetime | None = None,
    include_inactive: bool = False,
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[ConsultantProfile], int]:
    """Browse the consultant directory with the common filters."""
    query = select(ConsultantProfile).options(joinedload(ConsultantProfile.user))

    if not include_inactive:
        query = query.where(ConsultantProfile.is_accepting_bookings == True)  # noqa: E712

    if search:
        term = f"%{search.strip()}%"
        # Use has() to avoid inflating the total count.
        query = query.where(
            or_(
                ConsultantProfile.headline.ilike(term),
                ConsultantProfile.bio.ilike(term),
                ConsultantProfile.user.has(User.full_name.ilike(term)),
                ConsultantProfile.user.has(User.email.ilike(term)),
            )
        )

    if specialization:
        query = query.where(
            cast(ConsultantProfile.specializations, JSONB).contains([specialization])
        )
    if language:
        query = query.where(cast(ConsultantProfile.languages, JSONB).contains([language]))
    if max_rate is not None:
        query = query.where(ConsultantProfile.session_rate <= max_rate)

    if available_from is not None and available_to is not None:
        has_free_slot = (
            select(AvailabilitySlot.id)
            .where(
                AvailabilitySlot.consultant_id == ConsultantProfile.id,
                AvailabilitySlot.status == SlotStatus.available,
                AvailabilitySlot.start_time >= available_from,
                AvailabilitySlot.start_time <= available_to,
            )
            .exists()
        )
        query = query.where(has_free_slot)

    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    )
    consultants = db.scalars(
        query.order_by(
            ConsultantProfile.avg_rating.desc().nullslast(),
            ConsultantProfile.review_count.desc(),
            ConsultantProfile.created_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).unique().all()
    return consultants, int(total or 0)


def list_public_reviews(
    db: Session, consultant_id: uuid.UUID, *, limit: int = 20, offset: int = 0
) -> tuple[list[SessionFeedback], int]:
    query = select(SessionFeedback).where(
        SessionFeedback.consultant_id == consultant_id,
        SessionFeedback.is_public == True,  # noqa: E712
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    reviews = db.scalars(
        query.order_by(SessionFeedback.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return reviews, int(total or 0)


def get_consultant_stats(db: Session, consultant: ConsultantProfile) -> dict:
    """Aggregate counters for the consultant studio header."""
    now = _now()
    upcoming = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.consultant_id == consultant.id,
            Booking.status == BookingStatus.accepted,
            Booking.start_time >= now,
        )
    )
    pending = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.consultant_id == consultant.id,
            Booking.status == BookingStatus.pending,
        )
    )
    completed = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.consultant_id == consultant.id,
            Booking.status == BookingStatus.completed,
        )
    )
    cancelled = db.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.consultant_id == consultant.id,
            Booking.status.in_((BookingStatus.cancelled, BookingStatus.rejected)),
        )
    )
    open_slots = db.scalar(
        select(func.count())
        .select_from(AvailabilitySlot)
        .where(
            AvailabilitySlot.consultant_id == consultant.id,
            AvailabilitySlot.status == SlotStatus.available,
            AvailabilitySlot.start_time >= now,
        )
    )
    return {
        "upcoming_sessions": int(upcoming or 0),
        "pending_requests": int(pending or 0),
        "completed_sessions": int(completed or 0),
        "declined_or_cancelled": int(cancelled or 0),
        "open_slots": int(open_slots or 0),
        "total_sessions": int(consultant.total_sessions or 0),
        "avg_rating": float(consultant.avg_rating) if consultant.avg_rating is not None else None,
        "review_count": int(consultant.review_count or 0),
    }


# Availability


def list_rules(db: Session, consultant_id: uuid.UUID) -> list[AvailabilityRule]:
    return list(
        db.scalars(
            select(AvailabilityRule)
            .where(AvailabilityRule.consultant_id == consultant_id)
            .order_by(
                AvailabilityRule.weekday,
                AvailabilityRule.start_time,
            )
        ).all()
    )


def _rule_payload(data: dict) -> dict:
    """Normalise + validate a rule payload."""
    weekday = data.get("weekday")
    if weekday is None or not isinstance(weekday, int) or not 0 <= weekday <= 6:
        raise AvailabilityWindowInvalid("weekday must be an integer between 0 (Monday) and 6 (Sunday)")

    start_time = avail.coerce_time(data.get("start_time"))
    end_time = avail.coerce_time(data.get("end_time"))
    if end_time <= start_time:
        raise AvailabilityWindowInvalid("End time must be after the start time")

    duration = int(data.get("slot_duration_minutes") or 60)
    if duration <= 0:
        raise AvailabilityWindowInvalid("Slot duration must be a positive number of minutes")
    if duration > 60 * 12:
        raise AvailabilityWindowInvalid("Slot duration cannot exceed 12 hours")

    buffer_minutes = int(data.get("buffer_minutes") or 0)
    if not 0 <= buffer_minutes <= 240:
        raise AvailabilityWindowInvalid("Buffer must be between 0 and 240 minutes")

    effective_from = avail.coerce_date(data.get("effective_from") or date.today())
    effective_until = (
        avail.coerce_date(data["effective_until"])
        if data.get("effective_until")
        else None
    )
    if effective_until is not None and effective_until < effective_from:
        raise AvailabilityWindowInvalid("The end date must be on or after the start date")

    return {
        "weekday": weekday,
        "start_time": start_time,
        "end_time": end_time,
        "slot_duration_minutes": duration,
        "buffer_minutes": buffer_minutes,
        "timezone": (data.get("timezone") or "UTC")[:64],
        "effective_from": effective_from,
        "effective_until": effective_until,
        "is_active": bool(data.get("is_active", True)),
    }


def _assert_no_rule_overlap(
    db: Session,
    consultant_id: uuid.UUID,
    *,
    weekday: int,
    start_time,
    end_time,
    exclude_rule_id: uuid.UUID | None = None,
) -> None:
    siblings = list_rules(db, consultant_id)
    for other in siblings:
        if other.id == exclude_rule_id or not other.is_active:
            continue
        if other.weekday != weekday:
            continue
        if start_time < other.end_time and other.start_time < end_time:
            raise AvailabilityRuleOverlap(
                f"This window overlaps your existing {other.start_time:%H:%M}–{other.end_time:%H:%M} "
                f"window on day {weekday}"
            )


def create_availability_rule(
    db: Session, user: User, *, data: dict
) -> tuple[AvailabilityRule, int]:
    consultant = get_my_consultant_profile(db, user)
    payload = _rule_payload(data)
    _assert_no_rule_overlap(
        db,
        consultant.id,
        weekday=payload["weekday"],
        start_time=payload["start_time"],
        end_time=payload["end_time"],
    )
    rule = AvailabilityRule(consultant_id=consultant.id, **payload)
    db.add(rule)
    db.flush()
    created = avail.materialise_rule(db, rule)
    db.commit()
    db.refresh(rule)
    logger.info(
        "availability rule %s created for consultant %s (%s slots)", rule.id, consultant.id, created
    )
    return rule, created


def update_availability_rule(
    db: Session, user: User, rule_id: uuid.UUID, *, data: dict
) -> tuple[AvailabilityRule, int]:
    consultant = get_my_consultant_profile(db, user)
    rule = db.get(AvailabilityRule, rule_id)
    if rule is None or rule.consultant_id != consultant.id:
        raise AvailabilityRuleNotFound()

    payload = _rule_payload({**_as_dict(rule), **data})
    _assert_no_rule_overlap(
        db,
        consultant.id,
        weekday=payload["weekday"],
        start_time=payload["start_time"],
        end_time=payload["end_time"],
        exclude_rule_id=rule.id,
    )

    # Drop unbooked slots so the window change applies.
    stale = db.scalars(
        select(AvailabilitySlot).where(
            AvailabilitySlot.rule_id == rule.id,
            AvailabilitySlot.status == SlotStatus.available,
        )
    ).all()
    for slot in stale:
        db.delete(slot)

    for field, value in payload.items():
        setattr(rule, field, value)

    db.flush()
    created = avail.materialise_rule(db, rule)
    db.commit()
    db.refresh(rule)
    logger.info("availability rule %s updated (%s slots)", rule.id, created)
    return rule, created


def delete_availability_rule(db: Session, user: User, rule_id: uuid.UUID) -> int:
    consultant = get_my_consultant_profile(db, user)
    rule = db.get(AvailabilityRule, rule_id)
    if rule is None or rule.consultant_id != consultant.id:
        raise AvailabilityRuleNotFound()

    released = 0
    slots = db.scalars(
        select(AvailabilitySlot).where(AvailabilitySlot.rule_id == rule.id)
    ).all()
    for slot in slots:
        if slot.status == SlotStatus.available:
            db.delete(slot)
            released += 1
        else:
            # Keep booked slots; they detach from the rule via ON DELETE SET NULL.
            slot.rule_id = None
    db.delete(rule)
    db.commit()
    logger.info("availability rule %s deleted (%s slots released)", rule_id, released)
    return released


def _as_dict(rule: AvailabilityRule) -> dict:
    return {
        "weekday": rule.weekday,
        "start_time": rule.start_time,
        "end_time": rule.end_time,
        "slot_duration_minutes": rule.slot_duration_minutes,
        "buffer_minutes": rule.buffer_minutes,
        "timezone": rule.timezone,
        "effective_from": rule.effective_from,
        "effective_until": rule.effective_until,
        "is_active": rule.is_active,
    }


def list_my_slots(
    db: Session,
    user: User,
    *,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: SlotStatus | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[AvailabilitySlot], int]:
    consultant = get_my_consultant_profile(db, user)
    return list_slots(
        db,
        consultant.id,
        start_from=start_from,
        start_to=start_to,
        status=status,
        limit=limit,
        offset=offset,
    )


def list_slots(
    db: Session,
    consultant_id: uuid.UUID,
    *,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: SlotStatus | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[AvailabilitySlot], int]:
    query = select(AvailabilitySlot).where(AvailabilitySlot.consultant_id == consultant_id)
    if status is not None:
        query = query.where(AvailabilitySlot.status == status)
    if start_from is not None:
        query = query.where(AvailabilitySlot.start_time >= start_from)
    if start_to is not None:
        query = query.where(AvailabilitySlot.start_time <= start_to)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    slots = db.scalars(
        query.order_by(AvailabilitySlot.start_time).limit(limit).offset(offset)
    ).all()
    return slots, int(total or 0)


def generate_my_slots(
    db: Session, user: User, *, from_date: date, to_date: date
) -> int:
    consultant = get_my_consultant_profile(db, user)
    if to_date < from_date:
        raise AvailabilityWindowInvalid("The end date must be on or after the start date")
    horizon_end = date.today() + timedelta(days=settings.BOOKING_SLOT_HORIZON_DAYS)

    rules = db.scalars(
        select(AvailabilityRule).where(
            AvailabilityRule.consultant_id == consultant.id,
            AvailabilityRule.is_active == True,  # noqa: E712
        )
    ).all()

    created = 0
    for rule in rules:
        window_end = min(
            to_date,
            rule.effective_until or to_date,
            horizon_end,
        )
        if window_end < from_date:
            continue
        probe = AvailabilityRule(
            id=rule.id,
            consultant_id=rule.consultant_id,
            weekday=rule.weekday,
            start_time=rule.start_time,
            end_time=rule.end_time,
            slot_duration_minutes=rule.slot_duration_minutes,
            buffer_minutes=rule.buffer_minutes,
            timezone=rule.timezone,
            effective_from=max(rule.effective_from, from_date),
            effective_until=window_end,
            is_active=True,
        )
        created += avail.materialise_rule(db, probe)
    db.commit()
    logger.info("generated %s slots for consultant %s", created, consultant.id)
    return created


def _owned_slot(db: Session, consultant: ConsultantProfile, slot_id: uuid.UUID) -> AvailabilitySlot:
    slot = db.get(AvailabilitySlot, slot_id)
    if slot is None or slot.consultant_id != consultant.id:
        raise SlotNotFound()
    return slot


def block_slot(db: Session, user: User, slot_id: uuid.UUID) -> AvailabilitySlot:
    consultant = get_my_consultant_profile(db, user)
    slot = _owned_slot(db, consultant, slot_id)
    if slot.status == SlotStatus.booked:
        raise SlotNotBookable("A seeker already booked this slot; cancel the booking instead")
    slot.status = SlotStatus.blocked
    db.commit()
    db.refresh(slot)
    logger.info("slot %s blocked by consultant %s", slot.id, consultant.id)
    return slot


def unblock_slot(db: Session, user: User, slot_id: uuid.UUID) -> AvailabilitySlot:
    consultant = get_my_consultant_profile(db, user)
    slot = _owned_slot(db, consultant, slot_id)
    if slot.status != SlotStatus.blocked:
        raise SlotNotBookable("Only blocked slots can be reopened")
    if slot.start_time <= _now():
        raise SlotNotBookable("This slot is in the past")
    slot.status = SlotStatus.available
    db.commit()
    db.refresh(slot)
    return slot


def delete_slot(db: Session, user: User, slot_id: uuid.UUID) -> bool:
    consultant = get_my_consultant_profile(db, user)
    slot = _owned_slot(db, consultant, slot_id)
    if slot.status == SlotStatus.booked:
        raise SlotNotBookable("A seeker already booked this slot; cancel the booking instead")
    db.delete(slot)
    db.commit()
    logger.info("slot %s deleted by consultant %s", slot_id, consultant.id)
    return True


def get_available_days(
    db: Session,
    consultant_id: uuid.UUID,
    *,
    from_date: date,
    to_date: date,
) -> list[dict]:
    """Day -> free-slot-count map used to render the booking calendar."""
    if to_date < from_date:
        raise AvailabilityWindowInvalid("The end date must be on or after the start date")
    zone = None
    consultant = db.get(ConsultantProfile, consultant_id)
    if consultant is not None:
        zone = consultant.timezone
    day_start, day_end = avail.local_day_bounds(from_date, zone)
    _, range_end = avail.local_day_bounds(to_date + timedelta(days=1), zone)

    rows = db.execute(
        select(AvailabilitySlot.start_time)
        .where(
            AvailabilitySlot.consultant_id == consultant_id,
            AvailabilitySlot.status == SlotStatus.available,
            AvailabilitySlot.start_time >= day_start,
            AvailabilitySlot.start_time < range_end,
        )
        .order_by(AvailabilitySlot.start_time)
    ).all()

    counts: dict[str, int] = {}
    current = day_start
    while current < range_end:
        counts[current.astimezone(avail.safe_zone(zone)).date().isoformat()] = 0
        current += timedelta(days=1)
    for (start,) in rows:
        key = start.astimezone(avail.safe_zone(zone)).date().isoformat()
        counts[key] = counts.get(key, 0) + 1

    return [
        {"date": key, "available_slots": value}
        for key, value in sorted(counts.items())
    ]


def get_available_slots(
    db: Session, consultant_id: uuid.UUID, *, day: date
) -> list[AvailabilitySlot]:
    consultant = db.get(ConsultantProfile, consultant_id)
    if consultant is None:
        raise ConsultantProfileNotFound()
    day_start, day_end = avail.local_day_bounds(day, consultant.timezone)
    return list(
        db.scalars(
            select(AvailabilitySlot)
            .where(
                AvailabilitySlot.consultant_id == consultant_id,
                AvailabilitySlot.status == SlotStatus.available,
                AvailabilitySlot.start_time >= day_start,
                AvailabilitySlot.start_time < day_end,
            )
            .order_by(AvailabilitySlot.start_time)
        ).all()
    )


# Bookings — seeker side


def _validate_booking_window(start_time: datetime) -> None:
    now = _now()
    if start_time < now + timedelta(minutes=settings.BOOKING_MIN_LEAD_MINUTES):
        raise BookingTooSoon(
            f"Sessions must be booked at least {settings.BOOKING_MIN_LEAD_MINUTES} "
            "minutes in advance"
        )
    if start_time > now + timedelta(days=settings.BOOKING_MAX_ADVANCE_DAYS):
        raise BookingTooFar(
            f"Sessions can only be booked up to {settings.BOOKING_MAX_ADVANCE_DAYS} "
            "days ahead"
        )


def create_booking(
    db: Session,
    user: User,
    consultant_id: uuid.UUID,
    *,
    slot_id: uuid.UUID,
    subject: str,
    notes: str | None = None,
    meeting_link: str | None = None,
) -> Booking:
    """Reserve a slot. The booking starts `pending` until the consultant accepts."""
    consultant = db.scalar(
        select(ConsultantProfile)
        .where(ConsultantProfile.id == consultant_id)
        .options(joinedload(ConsultantProfile.user))
    )
    if consultant is None:
        raise ConsultantProfileNotFound()
    if consultant.user_id == user.id:
        raise BookingNotAllowed("You cannot book your own sessions")
    if not consultant.is_accepting_bookings:
        raise BookingNotAllowed("This consultant is not accepting bookings right now")

    slot = db.get(AvailabilitySlot, slot_id)
    if slot is None or slot.consultant_id != consultant_id:
        raise SlotNotFound()
    if slot.status != SlotStatus.available:
        raise SlotNotBookable("This slot has just been taken")

    _validate_booking_window(avail.as_utc(slot.start_time))

    duration = int(
        (avail.as_utc(slot.end_time) - avail.as_utc(slot.start_time)).total_seconds() // 60
    ) or consultant.session_duration_minutes

    seeker_link = (meeting_link or "").strip()[:500] or None
    booking = Booking(
        slot_id=slot.id,
        consultant_id=consultant.id,
        user_id=user.id,
        status=BookingStatus.pending,
        start_time=avail.as_utc(slot.start_time),
        end_time=avail.as_utc(slot.end_time),
        duration_minutes=duration,
        timezone=slot.timezone or consultant.timezone,
        subject=subject.strip()[:200],
        notes=(notes or "").strip() or None,
        price=consultant.session_rate,
        currency=consultant.currency,
        meet_link=seeker_link,
    )
    db.add(booking)
    db.flush()
    _occupy_slot(db, slot, booking)
    _record_event(
        db,
        booking,
        event_type="booking_created",
        actor=user,
        to_status=BookingStatus.pending,
        message=f"{user.full_name} requested this session",
    )
    db.commit()
    db.refresh(booking)

    booking_notifications.notify_booking_requested(db, booking)
    logger.info(
        "booking %s created (consultant=%s, user=%s, slot=%s)",
        booking.id,
        consultant.id,
        user.id,
        slot.id,
    )
    return booking


def _apply_time(
    booking: Booking,
    consultant: ConsultantProfile | None,
    *,
    start_time: datetime,
    duration_minutes: int | None,
    proposer: User,
) -> None:
    """Set the time currently on the table and record who proposed it."""
    start = avail.as_utc(start_time)
    default_duration = (
        booking.duration_minutes
        or (consultant.session_duration_minutes if consultant is not None else None)
        or 60
    )
    duration = int(duration_minutes or default_duration)
    booking.start_time = start
    booking.end_time = start + timedelta(minutes=duration)
    booking.duration_minutes = duration
    booking.last_proposed_by_id = proposer.id


def propose_booking(
    db: Session,
    user: User,
    consultant_id: uuid.UUID,
    *,
    start_time: datetime,
    subject: str,
    duration_minutes: int | None = None,
    notes: str | None = None,
    meeting_link: str | None = None,
) -> Booking:
    """Request a session at a seeker-proposed time (no pre-published slot)."""
    consultant = db.scalar(
        select(ConsultantProfile)
        .where(ConsultantProfile.id == consultant_id)
        .options(joinedload(ConsultantProfile.user))
    )
    if consultant is None:
        raise ConsultantProfileNotFound()
    if consultant.user_id == user.id:
        raise BookingNotAllowed("You cannot book your own sessions")
    if not consultant.is_accepting_bookings:
        raise BookingNotAllowed("This consultant is not accepting bookings right now")

    start = avail.as_utc(start_time)
    _validate_booking_window(start)
    duration = int(duration_minutes or consultant.session_duration_minutes or 60)

    seeker_link = (meeting_link or "").strip()[:500] or None
    booking = Booking(
        slot_id=None,
        origin=BookingOrigin.proposal,
        consultant_id=consultant.id,
        user_id=user.id,
        status=BookingStatus.pending,
        start_time=start,
        end_time=start + timedelta(minutes=duration),
        duration_minutes=duration,
        timezone=consultant.timezone,
        subject=subject.strip()[:200],
        notes=(notes or "").strip() or None,
        price=consultant.session_rate,
        currency=consultant.currency,
        last_proposed_by_id=user.id,
        meet_link=seeker_link,
    )
    db.add(booking)
    db.flush()
    _record_event(
        db,
        booking,
        event_type="booking_proposed",
        actor=user,
        to_status=BookingStatus.pending,
        message=f"{user.full_name} proposed a time for this session",
    )
    db.commit()
    db.refresh(booking)

    booking_notifications.notify_booking_requested(db, booking)
    logger.info(
        "booking %s proposed (consultant=%s, user=%s, start=%s)",
        booking.id,
        consultant.id,
        user.id,
        start,
    )
    return booking


def counter_booking(
    db: Session,
    user: User,
    booking_id: uuid.UUID,
    *,
    start_time: datetime,
    duration_minutes: int | None = None,
    message: str | None = None,
) -> Booking:
    """Either party suggests a different time; flips who the booking awaits."""
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise BookingNotFound()

    is_seeker = booking.user_id == user.id
    is_consultant_side = bool(
        booking.consultant is not None and booking.consultant.user_id == user.id
    )
    if not (is_seeker or is_consultant_side):
        raise BookingNotFound()
    if booking.status not in NEGOTIATING_STATUSES:
        raise InvalidBookingTransition(
            "Only a pending or awaiting booking can have its time changed"
        )

    start = avail.as_utc(start_time)
    _validate_booking_window(start)

    # A counter turns the booking into a free-form negotiation: drop any slot.
    if booking.slot_id is not None:
        _release_slot(db, booking)
        booking.slot_id = None
        booking.origin = BookingOrigin.proposal

    _apply_time(
        booking,
        booking.consultant,
        start_time=start,
        duration_minutes=duration_minutes,
        proposer=user,
    )

    previous = booking.status
    # Countering flips which party the booking awaits.
    target = (
        BookingStatus.pending
        if (is_seeker and not is_consultant_side)
        else BookingStatus.countered
    )
    _assert_transition(booking, target)
    booking.status = target
    _record_event(
        db,
        booking,
        event_type="booking_countered",
        actor=user,
        from_status=previous,
        to_status=target,
        message=message,
    )
    db.commit()
    db.refresh(booking)

    booking_notifications.notify_booking_countered(
        db, booking, awaiting=awaiting_party(booking) or "consultant"
    )
    logger.info("booking %s countered by %s -> %s", booking.id, user.id, target.value)
    return booking


def _my_bookings_query(db: Session, *, owner_field, owner_id, booking_status, scope, now):
    query = _base_booking_query().where(owner_field == owner_id)
    if booking_status is not None:
        query = query.where(Booking.status == booking_status)
    if scope == "upcoming":
        query = query.where(
            Booking.start_time >= now, Booking.status != BookingStatus.cancelled
        )
    elif scope == "past":
        query = query.where(or_(Booking.start_time < now, Booking.status.in_(CLOSED_STATUSES)))
    return query


def _paginate(db: Session, query: Select, *, scope: str, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = db.scalars(
        query.order_by(
            Booking.start_time.desc() if scope == "past" else Booking.start_time.asc()
        )
        .limit(limit)
        .offset(offset)
    ).unique().all()
    return rows, int(total or 0)


def list_my_bookings(
    db: Session,
    user: User,
    *,
    booking_status: BookingStatus | None = None,
    scope: str = "upcoming",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Booking], int]:
    return _paginate(
        db,
        _my_bookings_query(
            db,
            owner_field=Booking.user_id,
            owner_id=user.id,
            booking_status=booking_status,
            scope=scope,
            now=_now(),
        ),
        scope=scope,
        limit=limit,
        offset=offset,
    )


def get_my_booking(db: Session, user: User, booking_id: uuid.UUID) -> Booking:
    booking = _load_booking(db, booking_id)
    if booking is None or booking.user_id != user.id:
        raise BookingNotFound()
    return booking


def cancel_my_booking(
    db: Session, user: User, booking_id: uuid.UUID, *, reason: str | None = None
) -> Booking:
    booking = get_my_booking(db, user, booking_id)
    return _cancel(db, booking, actor=user, reason=reason)


# Bookings — consultant side


def list_consultant_bookings(
    db: Session,
    user: User,
    *,
    booking_status: BookingStatus | None = None,
    scope: str = "upcoming",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Booking], int]:
    consultant = get_my_consultant_profile(db, user)
    return _paginate(
        db,
        _my_bookings_query(
            db,
            owner_field=Booking.consultant_id,
            owner_id=consultant.id,
            booking_status=booking_status,
            scope=scope,
            now=_now(),
        ),
        scope=scope,
        limit=limit,
        offset=offset,
    )


def get_consultant_booking(
    db: Session, user: User, booking_id: uuid.UUID
) -> Booking:
    consultant = get_my_consultant_profile(db, user)
    booking = _load_booking(db, booking_id)
    if booking is None or booking.consultant_id != consultant.id:
        raise BookingNotFound()
    return booking


def _assert_transition(booking: Booking, target: BookingStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(booking.status, ())
    if target not in allowed:
        raise InvalidBookingTransition(
            f"A {booking.status.value} booking cannot become {target.value}"
        )


def _accept(db: Session, booking: Booking, *, actor: User) -> Booking:
    """Shared accept path: mark accepted and provision Calendar/Meet."""
    from_status = booking.status
    _assert_transition(booking, BookingStatus.accepted)

    booking.status = BookingStatus.accepted
    booking.accepted_at = _now()
    _record_event(
        db,
        booking,
        event_type="booking_accepted",
        actor=actor,
        from_status=from_status,
        to_status=BookingStatus.accepted,
    )
    db.commit()
    db.refresh(booking)

    # Calendar first: the notification copy points at the Meet link.
    try:
        create_calendar_event(db, booking)
    except Exception:  # pragma: no cover - create_calendar_event swallows its own
        logger.exception("unexpected calendar failure for booking %s", booking.id)

    booking_notifications.notify_status_changed(
        db, booking, status=BookingStatus.accepted, actor_id=actor.id
    )
    logger.info("booking %s accepted by %s", booking.id, actor.id)
    return booking


def accept_booking(db: Session, user: User, booking_id: uuid.UUID) -> Booking:
    """Consultant confirms a pending booking (slot or proposed time)."""
    booking = get_consultant_booking(db, user, booking_id)
    if booking.status != BookingStatus.pending:
        raise InvalidBookingTransition(
            "Only a pending request awaiting you can be accepted here"
        )
    return _accept(db, booking, actor=user)


def confirm_counter(db: Session, user: User, booking_id: uuid.UUID) -> Booking:
    """Seeker confirms the consultant's counter-proposed time."""
    booking = get_my_booking(db, user, booking_id)
    if booking.status != BookingStatus.countered:
        raise InvalidBookingTransition(
            "There is no proposed time from the consultant to confirm"
        )
    return _accept(db, booking, actor=user)


def reject_booking(
    db: Session, user: User, booking_id: uuid.UUID, *, reason: str | None = None
) -> Booking:
    booking = get_consultant_booking(db, user, booking_id)
    _assert_transition(booking, BookingStatus.rejected)

    previous = booking.status
    booking.status = BookingStatus.rejected
    booking.rejected_at = _now()
    booking.cancellation_reason = (reason or "").strip()[:2000] or None
    _release_slot(db, booking)
    _record_event(
        db,
        booking,
        event_type="booking_rejected",
        actor=user,
        from_status=previous,
        to_status=BookingStatus.rejected,
        message=reason,
    )
    db.commit()
    db.refresh(booking)

    booking_notifications.notify_status_changed(
        db, booking, status=BookingStatus.rejected, actor_id=user.id, reason=reason
    )
    logger.info("booking %s rejected by consultant %s", booking.id, user.id)
    return booking


def complete_booking(
    db: Session, user: User, booking_id: uuid.UUID, *, force: bool = False
) -> Booking:
    booking = get_consultant_booking(db, user, booking_id)
    _assert_transition(booking, BookingStatus.completed)
    if not force and avail.as_utc(booking.start_time) > _now():
        raise InvalidBookingTransition(
            "This session has not started yet; cancel it instead, or pass force=true"
        )

    booking.status = BookingStatus.completed
    booking.completed_at = _now()
    _record_event(
        db,
        booking,
        event_type="booking_completed",
        actor=user,
        from_status=BookingStatus.accepted,
        to_status=BookingStatus.completed,
    )

    consultant = booking.consultant
    if consultant is not None:
        consultant.total_sessions = int(consultant.total_sessions or 0) + 1
    db.commit()
    db.refresh(booking)

    booking_notifications.notify_status_changed(
        db, booking, status=BookingStatus.completed, actor_id=user.id
    )
    logger.info("booking %s completed", booking.id)
    return booking


def _cancel(
    db: Session,
    booking: Booking,
    *,
    actor: User,
    reason: str | None = None,
) -> Booking:
    _assert_transition(booking, BookingStatus.cancelled)

    is_consultant_side = bool(
        booking.consultant is not None and actor.id == booking.consultant.user_id
    )
    if not is_consultant_side:
        # Seekers lose the free-cancellation right inside the window.
        window = timedelta(hours=settings.BOOKING_CANCEL_WINDOW_HOURS)
        if _now() > avail.as_utc(booking.start_time) - window:
            raise BookingCancellationClosed(
                f"Sessions can only be cancelled at least "
                f"{settings.BOOKING_CANCEL_WINDOW_HOURS} hours before they start"
            )

    previous = booking.status
    booking.status = BookingStatus.cancelled
    booking.cancelled_at = _now()
    booking.cancelled_by_id = actor.id
    booking.cancellation_reason = (reason or "").strip()[:2000] or None
    _release_slot(db, booking)
    _record_event(
        db,
        booking,
        event_type="booking_cancelled",
        actor=actor,
        from_status=previous,
        to_status=BookingStatus.cancelled,
        message=reason,
    )
    db.commit()
    db.refresh(booking)

    try:
        cancel_calendar_event(db, booking)
    except Exception:  # pragma: no cover
        logger.exception("calendar cancel failed for booking %s", booking.id)

    booking_notifications.notify_status_changed(
        db,
        booking,
        status=BookingStatus.cancelled,
        actor_id=actor.id,
        reason=reason,
    )
    logger.info("booking %s cancelled by %s", booking.id, actor.id)
    return booking


def cancel_consultant_booking(
    db: Session, user: User, booking_id: uuid.UUID, *, reason: str | None = None
) -> Booking:
    booking = get_consultant_booking(db, user, booking_id)
    return _cancel(db, booking, actor=user, reason=reason)


def retry_calendar(db: Session, user: User, booking_id: uuid.UUID) -> Booking:
    booking = get_consultant_booking(db, user, booking_id)
    from app.services.booking.calendar import retry_calendar_event

    retry_calendar_event(db, booking)
    db.refresh(booking)
    return booking


# Session notes


def _visible_notes(db: Session, booking: Booking, user: User) -> list[SessionNote]:
    query = select(SessionNote).where(SessionNote.booking_id == booking.id)
    is_owner = booking.consultant is not None and booking.consultant.user_id == user.id
    if not is_owner:
        query = query.where(SessionNote.visibility == NoteVisibility.shared)
    return list(
        db.scalars(query.order_by(SessionNote.created_at.desc())).all()
    )


def list_booking_notes(
    db: Session, user: User, booking_id: uuid.UUID
) -> list[SessionNote]:
    """Notes for either side of a booking."""
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise BookingNotFound()
    is_seeker = booking.user_id == user.id
    is_consultant = booking.consultant is not None and booking.consultant.user_id == user.id
    if not (is_seeker or is_consultant):
        raise BookingNotFound()
    return _visible_notes(db, booking, user)


def add_session_note(
    db: Session,
    user: User,
    booking_id: uuid.UUID,
    *,
    body: str,
    visibility: str = NoteVisibility.private.value,
) -> SessionNote:
    booking = get_consultant_booking(db, user, booking_id)
    body = (body or "").strip()
    if not body:
        raise AvailabilityWindowInvalid("A note cannot be empty")
    try:
        note_visibility = NoteVisibility(visibility)
    except ValueError as exc:
        raise AvailabilityWindowInvalid(
            f"visibility must be one of {[v.value for v in NoteVisibility]}"
        ) from exc

    note = SessionNote(
        booking_id=booking.id,
        author_id=user.id,
        visibility=note_visibility,
        body=body,
    )
    db.add(note)
    db.flush()
    _record_event(
        db,
        booking,
        event_type="session_note_added",
        actor=user,
        message="Consultant added a session note",
        metadata={"note_id": str(note.id), "visibility": note_visibility.value},
    )
    db.commit()
    db.refresh(note)
    logger.info("session note %s added to booking %s", note.id, booking.id)
    return note


def update_session_note(
    db: Session,
    user: User,
    note_id: uuid.UUID,
    *,
    body: str | None = None,
    visibility: str | None = None,
) -> SessionNote:
    consultant = get_my_consultant_profile(db, user)
    note = db.get(SessionNote, note_id)
    if note is None or note.author_id != user.id:
        raise SessionNoteNotFound()
    if visibility is not None:
        try:
            note.visibility = NoteVisibility(visibility)
        except ValueError as exc:
            raise AvailabilityWindowInvalid(
                f"visibility must be one of {[v.value for v in NoteVisibility]}"
            ) from exc
    if body is not None:
        body = body.strip()
        if not body:
            raise AvailabilityWindowInvalid("A note cannot be empty")
        note.body = body
    db.commit()
    db.refresh(note)
    logger.info("session note %s updated", note.id)
    return note


def delete_session_note(db: Session, user: User, note_id: uuid.UUID) -> bool:
    note = db.get(SessionNote, note_id)
    if note is None or note.author_id != user.id:
        raise SessionNoteNotFound()
    db.delete(note)
    db.commit()
    logger.info("session note %s deleted", note_id)
    return True


# Booking chat (seeker <-> consultant)


def _booking_for_participant(db: Session, user: User, booking_id: uuid.UUID) -> Booking:
    """Load a booking only if `user` is its seeker or its consultant."""
    booking = _load_booking(db, booking_id)
    if booking is None:
        raise BookingNotFound()
    is_seeker = booking.user_id == user.id
    is_consultant = booking.consultant is not None and booking.consultant.user_id == user.id
    if not (is_seeker or is_consultant):
        raise BookingNotFound()
    return booking


def list_booking_messages(
    db: Session,
    user: User,
    booking_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[BookingMessage], int]:
    """Chat history for a booking, oldest first."""
    _booking_for_participant(db, user, booking_id)
    base = select(BookingMessage).where(BookingMessage.booking_id == booking_id)
    total = db.scalar(
        select(func.count()).select_from(base.order_by(None).subquery())
    )
    rows = db.scalars(
        base.options(joinedload(BookingMessage.sender))
        .order_by(BookingMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), int(total or 0)


def post_booking_message(
    db: Session, user: User, booking_id: uuid.UUID, *, body: str
) -> BookingMessage:
    """Add a chat message to a booking the user participates in."""
    booking = _booking_for_participant(db, user, booking_id)
    body = (body or "").strip()
    if not body:
        raise BookingNotAllowed("A message cannot be empty")

    message = BookingMessage(booking_id=booking.id, sender_id=user.id, body=body[:4000])
    db.add(message)
    db.commit()
    db.refresh(message)
    logger.info("booking %s chat message %s posted by %s", booking.id, message.id, user.id)
    return message


# Feedback


def submit_feedback(
    db: Session,
    user: User,
    booking_id: uuid.UUID,
    *,
    rating: int,
    review: str | None = None,
    is_public: bool = True,
) -> SessionFeedback:
    booking = get_my_booking(db, user, booking_id)
    if booking.status != BookingStatus.completed:
        raise FeedbackNotAllowed(
            "Feedback can only be left once a session has been completed"
        )
    if not 1 <= int(rating) <= 5:
        raise FeedbackNotAllowed("Rating must be between 1 and 5")
    if booking.feedback is not None:
        raise FeedbackExists()

    feedback = SessionFeedback(
        booking_id=booking.id,
        user_id=user.id,
        consultant_id=booking.consultant_id,
        rating=int(rating),
        review=(review or "").strip() or None,
        is_public=bool(is_public),
    )
    db.add(feedback)
    db.flush()

    _recalculate_consultant_rating(db, booking.consultant_id)
    db.commit()
    db.refresh(feedback)
    logger.info("feedback %s recorded for booking %s", feedback.id, booking.id)
    return feedback


def _recalculate_consultant_rating(db: Session, consultant_id: uuid.UUID) -> None:
    consultant = db.get(ConsultantProfile, consultant_id)
    if consultant is None:
        return
    avg, count = db.execute(
        select(func.avg(SessionFeedback.rating), func.count())
        .select_from(SessionFeedback)
        .where(SessionFeedback.consultant_id == consultant_id)
    ).one()
    consultant.avg_rating = round(float(avg), 2) if avg is not None else None
    consultant.review_count = int(count or 0)


# Google Calendar connection


def calendar_authorization_url(db: Session, user: User) -> dict:
    """Build the consent URL the frontend opens for "connect my calendar"."""
    get_my_consultant_profile(db, user)
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise GoogleOAuthUnavailable("Google OAuth is not configured on this server")
    state = secrets.token_urlsafe(24)
    return {
        "authorization_url": build_authorization_url(
            redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URI,
            state=state,
            login_hint=user.email,
        ),
        "state": state,
        "scopes": list(CALENDAR_SCOPES),
    }


def connect_calendar(db: Session, user: User, *, code: str) -> ConsultantCalendarConnection:
    """Exchange an OAuth code and store the consultant's refresh token."""
    consultant = get_my_consultant_profile(db, user)
    try:
        token = exchange_authorization_code(
            code, redirect_uri=settings.GOOGLE_CALENDAR_REDIRECT_URI
        )
    except CalendarApiError as exc:
        raise InvalidBookingTransition(f"Google rejected the consent code: {exc}") from exc

    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise InvalidBookingTransition(
            "Google did not return a refresh token; revoke access and try again"
        )

    connection = db.scalar(
        select(ConsultantCalendarConnection).where(
            ConsultantCalendarConnection.consultant_id == consultant.id
        )
    )
    if connection is None:
        connection = ConsultantCalendarConnection(consultant_id=consultant.id)
        db.add(connection)

    connection.refresh_token = refresh_token
    connection.google_email = user.email
    connection.calendar_id = connection.calendar_id or "primary"
    connection.timezone = consultant.timezone
    connection.is_active = True
    connection.last_error = None
    connection.connected_at = _now()
    db.commit()
    db.refresh(connection)
    logger.info("consultant %s connected Google Calendar %s", consultant.id, connection.id)
    return connection


def disconnect_calendar(db: Session, user: User) -> bool:
    consultant = get_my_consultant_profile(db, user)
    connection = db.scalar(
        select(ConsultantCalendarConnection).where(
            ConsultantCalendarConnection.consultant_id == consultant.id
        )
    )
    if connection is None:
        return False
    db.delete(connection)
    db.commit()
    logger.info("consultant %s disconnected Google Calendar", consultant.id)
    return True


def get_calendar_connection(
    db: Session, user: User
) -> ConsultantCalendarConnection | None:
    consultant = get_my_consultant_profile(db, user)
    return db.scalar(
        select(ConsultantCalendarConnection).where(
            ConsultantCalendarConnection.consultant_id == consultant.id
        )
    )


def update_calendar_connection(
    db: Session, user: User, *, calendar_id: str | None, is_active: bool | None
) -> ConsultantCalendarConnection:
    consultant = get_my_consultant_profile(db, user)
    connection = db.scalar(
        select(ConsultantCalendarConnection).where(
            ConsultantCalendarConnection.consultant_id == consultant.id
        )
    )
    if connection is None:
        raise BookingNotFound("No Google Calendar is connected yet")
    if calendar_id:
        connection.calendar_id = calendar_id[:255]
    if is_active is not None:
        connection.is_active = bool(is_active)
    db.commit()
    db.refresh(connection)
    return connection


__all__ = [name for name in dir() if not name.startswith("_")]

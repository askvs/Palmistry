"""Live consultation & booking API endpoints."""
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_roles
from app.db.session import get_db
from app.models.booking import AVAILABILITY_DAY_NAMES, BookingStatus, SlotStatus
from app.models.user import User, UserRole
from app.schemas.booking import (
    AvailabilityCalendarOut,
    AvailabilityRuleCreate,
    AvailabilityRuleCreatedOut,
    AvailabilityRuleOut,
    AvailabilityRuleUpdate,
    AvailableDayOut,
    BookingCancelIn,
    BookingCounterIn,
    BookingCreate,
    BookingDetailOut,
    BookingEventOut,
    BookingListOut,
    BookingMeetingLinkIn,
    BookingMessageCreate,
    BookingMessageListOut,
    BookingMessageOut,
    BookingNoteCreate,
    BookingNoteOut,
    BookingNoteUpdate,
    BookingOut,
    BookingProposeIn,
    DaySlotsOut,
    ConsultantListOut,
    ConsultantProfileCreate,
    ConsultantProfileDetail,
    ConsultantProfileOut,
    ConsultantProfileUpdate,
    ConsultantStatsOut,
    FeedbackCreate,
    FeedbackOut,
    GenerateSlotsIn,
    GenerateSlotsOut,
    ReviewListOut,
    ReviewOut,
    SlotListOut,
    SlotOut,
)
from app.services.booking import service as booking_service
from app.services.booking import availability as avail

logger = logging.getLogger(__name__)

# The two reading roles may host live sessions.
require_consultant_role = require_roles(
    UserRole.tarot_reader, UserRole.spiritual_consultant
)

# Every role that may participate in a booking (as its seeker).
require_session_role = require_roles(
    UserRole.user, UserRole.tarot_reader, UserRole.spiritual_consultant
)

consultants = APIRouter(
    prefix="/consultants",
    tags=["consultants"],
    dependencies=[Depends(get_current_user)],
)
consultant = APIRouter(
    prefix="/consultants",
    tags=["consultant-studio"],
    dependencies=[Depends(get_current_user), Depends(require_consultant_role)],
)
bookings = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    dependencies=[Depends(get_current_user), Depends(require_session_role)],
)


# Serialisation helpers


def _consultant_out(db: Session, profile, *, detail: bool = False) -> ConsultantProfileOut:
    payload = ConsultantProfileOut.model_validate(profile)
    if profile.user is not None:
        payload.full_name = profile.user.full_name
        payload.email = profile.user.email
    if detail:
        data = payload.model_dump()
        now = avail.now_utc()
        slots, _total = booking_service.list_slots(
            db,
            profile.id,
            start_from=now,
            start_to=now + timedelta(days=7),
            status=SlotStatus.available,
            limit=1,
        )
        data["next_available_at"] = slots[0].start_time if slots else None
        data["open_slots_next_7_days"] = _total
        return ConsultantProfileDetail(**data)
    return payload


def _rule_out(rule) -> AvailabilityRuleOut:
    payload = AvailabilityRuleOut.model_validate(rule)
    payload.weekday_name = AVAILABILITY_DAY_NAMES[rule.weekday]
    return payload


def _note_out(note) -> BookingNoteOut:
    payload = BookingNoteOut.model_validate(note)
    if note.author is not None:
        payload.author_name = note.author.full_name
    return payload


def _message_out(message, *, me: User) -> BookingMessageOut:
    payload = BookingMessageOut.model_validate(message)
    if message.sender is not None:
        payload.sender_name = message.sender.full_name
        payload.sender_role = (
            message.sender.role.value
            if hasattr(message.sender.role, "value")
            else str(message.sender.role)
        )
    payload.is_me = message.sender_id == me.id
    return payload


def _parse_date(value: str | None, field: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{field} must be an ISO date (YYYY-MM-DD)",
        ) from exc


def _parse_datetime(value: str | None, field: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{field} must be an ISO 8601 timestamp",
        ) from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _now_plus_grace(minutes: int = 30) -> datetime:
    """The Meet link opens 30 minutes before the session starts."""
    return avail.now_utc() + timedelta(minutes=minutes)


def _booking_out(booking, *, detail: bool = False) -> BookingOut:
    payload = BookingOut.model_validate(booking)
    if booking.consultant is not None:
        if booking.consultant.user is not None:
            payload.consultant_name = booking.consultant.user.full_name
            payload.consultant_user_id = booking.consultant.user.id
        payload.consultant_headline = booking.consultant.headline
    if booking.user is not None:
        payload.seeker_name = booking.user.full_name
        payload.seeker_email = booking.user.email
    if booking.cancelled_by is not None:
        payload.cancelled_by_name = booking.cancelled_by.full_name
    payload.can_join_meet = bool(
        booking.status == BookingStatus.accepted
        and booking.meet_link
        and avail.as_utc(booking.start_time)
        <= _now_plus_grace()
    )
    if booking.feedback is not None:
        payload.feedback = FeedbackOut.model_validate(booking.feedback)
    payload.notes_count = len(booking.notes_list or [])
    # Derived badge for who must act next.
    payload.awaiting_party = booking_service.awaiting_party(booking)

    if detail:
        data = payload.model_dump()
        data["message_count"] = len(booking.messages or [])
        data["events"] = [
            BookingEventOut.model_validate(event).model_copy(
                update={"actor_name": event.actor.full_name if event.actor else None}
            )
            for event in (booking.events or [])
        ]
        # Notes are attached by the caller (visibility depends on the viewer).
        return BookingDetailOut(**data)
    return payload


# /consultants — public directory (any authenticated role)


@consultants.get("", response_model=ConsultantListOut)
def list_consultants(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str | None = Query(default=None, max_length=120),
    specialization: str | None = Query(default=None, max_length=60),
    language: str | None = Query(default=None, max_length=40),
    max_rate: float | None = Query(default=None, ge=0),
    available_from: str | None = Query(default=None),
    available_to: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConsultantListOut:
    """Browse consultant profiles, optionally filtered by availability/price."""
    start = _parse_datetime(available_from, "available_from")
    end = _parse_datetime(available_to, "available_to")
    profiles, total = booking_service.list_consultants(
        db,
        search=search,
        specialization=specialization,
        language=language,
        max_rate=max_rate,
        available_from=start,
        available_to=end,
        limit=limit,
        offset=offset,
    )
    return ConsultantListOut(
        items=[_consultant_out(db, profile) for profile in profiles],
        total=total,
        limit=limit,
        offset=offset,
    )


@consultants.get("/me/profile", response_model=ConsultantProfileOut)
def get_my_consultant_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantProfileOut:
    """The signed-in consultant's own storefront."""
    profile = booking_service.get_my_consultant_profile(db, user)
    return _consultant_out(db, profile)


@consultants.get("/{consultant_id}", response_model=ConsultantProfileDetail)
def get_consultant(
    consultant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantProfileDetail:
    profile = booking_service.get_consultant_profile(db, consultant_id)
    return _consultant_out(db, profile, detail=True)


@consultants.get("/{consultant_id}/reviews", response_model=ReviewListOut)
def list_consultant_reviews(
    consultant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ReviewListOut:
    reviews, total = booking_service.list_public_reviews(
        db, consultant_id, limit=limit, offset=offset
    )
    items = []
    for review in reviews:
        payload = ReviewOut.model_validate(review)
        payload.author_name = (
            review.user.full_name if review.user is not None else None
        )
        payload.booking_subject = (
            review.booking.subject if review.booking is not None else None
        )
        items.append(payload)
    return ReviewListOut(items=items, total=total)


@consultants.get("/{consultant_id}/availability", response_model=AvailabilityCalendarOut)
def get_consultant_availability(
    consultant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
) -> AvailabilityCalendarOut:
    """Day -> open slot counts, used to render the booking calendar strip."""
    profile = booking_service.get_consultant_profile(db, consultant_id)
    start = _parse_date(from_date, "from") or date.today()
    end = _parse_date(to_date, "to") or (start + timedelta(days=30))
    days = booking_service.get_available_days(
        db, consultant_id, from_date=start, to_date=end
    )
    return AvailabilityCalendarOut(
        consultant_id=consultant_id,
        timezone=profile.timezone,
        from_date=start,
        to_date=end,
        days=[AvailableDayOut(**day) for day in days],
    )


@consultants.get("/{consultant_id}/slots", response_model=DaySlotsOut)
def get_consultant_day_slots(
    consultant_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    on: str | None = Query(default=None, alias="date"),
) -> DaySlotsOut:
    """Open slots for one calendar day (defaults to today)."""
    profile = booking_service.get_consultant_profile(db, consultant_id)
    day = _parse_date(on, "date") or date.today()
    slots = booking_service.get_available_slots(db, consultant_id, day=day)
    return DaySlotsOut(
        consultant_id=consultant_id,
        timezone=profile.timezone,
        date=day,
        slots=[SlotOut.model_validate(slot) for slot in slots],
    )


@consultants.post("/{consultant_id}/bookings", response_model=BookingOut, status_code=201)
def book_consultant(
    consultant_id: uuid.UUID,
    payload: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_session_role),
) -> BookingOut:
    """Reserve a slot. The consultant must accept before the session is confirmed."""
    booking = booking_service.create_booking(
        db,
        user,
        consultant_id,
        slot_id=payload.slot_id,
        subject=payload.subject,
        notes=payload.notes,
        meeting_link=payload.meeting_link,
    )
    return _booking_out(booking)


@consultants.post(
    "/{consultant_id}/bookings/propose", response_model=BookingOut, status_code=201
)
def propose_consultant_booking(
    consultant_id: uuid.UUID,
    payload: BookingProposeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_session_role),
) -> BookingOut:
    """Request a session at a custom, seeker-proposed time (no slot required)."""
    booking = booking_service.propose_booking(
        db,
        user,
        consultant_id,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        subject=payload.subject,
        notes=payload.notes,
        meeting_link=payload.meeting_link,
    )
    return _booking_out(booking)


# /consultants/me/... — consultant self-service


@consultant.put("/me/profile", response_model=ConsultantProfileOut)
def upsert_my_consultant_profile(
    payload: ConsultantProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantProfileOut:
    profile = booking_service.create_or_update_my_consultant_profile(
        db, user, payload=payload.model_dump(exclude_unset=True)
    )
    return _consultant_out(db, profile)


@consultant.patch("/me/profile", response_model=ConsultantProfileOut)
def patch_my_consultant_profile(
    payload: ConsultantProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantProfileOut:
    profile = booking_service.create_or_update_my_consultant_profile(
        db, user, payload=payload.model_dump(exclude_unset=True)
    )
    return _consultant_out(db, profile)


@consultant.post("/me/profile/availability-toggle", response_model=ConsultantProfileOut)
def toggle_accepting(
    is_accepting_bookings: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantProfileOut:
    profile = booking_service.set_accepting_bookings(
        db, user, is_accepting=is_accepting_bookings
    )
    return _consultant_out(db, profile)


@consultant.get("/me/stats", response_model=ConsultantStatsOut)
def my_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultantStatsOut:
    profile = booking_service.get_my_consultant_profile(db, user)
    return ConsultantStatsOut(**booking_service.get_consultant_stats(db, profile))


# Availability


@consultant.get("/me/availability/rules", response_model=list[AvailabilityRuleOut])
def list_my_rules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AvailabilityRuleOut]:
    profile = booking_service.get_my_consultant_profile(db, user)
    return [
        _rule_out(rule) for rule in booking_service.list_rules(db, profile.id)
    ]


@consultant.post(
    "/me/availability/rules",
    response_model=AvailabilityRuleCreatedOut,
    status_code=201,
)
def create_my_rule(
    payload: AvailabilityRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AvailabilityRuleCreatedOut:
    rule, created = booking_service.create_availability_rule(
        db, user, data=payload.model_dump(exclude_unset=True)
    )
    return AvailabilityRuleCreatedOut(rule=_rule_out(rule), slots_created=created)


@consultant.patch("/me/availability/rules/{rule_id}", response_model=AvailabilityRuleCreatedOut)
def update_my_rule(
    rule_id: uuid.UUID,
    payload: AvailabilityRuleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AvailabilityRuleCreatedOut:
    rule, created = booking_service.update_availability_rule(
        db, user, rule_id, data=payload.model_dump(exclude_unset=True)
    )
    return AvailabilityRuleCreatedOut(rule=_rule_out(rule), slots_created=created)


@consultant.delete("/me/availability/rules/{rule_id}", status_code=204)
def delete_my_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    booking_service.delete_availability_rule(db, user, rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@consultant.post("/me/availability/generate", response_model=GenerateSlotsOut)
def generate_my_slots(
    payload: GenerateSlotsIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GenerateSlotsOut:
    created = booking_service.generate_my_slots(
        db, user, from_date=payload.from_date, to_date=payload.to_date
    )
    return GenerateSlotsOut(slots_created=created)


@consultant.get("/me/availability/slots", response_model=SlotListOut)
def list_my_slots(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: SlotStatus | None = Query(default=None),
    from_time: str | None = Query(default=None),
    to_time: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SlotListOut:
    slots, total = booking_service.list_my_slots(
        db,
        user,
        start_from=_parse_datetime(from_time, "from_time"),
        start_to=_parse_datetime(to_time, "to_time"),
        status=status,
        limit=limit,
        offset=offset,
    )
    return SlotListOut(
        items=[SlotOut.model_validate(slot) for slot in slots],
        total=total,
        limit=limit,
        offset=offset,
    )


@consultant.post("/me/availability/slots/{slot_id}/block", response_model=SlotOut)
def block_my_slot(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SlotOut:
    slot = booking_service.block_slot(db, user, slot_id)
    return SlotOut.model_validate(slot)


@consultant.post("/me/availability/slots/{slot_id}/unblock", response_model=SlotOut)
def unblock_my_slot(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SlotOut:
    slot = booking_service.unblock_slot(db, user, slot_id)
    return SlotOut.model_validate(slot)


@consultant.delete("/me/availability/slots/{slot_id}", status_code=204)
def delete_my_slot(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    booking_service.delete_slot(db, user, slot_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Consultant bookings


@consultant.get("/me/bookings", response_model=BookingListOut)
def list_my_consultant_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    booking_status: BookingStatus | None = Query(default=None, alias="status"),
    scope: str = Query(default="upcoming", pattern="^(upcoming|past|all)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BookingListOut:
    rows, total = booking_service.list_consultant_bookings(
        db,
        user,
        booking_status=booking_status,
        scope=scope,
        limit=limit,
        offset=offset,
    )
    return BookingListOut(
        items=[_booking_out(row) for row in rows], total=total, limit=limit, offset=offset
    )


@consultant.get("/me/bookings/{booking_id}", response_model=BookingDetailOut)
def get_my_consultant_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingDetailOut:
    booking = booking_service.get_consultant_booking(db, user, booking_id)
    detail = _booking_out(booking, detail=True)
    return _attach_notes(db, detail, booking, user)


@consultant.post("/me/bookings/{booking_id}/accept", response_model=BookingOut)
def accept_my_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    booking = booking_service.accept_booking(db, user, booking_id)
    return _booking_out(booking)


@consultant.patch("/me/bookings/{booking_id}/meeting-link", response_model=BookingOut)
def update_my_booking_meeting_link(
    booking_id: uuid.UUID,
    payload: BookingMeetingLinkIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    """The consultant shares (or clears) the Google Meet link for a session."""
    booking = booking_service.set_booking_meeting_link(
        db, user, booking_id, meeting_link=payload.meeting_link
    )
    return _booking_out(booking)


@consultant.post("/me/bookings/{booking_id}/reject", response_model=BookingOut)
def reject_my_booking(
    booking_id: uuid.UUID,
    payload: BookingCancelIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    booking = booking_service.reject_booking(
        db, user, booking_id, reason=payload.reason if payload else None
    )
    return _booking_out(booking)


@consultant.post("/me/bookings/{booking_id}/counter", response_model=BookingOut)
def counter_my_booking(
    booking_id: uuid.UUID,
    payload: BookingCounterIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    """Consultant suggests a different time; the booking then awaits the seeker."""
    booking = booking_service.counter_booking(
        db,
        user,
        booking_id,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        message=payload.message,
    )
    return _booking_out(booking)


@consultant.post("/me/bookings/{booking_id}/complete", response_model=BookingOut)
def complete_my_booking(
    booking_id: uuid.UUID,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    booking = booking_service.complete_booking(db, user, booking_id, force=force)
    return _booking_out(booking)


@consultant.post("/me/bookings/{booking_id}/cancel", response_model=BookingOut)
def cancel_my_consultant_booking(
    booking_id: uuid.UUID,
    payload: BookingCancelIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    booking = booking_service.cancel_consultant_booking(
        db, user, booking_id, reason=payload.reason if payload else None
    )
    return _booking_out(booking)


# Session notes


@consultant.get("/me/bookings/{booking_id}/notes", response_model=list[BookingNoteOut])
def list_my_booking_notes(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BookingNoteOut]:
    notes = booking_service.list_booking_notes(db, user, booking_id)
    return [_note_out(note) for note in notes]


@consultant.post(
    "/me/bookings/{booking_id}/notes",
    response_model=BookingNoteOut,
    status_code=201,
)
def add_my_booking_note(
    booking_id: uuid.UUID,
    payload: BookingNoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingNoteOut:
    note = booking_service.add_session_note(
        db,
        user,
        booking_id,
        body=payload.body,
        visibility=payload.visibility.value,
    )
    return _note_out(note)


@consultant.patch("/me/notes/{note_id}", response_model=BookingNoteOut)
def update_my_note(
    note_id: uuid.UUID,
    payload: BookingNoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingNoteOut:
    note = booking_service.update_session_note(
        db,
        user,
        note_id,
        body=payload.body,
        visibility=payload.visibility.value if payload.visibility else None,
    )
    return _note_out(note)


@consultant.delete("/me/notes/{note_id}", status_code=204)
def delete_my_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    booking_service.delete_session_note(db, user, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# /bookings — seeker session hub


@bookings.get("", response_model=BookingListOut)
def list_my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    booking_status: BookingStatus | None = Query(default=None, alias="status"),
    scope: str = Query(default="upcoming", pattern="^(upcoming|past|all)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BookingListOut:
    rows, total = booking_service.list_my_bookings(
        db,
        user,
        booking_status=booking_status,
        scope=scope,
        limit=limit,
        offset=offset,
    )
    return BookingListOut(
        items=[_booking_out(row) for row in rows], total=total, limit=limit, offset=offset
    )


@bookings.get("/{booking_id}", response_model=BookingDetailOut)
def get_my_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingDetailOut:
    booking = booking_service.get_my_booking(db, user, booking_id)
    detail = _booking_out(booking, detail=True)
    return _attach_notes(db, detail, booking, user)


@bookings.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_my_booking(
    booking_id: uuid.UUID,
    payload: BookingCancelIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    booking = booking_service.cancel_my_booking(
        db, user, booking_id, reason=payload.reason if payload else None
    )
    return _booking_out(booking)


@bookings.post("/{booking_id}/counter", response_model=BookingOut)
def counter_my_booking_seeker(
    booking_id: uuid.UUID,
    payload: BookingCounterIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    """Seeker suggests a different time; the booking then awaits the consultant."""
    booking = booking_service.counter_booking(
        db,
        user,
        booking_id,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        message=payload.message,
    )
    return _booking_out(booking)


@bookings.post("/{booking_id}/confirm", response_model=BookingOut)
def confirm_my_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    """Seeker confirms the consultant's counter-proposed time."""
    booking = booking_service.confirm_counter(db, user, booking_id)
    return _booking_out(booking)


# Per-booking chat (seeker <-> consultant; either side may use these)


@bookings.get("/{booking_id}/messages", response_model=BookingMessageListOut)
def list_booking_chat(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> BookingMessageListOut:
    rows, total = booking_service.list_booking_messages(
        db, user, booking_id, limit=limit, offset=offset
    )
    return BookingMessageListOut(
        items=[_message_out(row, me=user) for row in rows], total=total
    )


@bookings.post(
    "/{booking_id}/messages", response_model=BookingMessageOut, status_code=201
)
def post_booking_chat(
    booking_id: uuid.UUID,
    payload: BookingMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingMessageOut:
    message = booking_service.post_booking_message(db, user, booking_id, body=payload.body)
    return _message_out(message, me=user)


@bookings.post("/{booking_id}/feedback", response_model=FeedbackOut, status_code=201)
def submit_my_feedback(
    booking_id: uuid.UUID,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FeedbackOut:
    feedback = booking_service.submit_feedback(
        db,
        user,
        booking_id,
        rating=payload.rating,
        review=payload.review,
        is_public=payload.is_public,
    )
    return FeedbackOut.model_validate(feedback)


@bookings.get("/{booking_id}/notes", response_model=list[BookingNoteOut])
def list_my_booking_notes_public(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BookingNoteOut]:
    notes = booking_service.list_booking_notes(db, user, booking_id)
    return [_note_out(note) for note in notes]


def _attach_notes(
    db: Session, detail: BookingDetailOut, booking, user: User
) -> BookingDetailOut:
    """Populate `session_notes` honouring each side's visibility."""
    notes = booking_service.list_booking_notes(db, user, booking.id)
    detail.session_notes = [_note_out(note) for note in notes]
    return detail

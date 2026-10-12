"""Schemas for the live consultation & booking module."""
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.booking import (
    BookingOrigin,
    BookingStatus,
    CalendarSyncStatus,
    NoteVisibility,
    SlotStatus,
)

_MIN_PASSWORDISH = object()  # sentinel kept out of the public namespace


# Shared


class PageMeta(BaseModel):
    """Envelope for paginated list responses."""

    model_config = ConfigDict(from_attributes=True)

    total: int = 0
    limit: int = 50
    offset: int = 0

    @property
    def has_more(self) -> bool:
        return self.offset + self.limit < self.total


class SlotBrief(BaseModel):
    """The slot a booking points at (kept readable after the slot is deleted)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: SlotStatus


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str


# Consultant profiles


class ConsultantProfileCreate(BaseModel):
    """Create/replace the signed-in consultant's profile (PUT semantics)."""

    headline: str = Field(min_length=3, max_length=160)
    bio: str | None = Field(default=None, max_length=4000)
    specializations: list[str] = Field(default_factory=list, max_length=20)
    modalities: list[str] = Field(default_factory=list, max_length=20)
    languages: list[str] = Field(default_factory=list, max_length=20)
    years_experience: int = Field(default=0, ge=0, le=80)
    session_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=Decimal("999999"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    session_duration_minutes: int = Field(default=60, ge=15, le=480)
    buffer_minutes: int = Field(default=15, ge=0, le=240)
    timezone: str = Field(default="UTC", max_length=64)
    is_accepting_bookings: bool = True

    @field_validator("headline")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()

    @field_validator("specializations", "modalities", "languages")
    @classmethod
    def _unique_tokens(cls, values: list[str]) -> list[str]:
        seen: list[str] = []
        for raw in values:
            token = str(raw).strip()[:60]
            if token and token.lower() not in {s.lower() for s in seen}:
                seen.append(token)
        return seen


class ConsultantProfileUpdate(BaseModel):
    """Partial update (PATCH semantics) of the signed-in consultant's profile."""

    headline: str | None = Field(default=None, min_length=3, max_length=160)
    bio: str | None = Field(default=None, max_length=4000)
    specializations: list[str] | None = Field(default=None, max_length=20)
    modalities: list[str] | None = Field(default=None, max_length=20)
    languages: list[str] | None = Field(default=None, max_length=20)
    years_experience: int | None = Field(default=None, ge=0, le=80)
    session_rate: Decimal | None = Field(default=None, ge=0, le=Decimal("999999"))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    session_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    buffer_minutes: int | None = Field(default=None, ge=0, le=240)
    timezone: str | None = Field(default=None, max_length=64)
    is_accepting_bookings: bool | None = None


class ConsultantProfileOut(BaseModel):
    """Public storefront of a consultant."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    headline: str
    bio: str | None
    specializations: list
    modalities: list
    languages: list
    years_experience: int
    session_rate: Decimal
    currency: str
    session_duration_minutes: int
    buffer_minutes: int
    timezone: str
    is_accepting_bookings: bool
    total_sessions: int
    avg_rating: Decimal | None
    review_count: int
    created_at: datetime
    updated_at: datetime

    # Joined presentation fields (filled in by the routers).
    full_name: str | None = None
    email: str | None = None
    calendar_connected: bool = False


class ConsultantProfileDetail(ConsultantProfileOut):
    """Consultant storefront plus the next open slot (used on the detail page)."""

    next_available_at: datetime | None = None
    open_slots_next_7_days: int = 0


class ConsultantListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[ConsultantProfileOut]
    total: int
    limit: int
    offset: int


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    rating: int
    review: str | None
    is_public: bool
    created_at: datetime
    author_name: str | None = None
    booking_subject: str | None = None


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int


class ConsultantStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upcoming_sessions: int
    pending_requests: int
    completed_sessions: int
    declined_or_cancelled: int
    open_slots: int
    total_sessions: int
    avg_rating: float | None
    review_count: int


# Availability


class AvailabilityRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=60, ge=15, le=480)
    buffer_minutes: int = Field(default=15, ge=0, le=240)
    timezone: str = Field(default="UTC", max_length=64)
    effective_from: date | None = None
    effective_until: date | None = None
    is_active: bool = True

    @field_validator("timezone")
    @classmethod
    def _tz(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value.strip() or "UTC")
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc
        return (value or "UTC").strip()


class AvailabilityRuleUpdate(BaseModel):
    weekday: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(default=None, ge=15, le=480)
    buffer_minutes: int | None = Field(default=None, ge=0, le=240)
    timezone: str | None = Field(default=None, max_length=64)
    effective_from: date | None = None
    effective_until: date | None = None
    is_active: bool | None = None


class AvailabilityRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultant_id: uuid.UUID
    weekday: int
    # Filled in by the routers from `AVAILABILITY_DAY_NAMES`.
    weekday_name: str = ""
    start_time: time
    end_time: time
    slot_duration_minutes: int
    buffer_minutes: int
    timezone: str
    effective_from: date
    effective_until: date | None
    is_active: bool
    created_at: datetime


class AvailabilityRuleCreatedOut(BaseModel):
    rule: AvailabilityRuleOut
    slots_created: int


class GenerateSlotsIn(BaseModel):
    from_date: date
    to_date: date


class GenerateSlotsOut(BaseModel):
    slots_created: int


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultant_id: uuid.UUID
    rule_id: uuid.UUID | None
    start_time: datetime
    end_time: datetime
    timezone: str
    status: SlotStatus
    booking_id: uuid.UUID | None
    created_at: datetime


class SlotListOut(BaseModel):
    items: list[SlotOut]
    total: int
    limit: int
    offset: int


class AvailableDayOut(BaseModel):
    date: date
    available_slots: int


class AvailabilityCalendarOut(BaseModel):
    consultant_id: uuid.UUID
    timezone: str
    from_date: date
    to_date: date
    days: list[AvailableDayOut]


class DaySlotsOut(BaseModel):
    consultant_id: uuid.UUID
    timezone: str
    date: date
    slots: list[SlotOut]


# Bookings


class BookingCreate(BaseModel):
    slot_id: uuid.UUID
    subject: str = Field(min_length=3, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    # Optional meeting link pasted by the seeker for this particular request.
    meeting_link: str | None = Field(default=None, max_length=500)

    @field_validator("subject")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()

    @field_validator("meeting_link")
    @classmethod
    def _meeting_link(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("Meeting link must be a full http(s) URL")
        return cleaned[:500]


class BookingProposeIn(BaseModel):
    """Seeker proposes a custom meeting time (no pre-published slot)."""

    start_time: datetime
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    subject: str = Field(min_length=3, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    # Optional meeting link pasted by the seeker for this particular request.
    meeting_link: str | None = Field(default=None, max_length=500)

    @field_validator("subject")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()

    @field_validator("meeting_link")
    @classmethod
    def _meeting_link(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("Meeting link must be a full http(s) URL")
        return cleaned[:500]


class BookingCounterIn(BaseModel):
    """Either party suggests a different time for a pending/countered booking."""

    start_time: datetime
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    message: str | None = Field(default=None, max_length=2000)


class BookingMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)

    @field_validator("body")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip()


class BookingMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    sender_id: uuid.UUID | None
    sender_name: str | None = None
    sender_role: str | None = None
    is_me: bool = False
    body: str
    created_at: datetime


class BookingMessageListOut(BaseModel):
    items: list[BookingMessageOut]
    total: int


class BookingCancelIn(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class BookingNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    visibility: NoteVisibility = NoteVisibility.private


class BookingNoteUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1, max_length=4000)
    visibility: NoteVisibility | None = None


class BookingNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    visibility: NoteVisibility
    body: str
    created_at: datetime
    updated_at: datetime


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: str | None = Field(default=None, max_length=4000)
    is_public: bool = True


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    review: str | None
    is_public: bool
    created_at: datetime


class BookingEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    from_status: str | None
    to_status: str | None
    message: str | None
    actor_name: str | None = None
    created_at: datetime


class BookingOut(BaseModel):
    """A booking, with the joined names both dashboards render."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slot_id: uuid.UUID | None = None
    origin: BookingOrigin = BookingOrigin.slot
    consultant_id: uuid.UUID
    user_id: uuid.UUID
    status: BookingStatus
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    timezone: str
    subject: str
    notes: str | None
    price: Decimal
    currency: str

    # Google Calendar / Meet
    google_event_id: str | None
    google_calendar_id: str | None
    meet_link: str | None
    meet_code: str | None
    calendar_sync_status: CalendarSyncStatus
    calendar_synced_at: datetime | None
    calendar_error: str | None

    reminder_sent_at: datetime | None
    short_reminder_sent_at: datetime | None
    accepted_at: datetime | None
    rejected_at: datetime | None
    cancelled_at: datetime | None
    completed_at: datetime | None
    cancellation_reason: str | None
    cancelled_by_name: str | None = None
    last_proposed_by_id: uuid.UUID | None = None

    created_at: datetime
    updated_at: datetime

    # Joined presentation fields.
    consultant_name: str | None = None
    consultant_user_id: uuid.UUID | None = None
    seeker_name: str | None = None
    seeker_email: str | None = None
    consultant_headline: str | None = None
    slot: SlotBrief | None = None
    can_join_meet: bool = False
    # Who the booking is currently waiting on: "consultant", "seeker", or None.
    awaiting_party: str | None = None
    feedback: FeedbackOut | None = None
    notes_count: int = 0
    message_count: int = 0


class BookingListOut(BaseModel):
    items: list[BookingOut]
    total: int
    limit: int
    offset: int


class BookingDetailOut(BookingOut):
    """Booking plus its audit trail and visible notes."""

    events: list[BookingEventOut] = Field(default_factory=list)
    session_notes: list[BookingNoteOut] = Field(default_factory=list)


# Google Calendar connection


class CalendarConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultant_id: uuid.UUID
    google_email: str | None
    calendar_id: str
    timezone: str
    is_active: bool
    connected_at: datetime
    last_error: str | None


class CalendarAuthorizeOut(BaseModel):
    authorization_url: str
    state: str
    scopes: list[str]


class CalendarConnectIn(BaseModel):
    code: str = Field(min_length=4, max_length=2048)
    state: str | None = None


class CalendarStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calendar_enabled: bool
    oauth_configured: bool
    service_account_configured: bool
    connection: CalendarConnectionOut | None = None
    synced_bookings: int = 0


class CalendarUpdateIn(BaseModel):
    calendar_id: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None

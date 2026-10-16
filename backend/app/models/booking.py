"""Live consultation & booking models (FR-BOOK-001 … FR-BOOK-010)."""
import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class BookingStatus(str, enum.Enum):
    """Booking lifecycle: Pending → Accepted/Rejected → Completed/Cancelled."""

    pending = "pending"
    countered = "countered"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"


class BookingOrigin(str, enum.Enum):
    """How the booking was first created."""

    slot = "slot"          # seeker picked a consultant-published slot
    proposal = "proposal"  # seeker proposed a custom time


class SlotStatus(str, enum.Enum):
    """Lifecycle of a single materialised availability slot."""

    available = "available"
    booked = "booked"
    blocked = "blocked"
    cancelled = "cancelled"


class NoteVisibility(str, enum.Enum):
    """Whether a consultant session note is visible to the seeker."""

    private = "private"
    shared = "shared"


# Roles allowed to publish availability and take bookings.
CONSULTANT_ROLES = ("tarot_reader", "spiritual_consultant")

# Human labels for AvailabilityRule.weekday (Monday = 0).
AVAILABILITY_DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


class ConsultantProfile(Base, TimestampMixin):
    """Public storefront for one consultant (a user with a staff role)."""

    __tablename__ = "consultant_profiles"
    __table_args__ = (
        Index("ix_consultant_profiles_accepting", "is_accepting_bookings"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    headline: Mapped[str] = mapped_column(String(160), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    specializations: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    modalities: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    languages: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    session_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    session_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    is_accepting_bookings: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="consultant_profile")
    availability_rules: Mapped[list["AvailabilityRule"]] = relationship(
        back_populates="consultant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AvailabilityRule.created_at",
    )
    slots: Mapped[list["AvailabilitySlot"]] = relationship(
        back_populates="consultant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="consultant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<ConsultantProfile id={self.id} user_id={self.user_id}>"


class AvailabilityRule(Base, TimestampMixin):
    """Recurring weekly window from which concrete slots are materialised."""

    __tablename__ = "availability_rules"
    __table_args__ = (
        UniqueConstraint(
            "consultant_id",
            "weekday",
            "start_time",
            "end_time",
            "effective_from",
            name="uq_availability_rule_window",
        ),
        Index("ix_availability_rules_consultant", "consultant_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    consultant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 0 = Monday … 6 = Sunday (matches date.weekday()).
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    buffer_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    consultant: Mapped["ConsultantProfile"] = relationship(back_populates="availability_rules")

    def __repr__(self) -> str:
        return (
            f"<AvailabilityRule id={self.id} consultant_id={self.consultant_id} "
            f"weekday={self.weekday} {self.start_time}-{self.end_time}>"
        )


class AvailabilitySlot(Base, TimestampMixin):
    """One concrete, bookable time window owned by a consultant."""

    __tablename__ = "availability_slots"
    __table_args__ = (
        Index("ix_availability_slots_consultant_start", "consultant_id", "start_time"),
        Index("ix_availability_slots_status", "consultant_id", "status", "start_time"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    consultant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("availability_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="booking_slot_status", native_enum=False, create_type=False),
        nullable=False,
        default=SlotStatus.available,
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    consultant: Mapped["ConsultantProfile"] = relationship(back_populates="slots")
    rule: Mapped["AvailabilityRule | None"] = relationship()

    def __repr__(self) -> str:
        return f"<AvailabilitySlot id={self.id} consultant_id={self.consultant_id} start={self.start_time}>"


class Booking(Base, TimestampMixin):
    """A booked session between one seeker and one consultant."""

    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_consultant_start", "consultant_id", "start_time"),
        Index("ix_bookings_user_start", "user_id", "start_time"),
        Index("ix_bookings_status_start", "status", "start_time"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    # Null for proposed-time bookings; set once a slot backs the session.
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("availability_slots.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    origin: Mapped[BookingOrigin] = mapped_column(
        Enum(BookingOrigin, name="booking_origin", native_enum=False, create_type=False),
        nullable=False,
        default=BookingOrigin.slot,
    )
    consultant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status", native_enum=False, create_type=False),
        nullable=False,
        default=BookingStatus.pending,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Google Meet link, created by a participant and shared with the other.
    meet_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Reminders
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    short_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Lifecycle timestamps
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Time negotiation
    last_proposed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Single link between the pair: `bookings.slot_id` owns it.
    slot: Mapped["AvailabilitySlot"] = relationship(
        foreign_keys="Booking.slot_id"
    )
    consultant: Mapped["ConsultantProfile"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(
        foreign_keys="Booking.user_id", back_populates="client_bookings"
    )
    cancelled_by: Mapped["User | None"] = relationship(
        foreign_keys="Booking.cancelled_by_id"
    )
    last_proposed_by: Mapped["User | None"] = relationship(
        foreign_keys="Booking.last_proposed_by_id"
    )
    messages: Mapped[list["BookingMessage"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BookingMessage.created_at",
    )
    events: Mapped[list["BookingEvent"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BookingEvent.created_at",
    )
    notes_list: Mapped[list["SessionNote"]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SessionNote.created_at)",
    )
    feedback: Mapped["SessionFeedback | None"] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Booking id={self.id} consultant_id={self.consultant_id} status={self.status}>"


class BookingEvent(Base, TimestampMixin):
    """Append-only audit trail for every booking status transition."""

    __tablename__ = "booking_events"
    __table_args__ = (
        Index("ix_booking_events_booking_created", "booking_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    booking_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict, server_default="{}"
    )

    booking: Mapped["Booking"] = relationship(back_populates="events")
    actor: Mapped["User | None"] = relationship(
        foreign_keys="BookingEvent.actor_id", back_populates="booking_events"
    )

    def __repr__(self) -> str:
        return f"<BookingEvent id={self.id} booking_id={self.booking_id} type={self.event_type}>"


class SessionNote(Base, TimestampMixin):
    """Consultant's post-session notes; optionally shared with the seeker."""

    __tablename__ = "session_notes"
    __table_args__ = (
        Index("ix_session_notes_booking_created", "booking_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visibility: Mapped[NoteVisibility] = mapped_column(
        Enum(NoteVisibility, name="booking_note_visibility", native_enum=False, create_type=False),
        nullable=False,
        default=NoteVisibility.private,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="notes_list")
    author: Mapped["User"] = relationship(
        foreign_keys="SessionNote.author_id", back_populates="session_notes"
    )

    def __repr__(self) -> str:
        return f"<SessionNote id={self.id} booking_id={self.booking_id}>"


class SessionFeedback(Base, TimestampMixin):
    """Seeker's rating/review for a completed booking."""

    __tablename__ = "session_feedbacks"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_session_feedback_booking"),
        Index("ix_session_feedbacks_consultant", "consultant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consultant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultant_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    booking: Mapped["Booking"] = relationship(back_populates="feedback")
    user: Mapped["User"] = relationship(
        foreign_keys="SessionFeedback.user_id", back_populates="session_feedbacks"
    )

    def __repr__(self) -> str:
        return f"<SessionFeedback id={self.id} booking_id={self.booking_id} rating={self.rating}>"


class BookingMessage(Base, TimestampMixin):
    """One chat message on a booking thread, between its seeker and consultant."""

    __tablename__ = "booking_messages"
    __table_args__ = (
        Index("ix_booking_messages_booking_created", "booking_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="messages")
    sender: Mapped["User | None"] = relationship(foreign_keys="BookingMessage.sender_id")

    def __repr__(self) -> str:
        return f"<BookingMessage id={self.id} booking_id={self.booking_id}>"

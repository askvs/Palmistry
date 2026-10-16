import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.booking import (
        AvailabilitySlot,
        Booking,
        BookingEvent,
        ConsultantProfile,
        SessionFeedback,
        SessionNote,
    )
    from app.models.consultation import Consultation
    from app.models.custom_spread import CustomSpread
    from app.models.profile import Profile
    from app.models.reading import Reading
    from app.models.refresh_token import RefreshToken


class UserRole(str, enum.Enum):
    user = "user"
    tarot_reader = "tarot_reader"
    spiritual_consultant = "spiritual_consultant"
    admin = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        default=UserRole.user,
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    profile: Mapped["Profile"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )
    readings: Mapped[list["Reading"]] = relationship(
        foreign_keys="Reading.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        foreign_keys="Consultation.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Live consultation and booking module
    consultant_profile: Mapped["ConsultantProfile"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    client_bookings: Mapped[list["Booking"]] = relationship(
        foreign_keys="Booking.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    booking_events: Mapped[list["BookingEvent"]] = relationship(
        foreign_keys="BookingEvent.actor_id",
        back_populates="actor",
        passive_deletes=True,
    )
    session_notes: Mapped[list["SessionNote"]] = relationship(
        foreign_keys="SessionNote.author_id",
        back_populates="author",
        passive_deletes=True,
    )
    session_feedbacks: Mapped[list["SessionFeedback"]] = relationship(
        foreign_keys="SessionFeedback.user_id",
        back_populates="user",
        passive_deletes=True,
    )
    # Tarot reader spread authoring
    custom_spreads: Mapped[list["CustomSpread"]] = relationship(
        foreign_keys="CustomSpread.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

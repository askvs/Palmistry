import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    age_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avatar_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_deck: Mapped[str] = mapped_column(
        String(80), nullable=False, server_default="Rider-Waite-Smith"
    )
    favorite_spread: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="Three Card"
    )
    tone: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Gentle")
    notify_daily_guidance: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_reminders: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notify_sms: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    notify_insights: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_growth: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_announcements: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    interests: Mapped[list["ProfileInterest"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProfileInterest.interest",
    )
    goals: Mapped[list["ProfileGoal"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProfileGoal.created_at",
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id}>"


class ProfileInterest(Base):
    __tablename__ = "profile_interests"
    __table_args__ = (UniqueConstraint("profile_id", "interest", name="uq_profile_interest"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interest: Mapped[str] = mapped_column(String(60), nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="interests")

    def __repr__(self) -> str:
        return f"<ProfileInterest profile_id={self.profile_id} interest={self.interest}>"


class ProfileGoal(Base, TimestampMixin):
    __tablename__ = "profile_goals"

    id: Mapped[uuid.UUID] = uuid_pk()
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="goals")

    def __repr__(self) -> str:
        return f"<ProfileGoal id={self.id} profile_id={self.profile_id}>"

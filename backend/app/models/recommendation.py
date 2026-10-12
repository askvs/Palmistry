"""Recommendation records and feedback events (Module 9, FR-034, TASK-012)."""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.reading import Reading
    from app.models.user import User


class RecommendationType(str, enum.Enum):
    personal_growth = "personal_growth"
    relationship = "relationship"
    career = "career"
    goal_alignment = "goal_alignment"
    spiritual_development = "spiritual_development"


class RecommendationStatus(str, enum.Enum):
    new = "new"
    accepted = "accepted"
    dismissed = "dismissed"
    completed = "completed"


class EventType(str, enum.Enum):
    shown = "shown"
    accepted = "accepted"
    dismissed = "dismissed"
    completed = "completed"
    rated = "rated"


class RecommendationRecord(Base, TimestampMixin):
    __tablename__ = "recommendation_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    reading_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("readings.id", ondelete="SET NULL"), nullable=True
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    rec_type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType, name="recommendation_type", native_enum=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0.0)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", native_enum=True),
        default=RecommendationStatus.new,
        nullable=False,
        index=True,
    )
    feedback_rating: Mapped[int | None] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User | None"] = relationship(foreign_keys=[user_id])
    reading: Mapped["Reading | None"] = relationship(foreign_keys=[reading_id])
    events: Mapped[list["RecommendationEvent"]] = relationship(
        back_populates="record", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return (
            f"<RecommendationRecord id={self.id} user_id={self.user_id} "
            f"type={self.rec_type} status={self.status}>"
        )


class RecommendationEvent(Base, TimestampMixin):
    __tablename__ = "recommendation_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="recommendation_event_type", native_enum=True), nullable=False, index=True
    )
    rating: Mapped[int | None] = mapped_column(nullable=True)

    record: Mapped["RecommendationRecord"] = relationship(back_populates="events")

    def __repr__(self) -> str:
        return f"<RecommendationEvent id={self.id} record_id={self.record_id} type={self.event_type}>"

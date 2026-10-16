"""Readings: palm and tarot reading records (FR-002, FR-003)."""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class ReadingType(str, enum.Enum):
    palm = "palm"
    tarot = "tarot"


class ReadingStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"


class Reading(Base, TimestampMixin):
    __tablename__ = "readings"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ReadingType] = mapped_column(Enum(ReadingType, name="reading_type", native_enum=True))
    status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus, name="reading_status", native_enum=True),
        default=ReadingStatus.pending,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="readings")
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<Reading id={self.id} user_id={self.user_id} type={self.type} status={self.status}>"

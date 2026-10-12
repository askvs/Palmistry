"""Reader-authored tarot spreads (Tarot Reader: create spreads)."""
import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk


class SpreadVisibility(str, enum.Enum):
    """Who may run a reading with a reader-authored spread."""

    private = "private"
    shared = "shared"


class CustomSpread(Base, TimestampMixin):
    """One reader-authored spread definition."""

    __tablename__ = "custom_spreads"
    __table_args__ = (
        Index("ix_custom_spreads_owner_name", "owner_id", "name"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="custom")
    # [{"position": 1, "name": "...", "description": "..."}] — 1..10 entries.
    positions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    card_count: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[SpreadVisibility] = mapped_column(
        String(20), nullable=False, default=SpreadVisibility.private.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    owner: Mapped["User"] = relationship(back_populates="custom_spreads")

    def __repr__(self) -> str:
        return f"<CustomSpread id={self.id} name={self.name} cards={self.card_count}>"

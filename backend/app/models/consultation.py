"""Consultation and audit-log models (FR-006, FR-007, §49.3 audit logs)."""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class ConsultationStatus(str, enum.Enum):
    open = "open"
    in_review = "in_review"
    resolved = "resolved"


class Consultation(Base, TimestampMixin):
    """A guidance/consultation thread a spiritual consultant works on."""

    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consultant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus, name="consultation_status", native_enum=True),
        default=ConsultationStatus.open,
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="consultations")
    consultant: Mapped["User | None"] = relationship(foreign_keys=[consultant_id])
    messages: Mapped[list["ConsultationMessage"]] = relationship(
        back_populates="consultation",
        cascade="all, delete-orphan",
        order_by="ConsultationMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<Consultation id={self.id} user_id={self.user_id} status={self.status}>"


class ConsultationMessage(Base, TimestampMixin):
    """A message in a consultation thread between a seeker and a responsible role."""

    __tablename__ = "consultation_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    consultation: Mapped["Consultation"] = relationship(back_populates="messages")
    sender: Mapped["User | None"] = relationship(foreign_keys=[sender_id])

    def __repr__(self) -> str:
        return f"<ConsultationMessage id={self.id} consultation_id={self.consultation_id}>"


class AuditLog(Base, TimestampMixin):
    """Append-only admin audit trail (§49.3: audit logs)."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target: Mapped[str] = mapped_column(String(200), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} target={self.target}>"

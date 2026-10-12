"""Operational error log (FR-038: monitor errors, security and performance)."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk


class ErrorLevel(str, enum.Enum):
    error = "error"
    security = "security"


class ErrorKind(str, enum.Enum):
    server_error = "server_error"
    auth_failure = "auth_failure"
    forbidden = "forbidden"
    rate_limited = "rate_limited"
    validation_error = "validation_error"


class ErrorLog(Base, TimestampMixin):
    """One operational failure or security event, deduplicated by fingerprint."""

    __tablename__ = "error_logs"
    __table_args__ = (
        Index(
            "ix_error_logs_fingerprint",
            "kind",
            "method",
            "path",
            "status_code",
            "message",
        ),
        Index("ix_error_logs_level_created", "level", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    level: Mapped[ErrorLevel] = mapped_column(
        Enum(ErrorLevel, name="error_level", native_enum=False),
        nullable=False,
        default=ErrorLevel.error,
        index=True,
    )
    kind: Mapped[ErrorKind] = mapped_column(
        Enum(ErrorKind, name="error_kind", native_enum=False),
        nullable=False,
        index=True,
    )
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return (
            f"<ErrorLog id={self.id} kind={self.kind} status={self.status_code} "
            f"path={self.path} occurrences={self.occurrences}>"
        )

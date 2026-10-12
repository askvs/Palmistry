"""Notification model for in-app notifications."""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    """Supported notification categories."""
    daily_guidance = "daily_guidance"
    reading_reminder = "reading_reminder"
    insight_update = "insight_update"
    growth_alert = "growth_alert"
    platform_announcement = "platform_announcement"
    reading_completed = "reading_completed"
    # Event-driven notifications (new activity across the platform).
    new_user = "new_user"
    new_reading = "new_reading"
    new_question = "new_question"
    # Live consultation & booking module (migration 0007 adds these enum values).
    booking_requested = "booking_requested"
    booking_accepted = "booking_accepted"
    booking_rejected = "booking_rejected"
    booking_cancelled = "booking_cancelled"
    booking_reminder = "booking_reminder"
    booking_completed = "booking_completed"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels."""
    low = "low"
    normal = "normal"
    high = "high"


class NotificationChannel(str, enum.Enum):
    """Delivery channels."""
    in_app = "in_app"
    email = "email"


class DeliveryStatus(str, enum.Enum):
    """Delivery status for tracking."""
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class Notification(Base, TimestampMixin):
    """User notification record."""
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority", native_enum=True),
        nullable=False,
        default=NotificationPriority.normal,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # The DB column is named `metadata` (see migration 0006).
    notification_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict, server_default="{}"
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type={self.type}>"


class NotificationDelivery(Base, TimestampMixin):
    """Track delivery per channel."""
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        Index("ix_notification_deliveries_notification", "notification_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", native_enum=True),
        nullable=False,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status", native_enum=True),
        nullable=False,
        default=DeliveryStatus.pending,
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempt_count: Mapped[int] = mapped_column(default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<NotificationDelivery id={self.id} notification_id={self.notification_id} channel={self.channel} status={self.status}>"

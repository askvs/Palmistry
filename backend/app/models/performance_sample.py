# Persisted API latency samples powering the admin performance report.
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.common import uuid_pk


class PerformanceSample(Base):
    __tablename__ = "performance_samples"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Captured when the request finished, not when the buffer was flushed.
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)

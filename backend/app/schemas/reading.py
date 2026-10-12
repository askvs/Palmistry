"""Reading schemas (FR-002, FR-003)."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.reading import ReadingStatus, ReadingType


class TarotReadingCreate(BaseModel):
    """User selects a spread and cards (FR-003)."""

    spread: str = Field(min_length=1, max_length=80)
    cards: list[str] = Field(min_length=1, max_length=10)
    question: str | None = Field(default=None, max_length=500)


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: ReadingType
    status: ReadingStatus
    title: str
    summary: str
    result: dict[str, Any]
    notes: str | None
    reviewed_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ReadingReviewUpdate(BaseModel):
    """Reader/admin update: track the session and manage the report (FR-004)."""

    status: ReadingStatus | None = None
    notes: str | None = Field(default=None, max_length=4000)


class ReadingUserUpdate(BaseModel):
    """Owner updates: rename or add their own notes/question context."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)


class ReadingListOut(BaseModel):
    items: list[ReadingOut]
    total: int


class DayCount(BaseModel):
    day: str
    count: int


class TypeCount(BaseModel):
    type: str
    count: int


class StatusCount(BaseModel):
    status: str
    count: int


class ReadingAnalytics(BaseModel):
    total: int
    by_status: list[StatusCount]
    by_type: list[TypeCount]
    per_day: list[DayCount]

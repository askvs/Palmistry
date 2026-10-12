"""Consultation schemas (FR-006)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.consultation import ConsultationStatus


class ConsultationCreate(BaseModel):
    """A user asks for spiritual guidance (FR-006)."""

    topic: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)


class ConsultationGuidanceUpdate(BaseModel):
    """Consultant provides personalized spiritual guidance (FR-006)."""

    guidance: str = Field(min_length=1, max_length=8000)
    status: ConsultationStatus | None = None


class ConsultantAssign(BaseModel):
    consultant_id: uuid.UUID | None = None


class ConsultationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    consultant_id: uuid.UUID | None
    topic: str
    message: str
    guidance: str | None
    status: ConsultationStatus
    created_at: datetime
    updated_at: datetime


class ConsultationListOut(BaseModel):
    items: list[ConsultationOut]
    total: int


class ConsultationMessageCreate(BaseModel):
    """A follow-up message in a consultation thread (seeker or responsible role)."""

    body: str = Field(min_length=1, max_length=4000)


class ConsultationMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    sender_id: uuid.UUID | None
    sender_name: str | None = None
    sender_role: str | None = None
    is_staff: bool = False
    body: str
    created_at: datetime


class ConsultationMessageListOut(BaseModel):
    items: list[ConsultationMessageOut]
    total: int


class GuidanceEffectiveness(BaseModel):
    total_guidance: int
    with_guidance: int
    avg_user_rating: float | None
    ratings_count: int
    resolution_rate: float
    avg_first_response_minutes: float | None
    awaiting_reply: int


class TopicCount(BaseModel):
    topic: str
    count: int


class ConsultationInsights(BaseModel):
    total_requests: int
    by_status: list[dict]
    top_topics: list[TopicCount]


class UserTrends(BaseModel):
    total_users: int
    active_users: int
    readings_per_day: list[dict]
    consultations_per_day: list[dict]

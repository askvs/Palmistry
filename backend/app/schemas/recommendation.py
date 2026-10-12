"""Pydantic schemas for the Recommendation Engine (Module 9, FR-034, TASK-012)."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

RecommendationTypeLiteral = Literal[
    "personal_growth",
    "relationship",
    "career",
    "goal_alignment",
    "spiritual_development",
]


# Requests

class RecommendationGenerateRequest(BaseModel):
    """Request to generate an LLM recommendation batch (palm and/or tarot)."""

    palm_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Palm analysis result JSON (from a completed reading)"
    )
    reading_id: Optional[str] = Field(
        default=None, min_length=1, description="Completed palm reading ID to use as source data"
    )
    tarot_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Tarot reading result JSON — usable as the sole source"
    )
    tarot_reading_id: Optional[str] = Field(
        default=None, min_length=1, description="Completed tarot reading ID — usable as the sole source"
    )
    question: Optional[str] = Field(
        default=None, max_length=500, description="Optional focus question steering the guidance"
    )
    types: Optional[List[RecommendationTypeLiteral]] = Field(
        default=None, description="Subset of recommendation types to include (default: all five)"
    )
    max_total: int = Field(default=8, ge=1, le=16, description="Maximum recommendations returned")
    per_type: int = Field(default=2, ge=1, le=4, description="Maximum recommendations per type")
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Context overrides (goals, interests, dominant_element, strengths, weaknesses)",
    )


class RecommendationFeedbackRequest(BaseModel):
    """Feedback on one served recommendation (steers the next LLM batch)."""

    action: Literal["accepted", "completed", "rated"]
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Required when action='rated'")


# Responses

class RecommendationScoreBreakdown(BaseModel):
    """LLM-scored relevance components (all in [0, 1])."""

    context_relevance: float = 0.0
    personalization: float = 0.0
    goal_alignment: float = 0.0
    blended: float = 0.0


class RecommendationItem(BaseModel):
    id: str
    type: RecommendationTypeLiteral
    title: str
    text: str
    tags: List[str] = Field(default_factory=list)
    elements: List[str] = Field(default_factory=list)
    effort: str = "low"
    horizon: str = "weekly"
    priority: str = "medium"
    rank: int = 0
    final_score: float = 0.0
    scores: RecommendationScoreBreakdown = Field(default_factory=RecommendationScoreBreakdown)
    matched_reasons: List[str] = Field(default_factory=list)
    cluster: int = 0
    reasoning: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    element_affinity: Optional[str] = None


class PersistedRecordRef(BaseModel):
    record_id: str
    item_id: str


class RecommendationGenerateResponse(BaseModel):
    batch_id: str
    count: int
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    persisted: List[PersistedRecordRef] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = ""


class RecommendationRecordOut(BaseModel):
    id: str
    batch_id: str
    reading_id: Optional[str] = None
    item_id: str
    rec_type: RecommendationTypeLiteral
    title: str
    text: str
    rank: int
    score: float
    priority: str
    status: Literal["new", "accepted", "dismissed", "completed"]
    feedback_rating: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class RecommendationListResponse(BaseModel):
    items: List[RecommendationRecordOut] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class RecommendationMetricsResponse(BaseModel):
    scope: str = "platform"
    total_recommendations: int = 0
    status_counts: Dict[str, int] = Field(default_factory=dict)
    engagement_rate: float = 0.0
    dismissal_rate: float = 0.0
    completion_rate: float = 0.0
    average_feedback_rating: Optional[float] = None
    guidance_relevance_score: Optional[float] = None
    type_counts: Dict[str, int] = Field(default_factory=dict)
    disclaimer: str = ""

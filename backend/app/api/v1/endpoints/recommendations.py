"""Recommendation Engine API endpoints (Module 9, FR-034, TASK-012)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.recommendations import (
    RecommendationServiceError,
    generate_recommendations,
    list_recommendations,
    recommendation_metrics,
    record_feedback,
)
from app.schemas.recommendation import (
    RecommendationFeedbackRequest,
    RecommendationGenerateRequest,
    RecommendationGenerateResponse,
    RecommendationListResponse,
    RecommendationMetricsResponse,
    RecommendationRecordOut,
)
from app.utils.logging import logger

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/generate",
    response_model=RecommendationGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalised LLM recommendations from a reading (FR-034)",
)
async def generate(
    payload: RecommendationGenerateRequest,
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Generate personalised guidance with the LLM engine (palm and/or tarot)."""
    try:
        result = generate_recommendations(
            db,
            user=user,
            reading_id=payload.reading_id,
            palm_data=payload.palm_data,
            tarot_reading_id=payload.tarot_reading_id,
            tarot_data=payload.tarot_data,
            question=payload.question,
            requested_types=payload.types,
            max_total=payload.max_total,
            per_type=payload.per_type,
            user_context=payload.user_context,
        )
    except RecommendationServiceError:
        raise
    except Exception as exc:
        logger.error("Recommendation endpoint failed: %s", exc)
        raise RecommendationServiceError(
            f"Recommendation generation failed: {exc}",
            code="RECOMMENDATION_GENERATION_ERROR",
            status_code=500,
        )
    return result


@router.get(
    "/me",
    response_model=RecommendationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List the signed-in user's recommendations",
)
async def my_recommendations(
    rec_type: Optional[str] = Query(default=None, alias="type"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    batch_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return list_recommendations(
        db,
        user=user,
        rec_type=rec_type,
        status=status_filter,
        batch_id=batch_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/metrics",
    response_model=RecommendationMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommendation effectiveness metrics (self, or platform for admins)",
)
async def metrics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Signed-in users see their own funnel; admins see platform-wide metrics."""
    scope_user = user if user.role != UserRole.admin else None
    return recommendation_metrics(db, user=scope_user)


@router.patch(
    "/{record_id}/feedback",
    response_model=RecommendationRecordOut,
    status_code=status.HTTP_200_OK,
    summary="Record feedback on a recommendation (accepted/dismissed/completed/rated)",
)
async def feedback(
    record_id: str,
    payload: RecommendationFeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Feedback steers the next LLM batch and powers effectiveness metrics."""
    try:
        return record_feedback(
            db, record_id=record_id, user=user, action=payload.action, rating=payload.rating
        )
    except RecommendationServiceError:
        raise
    except Exception as exc:
        logger.error("Recommendation feedback failed: %s", exc)
        raise RecommendationServiceError(
            f"Feedback failed: {exc}",
            code="RECOMMENDATION_FEEDBACK_ERROR",
            status_code=500,
        )

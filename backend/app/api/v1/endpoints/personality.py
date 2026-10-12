"""Personality Intelligence API endpoints (Spec Module 6, TASK-009)."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.reading import Reading, ReadingType
from app.models.user import User
from app.services.personality import (
    PersonalityError,
    PersonalityNotReady,
    build_personality_profile,
    enrich_with_llm,
)
from app.services.reading.service import ReadingNotFound, get_any
from app.schemas.personality import (
    PersonalityEnrichRequest,
    PersonalityProfileRequest,
    PersonalityProfileResponse,
)
from app.utils.logging import logger

router = APIRouter(prefix="/personality", tags=["personality"])


def _resolve_palm_data(
    db: Session,
    payload: PersonalityProfileRequest,
    user: User | None,
) -> Dict[str, Any]:
    """Resolve palm_data from reading_id or direct payload."""
    if payload.reading_id:
        try:
            rid = uuid.UUID(payload.reading_id)
        except (ValueError, AttributeError):
            raise PersonalityError(
                f"Invalid reading ID: '{payload.reading_id}'",
                code="PERSONALITY_INVALID_ID",
            )
        reading = get_any(db, rid)
        if reading.type != ReadingType.palm:
            raise PersonalityError(
                f"Reading is not a palm reading (type={reading.type})",
                code="PERSONALITY_TYPE_MISMATCH",
            )
        return reading.result or {}

    if payload.palm_data:
        return payload.palm_data

    raise PersonalityError(
        "Either reading_id or palm_data must be provided.",
        code="PERSONALITY_MISSING_DATA",
    )


def _resolve_tarot_data(
    db: Session,
    payload: PersonalityProfileRequest,
    user: User | None,
) -> Optional[Dict[str, Any]]:
    """Resolve tarot_data from tarot_reading_id or direct payload."""
    if payload.tarot_reading_id:
        try:
            rid = uuid.UUID(payload.tarot_reading_id)
        except (ValueError, AttributeError):
            raise PersonalityError(
                f"Invalid tarot reading ID: '{payload.tarot_reading_id}'",
                code="PERSONALITY_INVALID_ID",
            )
        reading = get_any(db, rid)
        if reading.type != ReadingType.tarot:
            raise PersonalityError(
                f"Reading is not a tarot reading (type={reading.type})",
                code="PERSONALITY_TYPE_MISMATCH",
            )
        return reading.result or {}

    return payload.tarot_data


def _build_user_context(payload: PersonalityProfileRequest, user: User | None) -> Dict[str, Any]:
    """Build user context from profile + request payload."""
    ctx: Dict[str, Any] = {}
    if user and user.profile:
        profile = user.profile
        ctx["age_group"] = profile.age_group
        ctx["interests"] = [i.interest for i in profile.interests] if profile.interests else []
        ctx["goals"] = [g.text for g in profile.goals] if profile.goals else []
        ctx["tone"] = profile.tone
        ctx["default_deck"] = profile.default_deck

    if payload.user_context:
        ctx.update(payload.user_context)

    return ctx


@router.post(
    "/profile",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Build personality intelligence profile (FR-022..FR-026)",
)
async def build_profile(
    payload: PersonalityProfileRequest,
    question: Optional[str] = None,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Build a personality intelligence profile from palm and optional tarot data."""
    palm_data = _resolve_palm_data(db, payload, user)
    tarot_data = _resolve_tarot_data(db, payload, user)
    user_context = _build_user_context(payload, user)

    effective_question = payload.question or question
    if effective_question:
        user_context["question"] = effective_question

    try:
        profile = build_personality_profile(
            palm_data=palm_data,
            tarot_data=tarot_data,
            user_context=user_context,
        )
    except PersonalityNotReady as exc:
        raise PersonalityError(exc.message, code="PERSONALITY_NOT_READY", status_code=422)
    except PersonalityError:
        raise
    except Exception as exc:
        logger.error("Personality profile build failed: %s", exc)
        raise PersonalityError(
            f"Failed to build personality profile: {exc}",
            code="PERSONALITY_BUILD_ERROR",
            status_code=500,
        )

    return profile


@router.post(
    "/enrich",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Enrich personality profile via LLM (best-effort)",
)
async def enrich_profile(
    payload: PersonalityEnrichRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Enrich an existing personality profile with LLM-generated insights."""
    try:
        enriched = enrich_with_llm(payload.profile)
    except Exception as exc:
        logger.error("Personality profile enrichment failed: %s", exc)
        raise PersonalityError(
            f"Failed to enrich personality profile: {exc}",
            code="PERSONALITY_ENRICH_ERROR",
            status_code=500,
        )

    return enriched
"""Recommendation service workflows (Module 9, FR-034, TASK-012)."""
from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reading import ReadingType
from app.models.profile import Profile
from app.models.recommendation import (
    EventType,
    RecommendationEvent,
    RecommendationRecord,
    RecommendationStatus,
    RecommendationType,
)
from app.models.user import User
from app.services.personality.service import (
    analyze_tarot_arcana_profile,
    behavioral_insights,
    build_personality_profile,
    profile_strengths,
    profile_weaknesses,
)
from app.services.reading.service import ReadingNotFound, get_any
from app.services.recommendations.engine import (
    ELEMENTS,
    RECOMMENDATION_DISCLAIMER,
    REC_TYPES,
    RecommendationEngineError,
    get_engine,
)

logger = logging.getLogger(__name__)

# Feedback weights used for the fallback scorer's item-level signals.
_EVENT_WEIGHTS: Dict[str, float] = {
    EventType.shown.value: 0.0,
    EventType.accepted.value: 1.0,
    EventType.dismissed.value: -1.0,
    EventType.completed.value: 1.5,
    EventType.rated.value: 0.0,  # rated contributes via its rating, not the type
}

VALID_ACTIONS = ("accepted", "dismissed", "completed", "rated")

# How many recent feedback rows feed the LLM prompt / fallback signals.
FEEDBACK_WINDOW = 30


class RecommendationServiceError(Exception):
    """Service-layer failure mapped to the standard error envelope (§49.14)."""

    def __init__(
        self,
        message: str = "Recommendation operation failed",
        *,
        code: str = "RECOMMENDATION_ERROR",
        status_code: int = 400,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class RecommendationRecordNotFound(RecommendationServiceError):
    def __init__(self, message: str = "Recommendation not found"):
        super().__init__(message, code="RECOMMENDATION_NOT_FOUND", status_code=404)


# Feedback context (replaces the collaborative-filtering state cache)

def _event_weight(event_type: Any, rating: Optional[int]) -> float:
    weight = _EVENT_WEIGHTS.get(getattr(event_type, "value", str(event_type)), 0.0)
    if event_type == EventType.rated and rating is not None:
        weight = 1.0 if rating >= 4 else (-0.5 if rating <= 2 else 0.25)
    return weight


def _recent_feedback(
    db: Session,
    user: Optional[User],
) -> Tuple[str, Dict[str, float]]:
    """Summarise the user's recent feedback."""
    if user is None:
        return "", {}
    rows = db.execute(
        select(
            RecommendationRecord.item_id,
            RecommendationRecord.title,
            RecommendationRecord.rec_type,
            RecommendationEvent.event_type,
            RecommendationEvent.rating,
        )
        .join(RecommendationRecord, RecommendationEvent.record_id == RecommendationRecord.id)
        .where(RecommendationEvent.user_id == user.id)
        .order_by(RecommendationEvent.created_at.desc())
        .limit(FEEDBACK_WINDOW)
    ).all()

    if not rows:
        return "", {}

    lines: List[str] = []
    item_scores: Dict[str, float] = {}
    for item_id, title, rec_type, event_type, rating in rows:
        action = getattr(event_type, "value", str(event_type))
        if action == "shown":
            continue
        label = action
        if action == "rated" and rating is not None:
            label = f"rated {rating}/5"
        type_label = getattr(rec_type, "value", str(rec_type))
        lines.append(f"- {label}: '{title}' ({type_label})")
        weight = _event_weight(event_type, rating)
        if weight:
            item_scores[item_id] = item_scores.get(item_id, 0.0) + weight

    summary = "\n".join(lines[:12]) if lines else ""
    return summary, {k: v for k, v in item_scores.items() if v != 0.0}


# Context assembly

def _resolve_reading(db: Session, reading_id: Optional[str], expected: ReadingType, *, field: str) -> Optional[Dict[str, Any]]:
    if not reading_id:
        return None
    try:
        rid = uuid.UUID(reading_id)
    except (ValueError, AttributeError):
        raise RecommendationServiceError(
            f"Invalid reading ID: '{reading_id}'",
            code="RECOMMENDATION_INVALID_ID",
        )
    try:
        reading = get_any(db, rid)
    except ReadingNotFound:
        raise RecommendationServiceError(
            f"Reading not found: '{reading_id}'",
            code="RECOMMENDATION_READING_NOT_FOUND",
            status_code=404,
        )
    if reading.type != expected:
        raise RecommendationServiceError(
            f"Reading is not a {expected.value} reading (type={reading.type})",
            code="RECOMMENDATION_TYPE_MISMATCH",
        )
    return reading.result or {}


def _tarot_only_personality(tarot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Personality profile derived from a tarot reading alone (no palm data)."""
    tarot_profile = analyze_tarot_arcana_profile(tarot_data)
    counts = tarot_profile.get("elemental_balance", {})
    total = sum(counts.values()) or 1
    element_scores = {el: round(counts.get(el, 0) / total * 100, 1) for el in ELEMENTS}
    ranked = sorted(element_scores.items(), key=lambda kv: kv[1], reverse=True)
    dominant = ranked[0][0] if ranked and ranked[0][1] > 0 else "Air"
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None

    elemental = {
        "dominant_element": dominant,
        "secondary_element": secondary,
        "element_scores": element_scores,
        "palm_shape_element": None,
        "confidence": 0.6,
    }
    return {
        "elemental_profile": elemental,
        "tarot_profile": tarot_profile,
        "strengths": profile_strengths(elemental, tarot_profile),
        "weaknesses": profile_weaknesses(elemental, tarot_profile),
        "behavioral_insights": behavioral_insights(elemental, tarot_profile, {}),
        "personality_alignment_score": None,
    }


def build_feature_context(
    db: Session,
    *,
    user: Optional[User],
    palm_data: Optional[Dict[str, Any]],
    tarot_data: Optional[Dict[str, Any]],
    question: Optional[str],
    user_context_override: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Assemble the LLM prompt context from personality output + profile data."""
    profile_ctx: Dict[str, Any] = {}
    if user is not None:
        profile = db.execute(
            select(Profile).where(Profile.user_id == user.id)
        ).scalar_one_or_none()
        if profile is not None:
            profile_ctx["goals"] = [g.text for g in profile.goals] if profile.goals else []
            profile_ctx["interests"] = [i.interest for i in profile.interests] if profile.interests else []
            profile_ctx["age_group"] = profile.age_group

    if user_context_override:
        profile_ctx.update(user_context_override)

    sources: List[str] = []
    if palm_data:
        sources.append("palm")
    if tarot_data:
        sources.append("tarot")

    if palm_data:
        # TASK-009 personality profile supplies the symbolic features.
        personality = build_personality_profile(
            palm_data=palm_data,
            tarot_data=tarot_data,
            user_context=profile_ctx,
        )
    else:
        personality = _tarot_only_personality(tarot_data or {})

    elemental = personality.get("elemental_profile", {})
    tarot_profile = personality.get("tarot_profile", {})

    ctx = {
        "dominant_element": elemental.get("dominant_element", "Unknown"),
        "secondary_element": elemental.get("secondary_element"),
        "strengths": personality.get("strengths", []),
        "weaknesses": personality.get("weaknesses", []),
        "behaviors": personality.get("behavioral_insights", []),
        "goals": profile_ctx.get("goals", []),
        "interests": profile_ctx.get("interests", []),
        "question": question or "",
        "tarot_summary": tarot_profile.get("narrative_summary", ""),
        "sources": sources,
    }
    return ctx, personality


# Public service API

def generate_recommendations(
    db: Session,
    *,
    user: Optional[User],
    reading_id: Optional[str] = None,
    palm_data: Optional[Dict[str, Any]] = None,
    tarot_reading_id: Optional[str] = None,
    tarot_data: Optional[Dict[str, Any]] = None,
    question: Optional[str] = None,
    requested_types: Optional[Sequence[str]] = None,
    max_total: int = 8,
    per_type: int = 2,
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a personalised LLM recommendation batch (palm and/or tarot)."""
    resolved_palm = palm_data or _resolve_reading(db, reading_id, ReadingType.palm, field="reading_id")
    resolved_tarot = tarot_data or _resolve_reading(db, tarot_reading_id, ReadingType.tarot, field="tarot_reading_id")

    if not resolved_palm and not resolved_tarot:
        raise RecommendationServiceError(
            "At least one reading source is required: reading_id / palm_data "
            "(palm) or tarot_reading_id / tarot_data (tarot).",
            code="RECOMMENDATION_MISSING_DATA",
        )

    types: Optional[List[str]] = None
    if requested_types:
        types = [t for t in requested_types if t in REC_TYPES]
        if not types:
            raise RecommendationServiceError(
                f"types must be a non-empty subset of {list(REC_TYPES)}",
                code="RECOMMENDATION_INVALID_TYPE",
            )

    ctx, personality = build_feature_context(
        db,
        user=user,
        palm_data=resolved_palm,
        tarot_data=resolved_tarot,
        question=question,
        user_context_override=user_context,
    )
    feedback_summary, feedback_scores = _recent_feedback(db, user)

    engine = get_engine()
    try:
        items, meta = engine.generate(
            ctx,
            requested_types=types,
            max_total=max_total,
            per_type=per_type,
            feedback_summary=feedback_summary,
            feedback_scores=feedback_scores,
        )
    except RecommendationEngineError:
        raise
    except Exception as exc:
        logger.error("Recommendation generation failed: %s", exc)
        raise RecommendationServiceError(
            f"Recommendation generation failed: {exc}",
            code="RECOMMENDATION_GENERATION_ERROR",
            status_code=500,
        )
    if not items:
        raise RecommendationServiceError(
            "No recommendations could be generated for this reading context.",
            code="RECOMMENDATION_GENERATION_ERROR",
            status_code=500,
        )

    meta["personality_alignment_score"] = personality.get("personality_alignment_score")
    meta["personality_type"] = personality.get("tarot_profile", {}).get("personality_type")

    batch_id = uuid.uuid4()
    persisted: List[Dict[str, Any]] = []
    if user is not None:
        persisted = _persist_batch(
            db,
            user=user,
            batch_id=batch_id,
            palm_reading_id=reading_id if resolved_palm else None,
            tarot_reading_id=tarot_reading_id if resolved_tarot else None,
            items=items,
        )

    return {
        "batch_id": str(batch_id),
        "recommendations": items,
        "persisted": persisted,
        "count": len(items),
        "metadata": meta,
        "disclaimer": RECOMMENDATION_DISCLAIMER,
    }


def _persist_batch(
    db: Session,
    *,
    user: User,
    batch_id: uuid.UUID,
    palm_reading_id: Optional[str],
    tarot_reading_id: Optional[str],
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    def _to_uuid(raw: Optional[str]) -> Optional[uuid.UUID]:
        if not raw:
            return None
        try:
            return uuid.UUID(raw)
        except (ValueError, AttributeError):
            return None

    reading_uuid = _to_uuid(palm_reading_id) or _to_uuid(tarot_reading_id)

    persisted: List[Dict[str, Any]] = []
    records: List[RecommendationRecord] = []
    for item in items:
        # Explicitly set a UUID so it is available before db.commit() flushes.
        record_id = uuid.uuid4()
        record = RecommendationRecord(
            id=record_id,
            user_id=user.id,
            reading_id=reading_uuid,
            batch_id=batch_id,
            item_id=item["id"][:80],
            rec_type=RecommendationType(item["type"]),
            title=item["title"][:200],
            text=item["text"],
            rank=item.get("rank", 0),
            score=item["scores"]["blended"],
            priority=item.get("priority", "medium"),
            payload={
                "scores": item.get("scores", {}),
                "matched_reasons": item.get("matched_reasons", []),
                "tags": item.get("tags", []),
                "elements": item.get("elements", []),
                "effort": item.get("effort"),
                "horizon": item.get("horizon"),
                "reasoning": item.get("reasoning", []),
            },
        )
        record.events.append(RecommendationEvent(user_id=user.id, event_type=EventType.shown))
        db.add(record)
        records.append(record)
        persisted.append({"record_id": str(record_id), "item_id": item["id"]})
    db.commit()
    # Refresh all records to reflect DB-generated fields (created_at, etc.)
    for record in records:
        db.refresh(record)
    return persisted


def list_recommendations(
    db: Session,
    *,
    user: User,
    rec_type: Optional[str] = None,
    status: Optional[str] = None,
    batch_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List the signed-in user's persisted recommendations (newest first)."""
    stmt = select(RecommendationRecord).where(RecommendationRecord.user_id == user.id)
    count_stmt = select(func.count()).select_from(RecommendationRecord).where(
        RecommendationRecord.user_id == user.id
    )
    if rec_type:
        if rec_type not in REC_TYPES:
            raise RecommendationServiceError(
                f"Unknown recommendation type '{rec_type}'",
                code="RECOMMENDATION_INVALID_TYPE",
            )
        stmt = stmt.where(RecommendationRecord.rec_type == RecommendationType(rec_type))
        count_stmt = count_stmt.where(RecommendationRecord.rec_type == RecommendationType(rec_type))
    if status:
        try:
            status_enum = RecommendationStatus(status)
        except ValueError:
            raise RecommendationServiceError(
                f"Unknown status '{status}'",
                code="RECOMMENDATION_INVALID_STATUS",
            )
        stmt = stmt.where(RecommendationRecord.status == status_enum)
        count_stmt = count_stmt.where(RecommendationRecord.status == status_enum)
    if batch_id:
        try:
            batch_uuid = uuid.UUID(batch_id)
        except (ValueError, AttributeError):
            raise RecommendationServiceError(
                f"Invalid batch ID: '{batch_id}'",
                code="RECOMMENDATION_INVALID_ID",
            )
        stmt = stmt.where(RecommendationRecord.batch_id == batch_uuid)
        count_stmt = count_stmt.where(RecommendationRecord.batch_id == batch_uuid)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(RecommendationRecord.created_at.desc(), RecommendationRecord.rank.asc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 200))
    ).all()
    return {"items": [_record_out(r) for r in rows], "total": int(total), "limit": limit, "offset": offset}


def _record_out(record: RecommendationRecord) -> Dict[str, Any]:
    return {
        "id": str(record.id),
        "batch_id": str(record.batch_id),
        "reading_id": str(record.reading_id) if record.reading_id else None,
        "item_id": record.item_id,
        "rec_type": record.rec_type.value if isinstance(record.rec_type, RecommendationType) else str(record.rec_type),
        "title": record.title,
        "text": record.text,
        "rank": record.rank,
        "score": float(record.score),
        "priority": record.priority,
        "status": record.status.value if isinstance(record.status, RecommendationStatus) else str(record.status),
        "feedback_rating": record.feedback_rating,
        "payload": record.payload or {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def record_feedback(
    db: Session,
    *,
    record_id: str,
    user: User,
    action: str,
    rating: Optional[int] = None,
) -> Dict[str, Any]:
    """Record user feedback on a recommendation; feeds the next LLM prompt and metrics."""
    if action not in VALID_ACTIONS:
        raise RecommendationServiceError(
            f"action must be one of {list(VALID_ACTIONS)}",
            code="RECOMMENDATION_INVALID_ACTION",
        )
    if rating is not None and not 1 <= rating <= 5:
        raise RecommendationServiceError(
            "rating must be between 1 and 5",
            code="RECOMMENDATION_INVALID_RATING",
        )
    if action == "rated" and rating is None:
        raise RecommendationServiceError(
            "rating is required when action is 'rated'",
            code="RECOMMENDATION_INVALID_RATING",
        )

    try:
        rid = uuid.UUID(record_id)
    except (ValueError, AttributeError):
        raise RecommendationServiceError(
            f"Invalid recommendation ID: '{record_id}'",
            code="RECOMMENDATION_INVALID_ID",
        )
    record = db.scalars(
        select(RecommendationRecord).where(
            RecommendationRecord.id == rid, RecommendationRecord.user_id == user.id
        )
    ).first()
    if record is None:
        raise RecommendationRecordNotFound()

    status_map = {
        "accepted": RecommendationStatus.accepted,
        "dismissed": RecommendationStatus.dismissed,
        "completed": RecommendationStatus.completed,
    }
    if action in status_map:
        record.status = status_map[action]
    if rating is not None:
        record.feedback_rating = rating

    db.add(RecommendationEvent(record_id=record.id, user_id=user.id, event_type=EventType(action), rating=rating))
    db.commit()
    db.refresh(record)
    return _record_out(record)


def recommendation_metrics(db: Session, *, user: Optional[User] = None) -> Dict[str, Any]:
    """Recommendation effectiveness metrics (Spec §49.12: guidance relevance,."""
    base = select(RecommendationRecord)
    count_base = select(func.count()).select_from(RecommendationRecord)
    if user is not None:
        base = base.where(RecommendationRecord.user_id == user.id)
        count_base = count_base.where(RecommendationRecord.user_id == user.id)

    records = db.scalars(base).all()
    total = len(records)
    status_counts = {"new": 0, "accepted": 0, "dismissed": 0, "completed": 0}
    type_counts: Dict[str, int] = {t: 0 for t in REC_TYPES}
    ratings: List[int] = []
    for r in records:
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1
        type_counts[r.rec_type.value] = type_counts[r.rec_type.value] + 1
        if r.feedback_rating is not None:
            ratings.append(r.feedback_rating)

    engaged = status_counts["accepted"] + status_counts["completed"]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    return {
        "scope": "self" if user is not None else "platform",
        "total_recommendations": total,
        "status_counts": status_counts,
        "engagement_rate": round(engaged / total, 4) if total else 0.0,
        "dismissal_rate": round(status_counts["dismissed"] / total, 4) if total else 0.0,
        "completion_rate": round(status_counts["completed"] / total, 4) if total else 0.0,
        "average_feedback_rating": avg_rating,
        # Proxy metric: normalised mean feedback rating (0-100).
        "guidance_relevance_score": round(avg_rating / 5 * 100, 1) if avg_rating is not None else None,
        "type_counts": type_counts,
        "disclaimer": RECOMMENDATION_DISCLAIMER,
    }

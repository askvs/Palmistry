"""Reading service: create, list, review (FR-002..FR-004)."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User
from app.services.interpretation.engine import (
    InterpretationError,
    generate_palm_interpretation,
    generate_reading_synthesis,
    generate_tarot_interpretation,
)


class ReadingError(Exception):
    code = "READING_ERROR"
    status_code = 400

    def __init__(self, message: str = "Reading operation failed"):
        self.message = message
        super().__init__(message)


class ReadingNotFound(ReadingError):
    code = "READING_NOT_FOUND"
    status_code = 404


class PalmImageEmpty(ReadingError):
    code = "PALM_IMAGE_EMPTY"
    status_code = 400


class PalmImageTooLarge(ReadingError):
    code = "PALM_IMAGE_TOO_LARGE"
    status_code = 413


def _owned_or_404(db: Session, reading_id: uuid.UUID, user_id: uuid.UUID | None) -> Reading:
    stmt = select(Reading).where(Reading.id == reading_id)
    if user_id is not None:
        stmt = stmt.where(Reading.user_id == user_id)
    reading = db.scalars(stmt).first()
    if reading is None:
        raise ReadingNotFound("Reading not found")
    return reading


def create_tarot_reading(
    db: Session, user, *, spread: str, cards: list[str], question: str | None
) -> Reading:
    from app.services.tarot.interpretation import ENGINE_NAME, interpret_explicit_cards

    interpretation = interpret_explicit_cards(spread_ref=spread, selections=cards, question=question)
    result = {
        "spread": spread,
        "cards": cards,
        "question": question,
        "engine": ENGINE_NAME,
        "interpretation": interpretation,
    }
    # Make the spread metadata available at a predictable top-level key for reporting & aggregation
    # (reader_engagement and reports expect result['spread_name'] and result['card_count']).
    if isinstance(interpretation, dict) and interpretation.get("spread_name"):
        result["spread_name"] = interpretation.get("spread_name")
    else:
        # Fallback to provided spread ref when interpretation lacks a spread_name
        result["spread_name"] = str(spread)
    result["card_count"] = int(len(cards))

    reading = Reading(
        user_id=user.id,
        type=ReadingType.tarot,
        status=ReadingStatus.completed,
        title=interpretation["spread_name"],
        summary=interpretation["narrative"]["summary"],
        result=result,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    try:
        generate_tarot_interpretation(tarot_data=reading.result or {})
        current_result = dict(reading.result or {})
        current_result["ai_interpretation"] = generate_tarot_interpretation(tarot_data=reading.result or {})
        reading.result = current_result
        db.commit()
    except Exception:
        db.rollback()
    return reading


def create_palm_reading(
    db: Session, user, *, filename: str | None, data: bytes, hand: str | None = None
) -> Reading:
    """Store the uploaded palm image, run the CV pipeline, and persist a completed reading."""
    import pathlib
    from app.config import settings
    from app.services.palm_analysis.pipeline import analyze_palm_image

    # Run computer vision pipeline
    analysis = analyze_palm_image(image_bytes=data, preferred_hand=hand, enforce_palmar=True)

    shape_elem = analysis.get("palm_shape", {}).get("element", "Hand")
    conf_pct = int(analysis.get("metadata", {}).get("overall_confidence", 0.0) * 100)
    lines_count = len(analysis.get("lines", {}))

    reading = Reading(
        user_id=user.id,
        type=ReadingType.palm,
        status=ReadingStatus.completed,
        title=filename or f"Palm Analysis ({shape_elem} Hand)",
        summary=f"Detected {shape_elem} hand with {lines_count} lines analyzed ({conf_pct}% confidence).",
        result=analysis,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Persist uploaded image for reference
    palm_dir = pathlib.Path(settings.UPLOAD_DIR) / "palm"
    palm_dir.mkdir(parents=True, exist_ok=True)
    (palm_dir / f"{reading.id}.img").write_bytes(data)

    # Attach reading_id to analysis
    analysis["reading_id"] = str(reading.id)

    # Auto-generate AI interpretation
    try:
        palm_interpretation = generate_palm_interpretation(palm_data=reading.result or {})
        current_result = dict(reading.result or {})
        current_result["ai_interpretation"] = palm_interpretation
        reading.result = current_result
        db.commit()
    except Exception:
        db.rollback()

    return reading


def generate_palm_ai_interpretation(db: Session, reading_id: str, user: User | None) -> dict:
    """Generate AI interpretation for an existing palm reading."""
    reading = _get_reading(db, reading_id, user)
    if reading.type != ReadingType.palm:
        raise InterpretationError(
            f"Reading is not a palm reading (type={reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    result = generate_palm_interpretation(palm_data=reading.result or {})
    current_result = dict(reading.result or {})
    current_result["ai_interpretation"] = result
    reading.result = current_result
    db.commit()
    return result


def generate_tarot_ai_interpretation(db: Session, reading_id: str, user: User | None) -> dict:
    """Generate AI interpretation enhancement for an existing tarot reading."""
    reading = _get_reading(db, reading_id, user)
    if reading.type != ReadingType.tarot:
        raise InterpretationError(
            f"Reading is not a tarot reading (type={reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    result = generate_tarot_interpretation(tarot_data=reading.result or {})
    current_result = dict(reading.result or {})
    current_result["ai_interpretation"] = result
    reading.result = current_result
    db.commit()
    return result


def generate_ai_synthesis(db: Session, palm_id: str, tarot_id: str, user: User | None) -> dict:
    """Generate AI synthesis of a palm and tarot reading."""
    palm = _get_reading(db, palm_id, user)
    tarot = _get_reading(db, tarot_id, user)
    if palm.type != ReadingType.palm:
        raise InterpretationError(
            f"Palm reading is not a palm reading (type={palm.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    if tarot.type != ReadingType.tarot:
        raise InterpretationError(
            f"Tarot reading is not a tarot reading (type={tarot.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    result = generate_reading_synthesis(
        palm_data=palm.result or {}, tarot_data=tarot.result or {}
    )
    return result


def _get_reading(db: Session, reading_id: str, user: User | None) -> Reading:
    try:
        rid = uuid.UUID(reading_id)
    except (ValueError, AttributeError):
        raise InterpretationError(
            f"Invalid reading ID: '{reading_id}'", code="INTERPRETATION_INVALID_ID", status_code=400
        )
    return _owned_or_404(db, rid, user.id if user else None)


def delete_reading(db: Session, reading: Reading) -> None:
    db.delete(reading)
    db.commit()


def list_for_user(
    db: Session,
    user_id: uuid.UUID | None,
    *,
    type_filter: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Reading], int]:
    conditions = []
    if user_id is not None:
        conditions.append(Reading.user_id == user_id)
    if type_filter:
        conditions.append(Reading.type == type_filter)
    if status_filter:
        conditions.append(Reading.status == status_filter)
    base = select(Reading).where(*conditions)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(
        base.order_by(Reading.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), int(total)


def get_owned(db: Session, reading_id: uuid.UUID, user_id: uuid.UUID) -> Reading:
    return _owned_or_404(db, reading_id, user_id)


def get_any(db: Session, reading_id: uuid.UUID) -> Reading:
    return _owned_or_404(db, reading_id, None)


def update_reading(db: Session, reading: Reading, updates: dict) -> Reading:
    for field, value in updates.items():
        setattr(reading, field, value)
    db.commit()
    db.refresh(reading)
    return reading


def mark_reviewed(db: Session, reading: Reading, reviewer) -> Reading:
    reading.status = ReadingStatus.completed
    reading.reviewed_by = reviewer.id
    db.commit()
    db.refresh(reading)
    return reading


def analytics(db: Session, *, user_id: uuid.UUID | None = None) -> dict:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_q = select(func.count()).select_from(Reading)
    if user_id is not None:
        total_q = total_q.where(Reading.user_id == user_id)
    total = db.scalar(total_q) or 0

    status_q = select(Reading.status, func.count()).group_by(Reading.status)
    type_q = select(Reading.type, func.count()).group_by(Reading.type)
    day_q = (
        select(
            func.date_trunc("day", Reading.created_at).label("day"),
            func.count().label("count"),
        )
        .where(Reading.created_at >= week_ago)
        .group_by("day")
        .order_by("day")
    )
    if user_id is not None:
        status_q = status_q.where(Reading.user_id == user_id)
        type_q = type_q.where(Reading.user_id == user_id)
        day_q = day_q.where(Reading.user_id == user_id)

    by_status = [
        {"status": row[0].value, "count": row[1]} for row in db.execute(status_q).all()
    ]
    by_type = [{"type": row[0].value, "count": row[1]} for row in db.execute(type_q).all()]
    per_day = [
        {"day": row[0].strftime("%Y-%m-%d"), "count": row[1]}
        for row in db.execute(day_q).all()
    ]
    return {"total": int(total), "by_status": by_status, "by_type": by_type, "per_day": per_day}

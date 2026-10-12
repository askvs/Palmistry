"""Reading endpoints: user readings + reader workspace (FR-002..FR-004)."""
import uuid

from fastapi import APIRouter, Depends, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_tarot_reader
from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.reading import (
    ReadingAnalytics,
    ReadingListOut,
    ReadingOut,
    ReadingReviewUpdate,
    ReadingUserUpdate,
    TarotReadingCreate,
)
from app.services import reading as reading_service
from app.services.reading.service import PalmImageEmpty, PalmImageTooLarge, ReadingNotFound
from app.utils.logging import logger

router = APIRouter(dependencies=[Depends(get_current_user)])

reader_router = APIRouter(
    prefix="/reader",
    dependencies=[Depends(require_tarot_reader)],
)


@router.post("/readings/palm", response_model=ReadingOut, status_code=201)
async def create_palm_reading(
    image: UploadFile,
    hand: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """User uploads a palm image (FR-002); runs CV analysis and saves completed reading."""
    data = await image.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    if not data:
        raise PalmImageEmpty("Palm image file is empty")
    if len(data) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise PalmImageTooLarge(
            f"Palm image must be {settings.MAX_UPLOAD_SIZE_MB} MB or smaller"
        )
    reading = reading_service.create_palm_reading(
        db, user, filename=image.filename, data=data, hand=hand
    )
    try:
        from app.services.notifications import notify_new_reading

        notify_new_reading(
            reading_id=reading.id,
            owner_id=reading.user_id,
            reading_type=reading.type,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to send reading notifications: %s", exc)
    return ReadingOut.model_validate(reading)


@router.post("/readings/tarot", response_model=ReadingOut, status_code=201)
async def create_tarot_reading(
    payload: TarotReadingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reading = reading_service.create_tarot_reading(
        db, user, spread=payload.spread, cards=payload.cards, question=payload.question
    )
    try:
        from app.services.notifications import notify_new_reading

        notify_new_reading(
            reading_id=reading.id,
            owner_id=reading.user_id,
            reading_type=reading.type,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to send reading notifications: %s", exc)
    return ReadingOut.model_validate(reading)


@router.get("/readings", response_model=ReadingListOut)
async def list_my_readings(
    type_filter: str | None = Query(default=None, alias="type"),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = reading_service.list_for_user(
        db,
        user.id,
        type_filter=type_filter,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return ReadingListOut(
        items=[ReadingOut.model_validate(r) for r in items],
        total=total,
    )


@router.get("/readings/{reading_id}", response_model=ReadingOut)
async def get_reading(
    reading_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Owner, tarot readers (workspace access), and admins may view a reading."""
    reading = reading_service.get_any(db, reading_id)
    if reading.user_id != user.id and user.role.value not in ("tarot_reader", "admin"):
        raise ReadingNotFound("Reading not found")
    return ReadingOut.model_validate(reading)


@router.patch("/readings/{reading_id}", response_model=ReadingOut)
async def update_my_reading(
    reading_id: uuid.UUID,
    payload: ReadingUserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reading = reading_service.get_owned(db, reading_id, user.id)
    reading = reading_service.update_reading(db, reading, payload.model_dump(exclude_unset=True))
    return ReadingOut.model_validate(reading)


@router.delete("/readings/{reading_id}", status_code=204)
async def delete_my_reading(
    reading_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a reading owned by the current user."""
    reading = reading_service.get_owned(db, reading_id, user.id)
    reading_service.delete_reading(db, reading)
    return None


@router.get("/readings/analytics/me", response_model=ReadingAnalytics)
async def my_reading_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReadingAnalytics(**reading_service.reading_analytics(db, user_id=user.id))


# Tarot Reader workspace (FR-004)


@reader_router.get("/readings", response_model=ReadingListOut)
async def reader_list_readings(
    type_filter: str | None = Query(default=None, alias="type"),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = reading_service.list_for_user(
        db,
        None,
        type_filter=type_filter,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return ReadingListOut(
        items=[ReadingOut.model_validate(r) for r in items],
        total=total,
    )


@reader_router.get("/readings/analytics", response_model=ReadingAnalytics)
async def reader_reading_analytics(db: Session = Depends(get_db)):
    return ReadingAnalytics(**reading_service.reading_analytics(db))


@reader_router.post("/readings/{reading_id}/review", response_model=ReadingOut)
async def reader_review_reading(
    reading_id: uuid.UUID,
    payload: ReadingReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reading = reading_service.get_any(db, reading_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        reading = reading_service.update_reading(db, reading, updates)
    reading = reading_service.mark_reviewed(db, reading, user)
    return ReadingOut.model_validate(reading)

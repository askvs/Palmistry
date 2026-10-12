"""Tarot Reader workspace: custom spreads, reading reports, engagement."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_tarot_reader
from app.db.session import get_db
from app.models.reading import Reading
from app.models.user import User
from app.schemas.tarot import CustomSpreadCreate, CustomSpreadUpdate
from app.services.tarot import catalog as tarot_catalog
from app.services.tarot import custom_spreads

reader_router = APIRouter(
    prefix="/reader",
    tags=["reader"],
    dependencies=[Depends(require_tarot_reader)],
)


def _spread_out(spread) -> dict[str, Any]:
    return {
        "id": spread.id,
        "name": spread.name,
        "description": spread.description,
        "category": spread.category,
        "card_count": spread.card_count,
        "positions": spread.positions,
        "visibility": spread.visibility.value
        if hasattr(spread.visibility, "value")
        else spread.visibility,
        "is_owner": True,
        "owner_id": spread.owner_id,
        "created_at": spread.created_at,
        "source": "custom",
    }


# Custom spreads


@reader_router.get("/spreads")
def list_spreads(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Standard spreads (spec-fixed) plus the reader's own and shared spreads."""
    standard = tarot_catalog.get_tarot_spreads()
    custom = custom_spreads.list_for_reader(db, user)
    return {
        "standard": [
            {
                "id": spread["id"],
                "name": spread["name"],
                "description": spread.get("description"),
                "category": spread.get("category"),
                "card_count": spread["card_count"],
                "positions": spread.get("positions", []),
                "source": "standard",
            }
            for spread in standard
        ],
        "custom": [_spread_out(spread) for spread in custom],
    }


@reader_router.post("/spreads", status_code=status.HTTP_201_CREATED)
def create_spread(
    payload: CustomSpreadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    spread = custom_spreads.create(db, user, data=payload.model_dump(exclude_unset=True))
    return _spread_out(spread)


@reader_router.patch("/spreads/{spread_id}")
def update_spread(
    spread_id: uuid.UUID,
    payload: CustomSpreadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    spread = custom_spreads.update(
        db, user, spread_id, data=payload.model_dump(exclude_unset=True)
    )
    return _spread_out(spread)


@reader_router.delete("/spreads/{spread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spread(
    spread_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    custom_spreads.deactivate(db, user, spread_id)
    return None


# Reading reports


@reader_router.get("/reports")
def list_reading_reports(
    type: str | None = Query(default=None, max_length=20),
    status_filter: str | None = Query(default=None, alias="status", max_length=20),
    search: str | None = Query(default=None, max_length=120),
    owner_email: str | None = Query(default=None, max_length=200),
    reviewed: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Every platform reading with its owner — the reader's report worklist."""
    conditions = []
    if type:
        conditions.append(Reading.type == type)
    if status_filter:
        conditions.append(Reading.status == status_filter)
    if reviewed is True:
        conditions.append(Reading.reviewed_by.is_not(None))
    elif reviewed is False:
        conditions.append(Reading.reviewed_by.is_(None))
    if search:
        like = f"%{search.lower()}%"
        conditions.append(func.lower(Reading.title).like(like))
    if owner_email:
        like = f"%{owner_email.lower()}%"
        conditions.append(
            Reading.user_id.in_(
                select(User.id).where(func.lower(User.email).like(like))
            )
        )

    base = (
        select(Reading, User.email)
        .join(User, Reading.user_id == User.id, isouter=True)
        .where(*conditions)
    )
    total = db.scalar(select(func.count()).select_from(Reading).where(*conditions)) or 0
    rows = db.execute(
        base.order_by(Reading.created_at.desc()).limit(limit).offset(offset)
    ).all()

    items = []
    for reading, email in rows:
        result = reading.result or {}
        cards = result.get("cards") if isinstance(result.get("cards"), list) else []
        lines = result.get("lines") if isinstance(result.get("lines"), list) else []
        reading_type = reading.type.value if hasattr(reading.type, "value") else reading.type
        if reading_type == "tarot":
            card_count = len(cards)
        elif reading_type == "palm":
            card_count = len(lines) if isinstance(lines, list) else 0
        else:
            card_count = result.get("card_count") or len(cards)
        items.append(
            {
                "id": reading.id,
                "type": reading.type.value if hasattr(reading.type, "value") else reading.type,
                "status": reading.status.value
                if hasattr(reading.status, "value")
                else reading.status,
                "title": reading.title,
                "summary": reading.summary,
                "owner_email": email,
                "spread_name": result.get("spread_name") or (reading.title if reading_type == "tarot" else None),
                "card_count": int(card_count or 0),
                "ai_interpreted": bool(result.get("ai_interpretation") or result.get("aiInterpretation")),
                "reviewed": reading.reviewed_by is not None,
                "reviewed_by": reading.reviewed_by,
                "created_at": reading.created_at,
                "updated_at": reading.updated_at,
            }
        )
    return {"items": items, "total": int(total), "limit": limit, "offset": offset}


# Engagement insights


@reader_router.get("/engagement")
def reader_engagement(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """User-engagement insights for the reader workspace (FR-036)."""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days)

    total = db.scalar(select(func.count()).select_from(Reading)) or 0
    unique_querents = db.scalar(select(func.count(func.distinct(Reading.user_id)))) or 0
    per_querent = (
        select(Reading.user_id, func.count().label("count"))
        .group_by(Reading.user_id)
        .subquery()
    )
    repeat_querents = (
        db.scalar(select(func.count()).select_from(per_querent).where(per_querent.c.count >= 2))
        or 0
    )
    active_querents = (
        db.scalar(
            select(func.count(func.distinct(Reading.user_id))).where(
                Reading.created_at >= window_start
            )
        )
        or 0
    )
    first_time_querents = (
        db.scalar(
            select(func.count(func.distinct(Reading.user_id))).where(
                Reading.created_at >= window_start,
                Reading.user_id.in_(
                    select(Reading.user_id)
                    .group_by(Reading.user_id)
                    .having(func.count() == 1)
                ),
            )
        )
        or 0
    )
    in_window = (
        db.scalar(select(func.count()).select_from(Reading).where(Reading.created_at >= window_start))
        or 0
    )
    reviewed_total = (
        db.scalar(select(func.count()).select_from(Reading).where(Reading.reviewed_by.is_not(None)))
        or 0
    )

    top_rows = db.execute(
        select(Reading.user_id, User.email, User.full_name, func.count().label("count"), func.max(Reading.created_at))
        .join(User, Reading.user_id == User.id, isouter=True)
        .group_by(Reading.user_id, User.email, User.full_name)
        .order_by(func.count().desc())
        .limit(5)
    ).all()

    # Aggregate spread popularity in Python.
    spread_counts: dict[str, int] = {}
    for (result,) in db.execute(select(Reading.result).where(Reading.type == "tarot")).all():
        name = (result or {}).get("spread_name") if isinstance(result, dict) else None
        if name:
            spread_counts[str(name)] = spread_counts.get(str(name), 0) + 1
    spread_rows = sorted(spread_counts.items(), key=lambda item: item[1], reverse=True)[:6]

    return {
        "days": days,
        "total_readings": int(total),
        "unique_querents": int(unique_querents),
        "repeat_querents": int(repeat_querents),
        "repeat_rate": round(repeat_querents / unique_querents, 4) if unique_querents else 0.0,
        "active_querents_in_window": int(active_querents),
        "first_time_querents_in_window": int(first_time_querents),
        "returning_querents_in_window": int(max(active_querents - first_time_querents, 0)),
        "readings_per_querent": round(total / unique_querents, 2) if unique_querents else 0.0,
        "readings_in_window": int(in_window),
        "reviewed_total": int(reviewed_total),
        "review_rate": round(reviewed_total / total, 4) if total else 0.0,
        "top_querents": [
            {
                "user_id": row[0],
                "email": row[1],
                "full_name": row[2],
                "reading_count": int(row[3]),
                "last_reading_at": row[4],
            }
            for row in top_rows
        ],
        "popular_spreads": [
            {"spread": row[0] or "Unnamed spread", "count": int(row[1])} for row in spread_rows
        ],
    }

"""Tarot engine API endpoints (Spec FR-012..FR-016, TASK-007)."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_optional_current_user
from app.db.session import get_db
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User
from app.schemas.tarot import TarotDrawRequest, TarotInterpretRequest, TarotInterpretationOut
from app.services.tarot.catalog import get_tarot_spreads, shuffle_deck
from app.services.tarot.interpretation import (
    interpret_draw,
    interpret_explicit_cards,
    list_decks,
)

router = APIRouter(prefix="/tarot", tags=["tarot"])


@router.get("/shuffle", summary="Get a shuffled deck order (FR-013)")
def get_shuffled_deck(
    deck_id: str = "rider_waite_smith",
    seed: int | None = None,
) -> Dict[str, Any]:
    cards = shuffle_deck(deck_id=deck_id, seed=seed)
    return {
        "deck_id": deck_id,
        "total": len(cards),
        "cards": [
            {
                "id": c["id"],
                "name": c["name"],
                "arcana": c.get("arcana"),
                "suit": c.get("suit"),
                "number": c.get("number"),
                "image_path": c.get("image_path"),
            }
            for c in cards
        ],
    }



def _persist_reading(db: Session, user: User | None, result: dict[str, Any]) -> str | None:
    """Persist reading for authenticated users."""
    reading_id: str | None = None
    if user is not None:
        reading = Reading(
            user_id=user.id,
            type=ReadingType.tarot,
            status=ReadingStatus.completed,
            title=result["spread_name"],
            summary=result["narrative"]["summary"],
            result=result,
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        reading_id = str(reading.id)

    result["ai_interpretation"] = None
    return reading_id


def _custom_spread_override(db: Session, user: User | None, spread_id: str) -> dict | None:
    """Resolve a reader-authored spread, if `spread_id` names one."""
    if user is None:
        return None
    from app.services.tarot import custom_spreads

    spread = custom_spreads.resolve_for_use(db, user, str(spread_id))
    return custom_spreads.to_definition(spread) if spread is not None else None


@router.get("/decks", summary="List available tarot decks (FR-012)")
def get_decks() -> List[Dict[str, Any]]:
    return list_decks()


@router.get("/spreads", summary="List supported spreads (FR-015)")
def get_spreads() -> List[Dict[str, Any]]:
    return get_tarot_spreads()


@router.post(
    "/draw",
    response_model=TarotInterpretationOut,
    status_code=status.HTTP_200_OK,
    summary="Shuffle, draw, and interpret a spread (FR-013..FR-016)",
)
def draw_reading(
    payload: TarotDrawRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    override = _custom_spread_override(db, user, payload.spread_id)
    spread_id = override["id"] if override else payload.spread_id
    result = interpret_draw(
        spread_id=spread_id,
        deck_id=payload.deck_id,
        question=payload.question,
        allow_reversals=payload.allow_reversals,
        seed=payload.seed,
        spread_override=override,
    )
    result["reading_id"] = _persist_reading(db, user, result)
    return result


@router.post(
    "/interpret",
    response_model=TarotInterpretationOut,
    status_code=status.HTTP_200_OK,
    summary="Interpret an explicit card selection (FR-014, FR-016)",
)
def interpret_selection(
    payload: TarotInterpretRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    override = _custom_spread_override(db, user, payload.spread_id)
    spread_id = override["id"] if override else payload.spread_id
    result = interpret_explicit_cards(
        spread_ref=spread_id,
        selections=[card.model_dump() for card in payload.cards],
        question=payload.question,
        deck_id=payload.deck_id,
        spread_override=override,
    )
    result["reading_id"] = _persist_reading(db, user, result)
    return result

"""Pydantic schemas for the Tarot engine API (Spec FR-012..FR-016, TASK-007)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TarotDrawRequest(BaseModel):
    """Shuffle, draw, and interpret a spread (FR-013..FR-016)."""

    spread_id: str = Field(default="three_card", min_length=1, max_length=80)
    deck_id: str = Field(default="rider_waite_smith", min_length=1, max_length=80)
    question: str | None = Field(default=None, max_length=500)
    allow_reversals: bool = True
    seed: int | None = Field(
        default=None,
        ge=0,
        le=4_294_967_295,
        description="Deterministic seed for reproducible draws (test mode only, FR-013).",
    )


class TarotCardSelection(BaseModel):
    """One user-selected card with orientation (FR-014)."""

    card: str = Field(min_length=1, max_length=120)
    is_reversed: bool = False


class TarotInterpretRequest(BaseModel):
    """Interpret an explicit card sequence placed onto a spread (FR-014, FR-016)."""

    spread_id: str = Field(default="three_card", min_length=1, max_length=80)
    deck_id: str = Field(default="rider_waite_smith", min_length=1, max_length=80)
    cards: list[TarotCardSelection] = Field(min_length=1, max_length=10)
    question: str | None = Field(default=None, max_length=500)


class TarotCardInterpretation(BaseModel):
    position: int
    position_name: str
    position_description: str
    card_id: str
    card_name: str
    number: int
    arcana: str
    suit: str | None
    element: str | None
    is_reversed: bool
    orientation: str
    keywords: list[str]
    core_meaning: str
    position_context: str
    domain_guidance: list[dict[str, str]]
    fortune_telling: list[str]
    expanded_meanings: list[str]
    image_path: str | None
    relevance: float


class TarotMetadata(BaseModel):
    engine: str
    engine_version: str
    model_name: str
    model_version: str
    rule_based: bool
    timestamp: str
    overall_relevance: float


class TarotInterpretationOut(BaseModel):
    spread_id: str
    spread_name: str
    spread_category: str | None
    card_count: int
    deck_id: str
    question: str | None
    domain_focus: str | None
    cards: list[TarotCardInterpretation]
    analysis: dict[str, Any]
    narrative: dict[str, Any]
    guidance: list[str]
    disclaimer: str
    metadata: TarotMetadata
    seed: int | None
    reading_id: str | None = None


class SpreadPosition(BaseModel):
    """One card position in a reader-authored spread."""

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)


class CustomSpreadCreate(BaseModel):
    """Author a new spread (Tarot Reader: create spreads)."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default="custom", max_length=60)
    positions: list[SpreadPosition] = Field(min_length=1, max_length=10)
    visibility: str = Field(default="private", pattern="^(private|shared)$")


class CustomSpreadUpdate(BaseModel):
    """Partial update of a reader-authored spread."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=60)
    positions: list[SpreadPosition] | None = Field(default=None, min_length=1, max_length=10)
    visibility: str | None = Field(default=None, pattern="^(private|shared)$")

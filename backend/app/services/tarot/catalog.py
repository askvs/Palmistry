"""Tarot reference catalog service (Spec §49.6, FR-012..FR-022, TASK-005)."""
from __future__ import annotations

import json
import secrets
import random
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
TAROT_DATA_DIR = ROOT_DIR / "data" / "tarot"

_CACHED_DECKS: dict[str, dict[str, Any]] = {}
_CACHED_SPREADS: dict[str, Any] | None = None


def get_tarot_deck(deck_id: str = "rider_waite_smith") -> dict[str, Any]:
    """Load and return the tarot deck catalog by deck_id."""
    if deck_id in _CACHED_DECKS:
        return _CACHED_DECKS[deck_id]

    file_map = {
        "rider_waite_smith": TAROT_DATA_DIR / "rider_waite_deck.json",
    }
    deck_path = file_map.get(deck_id, TAROT_DATA_DIR / f"{deck_id}.json")

    if not deck_path.exists():
        raise FileNotFoundError(f"Tarot deck catalog not found: {deck_path}")

    with open(deck_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHED_DECKS[deck_id] = data
    return data


def get_card_by_id(card_id: str, deck_id: str = "rider_waite_smith") -> dict[str, Any] | None:
    """Retrieve a single card by its unique identifier."""
    deck = get_tarot_deck(deck_id)
    for card in deck.get("cards", []):
        if card["id"] == card_id:
            return card
    return None


def get_tarot_spreads() -> list[dict[str, Any]]:
    """Load and return all standardized tarot spread definitions."""
    global _CACHED_SPREADS
    if _CACHED_SPREADS is not None:
        return _CACHED_SPREADS["spreads"]

    spreads_path = TAROT_DATA_DIR / "spreads.json"
    if not spreads_path.exists():
        raise FileNotFoundError(f"Tarot spreads definition not found: {spreads_path}")

    with open(spreads_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHED_SPREADS = data
    return data["spreads"]


def get_spread_by_id(spread_id: str) -> dict[str, Any] | None:
    """Retrieve a spread definition by its unique identifier."""
    spreads = get_tarot_spreads()
    for spread in spreads:
        if spread["id"] == spread_id:
            return spread
    return None


def shuffle_deck(deck_id: str = "rider_waite_smith", seed: int | None = None) -> list[dict[str, Any]]:
    """Shuffle a tarot deck using Fisher-Yates algorithm."""
    deck = get_tarot_deck(deck_id)
    cards = list(deck.get("cards", []))

    if seed is not None:
        rng = random.Random(seed)
        # Standard Fisher-Yates shuffle
        for i in range(len(cards) - 1, 0, -1):
            j = rng.randint(0, i)
            cards[i], cards[j] = cards[j], cards[i]
    else:
        # Cryptographically secure Fisher-Yates shuffle
        for i in range(len(cards) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            cards[i], cards[j] = cards[j], cards[i]

    return cards


def draw_spread(
    spread_id: str,
    deck_id: str = "rider_waite_smith",
    seed: int | None = None,
    allow_reversals: bool = True,
    reversal_probability: float = 0.2,
    spread_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Draw cards for a specific spread and assign them to positions."""
    spread = spread_override or get_spread_by_id(spread_id)
    if not spread:
        raise ValueError(f"Unknown tarot spread: {spread_id}")

    shuffled = shuffle_deck(deck_id=deck_id, seed=seed)
    card_count = spread["card_count"]
    selected_cards = shuffled[:card_count]

    rng = random.Random(seed) if seed is not None else None

    drawn_positions = []
    for idx, pos_def in enumerate(spread["positions"]):
        card = selected_cards[idx]
        if allow_reversals:
            if rng is not None:
                is_reversed = rng.random() < reversal_probability
            else:
                is_reversed = (secrets.randbelow(1000) / 1000.0) < reversal_probability
        else:
            is_reversed = False

        drawn_positions.append({
            "position": pos_def["position"],
            "position_name": pos_def["name"],
            "position_description": pos_def["description"],
            "card_id": card["id"],
            "card_name": card["name"],
            "number": card["number"],
            "arcana": card["arcana"],
            "suit": card["suit"],
            "is_reversed": is_reversed,
            "meaning": card["reversed_meaning"] if is_reversed else card["upright_meaning"],
            "keywords": card["keywords_reversed"] if is_reversed else card["keywords_upright"],
            "image_path": card["image_path"],
        })

    return {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "card_count": card_count,
        "seed": seed,
        "cards": drawn_positions,
    }

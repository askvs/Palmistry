"""Seed and validate Tarot deck and spread reference catalogs (TASK-005, Spec §49.6).

Usage (from backend/):
    python -m scripts.seed_tarot
"""
import sys
from pathlib import Path

from app.services.tarot.catalog import get_tarot_deck, get_tarot_spreads


def seed_tarot() -> None:
    print("Seeding & validating Tarot reference datasets...")

    # Validate deck
    deck = get_tarot_deck("rider_waite_smith")
    cards = deck.get("cards", [])
    if len(cards) != 78:
        raise ValueError(f"Expected 78 cards, found {len(cards)}")

    majors = [c for c in cards if c["arcana"] == "major"]
    minors = [c for c in cards if c["arcana"] == "minor"]
    if len(majors) != 22:
        raise ValueError(f"Expected 22 Major Arcana, found {len(majors)}")
    if len(minors) != 56:
        raise ValueError(f"Expected 56 Minor Arcana, found {len(minors)}")

    # Verify each card has required attributes
    for c in cards:
        assert c["id"], f"Missing id in card: {c}"
        assert c["name"], f"Missing name in card: {c}"
        assert c["upright_meaning"], f"Missing upright_meaning in {c['id']}"
        assert c["reversed_meaning"], f"Missing reversed_meaning in {c['id']}"
        assert c["image_path"], f"Missing image_path in {c['id']}"

    print(f"  [OK] Deck valid: {deck['name']} (78 cards: 22 Major, 56 Minor)")

    # Validate spreads
    spreads = get_tarot_spreads()
    if len(spreads) < 6:
        raise ValueError(f"Expected at least 6 spreads, found {len(spreads)}")

    required_spread_ids = {"single_card", "three_card", "relationship", "career", "celtic_cross", "life_path"}
    found_ids = {s["id"] for s in spreads}
    missing = required_spread_ids - found_ids
    if missing:
        raise ValueError(f"Missing required spreads: {missing}")

    for s in spreads:
        assert len(s["positions"]) == s["card_count"], f"Mismatch in {s['id']}"
        print(f"  [OK] Spread valid: {s['name']} ({s['card_count']} cards)")

    print("Tarot reference datasets verified and ready.")


if __name__ == "__main__":
    try:
        seed_tarot()
    except Exception as exc:
        print(f"seed_tarot failed: {exc}", file=sys.stderr)
        sys.exit(1)

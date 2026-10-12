# Reference datasets: tarot deck, spreads, palm catalogs, and landmarks schema.
from pathlib import Path
import pytest

from app.services.tarot.catalog import (
    get_tarot_deck,
    get_card_by_id,
    get_tarot_spreads,
    get_spread_by_id,
    shuffle_deck,
    draw_spread,
)
from app.services.palm_analysis.catalog import (
    get_palm_lines_catalog,
    get_palm_line_by_id,
    get_palm_mounts_catalog,
    get_palm_mount_by_id,
    get_hand_landmarks_schema,
    get_landmark_by_index,
)

ROOT_DIR = Path(__file__).resolve().parents[2]


class TestTarotReferenceDatasets:
    def test_rider_waite_deck_completeness(self):
        deck = get_tarot_deck("rider_waite_smith")
        assert deck["deck_id"] == "rider_waite_smith"
        cards = deck["cards"]
        assert len(cards) == 78

        majors = [c for c in cards if c["arcana"] == "major"]
        assert len(majors) == 22

        minors = [c for c in cards if c["arcana"] == "minor"]
        assert len(minors) == 56

        # Check suit distribution (14 per suit)
        suits = ["wands", "cups", "swords", "pentacles"]
        for suit in suits:
            suit_cards = [c for c in minors if c["suit"] == suit]
            assert len(suit_cards) == 14, f"Suit {suit} expected 14 cards, got {len(suit_cards)}"

    def test_card_structure_and_assets(self):
        deck = get_tarot_deck("rider_waite_smith")
        public_cards_dir = ROOT_DIR / "frontend" / "public" / "cards"
        assert public_cards_dir.exists(), "frontend/public/cards directory must exist"

        for card in deck["cards"]:
            assert card["id"], "Card must have unique ID"
            assert card["name"], f"Card {card['id']} missing name"
            assert card["arcana"] in ("major", "minor")
            assert len(card["keywords"]) > 0
            assert len(card["upright_meaning"]) > 0
            assert len(card["reversed_meaning"]) > 0
            assert "domains" in card
            assert "love" in card["domains"]
            assert "career" in card["domains"]
            assert "spiritual" in card["domains"]

            # Image asset check
            img_file = card["image_file"]
            assert img_file, f"Card {card['id']} missing image_file"
            img_path = public_cards_dir / img_file
            assert img_path.exists(), f"Image asset missing on disk: {img_path}"
            assert img_path.stat().st_size > 1000, f"Image asset too small / corrupt: {img_path}"

    def test_get_card_by_id(self):
        fool = get_card_by_id("major-00-the-fool")
        assert fool is not None
        assert fool["name"] == "The Fool"
        assert fool["arcana"] == "major"
        assert fool["number"] == 0

        magician = get_card_by_id("major-01-the-magician")
        assert magician is not None
        assert magician["name"] == "The Magician"

        non_existent = get_card_by_id("invalid-card-id")
        assert non_existent is None

    def test_standard_spreads(self):
        spreads = get_tarot_spreads()
        assert len(spreads) >= 6

        expected_spreads = {
            "single_card": 1,
            "three_card": 3,
            "relationship": 5,
            "career": 5,
            "celtic_cross": 10,
            "life_path": 7,
        }

        for spread_id, expected_count in expected_spreads.items():
            spread = get_spread_by_id(spread_id)
            assert spread is not None, f"Spread {spread_id} missing from catalog"
            assert spread["card_count"] == expected_count
            assert len(spread["positions"]) == expected_count
            assert len(spread["interpretation_order"]) == expected_count

            # Verify positions have clear descriptions
            for pos in spread["positions"]:
                assert pos["position"] >= 1
                assert pos["name"]
                assert pos["description"]

    def test_fisher_yates_deterministic_seed_reproducibility(self):
        # FR-013 & Spec §49.6: Deterministic seed produces identical order
        cards1 = shuffle_deck(seed=42)
        cards2 = shuffle_deck(seed=42)
        cards3 = shuffle_deck(seed=999)

        order1 = [c["id"] for c in cards1]
        order2 = [c["id"] for c in cards2]
        order3 = [c["id"] for c in cards3]

        assert order1 == order2
        assert order1 != order3

    def test_draw_spread_execution(self):
        draw_result = draw_spread(spread_id="three_card", seed=123, allow_reversals=True)
        assert draw_result["spread_id"] == "three_card"
        assert len(draw_result["cards"]) == 3

        pos_names = [c["position_name"] for c in draw_result["cards"]]
        assert pos_names == ["The Past", "The Present", "The Future"]

        for drawn in draw_result["cards"]:
            assert drawn["card_id"]
            assert drawn["card_name"]
            assert isinstance(drawn["is_reversed"], bool)
            assert drawn["meaning"]
            assert drawn["image_path"]


class TestPalmistryReferenceDatasets:
    def test_palm_lines_completeness(self):
        lines = get_palm_lines_catalog()
        assert len(lines) == 5

        expected_lines = {"life_line", "head_line", "heart_line", "fate_line", "sun_line"}
        found_lines = {line["id"] for line in lines}
        assert found_lines == expected_lines

        for line in lines:
            assert line["name"]
            assert line["description"]
            assert len(line["significance"]) >= 3
            assert len(line["variations"]) >= 3
            assert 0.0 < line["confidence_threshold_default"] <= 1.0

    def test_sun_line_spec_compliance(self):
        # Spec §49.5 explicitly mandates Sun Line
        sun_line = get_palm_line_by_id("sun_line")
        assert sun_line is not None
        assert "Apollo" in sun_line["description"] or "Apollo" in sun_line["classical_name"]
        assert len(sun_line["variations"]) > 0

    def test_palm_mounts_completeness(self):
        mounts = get_palm_mounts_catalog()
        assert len(mounts) == 6

        expected_mounts = {
            "mount_of_jupiter",
            "mount_of_saturn",
            "mount_of_apollo",
            "mount_of_mercury",
            "mount_of_venus",
            "mount_of_moon",
        }
        found_mounts = {m["id"] for m in mounts}
        assert found_mounts == expected_mounts

        for mount in mounts:
            assert mount["name"]
            anchor = mount["anatomical_anchor"]
            assert 0 <= anchor["mediapipe_index"] <= 20
            assert anchor["landmark_name"]
            assert len(mount["core_attributes"]) >= 3
            assert "balanced" in mount["prominence_meanings"]

    def test_hand_landmarks_schema(self):
        schema = get_hand_landmarks_schema()
        assert schema["total_landmarks"] == 21
        landmarks = schema["landmarks"]
        assert len(landmarks) == 21

        indices = [lm["index"] for lm in landmarks]
        assert indices == list(range(21))

        wrist = get_landmark_by_index(0)
        assert wrist is not None
        assert wrist["name"] == "WRIST"

        # Check connectivity topology
        connections = schema["connections"]
        assert len(connections) >= 21
        for u, v in connections:
            assert 0 <= u <= 20
            assert 0 <= v <= 20

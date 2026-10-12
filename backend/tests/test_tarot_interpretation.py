# Tarot interpretation engine: draws, synthesis, question focus, and endpoints.
from datetime import datetime

import pytest

from app.middleware import rate_limit
from app.services.tarot.interpretation import (
    SAFETY_DISCLAIMER,
    TarotInterpretationError,
    interpret_draw,
    interpret_explicit_cards,
    list_decks,
)


def _clear_rate_limit():
    rate_limit._buckets.clear()


def _register(client, email="tarot@example.com", password="passw0rd-long", name="Tarot Tester"):
    _clear_rate_limit()
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp


def _auth_headers(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestInterpretationEngineUnit:
    def test_seeded_draw_is_deterministic(self):
        first = interpret_draw(spread_id="three_card", seed=42)
        second = interpret_draw(spread_id="three_card", seed=42)
        assert [c["card_id"] for c in first["cards"]] == [c["card_id"] for c in second["cards"]]
        assert first["narrative"]["opening"] == second["narrative"]["opening"]

    def test_draw_payload_structure(self):
        result = interpret_draw(spread_id="three_card", seed=7)
        assert result["spread_id"] == "three_card"
        assert result["card_count"] == 3
        assert result["deck_id"] == "rider_waite_smith"
        assert result["seed"] == 7
        assert len(result["cards"]) == 3

        expected_positions = {"The Past", "The Present", "The Future"}
        assert {c["position_name"] for c in result["cards"]} == expected_positions

        for card in result["cards"]:
            assert card["card_id"]
            assert card["card_name"]
            assert card["orientation"] in ("upright", "reversed")
            assert card["is_reversed"] == (card["orientation"] == "reversed")
            assert card["keywords"]
            assert card["core_meaning"]
            assert "inquiry" in card["position_context"]
            assert card["relevance"] > 0
            assert card["element"] in ("Fire", "Water", "Air", "Earth")

        assert set(result["analysis"]) == {
            "arcana_balance", "elemental_balance", "reversal_analysis", "numerology",
        }
        assert result["disclaimer"] == SAFETY_DISCLAIMER
        metadata = result["metadata"]
        assert metadata["engine"] == "TarotInterpretationEngine"
        assert metadata["rule_based"] is True
        assert 0.0 <= metadata["overall_relevance"] <= 1.0
        datetime.fromisoformat(metadata["timestamp"])

        assert result["narrative"]["opening"]
        assert len(result["narrative"]["body"]) == 3
        assert result["narrative"]["closing"]
        assert result["narrative"]["summary"]
        assert result["guidance"]

    def test_no_reversals_forces_upright(self):
        result = interpret_draw(spread_id="celtic_cross", seed=11, allow_reversals=False)
        assert all(c["orientation"] == "upright" for c in result["cards"])
        reversal = result["analysis"]["reversal_analysis"]
        assert reversal["reversed_count"] == 0
        assert reversal["reversal_ratio"] == 0.0

    def test_analysis_counts_are_consistent(self):
        result = interpret_draw(spread_id="celtic_cross", seed=5)
        analysis = result["analysis"]
        arcana = analysis["arcana_balance"]
        assert arcana["major_arcana"] + arcana["minor_arcana"] == 10

        elemental = analysis["elemental_balance"]
        assert sum(elemental["counts"].values()) == 10
        assert set(elemental["counts"]) == {"Fire", "Water", "Air", "Earth"}

        reversal = analysis["reversal_analysis"]
        assert reversal["reversed_count"] + reversal["upright_count"] == 10

        for card in result["cards"]:
            repeats = analysis["numerology"]["repeats"]
            for repeat in repeats:
                assert repeat["count"] >= 2
                assert repeat["cards"]

    def test_question_sets_domain_focus(self):
        love = interpret_draw(spread_id="three_card", seed=3, question="When will I find love?")
        assert love["domain_focus"] == "love"
        career = interpret_draw(spread_id="three_card", seed=3, question="Should I change my job?")
        assert career["domain_focus"] == "career"
        none = interpret_draw(spread_id="three_card", seed=3, question=None)
        assert none["domain_focus"] is None

    def test_explicit_cards_by_name(self):
        result = interpret_explicit_cards(
            spread_ref="Three Card",
            selections=["The Fool", "The Magician", "The Star"],
            question="What should I focus on?",
        )
        assert result["spread_id"] == "three_card"
        assert "Three Card" in result["spread_name"]
        assert [c["card_name"] for c in result["cards"]] == ["The Fool", "The Magician", "The Star"]

    def test_explicit_cards_with_reversal_dict(self):
        result = interpret_explicit_cards(
            spread_ref="three_card",
            selections=[
                {"card": "major-00-the-fool", "is_reversed": True},
                {"card": "major-01-the-magician", "is_reversed": False},
            ],
        )
        reversed_card = result["cards"][0]
        assert reversed_card["orientation"] == "reversed"
        assert "recklessness" in reversed_card["keywords"]
        upright_card = result["cards"][1]
        assert upright_card["orientation"] == "upright"
        assert "manifestation" in upright_card["keywords"]

    def test_synthetic_spread_fallback(self):
        result = interpret_explicit_cards(
            spread_ref="My Custom Layout",
            selections=["The Sun", "The Moon"],
        )
        assert result["spread_id"] == "mycustomlayout"
        assert result["spread_name"] == "My Custom Layout"
        assert [c["position_name"] for c in result["cards"]] == ["Card 1", "Card 2"]

    def test_unknown_card_raises(self):
        with pytest.raises(TarotInterpretationError) as exc:
            interpret_explicit_cards(spread_ref="three_card", selections=["Not A Real Card"])
        assert exc.value.code == "TAROT_UNKNOWN_CARD"
        assert exc.value.status_code == 400

    def test_unknown_spread_raises(self):
        with pytest.raises(TarotInterpretationError) as exc:
            interpret_draw(spread_id="horseshoe", seed=1)
        assert exc.value.code == "TAROT_UNKNOWN_SPREAD"

    def test_list_decks(self):
        decks = list_decks()
        assert len(decks) == 1
        assert decks[0]["deck_id"] == "rider_waite_smith"
        assert decks[0]["total_cards"] == 78
        assert decks[0]["is_default"] is True


class TestTarotEndpoints:
    def test_get_decks(self, client):
        resp = client.get("/api/v1/tarot/decks")
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["deck_id"] == "rider_waite_smith"

    def test_get_spreads(self, client):
        resp = client.get("/api/v1/tarot/spreads")
        assert resp.status_code == 200
        body = resp.json()
        assert {s["id"] for s in body} >= {
            "single_card", "three_card", "relationship", "career", "celtic_cross", "life_path",
        }

    def test_draw_guest_no_persistence(self, client):
        _clear_rate_limit()
        resp = client.post(
            "/api/v1/tarot/draw",
            json={"spread_id": "three_card", "seed": 21},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["reading_id"] is None
        assert body["metadata"]["engine"] == "TarotInterpretationEngine"

    def test_draw_authenticated_persists_reading(self, client):
        headers = _auth_headers(_register(client))
        resp = client.post(
            "/api/v1/tarot/draw",
            headers=headers,
            json={"spread_id": "three_card", "seed": 99, "question": "What awaits me?"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["reading_id"]
        assert body["seed"] == 99

        history = client.get("/api/v1/readings", headers=headers).json()
        assert history["total"] == 1
        assert history["items"][0]["id"] == body["reading_id"]
        assert history["items"][0]["type"] == "tarot"
        assert history["items"][0]["status"] == "completed"

    def test_draw_deterministic_across_sessions(self, client):
        first = client.post("/api/v1/tarot/draw", json={"spread_id": "three_card", "seed": 77}).json()
        second = client.post("/api/v1/tarot/draw", json={"spread_id": "three_card", "seed": 77}).json()
        assert [c["card_id"] for c in first["cards"]] == [c["card_id"] for c in second["cards"]]

    def test_draw_unknown_spread_envelope(self, client):
        _clear_rate_limit()
        resp = client.post("/api/v1/tarot/draw", json={"spread_id": "horseshoe"})
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "TAROT_UNKNOWN_SPREAD"
        assert "request_id" in body

    def test_interpret_explicit_selection(self, client):
        _clear_rate_limit()
        resp = client.post(
            "/api/v1/tarot/interpret",
            json={
                "spread_id": "three_card",
                "cards": [
                    {"card": "The Fool", "is_reversed": True},
                    {"card": "The Star"},
                ],
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["card_count"] == 2
        assert body["cards"][0]["orientation"] == "reversed"
        assert body["disclaimer"]

    def test_interpret_unknown_card_envelope(self, client):
        _clear_rate_limit()
        resp = client.post(
            "/api/v1/tarot/interpret",
            json={"spread_id": "three_card", "cards": [{"card": "Mystery Card"}]},
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "TAROT_UNKNOWN_CARD"

    def test_readings_tarot_endpoint_uses_engine(self, client):
        headers = _auth_headers(_register(client, email="legacy@example.com"))
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=headers,
            json={
                "spread": "Three Card",
                "cards": ["The Fool", "The Magician", "The Star"],
                "question": "What should I focus on?",
            },
        )
        assert resp.status_code == 201, resp.text
        reading = resp.json()
        assert reading["title"] == "Three Card Spread (Past, Present, Future)"
        assert reading["summary"]
        result = reading["result"]
        assert result["cards"] == ["The Fool", "The Magician", "The Star"]
        assert result["engine"] == "TarotInterpretationEngine"
        interpretation = result["interpretation"]
        assert interpretation["spread_id"] == "three_card"
        assert [c["card_name"] for c in interpretation["cards"]] == ["The Fool", "The Magician", "The Star"]
        assert interpretation["metadata"]["engine"] == "TarotInterpretationEngine"

    def test_tarot_shuffle_endpoint(self, client):
        resp = client.get("/api/v1/tarot/shuffle?deck_id=rider_waite_smith")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["deck_id"] == "rider_waite_smith"
        assert data["total"] == 78
        assert len(data["cards"]) == 78
        assert "id" in data["cards"][0]
        assert "name" in data["cards"][0]
        assert "image_path" in data["cards"][0]


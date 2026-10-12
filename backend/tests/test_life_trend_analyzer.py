# Life Trend Engine: signals, scoring, personalization, and endpoint integration.
import datetime as dt
import uuid

import pytest

from app.auth.password import hash_password
from app.auth.tokens import create_access_token
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User, UserRole
from app.services.trends import LifeTrendEngine, extract_reading_signals

PALM_RESULT = {
    "metadata": {"overall_confidence": 0.82},
    "palm_shape": {"element": "Fire", "aspect_ratio": 0.92},
    "finger_structure": {"digit_ratio_2d_4d": 0.94},
    "mounts": [
        {"name": "Mount of Venus", "element": "Water", "prominence": "prominent", "score": 0.7},
        {"name": "Mount of Jupiter", "element": "Fire", "prominence": "balanced", "score": 0.4},
    ],
    "lines": [
        {
            "line_id": "heart_line",
            "detected": True,
            "confidence": 0.9,
            "depth_clarity": 0.85,
            "continuity": 0.9,
            "variation_type": "long_and_deep",
        },
        {
            "line_id": "life_line",
            "detected": True,
            "confidence": 0.7,
            "depth_clarity": 0.6,
            "continuity": 0.65,
            "variation_type": "standard",
        },
        {
            "line_id": "fate_line",
            "detected": True,
            "confidence": 0.6,
            "depth_clarity": 0.55,
            "continuity": 0.5,
            "variation_type": "standard",
        },
    ],
}

TAROT_RESULT = {
    "domain_focus": "love",
    "metadata": {"overall_relevance": 0.75},
    "cards": [
        {"card_name": "The Lovers", "arcana": "Major Arcana", "element": "Water", "orientation": "upright"},
        {"card_name": "Two of Cups", "arcana": "Minor Arcana", "element": "Water", "orientation": "upright"},
        {"card_name": "Queen of Cups", "arcana": "Minor Arcana", "element": "Water", "orientation": "reversed"},
    ],
}


def _ts(days_ago: int) -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)


# Unit tests: signal extraction


class TestSignalExtraction:
    def test_palm_signals_extracted_from_real_feature_shape(self):
        signals = extract_reading_signals("palm", PALM_RESULT)
        assert 0.0 <= signals["palm.heart_line_strength"] <= 1.0
        assert signals["palm.heart_line_strength"] == pytest.approx((0.85 + 0.9 + 0.9) / 3)
        assert signals["palm.element_fire"] == 1.0
        assert signals["palm.mount_water"] == pytest.approx(1 / 2)
        assert signals["palm.overall_confidence"] == 0.82
        assert "palm.growth_markers" not in signals  # no broken/chained lines

    def test_tarot_signals_extracted(self):
        signals = extract_reading_signals("tarot", TAROT_RESULT)
        assert signals["tarot.major_ratio"] == pytest.approx(1 / 3)
        assert signals["tarot.reversal_ratio"] == pytest.approx(1 / 3)
        assert signals["tarot.element_water"] == pytest.approx(1.0)
        assert signals["tarot.domain_love"] == 1.0

    def test_missing_or_malformed_result_is_graceful(self):
        assert extract_reading_signals("palm", {}) == {}
        assert extract_reading_signals("palm", None) == {}
        assert extract_reading_signals("tarot", {"cards": "bad"}) == {}


# Unit tests: engine behavior


def _reading(kind, days_ago, result, now=None):
    if now is None:
        return {"type": kind, "result": result, "created_at": _ts(days_ago)}
    return {"type": kind, "result": result, "created_at": now - dt.timedelta(days=days_ago)}


class TestEngine:
    def test_empty_history_is_graceful_and_honest(self):
        out = LifeTrendEngine([]).compute()
        assert out["data_coverage"]["readings_analyzed"] == 0
        assert out["current_trends"] == []
        assert "no completed readings" in out["explanation"].lower()

    def test_deterministic(self):
        # Pin the clock: recency weights depend on `now`, so wall-clock drift
        # between the two engine instances could flip a rounding boundary.
        now = dt.datetime.now(dt.timezone.utc)
        readings = [
            _reading("palm", 10, PALM_RESULT, now),
            _reading("tarot", 5, TAROT_RESULT, now),
        ]
        a = LifeTrendEngine(readings, now=now).compute()
        b = LifeTrendEngine(readings, now=now).compute()
        assert a["current_trends"] == b["current_trends"]
        assert a["growth_potential"] == b["growth_potential"]

    def test_personalization_different_data_different_results(self):
        love_user = LifeTrendEngine(
            [_reading("palm", 10, PALM_RESULT), _reading("tarot", 5, TAROT_RESULT)]
        ).compute()
        # A user with only faint, undetected lines and no tarot cards.
        weak_palm = {
            "metadata": {"overall_confidence": 0.3},
            "palm_shape": {"element": "Earth"},
            "mounts": [],
            "lines": [
                {"line_id": "heart_line", "detected": True, "confidence": 0.2,
                 "depth_clarity": 0.1, "continuity": 0.1, "variation_type": "faint_or_shallow"},
            ],
        }
        other_user = LifeTrendEngine([_reading("palm", 10, weak_palm)]).compute()
        love_scores = {t["domain"]: t["score"] for t in love_user["current_trends"]}
        other_scores = {t["domain"]: t["score"] for t in other_user["current_trends"]}
        assert love_scores["relationships"] > other_scores["relationships"]
        assert love_user["life_path"] != other_user["life_path"]

    def test_goals_boost_aligned_domain(self):
        base = [_reading("tarot", 5, {"domain_focus": "career", "metadata": {}, "cards": [
            {"card_name": "Two of Wands", "arcana": "Minor Arcana", "element": "Fire",
             "orientation": "upright"}]})]
        without = LifeTrendEngine(list(base)).compute()
        with_goal = LifeTrendEngine(list(base), goals=["improve my health and sleep"]).compute()
        s_without = {t["domain"]: t["score"] for t in without["current_trends"]}
        s_with = {t["domain"]: t["score"] for t in with_goal["current_trends"]}
        assert s_with["vitality"] > s_without["vitality"]

    def test_direction_rising_when_recent_readings_stronger(self):
        weak = dict(PALM_RESULT)
        weak = {
            **PALM_RESULT,
            "lines": [
                {**PALM_RESULT["lines"][0], "depth_clarity": 0.2, "continuity": 0.2,
                 "confidence": 0.2, "variation_type": "faint_or_shallow"},
            ],
        }
        strong = PALM_RESULT
        readings = [
            _reading("palm", 200, weak),
            _reading("palm", 180, weak),
            _reading("palm", 5, strong),
            _reading("palm", 2, strong),
        ]
        out = LifeTrendEngine(readings).compute()
        rel = next(t for t in out["current_trends"] if t["domain"] == "relationships")
        assert rel["direction"] == "rising"
        assert rel["momentum"] > 0

    def test_every_trend_carries_signal_evidence(self):
        out = LifeTrendEngine(
            [_reading("palm", 10, PALM_RESULT), _reading("tarot", 5, TAROT_RESULT)]
        ).compute()
        assert out["current_trends"]
        for trend in out["current_trends"]:
            assert trend["signals"], f"no evidence listed for {trend['domain']}"
            assert 0.0 <= trend["strength"] <= 1.0
            assert 0.0 <= trend["confidence"] <= 0.9
        assert out["feature_vector"]["n_readings"] == 2
        assert out["data_coverage"]["completeness"] > 0

    def test_growth_potential_bounded_and_composite(self):
        out = LifeTrendEngine(
            [_reading("palm", 10, PALM_RESULT), _reading("tarot", 5, TAROT_RESULT)]
        ).compute()
        assert 0.0 <= out["growth_potential"] <= 1.0


# Endpoint integration


def _create_user(test_engine, email):
    from sqlalchemy.orm import Session

    with Session(test_engine) as session:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("TrendTest123!"),
            full_name="Trend Tester",
            role=UserRole.user,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


class TestLifeTrendsEndpoint:
    def test_requires_auth(self, client):
        res = client.get("/api/v1/life-trends")
        assert res.status_code in (401, 403)

    def test_returns_analysis_for_user_with_readings(self, client, test_engine):
        user = _create_user(test_engine, "trenduser@example.com")
        with test_engine.begin() as conn:
            pass
        from sqlalchemy.orm import Session

        with Session(test_engine) as session:
            session.add(
                Reading(
                    user_id=user.id,
                    type=ReadingType.palm,
                    status=ReadingStatus.completed,
                    title="Palm analysis",
                    summary="test",
                    result=PALM_RESULT,
                )
            )
            session.add(
                Reading(
                    user_id=user.id,
                    type=ReadingType.tarot,
                    status=ReadingStatus.completed,
                    title="Love spread",
                    summary="test",
                    result=TAROT_RESULT,
                )
            )
            session.commit()

        headers = {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}
        res = client.get("/api/v1/life-trends", headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["method"] == "feature_based_trend_scoring"
        assert body["data_coverage"]["readings_analyzed"] == 2
        assert body["current_trends"]
        rel = next(t for t in body["current_trends"] if t["domain"] == "relationships")
        assert rel["signals"]
        assert 0.0 <= body["growth_potential"] <= 1.0
        assert "disclaimer" in body
        assert len(body["history"]) == 2

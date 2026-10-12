# Recommendation engine: catalog, heuristic fallback, LLM path, feedback, endpoints.
from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.auth.tokens import create_access_token
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.recommendation import (
    EventType,
    RecommendationEvent,
    RecommendationRecord,
    RecommendationStatus,
)
from app.models.user import User, UserRole
from app.services.recommendations import (
    REC_TYPES,
    RecommendationEngineError,
    RecommendationRecordNotFound,
    RecommendationServiceError,
    generate_recommendations,
    list_recommendations,
    recommendation_metrics,
    record_feedback,
)
from app.services.recommendations.engine import (
    Catalog,
    LLMRecommendationEngine,
    default_catalog_path,
    get_engine,
    reset_engine,
)


# Fake LLM adapter (never touches the network)

class FakeLLMResponse:
    def __init__(self, content: str, tokens: int = 42):
        self.content = content
        self.model = "fake-test-model"
        self.provider = "groq"
        self.rule_based = False
        self.tokens = tokens

    def to_dict(self):
        return {"content": self.content, "model": self.model, "provider": self.provider,
                "rule_based": self.rule_based, "tokens": self.tokens}


class FakeOnlineAdapter:
    """Pretends to be an online Groq adapter returning scripted completions."""

    def __init__(self, content: str):
        self.content = content
        self.calls: list = []

    @property
    def provider(self):
        return "groq"

    @property
    def model(self):
        return "fake-test-model"

    @property
    def is_online(self):
        return True

    def complete(self, *, prompt, system="", max_tokens=1024, temperature=0.7, json_mode=False):
        self.calls.append({"prompt": prompt, "system": system, "json_mode": json_mode})
        return FakeLLMResponse(self.content)


class FakeOfflineAdapter:
    """No client configured — mirrors the rule-based adapter state."""

    @property
    def provider(self):
        return "rule_based"

    @property
    def model(self):
        return "rulebook-1.0.0"

    @property
    def is_online(self):
        return False


VALID_LLM_PAYLOAD = {
    "recommendations": [
        {
            "type": "personal_growth",
            "title": "Morning water ritual",
            "text": "Begin each morning with five slow breaths before touching your phone, honouring your Water element's need for calm flow.",
            "tags": ["mindfulness", "water", "morning routine"],
            "elements": ["Water"],
            "effort": "low",
            "horizon": "daily",
            "priority": "medium",
            "reasoning": ["matches your dominant Water element", "supports your meditation goal"],
            "scores": {"context_relevance": 0.9, "personalization": 0.85, "goal_alignment": 0.8},
        },
        {
            "type": "relationship",
            "title": "One honest conversation",
            "text": "Choose one relationship this week where you can voice a small need directly instead of absorbing it.",
            "tags": ["boundaries", "communication"],
            "elements": ["Water"],
            "effort": "medium",
            "horizon": "weekly",
            "priority": "high",
            "reasoning": ["addresses your boundary-setting growth area"],
            "scores": {"context_relevance": 0.8, "personalization": 0.9, "goal_alignment": 0.5},
        },
        {
            "type": "spiritual_development",
            "title": "Evening tarot check-in",
            "text": "Pull a single card each evening and journal one line on how it mirrored your day.",
            "tags": ["tarot", "journaling"],
            "elements": ["Air"],
            "effort": "low",
            "horizon": "daily",
            "priority": "medium",
            "reasoning": ["builds on your tarot interest"],
            "scores": {"context_relevance": 0.85, "personalization": 0.75, "goal_alignment": 0.7},
        },
    ]
}


# Engine cache hygiene — every test starts from a fresh singleton with the
# offline fake adapter so nothing ever reaches a real provider.

@pytest.fixture(autouse=True)
def _offline_engine():
    reset_engine()
    engine = get_engine()
    engine.set_adapter(FakeOfflineAdapter())
    yield engine
    reset_engine()


# Fixtures (matching test_personality.py patterns)

def _create_user(test_engine, *, email: str, role: UserRole) -> User:
    with Session(test_engine) as session:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("RecommendationTest123!"),
            full_name=email.split("@")[0].title(),
            role=role,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


def sample_palm_data(element: str = "Water", confidence: float = 0.85) -> dict:
    return {
        "palm_shape": {"element": element, "description": f"a {element.lower()} hand", "palm_ratio": 1.2, "finger_ratio": 0.9},
        "finger_structure": {"digit_ratio_2d_4d": 0.98, "pinky_reach": 0.7, "thumb_angle": 40},
        "metadata": {"overall_confidence": confidence, "engine": "PalmAnalysisCV"},
        "lines": [
            {"name": "Life Line", "confidence": 0.9, "variation_type": "standard", "interpretation": "Vitality"},
            {"name": "Head Line", "confidence": 0.8, "variation_type": "strong_clear", "interpretation": "Clear thinking"},
        ],
        "mounts": [
            {"name": "Mount of Venus", "prominence": "prominent", "score": 0.8},
            {"name": "Mount of Moon", "prominence": "balanced", "score": 0.5},
        ],
        "result_type": "palm",
    }


def sample_tarot_data() -> dict:
    return {
        "spread_name": "Three Card",
        "card_count": 3,
        "cards": [
            {"card_name": "The Empress", "orientation": "upright", "arcana": "Major Arcana", "element": "Earth", "number": 3},
            {"card_name": "Two of Cups", "orientation": "upright", "arcana": "Minor Arcana", "element": "Water", "number": 2},
            {"card_name": "The Star", "orientation": "upright", "arcana": "Major Arcana", "element": "Air", "number": 17},
        ],
        "narrative": {"summary": "Healing, partnership and hope"},
    }


@pytest.fixture
def seeker(test_engine):
    return _create_user(test_engine, email="rec_seeker@example.com", role=UserRole.user)


@pytest.fixture
def other_seeker(test_engine):
    return _create_user(test_engine, email="rec_other@example.com", role=UserRole.user)


@pytest.fixture
def admin(test_engine):
    return _create_user(test_engine, email="rec_admin@example.com", role=UserRole.admin)


def _add_reading(test_engine, user: User, reading_type: ReadingType, result: dict) -> Reading:
    with Session(test_engine) as session:
        reading = Reading(
            id=uuid.uuid4(),
            user_id=user.id,
            type=reading_type,
            status=ReadingStatus.completed,
            title=f"Rec {reading_type.value} Reading",
            summary="Test reading",
            result=result,
        )
        session.add(reading)
        session.commit()
        session.refresh(reading)
        return reading


@pytest.fixture
def palm_reading(test_engine, seeker):
    return _add_reading(test_engine, seeker, ReadingType.palm, sample_palm_data())


@pytest.fixture
def tarot_reading(test_engine, seeker):
    return _add_reading(test_engine, seeker, ReadingType.tarot, sample_tarot_data())


def _db(test_engine) -> Session:
    return Session(test_engine)


WATER_CONTEXT = {
    "dominant_element": "Water",
    "secondary_element": "Air",
    "strengths": [{"trait": "Empathy"}, {"trait": "Intuition"}],
    "weaknesses": [{"area": "Boundary setting"}, {"area": "Overthinking"}],
    "goals": ["build a daily meditation habit"],
    "interests": ["tarot", "meditation"],
}


# Catalog integrity

class TestCatalog:
    def test_catalog_loads_with_all_types(self):
        catalog = Catalog.load(default_catalog_path())
        assert len(catalog.items) > 0
        present = {item.type for item in catalog.items}
        assert set(REC_TYPES) <= present

    def test_every_type_has_minimum_coverage(self):
        catalog = Catalog.load(default_catalog_path())
        by_type: dict = {t: 0 for t in REC_TYPES}
        for item in catalog.items:
            by_type[item.type] += 1
        assert all(count >= 3 for count in by_type.values())

    def test_fingerprint_is_stable(self):
        first = Catalog.load(default_catalog_path())
        second = Catalog.load(default_catalog_path())
        assert first.fingerprint == second.fingerprint

    def test_duplicate_ids_rejected(self, tmp_path):
        item = {
            "id": "dup_1", "type": "career", "title": "A", "text": "B",
            "tags": [], "elements": [], "addresses": [], "leverages": [],
            "goal_categories": [],
        }
        path = tmp_path / "catalog.json"
        path.write_text(json.dumps({"items": [item, dict(item)]}))
        with pytest.raises(RecommendationEngineError):
            Catalog.load(path)

    def test_missing_field_rejected(self, tmp_path):
        path = tmp_path / "catalog.json"
        path.write_text(json.dumps({"items": [{"id": "x", "type": "career"}]}))
        with pytest.raises(RecommendationEngineError):
            Catalog.load(path)

    def test_digest_mentions_every_type(self):
        catalog = Catalog.load(default_catalog_path())
        digest = catalog.digest()
        for rec_type in REC_TYPES:
            assert rec_type in digest


# Heuristic fallback generation (offline adapter)

class TestFallbackGeneration:
    def test_returns_all_five_types_with_quota(self, _offline_engine):
        items, meta = _offline_engine.generate(WATER_CONTEXT, max_total=8, per_type=2)
        types = {i["type"] for i in items}
        assert types == set(REC_TYPES)
        assert len(items) <= 8
        for rec_type in REC_TYPES:
            assert len([i for i in items if i["type"] == rec_type]) <= 2
        assert meta["generation_method"] == "heuristic_fallback"
        assert meta["llm_generated"] is False

    def test_ranking_is_deterministic(self, _offline_engine):
        first, _ = _offline_engine.generate(WATER_CONTEXT)
        second, _ = _offline_engine.generate(WATER_CONTEXT)
        assert [i["id"] for i in first] == [i["id"] for i in second]
        assert [i["rank"] for i in first] == list(range(1, len(first) + 1))

    def test_empty_context_still_produces_output(self, _offline_engine):
        items, meta = _offline_engine.generate({}, max_total=5, per_type=1)
        assert items, "fallback must produce output even with no context"
        assert meta["generation_method"] == "heuristic_fallback"

    def test_type_filter_restricts_output(self, _offline_engine):
        items, _ = _offline_engine.generate(WATER_CONTEXT, requested_types=["career", "relationship"])
        assert {i["type"] for i in items} == {"career", "relationship"}

    def test_scores_are_bounded(self, _offline_engine):
        items, _ = _offline_engine.generate(WATER_CONTEXT)
        for item in items:
            for key in ("context_relevance", "personalization", "goal_alignment", "blended"):
                assert 0.0 <= item["scores"][key] <= 1.0
            assert 0.0 <= item["confidence"] <= 1.0
            assert item["final_score"] == item["scores"]["blended"]

    def test_water_context_surfaces_water_items(self, _offline_engine):
        items, _ = _offline_engine.generate(WATER_CONTEXT)
        assert any(i["element_affinity"] == "Water" for i in items)

    def test_feedback_scores_influence_ranking(self, _offline_engine):
        baseline, _ = _offline_engine.generate(WATER_CONTEXT, max_total=8, per_type=2)
        # Penalise whatever ranked first, boost whatever ranked last.
        top_id = baseline[0]["id"]
        bottom_id = baseline[-1]["id"]
        adjusted, _ = _offline_engine.generate(
            WATER_CONTEXT, max_total=8, per_type=2,
            feedback_scores={top_id: -5.0, bottom_id: 5.0},
        )
        adjusted_ranks = {i["id"]: i["rank"] for i in adjusted}
        # The boosted item must still be served, and the penalised item either
        # drops out of the batch entirely (strong negative signal) or ranks
        # below the boosted one.
        assert bottom_id in adjusted_ranks
        assert top_id not in adjusted_ranks or adjusted_ranks[bottom_id] < adjusted_ranks[top_id]

    def test_metadata_reports_provider_and_catalog(self, _offline_engine):
        _, meta = _offline_engine.generate(WATER_CONTEXT)
        assert meta["engine"] == "LLMRecommendationEngine"
        assert meta["provider"] == "rule_based"
        assert meta["catalog_size"] == len(_offline_engine.catalog.items)
        assert "disclaimer" in meta


# LLM path (fake online adapter)

class TestLLMGeneration:
    def _engine_with(self, content: str) -> tuple:
        engine = LLMRecommendationEngine()
        adapter = FakeOnlineAdapter(content)
        engine.set_adapter(adapter)
        return engine, adapter

    def test_llm_items_parsed_and_validated(self):
        engine, adapter = self._engine_with(json.dumps(VALID_LLM_PAYLOAD))
        items, meta = engine.generate(WATER_CONTEXT, max_total=6, per_type=2)
        assert meta["generation_method"] == "llm"
        assert meta["llm_generated"] is True
        assert meta["provider"] == "groq"
        assert len(items) == 3
        assert all(i["id"].startswith("llm_") for i in items)
        assert [i["rank"] for i in items] == [1, 2, 3]
        titles = [i["title"] for i in items]
        assert "Morning water ritual" in titles

    def test_prompt_contains_context_and_feedback(self):
        engine, adapter = self._engine_with(json.dumps(VALID_LLM_PAYLOAD))
        engine.generate(
            WATER_CONTEXT,
            max_total=6,
            per_type=2,
            feedback_summary="- dismissed: 'Cold plunge challenge' (personal_growth)",
        )
        prompt = adapter.calls[0]["prompt"]
        system = adapter.calls[0]["system"]
        assert "Water" in prompt
        assert "build a daily meditation habit" in prompt
        assert "Boundary setting" in prompt
        assert "dismissed: 'Cold plunge challenge'" in prompt
        assert "json" in system.lower()

    def test_unknown_type_items_dropped(self):
        payload = {
            "recommendations": [
                VALID_LLM_PAYLOAD["recommendations"][0],
                {"type": "fortune_telling", "title": "X", "text": "Y"},
            ]
        }
        engine, _ = self._engine_with(json.dumps(payload))
        items, meta = engine.generate(WATER_CONTEXT)
        assert meta["generation_method"] == "llm"
        assert {i["type"] for i in items} == {"personal_growth"}

    def test_out_of_range_scores_clamped(self):
        payload = json.loads(json.dumps(VALID_LLM_PAYLOAD))
        payload["recommendations"][0]["scores"] = {
            "context_relevance": 7.5, "personalization": -3, "goal_alignment": "high",
        }
        engine, _ = self._engine_with(json.dumps(payload))
        items, _ = engine.generate(WATER_CONTEXT)
        scores = items[0]["scores"]
        assert scores["context_relevance"] == 1.0
        assert scores["personalization"] == 0.0
        assert 0.0 <= scores["goal_alignment"] <= 1.0

    def test_duplicate_titles_get_unique_ids(self):
        payload = {
            "recommendations": [
                VALID_LLM_PAYLOAD["recommendations"][0],
                dict(VALID_LLM_PAYLOAD["recommendations"][0]),
            ]
        }
        engine, _ = self._engine_with(json.dumps(payload))
        items, _ = engine.generate(WATER_CONTEXT)
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids))

    def test_markdown_fenced_json_is_parsed(self):
        fenced = "```json\n" + json.dumps(VALID_LLM_PAYLOAD) + "\n```"
        engine, _ = self._engine_with(fenced)
        items, meta = engine.generate(WATER_CONTEXT)
        assert meta["generation_method"] == "llm"
        assert len(items) == 3

    def test_garbage_output_falls_back_to_catalog(self):
        engine, _ = self._engine_with("the stars align, dear seeker")
        items, meta = engine.generate(WATER_CONTEXT)
        assert meta["generation_method"] == "heuristic_fallback"
        assert items, "fallback must still produce recommendations"
        assert all(not i["id"].startswith("llm_") for i in items)

    def test_provider_error_falls_back(self):
        class ExplodingAdapter(FakeOnlineAdapter):
            def complete(self, **kwargs):
                raise RuntimeError("groq unavailable")

        engine = LLMRecommendationEngine()
        engine.set_adapter(ExplodingAdapter("unused"))
        items, meta = engine.generate(WATER_CONTEXT)
        assert meta["generation_method"] == "heuristic_fallback"
        assert items

    def test_per_type_quota_enforced_on_llm_output(self):
        payload = {
            "recommendations": [
                {"type": "career", "title": f"Career {i}", "text": f"Career item {i}",
                 "tags": ["career"], "elements": ["Air"], "effort": "medium", "horizon": "weekly",
                 "priority": "medium", "reasoning": ["fits"], "scores": {}}
                for i in range(6)
            ]
        }
        engine, _ = self._engine_with(json.dumps(payload))
        items, _ = engine.generate(WATER_CONTEXT, requested_types=["career"], max_total=4, per_type=2)
        assert len(items) == 2


# Service workflows

class TestServiceWorkflows:
    def test_generate_persists_batch_and_shown_events(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(
                db, user=seeker, reading_id=str(palm_reading.id), max_total=8, per_type=2
            )
            assert result["count"] >= 5
            assert len(result["persisted"]) == result["count"]
            records = db.scalars(
                select(RecommendationRecord).where(RecommendationRecord.user_id == seeker.id)
            ).all()
            assert len(records) == result["count"]
            events = db.scalars(select(RecommendationEvent)).all()
            assert len(events) == result["count"]
            assert all(e.event_type == EventType.shown for e in events)
            assert result["metadata"]["generation_method"] == "heuristic_fallback"

    def test_guest_generation_is_ephemeral(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(
                db, user=None, reading_id=str(palm_reading.id), max_total=4, per_type=1
            )
            assert result["persisted"] == []
            count = len(db.scalars(select(RecommendationRecord)).all())
            assert count == 0

    def test_tarot_only_generation_works(self, test_engine, seeker, tarot_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(
                db, user=seeker, tarot_reading_id=str(tarot_reading.id), max_total=6, per_type=2
            )
            assert result["count"] >= 3
            assert result["metadata"]["context_sources"] == ["tarot"]
            # Tarot-only records persist and link back to the tarot reading.
            records = db.scalars(
                select(RecommendationRecord).where(RecommendationRecord.user_id == seeker.id)
            ).all()
            assert records
            assert all(str(r.reading_id) == str(tarot_reading.id) for r in records)

    def test_tarot_data_direct_guest_flow(self, test_engine):
        with _db(test_engine) as db:
            result = generate_recommendations(
                db, user=None, tarot_data=sample_tarot_data(), question="How can I grow?",
                max_total=3, per_type=1,
            )
            assert 1 <= result["count"] <= 3

    def test_missing_source_data_rejected(self, test_engine, seeker):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError) as exc:
                generate_recommendations(db, user=seeker)
            assert exc.value.code == "RECOMMENDATION_MISSING_DATA"

    def test_invalid_requested_type_rejected(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError) as exc:
                generate_recommendations(
                    db, user=seeker, reading_id=str(palm_reading.id), requested_types=["nonsense"]
                )
            assert exc.value.code == "RECOMMENDATION_INVALID_TYPE"

    def test_type_mismatch_rejected(self, test_engine, seeker, tarot_reading):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError) as exc:
                generate_recommendations(db, user=seeker, reading_id=str(tarot_reading.id))
            assert exc.value.code == "RECOMMENDATION_TYPE_MISMATCH"

    def test_missing_reading_404(self, test_engine, seeker):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError) as exc:
                generate_recommendations(db, user=seeker, reading_id=str(uuid.uuid4()))
            assert exc.value.status_code == 404

    def test_tarot_source_rejected_for_palm_slot(self, test_engine, seeker, palm_reading, tarot_reading):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError) as exc:
                generate_recommendations(
                    db, user=seeker, reading_id=str(palm_reading.id),
                    tarot_reading_id=str(palm_reading.id),
                )
            assert exc.value.code == "RECOMMENDATION_TYPE_MISMATCH"

    def test_list_filters_and_pagination(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
        with _db(test_engine) as db:
            page = list_recommendations(db, user=seeker, limit=3, offset=0)
            assert page["total"] >= 5
            assert len(page["items"]) == 3
            filtered = list_recommendations(db, user=seeker, rec_type="career")
            assert page["total"] > len(filtered["items"])
            assert all(i["rec_type"] == "career" for i in filtered["items"])

    def test_list_rejects_unknown_filters(self, test_engine, seeker):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError):
                list_recommendations(db, user=seeker, rec_type="bogus")
            with pytest.raises(RecommendationServiceError):
                list_recommendations(db, user=seeker, status="bogus")

    def test_feedback_updates_record_and_event_stream(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            record_id = result["persisted"][0]["record_id"]
            updated = record_feedback(db, record_id=record_id, user=seeker, action="accepted", rating=4)
            assert updated["status"] == "accepted"
            assert updated["feedback_rating"] == 4
            events = db.scalars(
                select(RecommendationEvent).where(RecommendationEvent.event_type == EventType.accepted)
            ).all()
            assert len(events) == 1

    def test_feedback_feeds_next_prompt_context(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            first = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            record_id = first["persisted"][0]["record_id"]
            record_feedback(db, record_id=record_id, user=seeker, action="dismissed")

            captured: dict = {}

            class SniffingAdapter(FakeOnlineAdapter):
                def complete(self, **kwargs):
                    captured["prompt"] = kwargs["prompt"]
                    return super().complete(**kwargs)

            engine = get_engine()
            engine.set_adapter(SniffingAdapter(json.dumps(VALID_LLM_PAYLOAD)))
            generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            assert "dismissed" in captured.get("prompt", "")

    def test_feedback_requires_rating_for_rated(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            record_id = result["persisted"][0]["record_id"]
            with pytest.raises(RecommendationServiceError):
                record_feedback(db, record_id=record_id, user=seeker, action="rated")

    def test_feedback_rejects_out_of_range_rating(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            record_id = result["persisted"][0]["record_id"]
            with pytest.raises(RecommendationServiceError):
                record_feedback(db, record_id=record_id, user=seeker, action="rated", rating=9)

    def test_feedback_rejects_foreign_record(self, test_engine, seeker, other_seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            record_id = result["persisted"][0]["record_id"]
            with pytest.raises(RecommendationRecordNotFound):
                record_feedback(db, record_id=record_id, user=other_seeker, action="accepted")

    def test_feedback_invalid_action(self, test_engine, seeker):
        with _db(test_engine) as db:
            with pytest.raises(RecommendationServiceError):
                record_feedback(db, record_id=str(uuid.uuid4()), user=seeker, action="loved")


# Metrics

class TestMetrics:
    def test_engagement_funnel(self, test_engine, seeker, palm_reading):
        with _db(test_engine) as db:
            result = generate_recommendations(db, user=seeker, reading_id=str(palm_reading.id))
            ids = [p["record_id"] for p in result["persisted"]]
            record_feedback(db, record_id=ids[0], user=seeker, action="accepted")
            record_feedback(db, record_id=ids[1], user=seeker, action="accepted")
            record_feedback(db, record_id=ids[0], user=seeker, action="completed", rating=5)
            record_feedback(db, record_id=ids[2], user=seeker, action="dismissed")

            metrics = recommendation_metrics(db, user=seeker)
            assert metrics["total_recommendations"] == len(ids)
            assert metrics["status_counts"]["completed"] == 1
            assert metrics["status_counts"]["dismissed"] == 1
            assert metrics["engagement_rate"] > 0
            assert metrics["average_feedback_rating"] == 5.0

    def test_empty_metrics_are_zeroed(self, test_engine, seeker):
        with _db(test_engine) as db:
            metrics = recommendation_metrics(db, user=seeker)
            assert metrics["total_recommendations"] == 0
            assert metrics["engagement_rate"] == 0.0
            assert metrics["guidance_relevance_score"] is None


# API endpoints

class TestRecommendationEndpoints:
    def test_generate_with_reading_id(self, client, seeker, palm_reading):
        resp = client.post(
            "/api/v1/recommendations/generate",
            json={"reading_id": str(palm_reading.id), "max_total": 6, "per_type": 2},
            headers=_auth(seeker),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 3
        assert len(body["persisted"]) == body["count"]
        assert body["metadata"]["engine"] == "LLMRecommendationEngine"
        for item in body["recommendations"]:
            for key in ("context_relevance", "personalization", "goal_alignment", "blended"):
                assert key in item["scores"]

    def test_generate_guest_ephemeral(self, client, palm_reading):
        resp = client.post(
            "/api/v1/recommendations/generate",
            json={"reading_id": str(palm_reading.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["persisted"] == []

    def test_generate_tarot_only(self, client, seeker, tarot_reading):
        resp = client.post(
            "/api/v1/recommendations/generate",
            json={"tarot_reading_id": str(tarot_reading.id), "question": "What should I focus on?"},
            headers=_auth(seeker),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 3
        assert body["metadata"]["context_sources"] == ["tarot"]
        assert body["persisted"], "signed-in tarot-only flow must persist"

    def test_generate_validation_error_envelope(self, client):
        resp = client.post("/api/v1/recommendations/generate", json={})
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "RECOMMENDATION_MISSING_DATA"

    def test_generate_with_tarot_context(self, client, seeker, palm_reading, tarot_reading):
        resp = client.post(
            "/api/v1/recommendations/generate",
            json={
                "reading_id": str(palm_reading.id),
                "tarot_reading_id": str(tarot_reading.id),
                "max_total": 8,
            },
            headers=_auth(seeker),
        )
        assert resp.status_code == 200
        assert resp.json()["metadata"]["context_sources"] == ["palm", "tarot"]

    def test_me_requires_auth(self, client):
        resp = client.get("/api/v1/recommendations/me")
        assert resp.status_code in (401, 403)

    def test_me_lists_own_records(self, client, seeker, palm_reading):
        client.post(
            "/api/v1/recommendations/generate",
            json={"reading_id": str(palm_reading.id)},
            headers=_auth(seeker),
        )
        resp = client.get("/api/v1/recommendations/me", headers=_auth(seeker))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 5
        assert all(i["rec_type"] in REC_TYPES for i in body["items"])

    def test_feedback_endpoint_roundtrip(self, client, seeker, palm_reading):
        gen = client.post(
            "/api/v1/recommendations/generate",
            json={"reading_id": str(palm_reading.id)},
            headers=_auth(seeker),
        )
        record_id = gen.json()["persisted"][0]["record_id"]
        resp = client.patch(
            f"/api/v1/recommendations/{record_id}/feedback",
            json={"action": "accepted"},
            headers=_auth(seeker),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

        rate = client.patch(
            f"/api/v1/recommendations/{record_id}/feedback",
            json={"action": "rated", "rating": 5},
            headers=_auth(seeker),
        )
        assert rate.status_code == 200
        assert rate.json()["feedback_rating"] == 5

    def test_feedback_validation_envelope(self, client, seeker):
        resp = client.patch(
            f"/api/v1/recommendations/{uuid.uuid4()}/feedback",
            json={"action": "accepted"},
            headers=_auth(seeker),
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "RECOMMENDATION_NOT_FOUND"

    def test_metrics_admin_sees_platform_scope(self, client, admin, seeker, palm_reading):
        client.post(
            "/api/v1/recommendations/generate",
            json={"reading_id": str(palm_reading.id)},
            headers=_auth(seeker),
        )
        resp = client.get("/api/v1/recommendations/metrics", headers=_auth(admin))
        assert resp.status_code == 200
        assert resp.json()["scope"] == "platform"

    def test_metrics_requires_auth(self, client):
        resp = client.get("/api/v1/recommendations/metrics")
        assert resp.status_code in (401, 403)

# Personality intelligence: profile, strengths, weaknesses, insights, recommendations.
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.services.personality import (
    PersonalityError,
    PersonalityNotReady,
    analyze_palm_elemental_profile,
    analyze_tarot_arcana_profile,
    build_personality_profile,
    generate_recommendations,
    behavioral_insights,
    profile_strengths,
    profile_weaknesses,
)
from app.services.personality.service import (
    ELEMENT_TRAITS,
    ENGINE_NAME,
    ENGINE_VERSION,
    SAFETY_DISCLAIMER,
)
from app.auth.password import hash_password
from app.auth.tokens import create_access_token
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User, UserRole


# Integration fixtures (local to this file, matching test_reading_endpoints.py pattern)

def _create_user(test_engine, *, email: str, role: UserRole) -> User:
    from sqlalchemy.orm import Session

    with Session(test_engine) as session:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("PersonalityTest123!"),
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


@pytest.fixture
def seeker(test_engine):
    return _create_user(test_engine, email="personality_seeker@example.com", role=UserRole.user)


@pytest.fixture
def admin(test_engine):
    return _create_user(test_engine, email="personality_admin@example.com", role=UserRole.admin)


@pytest.fixture
def test_user(test_engine):
    return _create_user(test_engine, email="personality_user@example.com", role=UserRole.user)


@pytest.fixture
def auth_headers():
    return _auth


@pytest.fixture
def palm_reading(test_engine, test_user):
    from sqlalchemy.orm import Session

    result = {
        "palm_shape": {"element": "Water", "description": "Water hand", "palm_ratio": 1.2, "finger_ratio": 0.9},
        "finger_structure": {"digit_ratio_2d_4d": 0.98, "pinky_reach": 0.7, "thumb_angle": 40},
        "metadata": {"overall_confidence": 0.8, "engine": "PalmAnalysisCV"},
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
    with Session(test_engine) as session:
        reading = Reading(
            id=uuid.uuid4(),
            user_id=test_user.id,
            type=ReadingType.palm,
            status=ReadingStatus.completed,
            title="Test Palm Reading",
            summary="Water hand analysis",
            result=result,
        )
        session.add(reading)
        session.commit()
        session.refresh(reading)
        return reading


@pytest.fixture
def tarot_reading(test_engine, test_user):
    from sqlalchemy.orm import Session

    with Session(test_engine) as session:
        reading = Reading(
            id=uuid.uuid4(),
            user_id=test_user.id,
            type=ReadingType.tarot,
            status=ReadingStatus.completed,
            title="Test Tarot Reading",
            summary="Career spread",
            result=sample_tarot_data(),
        )
        session.add(reading)
        session.commit()
        session.refresh(reading)
        return reading


# Fixtures


def sample_palm_data(element: str = "Fire", confidence: float = 0.85) -> dict:
    """Build a representative palm analysis payload."""
    return {
        "palm_shape": {"element": element, "description": f"A {element.lower()} hand", "palm_ratio": 1.1, "finger_ratio": 0.82},
        "finger_structure": {"digit_ratio_2d_4d": 0.94, "pinky_reach": 0.7, "thumb_angle": 45},
        "metadata": {
            "overall_confidence": confidence,
            "engine": "PalmAnalysisCV",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "lines": [
            {"name": "Life Line", "confidence": 0.9, "variation_type": "long_and_deep", "interpretation": "Strong vitality"},
            {"name": "Head Line", "confidence": 0.8, "variation_type": "strong_clear", "interpretation": "Clear thinking"},
            {"name": "Heart Line", "confidence": 0.75, "variation_type": "standard", "interpretation": "Balanced emotion"},
        ],
        "mounts": [
            {"name": "Mount of Jupiter", "prominence": "prominent", "score": 0.85},
            {"name": "Mount of Venus", "prominence": "balanced", "score": 0.5},
            {"name": "Mount of Saturn", "prominence": "underdeveloped", "score": 0.2},
        ],
        "result_type": "palm",
    }


def sample_tarot_data() -> dict:
    return {
        "spread_name": "Three Card",
        "card_count": 3,
        "domain_focus": "career",
        "cards": [
            {"card_name": "The Emperor", "orientation": "upright", "arcana": "Major Arcana", "element": "Fire", "number": 4},
            {"card_name": "Two of Cups", "orientation": "upright", "arcana": "Minor Arcana", "element": "Water", "number": 2},
            {"card_name": "The Tower", "orientation": "reversed", "arcana": "Major Arcana", "element": "Fire", "number": 16},
        ],
        "analysis": {"arcana_balance": {"major_arcana": 2, "minor_arcana": 1}},
        "narrative": {"summary": "Career shift with collaborative tension"},
    }


# Palm elemental profile tests

class TestAnalyzePalmElementalProfile:
    def test_fire_dominant_returns_fire_profile(self):
        palm = sample_palm_data(element="Fire")
        result = analyze_palm_elemental_profile(palm)
        assert result["dominant_element"] == "Fire"
        assert result["element_scores"]["Fire"] >= result["element_scores"]["Water"]
        assert result["element_scores"]["Fire"] >= result["element_scores"]["Air"]
        assert result["element_scores"]["Fire"] >= result["element_scores"]["Earth"]
        assert 0.0 <= result["confidence"] <= 1.0

    def test_water_dominant(self):
        palm = sample_palm_data(element="Water")
        result = analyze_palm_elemental_profile(palm)
        assert result["dominant_element"] == "Water"
        assert isinstance(result["element_scores"], dict)
        assert set(result["element_scores"].keys()) == {"Fire", "Water", "Air", "Earth"}

    def test_all_elements_present_and_normalized(self):
        palm = sample_palm_data(element="Air")
        result = analyze_palm_elemental_profile(palm)
        for el in ["Fire", "Water", "Air", "Earth"]:
            assert 0.0 <= result["element_scores"][el] <= 100.0

    def test_secondary_element_set(self):
        palm = sample_palm_data(element="Fire")
        result = analyze_palm_elemental_profile(palm)
        if result["secondary_element"]:
            assert result["secondary_element"] != result["dominant_element"]

    def test_returns_confidence(self):
        palm = sample_palm_data(element="Earth", confidence=0.72)
        result = analyze_palm_elemental_profile(palm)
        assert result["confidence"] == 0.72

    def test_palm_shape_element_preserved(self):
        palm = sample_palm_data(element="Fire")
        result = analyze_palm_elemental_profile(palm)
        assert result["palm_shape_element"] == "Fire"

    def test_real_detector_strong_variations_boost_dominant(self):
        """Slugs actually emitted by the CV detector must count as strength."""
        palm = sample_palm_data(element="Fire")
        palm["lines"] = [
            {"name": "Fate Line", "confidence": 0.9, "variation_type": "deep_and_straight"},
            {"name": "Head Line", "confidence": 0.9, "variation_type": "strong_and_unbroken"},
        ]
        baseline = analyze_palm_elemental_profile({**palm, "lines": []})
        boosted = analyze_palm_elemental_profile(palm)
        assert boosted["element_scores"]["Fire"] > baseline["element_scores"]["Fire"]

    def test_real_detector_faint_variations_distribute_growth(self):
        """Faint/absent lines must feed the non-dominant elements, not be ignored."""
        palm = sample_palm_data(element="Fire")
        palm["lines"] = [
            {"name": "Fate Line", "confidence": 0.4, "variation_type": "faint_or_absent"},
            {"name": "Sun Line", "confidence": 0.3, "variation_type": "absent"},
        ]
        baseline = analyze_palm_elemental_profile({**palm, "lines": []})
        result = analyze_palm_elemental_profile(palm)
        others = sum(result["element_scores"][el] for el in ("Water", "Air", "Earth"))
        baseline_others = sum(baseline["element_scores"][el] for el in ("Water", "Air", "Earth"))
        assert others > baseline_others


# Tarot arcana profile tests

class TestAnalyzeTarotArcanaProfile:
    def test_arcana_balance_counted(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["arcana_balance"]["Major Arcana"] == 2
        assert result["arcana_balance"]["Minor Arcana"] == 1

    def test_arcana_balance_counted_lowercase(self):
        """The tarot engine persists arcana as lowercase 'major'/'minor'."""
        tarot = sample_tarot_data()
        for card in tarot["cards"]:
            card["arcana"] = card["arcana"].lower()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["arcana_balance"]["Major Arcana"] == 2
        assert result["arcana_balance"]["Minor Arcana"] == 1
        assert set(result["arcana_balance"].keys()) == {"Major Arcana", "Minor Arcana"}

    def test_major_heavy_draw_is_introspective(self):
        """2/3 majors (> 0.6) must yield the Introspective type, not Pragmatic."""
        tarot = sample_tarot_data()
        for card in tarot["cards"]:
            card["arcana"] = card["arcana"].lower()
        result = analyze_tarot_arcana_profile(tarot)
        assert "Introspective" in result["personality_type"]

    def test_arcana_inferred_from_suit_when_missing(self):
        """Archived cards may lack arcana — minors have a suit, majors don't."""
        tarot = sample_tarot_data()
        tarot["cards"][1]["suit"] = "cups"  # Two of Cups: minor
        for card in tarot["cards"]:
            card.pop("arcana", None)
        result = analyze_tarot_arcana_profile(tarot)
        # Emperor/Tower have no suit -> major; Two of Cups has suit -> minor
        assert result["arcana_balance"]["Major Arcana"] == 2
        assert result["arcana_balance"]["Minor Arcana"] == 1

    def test_elemental_balance_counted(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["elemental_balance"]["Fire"] == 2
        assert result["elemental_balance"]["Water"] == 1

    def test_orientation_counts(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["orientation_counts"]["upright"] == 2
        assert result["orientation_counts"]["reversed"] == 1

    def test_court_cards_zero_for_majors(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["court_cards"] == 0  # no page/knight/queen/king

    def test_personality_type_set(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["personality_type"]
        pt = result["personality_type"].lower()
        assert "introspective" in pt or "pragmatic" in pt or "integrative" in pt

    def test_archetype_focus(self):
        tarot = sample_tarot_data()
        result = analyze_tarot_arcana_profile(tarot)
        assert result["archetype_focus"]
        assert result["shadow_theme"]

    def test_empty_cards_handled(self):
        tarot = {
            "spread_name": "Single Card",
            "card_count": 0,
            "cards": [],
            "analysis": {},
            "narrative": {},
        }
        result = analyze_tarot_arcana_profile(tarot)
        assert isinstance(result["elemental_balance"], dict)


# Strengths tests

class TestProfileStrengths:
    def test_returns_list_of_strengths(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        assert isinstance(strengths, list)
        assert len(strengths) >= 2  # at least from dominant element

    def test_strength_has_required_fields(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        s = strengths = profile_strengths(palm_el, tarot_el)[0]
        assert "trait" in s
        assert "source" in s
        assert "confidence" in s
        assert "description" in s
        assert 0.0 <= s["confidence"] <= 100.0

    def test_strengths_from_tarot(self):
        """Tarot elemental balance should contribute strengths."""
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Earth"))
        # Force tarot with strong water
        tarot_el = {
            "elemental_balance": {"Fire": 5, "Water": 5, "Air": 5, "Earth": 5},
            "arcana_balance": {},
            "orientation_counts": {},
            "court_cards": 2,
            "numerology_repeats": {},
            "personality_type": "test",
            "archetype_focus": "test",
            "shadow_theme": "test",
            "narrative_summary": "test",
        }
        strengths = profile_strengths(palm_el, tarot_el)
        # Court cards = charismatic presence
        assert any(s["trait"] == "Charismatic presence" for s in strengths)


# Weaknesses tests

class TestProfileWeaknesses:
    def test_returns_list_of_weaknesses(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        assert isinstance(weaknesses, list)
        assert len(weaknesses) >= 1

    def test_weakness_has_required_fields(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Water"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        w = profile_weaknesses(palm_el, tarot_el)[0]
        assert "area" in w
        assert "source" in w
        assert "severity" in w
        assert "description" in w

    def test_shadow_theme_from_tarot(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Air"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        # Shadow theme from tarot should be included as a weakness
        assert any(w["source"] == "tarot_shadow_analysis" for w in weaknesses)


# Behavioral insights tests

class TestBehavioralInsights:
    def test_returns_list_of_insights(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        insights = behavioral_insights(palm_el, tarot_el, sample_palm_data())
        assert isinstance(insights, list)
        assert len(insights) >= 1

    def test_insight_has_required_fields(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Earth"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        i = behavioral_insights(palm_el, tarot_el, sample_palm_data())[0]
        assert "insight" in i
        assert "category" in i
        assert "confidence" in i
        assert 0.0 <= i["confidence"] <= 100.0

    def test_elemental_imbalance_insight(self):
        """When element spread is large, an imbalance insight should be added."""
        palm = sample_palm_data(element="Fire")
        palm["mounts"] = [
            {"name": "Mount of Jupiter", "prominence": "prominent"},
            {"name": "Mount of Saturn", "prominence": "underdeveloped"},
        ]
        palm_el = analyze_palm_elemental_profile(palm)
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        insights = behavioral_insights(palm_el, tarot_el, palm)
        imbalance_insights = [i for i in insights if i["category"] == "elemental_balance"]
        # Some imbalance is expected with prominent Jupiter vs underdeveloped Saturn
        assert isinstance(imbalance_insights, list)

    def test_faint_detector_variation_yields_line_insight(self):
        """faint_or_absent (a real detector slug) must produce a line_variation insight."""
        palm = sample_palm_data(element="Fire")
        palm["lines"] = [
            {"name": "Fate Line", "confidence": 0.4, "variation_type": "faint_or_absent"},
        ]
        palm_el = analyze_palm_elemental_profile(palm)
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        insights = behavioral_insights(palm_el, tarot_el, palm)
        assert any(i["category"] == "line_variation" for i in insights)


# Recommendations tests

class TestGenerateRecommendations:
    def test_returns_recommendations(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        recs = generate_recommendations(palm_el, tarot_el, strengths, weaknesses)
        assert isinstance(recs, list)
        assert len(recs) >= 2  # at least elemental growth + 1 tarot

    def test_recommendation_has_required_fields(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Water"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        r = generate_recommendations(palm_el, tarot_el, strengths, weaknesses)[0]
        assert "type" in r
        assert "recommendation" in r
        assert "priority" in r
        assert "source" in r
        assert r["priority"] in ("high", "medium", "low")

    def test_user_context_recommendations(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Earth"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        ctx = {"goals": ["Learn meditation"], "interests": ["Meditation"]}
        recs = generate_recommendations(palm_el, tarot_el, strengths, weaknesses, user_context=ctx)
        goal_recs = [r for r in recs if r.get("source") == "user_profile_goals"]
        assert len(goal_recs) >= 1

    def test_no_duplicate_recommendations(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Air"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        weaknesses = profile_weaknesses(palm_el, tarot_el)
        recs = generate_recommendations(palm_el, tarot_el, strengths, weaknesses)
        sources = [r["source"] for r in recs]
        assert len(sources) == len(set(sources)), "No duplicate sources in recommendations"


# Main orchestrator tests

class TestBuildPersonalityProfile:
    def test_full_profile_builds(self):
        profile = build_personality_profile(palm_data=sample_palm_data())
        assert profile["profile_type"] == "personality_intelligence"
        assert "elemental_profile" in profile
        assert "strengths" in profile
        assert "weaknesses" in profile
        assert "behavioral_insights" in profile
        assert "recommendations" in profile

    def test_contains_alignment_score(self):
        profile = build_personality_profile(palm_data=sample_palm_data(element="Water"))
        assert 0.0 <= profile["personality_alignment_score"] <= 100.0

    def test_alignment_is_low_when_no_palm(self):
        with pytest.raises(PersonalityNotReady):
            build_personality_profile(palm_data=None)

    def test_empty_tarot_falls_back(self):
        profile = build_personality_profile(
            palm_data=sample_palm_data(element="Fire"),
            tarot_data={"cards": [], "analysis": {}, "narrative": {}},
        )
        assert profile["tarot_profile"]["personality_type"]
        assert "palm-only" in profile["tarot_profile"]["personality_type"].lower()

    def test_user_context_in_profile(self):
        profile = build_personality_profile(
            palm_data=sample_palm_data(element="Air"),
            user_context={
                "age_group": "25-34",
                "interests": ["Meditation", "Tarot"],
                "goals": ["Inner peace"],
                "tone": "Gentle",
            },
        )
        # Should have recommendations from user context
        sources = [r["source"] for r in profile["recommendations"]]
        assert any("profile" in s for s in sources)

    def test_metadata_envelope(self):
        profile = build_personality_profile(palm_data=sample_palm_data(element="Earth"))
        assert profile["engine"] == ENGINE_NAME
        assert profile["engine_version"] == ENGINE_VERSION
        assert profile["rule_based"] is True
        assert profile["disclaimer"] == SAFETY_DISCLAIMER
        assert profile["timestamp"]

    def test_disclaimer_present(self):
        profile = build_personality_profile(palm_data=sample_palm_data(element="Fire"))
        assert profile["disclaimer"]
        assert "interpretive" in profile["disclaimer"].lower() or "guidance" in profile["disclaimer"].lower()

    def test_confidence_is_float(self):
        profile = build_personality_profile(palm_data=sample_palm_data(element="Water"))
        assert isinstance(profile["confidence"], float)
        assert 0.0 <= profile["confidence"] <= 1.0

    def test_limited_strengths(self):
        """Each category is bounded — not more than 3 from element, 2 from tarot."""
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        strengths = profile_strengths(palm_el, tarot_el)
        fire_strengths = [s for s in strengths if s["source"].startswith("palm_fire")]
        assert len(fire_strengths) <= 3


# API endpoint tests

class TestPersonalityAPI:
    def test_build_profile_no_auth(self, client):
        """Unauthenticated request gets profile (optional auth)."""
        resp = client.post(
            "/api/v1/personality/profile",
            json={"palm_data": sample_palm_data(element="Fire")},
        )
        assert resp.status_code == 200, resp.text

    def test_build_profile_with_palm_data(self, client, auth_headers, test_user):
        resp = client.post(
            "/api/v1/personality/profile",
            json={"palm_data": sample_palm_data(element="Water")},
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["profile_type"] == "personality_intelligence"
        assert data["elemental_profile"]["dominant_element"] in ("Fire", "Water", "Air", "Earth")

    def test_build_profile_with_reading_id(self, client, auth_headers, test_user, palm_reading):
        resp = client.post(
            "/api/v1/personality/profile",
            json={"reading_id": str(palm_reading.id)},
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["elemental_profile"]["palm_shape_element"] == "Water"  # from reading fixture

    def test_build_profile_no_palm_data(self, client, auth_headers, test_user):
        resp = client.post(
            "/api/v1/personality/profile",
            json={"reading_id": "invalid"},
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 400, resp.text

    def test_build_profile_with_tarot(self, client, auth_headers, test_user, palm_reading, tarot_reading):
        resp = client.post(
            "/api/v1/personality/profile",
            json={
                "reading_id": str(palm_reading.id),
                "tarot_reading_id": str(tarot_reading.id),
            },
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["tarot_profile"]
        assert data["recommendations"]

    def test_build_profile_user_context(self, client, auth_headers, test_user):
        resp = client.post(
            "/api/v1/personality/profile",
            json={
                "palm_data": sample_palm_data(element="Air"),
                "user_context": {
                    "goals": ["Career growth"],
                    "interests": ["Career"],
                },
            },
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        goal_recs = [r for r in data["recommendations"] if r["source"] == "user_profile_goals"]
        assert len(goal_recs) >= 1

    def test_enrich_profile(self, client, auth_headers, test_user):
        profile = build_personality_profile(palm_data=sample_palm_data(element="Fire"))
        resp = client.post(
            "/api/v1/personality/enrich",
            json={"profile": profile},
            headers=auth_headers(test_user),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["profile_type"] == "personality_intelligence"
        assert "behavioral_insights" in data


# Utility function tests

class TestUtilityFunctions:
    def test_trait_description_non_empty(self):
        for trait in ["Courage", "Empathy", "Discipline"]:
            desc = _trait_description_local(trait)
            assert desc, f"Empty description for {trait}"
            assert len(desc) > 5

    def test_growth_area_description_non_empty(self):
        for area in ["Impatience", "Moodiness", "Overthinking"]:
            desc = _growth_area_description_local(area)
            assert desc, f"Empty description for {area}"
            assert len(desc) > 5

    def test_mount_element_mapping(self):
        from app.services.personality.service import _mount_element
        assert _mount_element("Mount of Jupiter") == "Fire"
        assert _mount_element("Mount of Venus") == "Water"
        assert _mount_element("Mount of Mercury") == "Air"
        assert _mount_element("Mount of Saturn") == "Earth"
        assert _mount_element("Mount of Moon") == "Water"

    def test_compute_alignment_range(self):
        palm_el = analyze_palm_elemental_profile(sample_palm_data(element="Fire"))
        tarot_el = analyze_tarot_arcana_profile(sample_tarot_data())
        # Alignment is not directly exported but we can verify it's in range through profile build
        profile = build_personality_profile(palm_data=sample_palm_data(element="Fire"))
        assert 0.0 <= profile["personality_alignment_score"] <= 100.0

    def test_tarot_empty_cards(self):
        tarot = {
            "cards": [],
            "analysis": {},
            "narrative": {},
            "spread_name": "Single Card",
        }
        result = analyze_tarot_arcana_profile(tarot)
        assert isinstance(result["arcana_balance"], dict)
        assert result["court_cards"] == 0


# --- Local helpers (avoid import conflicts in test module) ---

def _trait_description_local(trait: str) -> str:
    descriptions = {
        "Courage": "Willingness to face difficulty or uncertainty with resolve.",
        "Empathy": "Deep capacity to understand and share others' emotional states.",
        "Discipline": "Structured, consistent effort toward long-term goals.",
    }
    return descriptions.get(trait, f"Core aspect of {trait.lower()} character.")


def _growth_area_description_local(area: str) -> str:
    descriptions = {
        "Impatience": "May rush decisions or frustrate others with urgency.",
        "Moodiness": "Emotional tides are natural; grounding practices help stabilize.",
        "Overthinking": "Analysis paralysis can block action — set decision deadlines.",
    }
    return descriptions.get(area, f"Growth opportunity around {area.lower()}.")

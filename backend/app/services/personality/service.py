"""Personality Intelligence workflows (Spec Module 6, TASK-009, FR-022..FR-026)."""
from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.interpretation.engine import LLM_SAFETY_DISCLAIMER
from app.services.palm_analysis.catalog import get_palm_lines_catalog, get_palm_mounts_catalog
from app.services.tarot.catalog import get_card_by_id, get_tarot_deck
from app.services.interpretation.llm_adapter import (
    LLMAdapter,
    LLMError,
    LLMResponse,
    get_llm_adapter,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "PersonalityIntelligenceEngine"
ENGINE_VERSION = "1.0.0"
MODEL_NAME = "personality-ai-1.0.0"
MODEL_VERSION = "1.0.0"

SAFETY_DISCLAIMER = (
    "Personality insights are interpretive guidance for self-reflection and "
    "entertainment only — not psychological diagnosis, career counsel, or "
    "guaranteed life predictions (Spec §49.19)."
)

# Element-to-trait map (speculative, symbolic — not clinical)
ELEMENT_TRAITS: Dict[str, Dict[str, List[str]]] = {
    "Fire": {
        "strengths": ["Courage", "Initiative", "Leadership", "Enthusiasm", "Decisiveness"],
        "growth_areas": ["Impatience", "Impulsiveness", "Anger management", "Ego control"],
        "behaviors": ["Action-oriented", "Competitive", "Inspirational", "Direct communicator"],
    },
    "Water": {
        "strengths": ["Empathy", "Intuition", "Creativity", "Emotional depth", "Adaptability"],
        "growth_areas": ["Moodiness", "Emotional reactivity", "Boundary setting", "Over-sensitivity"],
        "behaviors": ["Intuitive listener", "Nurturing", "Imaginative", "Sensitive to atmosphere"],
    },
    "Air": {
        "strengths": ["Analytical thinking", "Communication", "Curiosity", "Adaptability", "Objectivity"],
        "growth_areas": ["Overthinking", "Detachment", "Anxiety", "Scattered focus"],
        "behaviors": ["Intellectual explorer", "Clear communicator", "Curious learner", "Strategic thinker"],
    },
    "Earth": {
        "strengths": ["Reliability", "Patience", "Practicality", "Discipline", "Steadiness"],
        "growth_areas": ["Rigidity", "Stubbornness", "Material attachment", "Resistance to change"],
        "behaviors": ["Grounded planner", "Patient teacher", "Detail-oriented", "Conservative executor"],
    },
}

# Trait keyword -> personality dimension mapping for behavioral insights
TRAIT_DIMENSIONS: Dict[str, List[str]] = {
    "leadership": ["ambition", "confidence", "initiative"],
    "empathy": ["sensitivity", "compassion", "intuition"],
    "analytical": ["curiosity", "objectivity", "precision"],
    "creativity": ["imagination", "expression", "originality"],
    "discipline": ["patience", "reliability", "structure"],
    "adaptability": ["flexibility", "openness", "resilience"],
    "communication": ["expression", "clarity", "persuasion"],
    "introspection": ["self-awareness", "contemplation", "depth"],
}


# Line-variation slugs actually produced by the CV detector
STRONG_LINE_VARIATIONS = frozenset({
    "long_and_deep",       # life line, confidence > 0.8
    "strong_and_unbroken", # head/sun line, strong etch
    "deep_and_straight",   # fate line, confidence > 0.72
    "wide_arc",            # life line, curvature > 1.25
    "strong_clear",        # legacy slug
})
FAINT_LINE_VARIATIONS = frozenset({
    "faint_or_absent",     # fate/sun line, low confidence
    "absent",              # sun line, not traceable
    "broken",              # legacy slug
    "chain",               # legacy slug
    "faint_or_shallow",    # legacy slug
})


def _arcana_key(card: Dict[str, Any]) -> str:
    """Normalize one card's arcana to the engine's canonical labels."""
    arcana = str(card.get("arcana") or "").strip().lower()
    if arcana.startswith("major"):
        return "Major Arcana"
    if arcana.startswith("minor"):
        return "Minor Arcana"
    suit = str(card.get("suit") or "").strip().lower()
    return "Minor Arcana" if suit and suit != "none" else "Major Arcana"


class PersonalityError(Exception):
    """Personality engine failure mapped to the standard error envelope (§49.14)."""

    def __init__(
        self,
        message: str = "Personality analysis failed",
        *,
        code: str = "PERSONALITY_ERROR",
        status_code: int = 400,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class PersonalityNotReady(PersonalityError):
    def __init__(self, message: str = "Insufficient data for personality profiling."):
        super().__init__(message, code="PERSONALITY_NOT_READY", status_code=422)


# Core analysis functions

def analyze_palm_elemental_profile(palm_data: Dict[str, Any]) -> Dict[str, Any]:
    """Derive elemental personality profile from palm analysis data."""
    palm_shape = palm_data.get("palm_shape", {})
    dominant_element = palm_shape.get("element", "Unknown")
    finger_structure = palm_data.get("finger_structure", {})
    mounts = palm_data.get("mounts", [])
    lines = palm_data.get("lines", [])

    # Score each element based on palm indicators
    element_scores: Dict[str, float] = {"Fire": 0.0, "Water": 0.0, "Air": 0.0, "Earth": 0.0}

    # Base score from hand element
    if dominant_element in element_scores:
        element_scores[dominant_element] += 40.0

    # Finger ratio analysis (2D:4D — lower = more testosterone-linked traits)
    digit_ratio = finger_structure.get("digit_ratio_2d_4d", 0.0)
    if digit_ratio > 0:
        if digit_ratio < 0.95:
            element_scores["Fire"] += 15.0  # assertiveness
            element_scores["Air"] += 5.0
        else:
            element_scores["Water"] += 10.0  # relational
            element_scores["Earth"] += 10.0

    # Mount prominence
    prominent_mounts = [m for m in mounts if isinstance(m, dict) and m.get("prominence") == "prominent"]
    for mount in prominent_mounts:
        mount_element = _mount_element(mount.get("name", ""))
        if mount_element in element_scores:
            element_scores[mount_element] += 15.0

    # Line characteristics
    for line in lines if isinstance(lines, list) else []:
        if not isinstance(line, dict):
            continue
        variation = line.get("variation_type", "standard")
        if variation in STRONG_LINE_VARIATIONS:
            element_scores[dominant_element] = element_scores.get(dominant_element, 0.0) + 10.0
        elif variation in FAINT_LINE_VARIATIONS:
            # Growth indicator — distribute as potential
            for el in element_scores:
                if el != dominant_element:
                    element_scores[el] += 3.0

    # Normalize to 0-100
    total = sum(element_scores.values()) or 1.0
    normalized = {k: round(min(v / total * 100, 100), 1) for k, v in element_scores.items()}

    sorted_elements = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_elements[0][0] if sorted_elements and sorted_elements[0][1] > 0 else dominant_element
    secondary = sorted_elements[1][0] if len(sorted_elements) > 1 and sorted_elements[1][1] > 10 else None

    return {
        "dominant_element": primary,
        "secondary_element": secondary,
        "element_scores": normalized,
        "palm_shape_element": dominant_element,
        "confidence": float(palm_data.get("metadata", {}).get("overall_confidence", 0.5)),
    }


def analyze_tarot_arcana_profile(tarot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Derive personality insights from tarot card selection and synthesis."""
    cards = tarot_data.get("cards", [])
    analysis = tarot_data.get("analysis", {})
    narrative = tarot_data.get("narrative", {})

    arcana_counts = {"Major Arcana": 0, "Minor Arcana": 0}
    element_counts: Dict[str, int] = {"Fire": 0, "Water": 0, "Air": 0, "Earth": 0}
    orientation_counts = {"upright": 0, "reversed": 0}
    court_cards = 0
    numerology_repeats: Dict[str, int] = {}

    for card in cards:
        if not isinstance(card, dict):
            continue
        arcana_key = _arcana_key(card)
        arcana_counts[arcana_key] = arcana_counts.get(arcana_key, 0) + 1

        element = card.get("element")
        if element in element_counts:
            element_counts[element] += 1

        orientation = card.get("orientation", "upright")
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1

        card_name = card.get("card_name", "")
        if any(t in card_name for t in ("Page", "Knight", "Queen", "King")):
            court_cards += 1

        num_str = str(card.get("number", ""))
        if num_str:
            numerology_repeats[num_str] = numerology_repeats.get(num_str, 0) + 1

    # Personality from arcana balance
    major_ratio = arcana_counts["Major Arcana"] / max(len(cards), 1)
    if major_ratio > 0.6:
        archetype_focus = "Major life themes, archetypal transformation, spiritual lessons"
        personality_type = "Introspective — driven by deep symbolic patterns"
    elif major_ratio < 0.3:
        archetype_focus = "Everyday situations, practical matters, interpersonal dynamics"
        personality_type = "Pragmatic — grounded in daily realities"
    else:
        archetype_focus = "Balanced between spiritual symbolism and practical matters"
        personality_type = "Integrative — bridges inner vision and outer action"

    # Reversal interpretation
    reversal_ratio = orientation_counts.get("reversed", 0) / max(len(cards), 1)
    if reversal_ratio > 0.4:
        shadow_theme = "Confronting internal blocks, shadow work, unresolved tensions"
    elif reversal_ratio > 0:
        shadow_theme = "Nuanced perspective — exploring alternative angles"
    else:
        shadow_theme = "Clear external expression — energy flowing openly"

    return {
        "arcana_balance": arcana_counts,
        "elemental_balance": element_counts,
        "orientation_counts": orientation_counts,
        "court_cards": court_cards,
        "numerology_repeats": numerology_repeats,
        "personality_type": personality_type,
        "archetype_focus": archetype_focus,
        "shadow_theme": shadow_theme,
        "narrative_summary": narrative.get("summary", "") if isinstance(narrative, dict) else "",
    }


def profile_strengths(
    elemental_profile: Dict[str, Any],
    tarot_profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Identify personality strengths from elemental and tarot profiles."""
    strengths: List[Dict[str, Any]] = []
    dominant = elemental_profile.get("dominant_element", "Fire")
    traits = ELEMENT_TRAITS.get(dominant, ELEMENT_TRAITS["Fire"])

    for trait in traits["strengths"][:3]:
        strengths.append({
            "trait": trait,
            "source": f"palm_{dominant.lower()}_element",
            "confidence": min(100.0, elemental_profile.get("confidence", 0.5) * 100 + 10),
            "description": _trait_description(trait),
        })

    # Tarot-derived strengths
    element_counts = tarot_profile.get("elemental_balance", {})
    if isinstance(element_counts, dict):
        strongest_tarot_el = max(element_counts, key=element_counts.get) if element_counts else "Fire"
        tarot_traits = ELEMENT_TRAITS.get(strongest_tarot_el, {}).get("strengths", [])
        for trait in tarot_traits[:2]:
            # Avoid duplicates
            if not any(s["trait"] == trait for s in strengths):
                strengths.append({
                    "trait": trait,
                    "source": f"tarot_{strongest_tarot_el.lower()}_element",
                    "confidence": 70.0,
                    "description": _trait_description(trait),
                })

    # Court cards = interpersonal strengths
    court = tarot_profile.get("court_cards", 0)
    if court >= 2:
        strengths.append({
            "trait": "Charismatic presence",
            "source": "tarot_court_cards",
            "confidence": 65.0,
            "description": "Natural ability to engage and influence others in social settings.",
        })

    return strengths


def profile_weaknesses(
    elemental_profile: Dict[str, Any],
    tarot_profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Identify growth areas / weaknesses from elemental and tarot profiles."""
    weaknesses: List[Dict[str, Any]] = []
    dominant = elemental_profile.get("dominant_element", "Fire")
    traits = ELEMENT_TRAITS.get(dominant, ELEMENT_TRAITS["Fire"])

    for trait in traits["growth_areas"][:3]:
        weaknesses.append({
            "area": trait,
            "source": f"palm_{dominant.lower()}_element",
            "severity": "moderate",
            "description": _growth_area_description(trait),
        })

    # Shadow theme from tarot
    shadow = tarot_profile.get("shadow_theme", "")
    if shadow:
        weaknesses.append({
            "area": shadow,
            "source": "tarot_shadow_analysis",
            "severity": "insight",
            "description": f"Explored through tarot pattern: {shadow}.",
        })

    # Reversals as growth indicators
    orientations = tarot_profile.get("orientation_counts", {})
    if isinstance(orientations, dict) and orientations.get("reversed", 0) >= 2:
        weaknesses.append({
            "area": "Internal resistance — facing hidden blocks",
            "source": "tarot_reversal_pattern",
            "severity": "growth",
            "description": "Multiple reversed cards suggest inner tensions ready for conscious work.",
        })

    return weaknesses


def behavioral_insights(
    elemental_profile: Dict[str, Any],
    tarot_profile: Dict[str, Any],
    palm_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate behavioral insight observations."""
    insights: List[Dict[str, Any]] = []
    dominant = elemental_profile.get("dominant_element", "Fire")
    traits = ELEMENT_TRAITS.get(dominant, {})

    behavior_list = traits.get("behaviors", [])
    for behavior in behavior_list[:3]:
        insights.append({
            "insight": behavior,
            "category": "behavioral_pattern",
            "confidence": 75.0,
            "context": f"Derived from dominant {dominant} element in palm profile.",
        })

    # Line-based insight
    lines = palm_data.get("lines", [])
    if isinstance(lines, list):
        for line in lines[:3]:
            if isinstance(line, dict):
                var = line.get("variation_type", "standard")
                if var in FAINT_LINE_VARIATIONS:
                    insights.append({
                        "insight": f"{line.get('name', '')} traces a {var.replace('_', ' ')} pattern — energy in this area renews through deliberate pauses rather than constant flow.",
                        "category": "line_variation",
                        "confidence": 60.0,
                        "context": "Palm line morphology interpreted symbolically.",
                    })

    # Elemental imbalance insight
    scores = elemental_profile.get("element_scores", {})
    if isinstance(scores, dict):
        max_el = max(scores, key=scores.get) if scores else None
        min_el = min(scores, key=scores.get) if scores else None
        if max_el and min_el and scores.get(max_el, 0) - scores.get(min_el, 0) > 30:
            insights.append({
                "insight": f"Strong {max_el.lower()} leaning with less {min_el.lower()} expression — balancing these elements supports whole-person development.",
                "category": "elemental_balance",
                "confidence": 65.0,
                "context": "Elemental imbalance indicator from palm shape and mount analysis.",
            })

    return insights


def generate_recommendations(
    elemental_profile: Dict[str, Any],
    tarot_profile: Dict[str, Any],
    strengths: List[Dict[str, Any]],
    weaknesses: List[Dict[str, Any]],
    user_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate personal development recommendations."""
    recommendations: List[Dict[str, Any]] = []
    dominant = elemental_profile.get("dominant_element", "Fire")
    traits = ELEMENT_TRAITS.get(dominant, {})

    # Element-specific growth practices
    growth_practices: Dict[str, List[str]] = {
        "Fire": [
            "Practice pause-before-action: count to 5 before major decisions",
            "Channel competitive energy into structured fitness or skill challenges",
            "Develop active listening to balance natural assertiveness",
        ],
        "Water": [
            "Set clear emotional boundaries in relationships",
            "Use journaling for emotional clarity before reacting",
            "Practice grounding exercises when feelings feel overwhelming",
        ],
        "Air": [
            "Schedule single-task focus blocks to counter mental scattering",
            "Practice mindfulness breathing to reduce overthinking cycles",
            "Share ideas with a trusted person before finalizing plans",
        ],
        "Earth": [
            "Try one small change each week to build flexibility muscle",
            "Set creative 'play' time without outcome goals",
            "Practice verbalizing feelings to soften rigidity in relationships",
        ],
    }

    practices = growth_practices.get(dominant, growth_practices["Fire"])[:2]
    for idx, rec in enumerate(practices, 1):
        recommendations.append({
            "type": "personal_growth",
            "category": "elemental_balance",
            "recommendation": rec,
            "priority": "high" if idx == 1 else "medium",
            "source": f"dominant_{dominant.lower()}_element_{idx}",
        })

    # Strength-based recommendations
    for strength in strengths[:1]:
        recommendations.append({
            "type": "strength_development",
            "category": "strength_amplification",
            "recommendation": f"Leverage your '{strength['trait']}' strength by volunteering it in a team setting this week.",
            "priority": "medium",
            "source": strength.get("source", "profile"),
        })

    # Tarot-informed recommendation
    archetype = tarot_profile.get("archetype_focus", "")
    if archetype:
        recommendations.append({
            "type": "spiritual_development",
            "category": "archetype_awareness",
            "recommendation": f"Explore your archetype focus ({archetype}) through meditation or reflective journaling.",
            "priority": "medium",
            "source": "tarot_profile",
        })

    # User goal alignment (if context provided)
    if user_context:
        goals = user_context.get("goals", [])
        interests = user_context.get("interests", [])
        if goals:
            recommendations.append({
                "type": "goal_alignment",
                "category": "personal_development",
                "recommendation": f"Align your '{goals[0]}' goal with your dominant {dominant.lower()} element strengths for motivated progress.",
                "priority": "high",
                "source": "user_profile_goals",
            })
        if interests:
            recommendations.append({
                "type": "interest_driven_growth",
                "category": "engagement",
                "recommendation": f"Pursue your interest in '{interests[0]}' as a joyful complement to your structured growth plan.",
                "priority": "low",
                "source": "user_profile_interests",
            })

    return recommendations


# Main orchestrator

def build_personality_profile(
    palm_data: Dict[str, Any],
    tarot_data: Optional[Dict[str, Any]] = None,
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a complete personality intelligence profile."""
    if not palm_data or not isinstance(palm_data, dict):
        raise PersonalityNotReady("Palm analysis data is required for personality profiling.")

    elemental_profile = analyze_palm_elemental_profile(palm_data)

    tarot_profile: Dict[str, Any] = {}
    if tarot_data and isinstance(tarot_data, dict) and tarot_data.get("cards"):
        tarot_profile = analyze_tarot_arcana_profile(tarot_data)
    else:
        tarot_profile = {
            "arcana_balance": {},
            "elemental_balance": {},
            "orientation_counts": {},
            "court_cards": 0,
            "numerology_repeats": {},
            "personality_type": "Insufficient tarot data — palm-only profile",
            "archetype_focus": "Palm-derived insights only",
            "shadow_theme": "N/A",
            "narrative_summary": "",
        }

    strengths = profile_strengths(elemental_profile, tarot_profile)
    weaknesses = profile_weaknesses(elemental_profile, tarot_profile)
    insights = behavioral_insights(elemental_profile, tarot_profile, palm_data)
    recommendations = generate_recommendations(elemental_profile, tarot_profile, strengths, weaknesses, user_context)

    # Personality alignment score (for FR-038, used by guidance scoring)
    alignment_score = _compute_personality_alignment(elemental_profile, tarot_profile, palm_data)

    meta = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "provider": "rule_based" if not settings.OPENAI_API_KEY else "openai",
        "rule_based": True,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": SAFETY_DISCLAIMER,
    }

    return {
        "profile_type": "personality_intelligence",
        "elemental_profile": elemental_profile,
        "tarot_profile": tarot_profile,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "behavioral_insights": insights,
        "recommendations": recommendations,
        "personality_alignment_score": alignment_score,
        "confidence": min(
            elemental_profile.get("confidence", 0.5),
            0.95,
        ),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": MODEL_NAME,
        "provider": meta["provider"],
        "rule_based": meta["rule_based"],
        "timestamp": meta["timestamp"],
        "disclaimer": SAFETY_DISCLAIMER,
        "metadata": meta,
    }


# LLM-enhanced enrichment (optional — falls back to rule-based above)

def enrich_with_llm(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Optionally enrich the personality profile via LLM adapter."""
    adapter = get_llm_adapter()
    prompt = (
        f"Given this personality profile, provide 3-5 additional nuanced behavioral "
        f"insights that complement (never contradict) the existing analysis.\n"
        f"Profile summary: Elemental={profile.get('elemental_profile', {}).get('dominant_element')}, "
        f"Strengths={[s['trait'] for s in profile.get('strengths', [])[:3]]}, "
        f"Weaknesses={[w['area'] for w in profile.get('weaknesses', [])[:3]]}.\n"
        f"Return as JSON with key 'additional_insights' (list of strings)."
    )
    try:
        response: LLMResponse = adapter.complete(prompt=prompt, max_tokens=500, temperature=0.5, json_mode=True)
        content = response.content
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(content[json_start:json_end])
            extra = parsed.get("additional_insights", [])
        else:
            extra = []
    except (LLMError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("LLM personality enrichment failed, using rule-based: %s", exc)
        extra = []

    profile.setdefault("behavioral_insights", [])
    for item in extra:
        profile["behavioral_insights"].append({
            "insight": item,
            "category": "llm_enrichment",
            "confidence": 60.0,
            "context": "LLM-generated supplementary insight (rule-based fallback active when offline).",
        })
    profile["metadata"]["llm_enriched"] = bool(extra)
    return profile


# Helpers

def _mount_element(mount_name: str) -> str:
    mapping = {
        "Mount of Jupiter": "Fire",
        "Mount of Saturn": "Earth",
        "Mount of Apollo": "Fire",
        "Mount of Mercury": "Air",
        "Mount of Venus": "Water",
        "Mount of Moon": "Water",
    }
    for key, el in mapping.items():
        if key.lower() in mount_name.lower():
            return el
    return "Earth"


def _trait_description(trait: str) -> str:
    descriptions = {
        "Courage": "Willingness to face difficulty or uncertainty with resolve.",
        "Initiative": "Natural tendency to take first action without external prompting.",
        "Leadership": "Ability to guide, inspire, and direct others toward shared goals.",
        "Enthusiasm": "Genuine excitement and energy invested in pursuits.",
        "Decisiveness": "Capacity to make clear choices under uncertainty.",
        "Empathy": "Deep capacity to understand and share others' emotional states.",
        "Intuition": "Reliable gut-level perception beyond rational analysis.",
        "Creativity": "Ability to generate novel, valuable ideas and expressions.",
        "Emotional depth": "Rich inner emotional life with nuanced self-awareness.",
        "Adaptability": "Flexibility in adjusting to new conditions and perspectives.",
        "Analytical thinking": "Systematic, logical approach to problem-solving.",
        "Communication": "Natural skill in expressing ideas clearly and persuasively.",
        "Curiosity": "Genuine desire to learn, explore, and understand.",
        "Objectivity": "Ability to evaluate situations without personal bias.",
        "Reliability": "Consistent, dependable follow-through on commitments.",
        "Patience": "Capacity to endure delay or difficulty without frustration.",
        "Practicality": "Grounded, realistic approach to tasks and decisions.",
        "Discipline": "Structured, consistent effort toward long-term goals.",
        "Steadiness": "Calm, unwavering presence that stabilizes those around.",
    }
    return descriptions.get(trait, f"Core aspect of {trait.lower()} character.")


def _growth_area_description(area: str) -> str:
    descriptions = {
        "Impatience": "May rush decisions or frustrate others with urgency.",
        "Impulsiveness": "Acting before reflecting can lead to avoidable consequences.",
        "Anger management": "Channeling fiery intensity into constructive outlets.",
        "Ego control": "Balancing confidence with openness to feedback.",
        "Moodiness": "Emotional tides are natural; grounding practices help stabilize.",
        "Emotional reactivity": "Pausing before responding builds emotional maturity.",
        "Boundary setting": "Protecting your energy is essential for sustained giving.",
        "Over-sensitivity": "Distinguishing others' emotions from your own center.",
        "Overthinking": "Analysis paralysis can block action — set decision deadlines.",
        "Detachment": "Connecting emotionally enhances relationships and impact.",
        "Anxiety": "Grounding in the present moment reduces future-focused worry.",
        "Scattered focus": "Single-tasking and prioritization restore clarity.",
        "Rigidity": "Flexibility does not weaken principles — it strengthens them.",
        "Stubbornness": "Listening to alternative views enriches your solid foundation.",
        "Material attachment": "Balance practical goals with spiritual and relational values.",
        "Resistance to change": "Small experiments with novelty build adaptive capacity.",
    }
    return descriptions.get(area, f"Growth opportunity around {area.lower()}.")


def _compute_personality_alignment(
    elemental_profile: Dict[str, Any],
    tarot_profile: Dict[str, Any],
    palm_data: Dict[str, Any],
) -> float:
    """Compute personality alignment score (0-100) per FR-038."""
    conf = float(palm_data.get("metadata", {}).get("overall_confidence", 0.5))
    element_scores = elemental_profile.get("element_scores", {})
    if not element_scores:
        return round(conf * 50, 1)

    max_score = max(element_scores.values())
    min_score = min(element_scores.values())
    spread = max_score - min_score

    # Lower spread = higher alignment (balanced personality)
    balance_factor = max(0.0, 1.0 - spread / 100.0)

    # Tarot harmony
    arcana = tarot_profile.get("arcana_balance", {})
    if isinstance(arcana, dict) and arcana:
        total = sum(arcana.values()) or 1
        majors = sum(v for k, v in arcana.items() if str(k).lower().startswith("major"))
        major_ratio = majors / total
        harmony = 1.0 - abs(major_ratio - 0.5) * 2  # 1.0 when 50/50
    else:
        harmony = 0.5

    alignment = round((conf * 0.4 + balance_factor * 0.35 + harmony * 0.25) * 100, 1)
    return alignment

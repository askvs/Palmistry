"""Pydantic schemas for Personality Intelligence (TASK-009, FR-022..FR-026)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Request

class PersonalityProfileRequest(BaseModel):
    """Request to build a personality intelligence profile."""

    palm_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Palm analysis result JSON (from a completed reading)"
    )
    reading_id: Optional[str] = Field(
        default=None, min_length=1, description="Completed palm reading ID to use as source data"
    )
    tarot_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional tarot reading result for combined profile"
    )
    tarot_reading_id: Optional[str] = Field(
        default=None, min_length=1, description="Completed tarot reading ID"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user profile context (age_group, interests, goals, preferences)",
    )
    question: Optional[str] = Field(
        default=None, max_length=500, description="Optional focus question"
    )


class PersonalityEnrichRequest(BaseModel):
    """Request to enrich an existing personality profile via LLM."""

    profile: Dict[str, Any] = Field(..., description="Personality profile to enrich")


# Response components

class ElementScore(BaseModel):
    element: str
    score: float
    source: str = ""


class ElementalProfile(BaseModel):
    dominant_element: str = "Fire"
    secondary_element: Optional[str] = None
    element_scores: Dict[str, float] = Field(default_factory=dict)
    palm_shape_element: str = "Unknown"
    confidence: float = 0.5


class TarotArcanaProfile(BaseModel):
    arcana_balance: Dict[str, int] = Field(default_factory=dict)
    elemental_balance: Dict[str, int] = Field(default_factory=dict)
    orientation_counts: Dict[str, int] = Field(default_factory=dict)
    court_cards: int = 0
    numerology_repeats: Dict[str, int] = Field(default_factory=dict)
    personality_type: str = "Palm-only profile"
    archetype_focus: str = "Palm-derived insights only"
    shadow_theme: str = "N/A"
    narrative_summary: str = ""


class TraitInsight(BaseModel):
    trait: str = ""
    source: str = ""
    confidence: float = 0.0
    description: str = ""


class GrowthArea(BaseModel):
    area: str = ""
    source: str = ""
    severity: str = "moderate"
    description: str = ""


class BehavioralInsight(BaseModel):
    insight: str = ""
    category: str = "behavioral_pattern"
    confidence: float = 0.0
    context: str = ""


class Recommendation(BaseModel):
    type: str = "personal_growth"
    category: str = "elemental_balance"
    recommendation: str = ""
    priority: str = "medium"
    source: str = ""


# Main response

class PersonalityProfileResponse(BaseModel):
    """Complete personality intelligence profile response."""

    profile_type: str = "personality_intelligence"
    elemental_profile: ElementalProfile
    tarot_profile: TarotArcanaProfile
    strengths: List[TraitInsight] = Field(default_factory=list)
    weaknesses: List[GrowthArea] = Field(default_factory=list)
    behavioral_insights: List[BehavioralInsight] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    personality_alignment_score: float = 0.0
    confidence: float = 0.5
    engine: str = "PersonalityIntelligenceEngine"
    engine_version: str = "1.0.0"
    model: str = "personality-ai-1.0.0"
    provider: str = "rule_based"
    rule_based: bool = True
    timestamp: str = ""
    disclaimer: str = ""
    metadata: Optional[Dict[str, Any]] = None


class PersonalityErrorEnvelope(BaseModel):
    """Error envelope for personality endpoint failures (§49.14)."""

    code: str = "PERSONALITY_ERROR"
    message: str
    request_id: Optional[str] = None

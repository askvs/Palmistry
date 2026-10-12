"""Pydantic schemas for the AI Interpretation Engine API (Spec Module 5, TASK-008)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PalmInterpretationRequest(BaseModel):
    """Request to generate a palm interpretation from existing analysis data."""

    reading_id: Optional[str] = Field(default=None, description="ID of the completed palm reading")
    palm_data: Optional[Dict[str, Any]] = Field(default=None, description="Direct palm analysis data for unsaved or guest readings")
    question: Optional[str] = Field(default=None, max_length=500, description="Optional user question")


class TarotInterpretationRequest(BaseModel):
    """Request to enhance a tarot interpretation with AI."""

    reading_id: Optional[str] = Field(default=None, description="ID of the completed tarot reading")
    tarot_data: Optional[Dict[str, Any]] = Field(default=None, description="Direct tarot reading data for unsaved or guest readings")
    question: Optional[str] = Field(default=None, max_length=500, description="Optional user question")


class SynthesisRequest(BaseModel):
    """Request to synthesize palm and tarot readings."""

    palm_reading_id: str = Field(..., min_length=1, description="ID of completed palm reading")
    tarot_reading_id: str = Field(..., min_length=1, description="ID of completed tarot reading")
    question: Optional[str] = Field(default=None, max_length=500, description="Optional user question")


class PalmInterpretationResponse(BaseModel):
    """Response for palm interpretation."""

    reading_id: Optional[str] = None
    interpretation_type: str = "palm"
    summary: str
    body: str
    guidance: List[str]
    domain_insights: Dict[str, str] = Field(default_factory=dict)
    element: str
    confidence: float
    engine: str
    engine_version: str
    model: str
    provider: str
    rule_based: bool
    timestamp: str
    disclaimer: str
    metadata: Optional[Dict[str, Any]] = None


class TarotEnhancementResponse(BaseModel):
    """Response for tarot interpretation enhancement."""

    reading_id: Optional[str] = None
    interpretation_type: str = "tarot_enhancement"
    spread_name: str
    deep_narrative: str
    wisdom_points: List[str] = Field(default_factory=list)
    action_plan: List[str] = Field(default_factory=list)
    contextual_insight: str = ""
    domain_focus: Optional[str] = None
    engine: str
    engine_version: str
    model: str
    provider: str
    rule_based: bool
    timestamp: str
    disclaimer: str
    metadata: Optional[Dict[str, Any]] = None


class SynthesisResponse(BaseModel):
    """Response for reading synthesis."""

    palm_reading_id: Optional[str] = None
    tarot_reading_id: Optional[str] = None
    interpretation_type: str = "synthesis"
    life_narrative: str
    cross_references: List[str] = Field(default_factory=list)
    integrated_guidance: List[str] = Field(default_factory=list)
    growth_areas: List[str] = Field(default_factory=list)
    overall_confidence: float
    palm_element: str
    tarot_domain: str
    engine: str
    engine_version: str
    model: str
    provider: str
    rule_based: bool
    timestamp: str
    disclaimer: str
    metadata: Optional[Dict[str, Any]] = None


class InterpretationMetadata(BaseModel):
    """Metadata common to all interpretation responses."""

    engine: str
    engine_version: str
    model: str
    provider: str
    rule_based: bool
    timestamp: str
    disclaimer: str


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)
    timestamp: str


class ChatRequest(BaseModel):
    """Request to chat with AI about a reading."""

    reading_id: str = Field(..., min_length=1, description="ID of the reading")
    reading_type: str = Field(..., pattern="^(palm|tarot)$", description="Type of reading")
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_history: list[ChatMessage] = Field(default_factory=list, description="Previous messages")


class ChatResponse(BaseModel):
    """Response from AI chat."""

    reading_id: str
    reading_type: str
    answer: str
    conversation_history: list[ChatMessage]
    metadata: InterpretationMetadata
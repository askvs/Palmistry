"""Pydantic schemas for the Dashboard AI Assistant (overall analysis chat)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssistantMessageIn(BaseModel):
    """One prior turn, as supplied by the client."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class AssistantMetric(BaseModel):
    """A single number the assistant is allowed to quote."""

    label: str
    value: str
    hint: Optional[str] = None


class AssistantHighlight(BaseModel):
    """A short observational note derived from the snapshot."""

    label: str
    detail: str


class AssistantContextOut(BaseModel):
    """Role-scoped snapshot of everything the assistant can reason about."""

    role: str
    role_label: str
    scope: str
    headline: str
    metrics: List[AssistantMetric] = Field(default_factory=list)
    highlights: List[AssistantHighlight] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    disclaimer: str
    generated_at: str


class AssistantChatRequest(BaseModel):
    """A question for the assistant, or a request for the overall analysis."""

    question: str = Field(..., min_length=1, max_length=2000)
    intent: str = Field(
        default="question",
        pattern="^(question|overview)$",
        description="'overview' asks for the full dashboard analysis narrative",
    )
    conversation_history: List[AssistantMessageIn] = Field(default_factory=list)


class AssistantChatOut(BaseModel):
    """Assistant answer plus the stamped conversation it belongs to."""

    role: str
    intent: str
    answer: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

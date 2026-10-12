"""Pydantic schemas for the AI chat API."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the AI chat conversation."""

    role: str = Field(..., min_length=1, max_length=10, description="Message role")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")
    timestamp: str = Field(..., description="ISO timestamp of the message")


class ChatRequest(BaseModel):
    """Request to start or continue an AI chat about a reading."""

    reading_id: str = Field(..., min_length=1, description="ID of the reading")
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list, description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    """Response from the AI chat endpoint."""

    reading_id: str
    answer: str
    conversation_history: List[ChatMessage]
    metadata: Dict[str, Any]

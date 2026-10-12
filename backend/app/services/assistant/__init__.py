"""Dashboard AI Assistant (overall analysis chat for every role)."""
from app.services.assistant.chat import AssistantError, answer
from app.services.assistant.context import (
    DISCLAIMER,
    ENGINE_NAME,
    ENGINE_VERSION,
    build_context,
)

__all__ = [
    "answer",
    "build_context",
    "AssistantError",
    "DISCLAIMER",
    "ENGINE_NAME",
    "ENGINE_VERSION",
]

"""Dashboard AI Assistant endpoints — overall analysis for every role."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant import (
    AssistantChatOut,
    AssistantChatRequest,
    AssistantContextOut,
)
from app.services.assistant import answer, build_context

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get(
    "/context",
    response_model=AssistantContextOut,
    summary="Role-scoped data snapshot behind the dashboard AI assistant",
)
def get_context(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return the live figures, highlights and suggested prompts for the caller's role."""
    return build_context(db, user)


@router.post(
    "/chat",
    response_model=AssistantChatOut,
    summary="Ask the dashboard AI assistant about your overall platform data",
)
def chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Answer one turn grounded in the caller's role-scoped snapshot."""
    return answer(
        db,
        user,
        question=payload.question,
        intent=payload.intent,
        history=[m.model_dump() for m in payload.conversation_history],
    )


__all__ = ["router"]

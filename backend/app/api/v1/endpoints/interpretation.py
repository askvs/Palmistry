"""AI Interpretation Engine API endpoints (Spec Module 5, TASK-008)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.reading import Reading, ReadingType
from app.models.user import User
from app.services.interpretation.engine import (
    InterpretationError,
    generate_palm_interpretation,
    generate_reading_synthesis,
    generate_tarot_interpretation,
    get_llm_adapter,
)
from app.services.reading.service import ReadingError, ReadingNotFound, get_any
from app.schemas.interpretation import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    PalmInterpretationRequest,
    PalmInterpretationResponse,
    SynthesisRequest,
    SynthesisResponse,
    TarotEnhancementResponse,
    TarotInterpretationRequest,
)

router = APIRouter(prefix="/interpret", tags=["interpretation"])

LLM_SAFETY_DISCLAIMER = (
    "All palmistry, tarot, health, career, and life-trend insights presented in this "
    "interpretation are offered strictly for interpretive guidance, entertainment, "
    "and self-reflection. They do not constitute medical advice, legal counsel, or "
    "guaranteed financial forecasts (Spec §49.19)."
)

TAROT_SAFETY_DISCLAIMER = (
    "All tarot interpretations are offered strictly for interpretive guidance, entertainment, "
    "and self-reflection. They do not constitute medical advice, legal counsel, or "
    "guaranteed financial forecasts (Spec §49.19)."
)


def _get_reading(db: Session, reading_id: str, user: User | None) -> Reading:
    """Retrieve a reading by ID, allowing owner/reader/admin access."""
    try:
        rid = uuid.UUID(reading_id)
    except (ValueError, AttributeError):
        raise InterpretationError(
            f"Invalid reading ID: '{reading_id}'", code="INTERPRETATION_INVALID_ID", status_code=400
        )
    return get_any(db, rid)


@router.post(
    "/palm",
    response_model=PalmInterpretationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI interpretation from a palm reading (FR-017)",
)
def interpret_palm(
    payload: PalmInterpretationRequest,
    question: Optional[str] = None,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate an AI-powered interpretation from an existing palm reading or direct palm data."""
    effective_question = payload.question or question
    palm_data = None
    reading = None

    if payload.reading_id:
        reading = _get_reading(db, payload.reading_id, user)
        if reading.type != ReadingType.palm:
            raise InterpretationError(
                f"Reading is not a palm reading (type={reading.type})",
                code="INTERPRETATION_TYPE_MISMATCH",
                status_code=400,
            )
        palm_data = reading.result or {}
    elif payload.palm_data:
        palm_data = payload.palm_data
    else:
        raise InterpretationError(
            "Either reading_id or palm_data must be provided.",
            code="INTERPRETATION_MISSING_DATA",
            status_code=400,
        )

    result = generate_palm_interpretation(
        palm_data=palm_data,
        question=effective_question,
    )
    if reading is not None:
        result["reading_id"] = str(reading.id)
        try:
            current_result = dict(reading.result or {})
            current_result["ai_interpretation"] = result
            reading.result = current_result
            db.add(reading)
            db.commit()
        except Exception:
            db.rollback()
    else:
        result["reading_id"] = None

    return result


@router.post(
    "/tarot",
    response_model=TarotEnhancementResponse,
    status_code=status.HTTP_200_OK,
    summary="Enhance a tarot reading with AI insights (FR-016)",
)
def interpret_tarot(
    payload: TarotInterpretationRequest,
    question: Optional[str] = None,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate AI-powered enhancement of an existing tarot reading or direct tarot data."""
    effective_question = payload.question or question
    tarot_data = None
    reading = None

    if payload.reading_id:
        reading = _get_reading(db, payload.reading_id, user)
        if reading.type != ReadingType.tarot:
            raise InterpretationError(
                f"Reading is not a tarot reading (type={reading.type})",
                code="INTERPRETATION_TYPE_MISMATCH",
                status_code=400,
            )
        tarot_data = reading.result or {}
    elif payload.tarot_data:
        tarot_data = payload.tarot_data
    else:
        raise InterpretationError(
            "Either reading_id or tarot_data must be provided.",
            code="INTERPRETATION_MISSING_DATA",
            status_code=400,
        )

    result = generate_tarot_interpretation(
        tarot_data=tarot_data,
        question=effective_question,
    )
    if reading is not None:
        result["reading_id"] = str(reading.id)
        try:
            current_result = dict(reading.result or {})
            current_result["ai_interpretation"] = result
            reading.result = current_result
            db.add(reading)
            db.commit()
        except Exception:
            db.rollback()
    else:
        result["reading_id"] = None

    return result


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI about a reading",
)
def chat_with_ai(
    payload: ChatRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Continue a conversation about a reading with the AI interpreter."""
    # Verify reading access and type
    reading = _get_reading(db, payload.reading_id, user)
    if payload.reading_type == "palm" and reading.type != ReadingType.palm:
        raise InterpretationError(
            f"Reading is not a palm reading (type={reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    if payload.reading_type == "tarot" and reading.type != ReadingType.tarot:
        raise InterpretationError(
            f"Reading is not a tarot reading (type={reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )

    reading_data = reading.result or {}
    ai_interpretation = reading_data.get("ai_interpretation") or {}

    # Build system prompt incorporating existing AI interpretation
    if payload.reading_type == "palm":
        element = reading_data.get("palm_shape", {}).get("element", "Unknown")
        lines_summary = "; ".join(
            f"{l.get('name', l.get('line_id', ''))}: {l.get('interpretation', '')}"
            for l in reading_data.get("lines", [])
            if isinstance(l, dict)
        )
        system_prompt = (
            f"You are a wise palmistry interpreter specializing in {element} hand analysis. "
            f"Here is the reading data for context: Element: {element}. "
            f"Detected lines: {lines_summary}. "
            f"The previously generated AI summary was: {ai_interpretation.get('summary', '')}. "
            f"Previous guidance: {ai_interpretation.get('guidance', [])}. "
            f"Domain insights: {ai_interpretation.get('domain_insights', {})}. "
            f"Answer the user's question conversationally, incorporating these insights. "
            f"Be direct, insightful, and draw specific connections to the reading data. "
            f"Never present interpretations as guaranteed facts."
        )
    else:
        spread_name = reading_data.get("spread_name", "Unknown")
        cards_summary = "; ".join(
            f"{c.get('card_name', c.get('name', ''))} ({c.get('orientation', 'upright')})"
            for c in reading_data.get("cards", [])
            if isinstance(c, dict)
        )
        system_prompt = (
            f"You are a master tarot interpreter specializing in {spread_name} spreads. "
            f"Cards drawn: {cards_summary}. "
            f"The previously generated AI narrative was: {ai_interpretation.get('deep_narrative', '')}. "
            f"Previous wisdom points: {ai_interpretation.get('wisdom_points', [])}. "
            f"Previous action plan: {ai_interpretation.get('action_plan', [])}. "
            f"Answer the user's question conversationally, incorporating these insights. "
            f"Be direct, insightful, and draw specific connections to the card meanings. "
            f"Never present interpretations as guaranteed facts."
        )

    # Build conversation messages for the LLM
    llm_messages: list[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in payload.conversation_history:
        llm_messages.append({"role": msg.role, "content": msg.content})
    llm_messages.append({"role": "user", "content": payload.question})

    # Generate response via LLM adapter
    adapter = get_llm_adapter()
    response = adapter.complete(
        prompt=payload.question,
        system=system_prompt,
        max_tokens=1000,
        temperature=0.7,
        json_mode=False,
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    # Build updated conversation history
    updated_history = list(payload.conversation_history) + [
        ChatMessage(role="user", content=payload.question, timestamp=now_iso),
        ChatMessage(role="assistant", content=response.content, timestamp=now_iso),
    ]

    return {
        "reading_id": str(reading.id),
        "reading_type": payload.reading_type,
        "answer": response.content,
        "conversation_history": updated_history,
        "metadata": {
            "engine": "AIInterpretationEngine",
            "engine_version": "1.0.0",
            "model": response.model,
            "provider": response.provider,
            "rule_based": response.rule_based,
            "timestamp": now_iso,
            "disclaimer": LLM_SAFETY_DISCLAIMER if payload.reading_type == "palm" else TAROT_SAFETY_DISCLAIMER,
        },
    }


@router.post(
    "/synthesize",
    response_model=SynthesisResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize palm and tarot readings into a unified narrative",
)
def synthesize(
    payload: SynthesisRequest,
    question: Optional[str] = None,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate a unified synthesis of palm and tarot readings."""
    palm_reading = _get_reading(db, payload.palm_reading_id, user)
    tarot_reading = _get_reading(db, payload.tarot_reading_id, user)

    if palm_reading.type != ReadingType.palm:
        raise InterpretationError(
            f"Palm reading is not a palm reading (type={palm_reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )
    if tarot_reading.type != ReadingType.tarot:
        raise InterpretationError(
            f"Tarot reading is not a tarot reading (type={tarot_reading.type})",
            code="INTERPRETATION_TYPE_MISMATCH",
            status_code=400,
        )

    effective_question = payload.question or question
    result = generate_reading_synthesis(
        palm_data=palm_reading.result or {},
        tarot_data=tarot_reading.result or {},
        question=effective_question,
    )
    result["palm_reading_id"] = str(palm_reading.id)
    result["tarot_reading_id"] = str(tarot_reading.id)
    return result

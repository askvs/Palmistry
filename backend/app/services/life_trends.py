"""Life Trend Analyzer service (TASK-008 / FR-017, Milestone 3)."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.reading import Reading, ReadingStatus
from app.models.user import User
from app.services.interpretation.llm_adapter import LLMError, get_llm_adapter
from app.services.trends import ENGINE_NAME, ENGINE_VERSION, METHOD, LifeTrendEngine

logger = logging.getLogger(__name__)

SAFETY_DISCLAIMER = (
    "All palmistry, tarot, health, career, and life-trend insights presented in this "
    "analysis are offered strictly for interpretive guidance, entertainment, and "
    "self-reflection. They do not constitute medical advice, legal counsel, or "
    "guaranteed financial forecasts (Spec §49.19)."
)


def _gather_user_data(db: Session, user: User) -> Dict[str, Any]:
    """Collect the user's real stored readings and profile goals/interests."""
    readings_q = (
        select(Reading)
        .where(Reading.user_id == user.id, Reading.status == ReadingStatus.completed)
        .order_by(Reading.created_at.asc())
    )
    readings = db.scalars(readings_q).all()

    goals: List[str] = []
    interests: List[str] = []
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile:
        goals = [g.text for g in (profile.goals or []) if getattr(g, "text", None)]
        interests = [i.interest for i in (profile.interests or []) if getattr(i, "interest", None)]

    return {
        "readings": [
            {
                "type": r.type.value if hasattr(r.type, "value") else str(r.type),
                "result": r.result or {},
                "created_at": r.created_at,
            }
            for r in readings
        ],
        "goals": goals,
        "interests": interests,
    }


def _enrich_explanation_with_llm(
    engine_result: Dict[str, Any], user_data: Dict[str, Any]
) -> str:
    """Best-effort LLM rephrasing of the explanation, grounded in computed facts."""
    adapter = get_llm_adapter()
    trends = engine_result.get("current_trends", [])
    facts = {
        "life_path": engine_result.get("life_path"),
        "top_trends": [
            {"name": t["name"], "score": t["score"], "direction": t["direction"]}
            for t in trends[:3]
        ],
        "growth_potential": engine_result.get("growth_potential"),
        "readings_analyzed": engine_result.get("data_coverage", {}).get("readings_analyzed"),
        "goals": user_data.get("goals", [])[:3],
    }
    prompt = (
        "Rewrite the following life trend analysis explanation into a warm, natural "
        "paragraph (max 120 words). Use ONLY the facts given — do not add, invent, or "
        "exaggerate any prediction. Keep the interpretive, non-deterministic tone.\n"
        f"Facts: {json.dumps(facts, default=str)}"
    )
    try:
        response = adapter.complete(prompt=prompt, max_tokens=300, temperature=0.5)
        if response.rule_based or not response.content:
            return engine_result["explanation"]
        text = response.content.strip().strip('"')
        return text if len(text) > 40 else engine_result["explanation"]
    except LLMError as exc:
        logger.warning("LLM explanation enrichment failed, using deterministic text: %s", exc)
        return engine_result["explanation"]


def generate_life_trends(db: Session, user: User) -> Dict[str, Any]:
    """Generate the data-driven life trend analysis for a user."""
    user_data = _gather_user_data(db, user)
    engine = LifeTrendEngine(
        readings=user_data["readings"],
        goals=user_data["goals"],
        interests=user_data["interests"],
    )
    result = engine.compute()
    result["explanation"] = _enrich_explanation_with_llm(result, user_data)
    result["disclaimer"] = SAFETY_DISCLAIMER
    result["generated_at"] = datetime.utcnow().isoformat()
    return result


class LifeTrendAnalyzer:
    """Backwards-compatible façade over the feature-based trend engine."""

    def analyze(self, db: Session, user: User) -> Dict[str, Any]:
        return generate_life_trends(db, user)

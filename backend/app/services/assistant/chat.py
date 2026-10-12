"""Dashboard AI Assistant — grounded chat over the role-scoped snapshot."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.assistant.context import (
    DISCLAIMER,
    ENGINE_NAME,
    ENGINE_VERSION,
    build_context,
)
from app.services.interpretation.llm_adapter import LLMError, LLMResponse, get_llm_adapter

MAX_HISTORY_TURNS = 12

_PERSONA = {
    "user": (
        "You are the Palmistry & Tarot platform's personal AI companion speaking to a seeker. "
        "You read their whole divination history — palm scans, tarot spreads, recommendations and "
        "guidance threads — and translate it into an overall analysis: recurring themes, "
        "strengths, tensions, and the single most useful next step. Speak warmly, in plain "
        "language, in the second person."
    ),
    "tarot_reader": (
        "You are the Palmistry & Tarot platform's AI co-pilot for a tarot reader. You summarise "
        "the querent reading queue: volume, backlog, type mix, and where certification effort "
        "pays off first. Be operational and concise — this is a work console, not a reading."
    ),
    "spiritual_consultant": (
        "You are the Palmistry & Tarot platform's AI co-pilot for a spiritual consultant. You "
        "summarise the guidance queue, dominant seeker themes, and the consultant's own "
        "responsiveness so they can triage the next thread well. Be compassionate but concrete."
    ),
    "admin": (
        "You are the Palmistry & Tarot platform's AI analyst for an administrator. You report "
        "growth, engagement, role mix, content volume and governance signals from the live "
        "platform data. Be precise, quote numbers exactly as given, and flag anything that "
        "looks anomalous."
    ),
}


class AssistantError(Exception):
    """Assistant failure mapped to the standard error envelope (§49.14)."""

    code = "ASSISTANT_ERROR"
    status_code = 400

    def __init__(self, message: str = "Assistant request failed"):
        self.message = message
        super().__init__(message)


def _system_prompt(context: Dict[str, Any]) -> str:
    persona = _PERSONA.get(context["role"], _PERSONA["user"])
    facts = "\n".join(f"- {fact}" for fact in context.get("facts", []))
    return (
        f"{persona}\n\n"
        f"GROUND TRUTH — live platform data for this caller (role: {context['role_label']}, "
        f"scope: {context['scope']}). These are the ONLY figures you may quote:\n{facts}\n\n"
        "Rules:\n"
        "1. Base every claim on the ground truth above. If a number is not there, say the data "
        "does not show it instead of estimating.\n"
        "2. Never invent readings, users, threads, or dates.\n"
        "3. Keep the answer compact: a short synthesis, then at most five bullets, then one "
        "clear next action. Use plain prose and short paragraphs — no markdown headings.\n"
        "4. Treat every divinatory statement as interpretive guidance, never as guaranteed fact.\n"
        f"5. Close with this disclaimer verbatim: \"{DISCLAIMER}\""
    )


def _overview_prompt(context: Dict[str, Any]) -> str:
    return (
        f"Produce the overall analysis of {context['scope']} for this "
        f"{context['role_label'].lower()}, using only the ground truth provided. "
        "Cover, in order: (1) a two-sentence headline, (2) the three most significant "
        "signals with their numbers, (3) one risk or gap worth attention, (4) the single "
        "most useful next action."
    )


def _trim_history(history: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep the most recent user/assistant turns, role and content only."""
    turns: List[Dict[str, str]] = []
    for m in history:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            continue
        content = m.get("content")
        if not content:
            continue
        turns.append({"role": m["role"], "content": content})
    return turns[-MAX_HISTORY_TURNS:]


def _complete(adapter, *, prompt: str, system: str) -> LLMResponse:
    """Call the LLM adapter, normalising its failure mode to AssistantError."""
    try:
        return adapter.complete(
            prompt=prompt,
            system=system,
            max_tokens=900,
            temperature=0.5,
            json_mode=False,
        )
    except LLMError as exc:  # pragma: no cover - adapter only raises for online providers
        raise AssistantError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise AssistantError("The assistant is temporarily unavailable.") from exc


def answer(
    db: Session,
    user: User,
    *,
    question: str,
    intent: str = "question",
    history: Sequence[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """Answer one assistant turn grounded in the caller's live dashboard data."""
    context = build_context(db, user)
    system = _system_prompt(context)

    if intent == "overview":
        prompt = _overview_prompt(context)
    else:
        prompt = question.strip()
        if not prompt:
            raise AssistantError("A question is required.")

    response = _complete(get_llm_adapter(), prompt=prompt, system=system)

    now = datetime.now(timezone.utc).isoformat()
    # Re-stamp transcript timestamps server-side.
    turns = [
        {"role": m["role"], "content": m["content"], "timestamp": now}
        for m in _trim_history(history or [])
    ]
    turns.append({"role": "user", "content": prompt, "timestamp": now})
    turns.append({"role": "assistant", "content": response.content, "timestamp": now})

    return {
        "role": context["role"],
        "intent": intent,
        "answer": response.content,
        "conversation_history": turns,
        "metadata": {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "model": response.model,
            "provider": response.provider,
            "rule_based": response.rule_based,
            "context_scope": context["scope"],
            "generated_at": now,
            "disclaimer": DISCLAIMER,
        },
    }

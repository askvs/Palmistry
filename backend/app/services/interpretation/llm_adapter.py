"""LLM adapter layer for the AI Interpretation Engine (Spec Module 5, TASK-008)."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_ENGINE_NAME = "LLMAdapter"
_ENGINE_VERSION = "1.0.0"

# Rate-limited requests are retried with a bounded backoff before falling back.
_RATE_LIMIT_RETRIES = 2
_RATE_LIMIT_BACKOFF_SECONDS = (2.0, 5.0)


def _is_rate_limit_error(exc: Exception) -> bool:
    """Detect provider rate limiting (HTTP 429) without importing SDK-specific errors."""
    if getattr(exc, "status_code", None) == 429:
        return True
    text = str(exc).lower()
    return "429" in text and ("rate limit" in text or "too many requests" in text)


def _describe_failure(exc: Exception) -> str:
    """Human-readable, non-sensitive reason for falling back to the rule engine."""
    if _is_rate_limit_error(exc):
        return "the provider rate limit was reached"
    return f"the provider request failed ({type(exc).__name__})"


class LLMError(Exception):
    """LLM adapter failure mapped to the standard error envelope (§49.14)."""

    def __init__(self, message: str, *, code: str = "LLM_ADAPTER_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class LLMResponse:
    """Structured response from an LLM completion call."""

    def __init__(self, content: str, model: str, provider: str, *, rule_based: bool = False, tokens: int = 0):
        self.content = content
        self.model = model
        self.provider = provider
        self.rule_based = rule_based
        self.tokens = tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "rule_based": self.rule_based,
            "tokens": self.tokens,
        }


class LLMAdapter:
    """Adapter that selects between OpenAI (online), Groq (online), or a deterministic rule engine."""

    def __init__(self) -> None:
        self._client = None
        self._provider = "rule_based"
        self._model = "rulebook-1.0.0"
        self._fallback_reason = ""
        self._api_key = (settings.OPENAI_API_KEY or "").strip()
        self._groq_api_key = (settings.GROQ_API_KEY or "").strip()
        self._groq_model = settings.GROQ_MODEL or "llama3-8b-8192"

        # Initialize OpenAI if API key provided
        if self._api_key:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI(api_key=self._api_key)
                self._provider = "openai"
                self._model = settings.OPENAI_MODEL or "gpt-4o-mini"
                logger.info("LLM adapter initialized with OpenAI provider (model=%s)", self._model)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to initialize OpenAI client: %s", exc)
                self._client = None

        # Initialize Groq if API key provided and OpenAI not available
        if not self._client and self._groq_api_key:
            try:
                from groq import Groq  # type: ignore

                self._client = Groq(api_key=self._groq_api_key)
                self._provider = "groq"
                self._model = self._groq_model
                logger.info("LLM adapter initialized with Groq provider (model=%s)", self._model)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to initialize Groq client: %s", exc)
                self._client = None

        # Fallback to rule-based if no client initialized
        if not self._client:
            logger.info("LLM adapter using rule-based provider (model=%s)", self._model)

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_online(self) -> bool:
        return self._client is not None

    def complete(
        self,
        *,
        prompt: str,
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a completion, retrying rate limits and falling back to the rule engine."""
        if self._client is not None:
            self._fallback_reason = ""
            try:
                # If json_mode requested, ensure "json" is explicitly present in messages
                if json_mode:
                    system_text = system or "You are a wise spiritual interpretation engine that outputs valid JSON."
                    if "json" not in system_text.lower() and "json" not in prompt.lower():
                        system_text += " Respond in JSON format."
                else:
                    system_text = system

                messages: List[Dict[str, str]] = []
                if system_text:
                    messages.append({"role": "system", "content": system_text})
                messages.append({"role": "user", "content": prompt})

                kwargs: Dict[str, Any] = {
                    "model": self._model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if json_mode and self._provider in ("openai", "groq"):
                    kwargs["response_format"] = {"type": "json_object"}

                attempts = _RATE_LIMIT_RETRIES + 1
                for attempt in range(attempts):
                    try:
                        resp = self._client.chat.completions.create(**kwargs)
                        content = resp.choices[0].message.content or ""
                        tokens = getattr(resp.usage, "total_tokens", 0) if resp.usage else 0
                        return LLMResponse(
                            content=content,
                            model=self._model,
                            provider=self._provider,
                            rule_based=False,
                            tokens=tokens,
                        )
                    except Exception as exc:
                        if _is_rate_limit_error(exc) and attempt + 1 < attempts:
                            delay = _RATE_LIMIT_BACKOFF_SECONDS[
                                min(attempt, len(_RATE_LIMIT_BACKOFF_SECONDS) - 1)
                            ]
                            logger.warning(
                                "%s completion rate-limited; retrying in %.1fs (attempt %d/%d)",
                                self._provider.capitalize(),
                                delay,
                                attempt + 1,
                                attempts,
                            )
                            time.sleep(delay)
                            continue
                        logger.warning(
                            "%s completion failed, falling back to rule engine: %s",
                            self._provider.capitalize(),
                            exc,
                        )
                        self._fallback_reason = _describe_failure(exc)
                        break
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "%s completion setup failed, falling back to rule engine: %s",
                    self._provider.capitalize(),
                    exc,
                )
                self._fallback_reason = _describe_failure(exc)

        # Deterministic fallback
        content = self._rule_complete(prompt, system, json_mode=json_mode)
        return LLMResponse(
            content=content,
            model=self._model,
            provider=self._provider,
            rule_based=True,
            tokens=len(content.split()),
        )

    def _rule_complete(self, prompt: str, system: str, *, json_mode: bool = False) -> str:
        """Produce a deterministic, structured fallback payload."""
        digest = hashlib.sha256((system + "\n" + prompt).encode("utf-8")).hexdigest()[:12]
        if self._client is None:
            reason = "no external language model credentials are configured"
            remedy = "Set GROQ_API_KEY or OPENAI_API_KEY to enable online interpretation generation."
        else:
            reason = self._fallback_reason or "the external language model request did not succeed"
            remedy = "Please try again in a moment."
        if json_mode:
            return json.dumps(
                {
                    "rule_based": True,
                    "request_digest": digest,
                    "provider": self._provider,
                    "model": self._model,
                    "guidance": [
                        "Reflect on the symbols drawn and consider how they mirror your current life chapter.",
                        "Approach the reading as interpretive guidance for self-reflection, not as guaranteed fact.",
                    ],
                    "narrative": (
                        "This interpretation was generated by the deterministic rule engine "
                        f"because {reason}. {remedy}"
                    ),
                    "disclaimer": (
                        "All insights are offered strictly for interpretive guidance, entertainment, "
                        "and self-reflection. They are not medical diagnoses, legal facts, or guaranteed "
                        "financial advice."
                    ),
                },
                ensure_ascii=False,
            )
        return (
            f"[rule-based fallback] request_digest={digest}\n"
            f"This response was generated by the deterministic rule engine because {reason}. {remedy}"
        )


_ADAPTER: Optional[LLMAdapter] = None


def get_llm_adapter() -> LLMAdapter:
    """Return a process-wide singleton LLM adapter instance."""
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = LLMAdapter()
    return _ADAPTER


def reset_llm_adapter() -> None:
    """Reset the singleton (used by tests)."""
    global _ADAPTER
    _ADAPTER = None

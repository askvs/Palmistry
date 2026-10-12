"""AI Interpretation Engine (Spec Module 5, TASK-008)."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional

from app.services.interpretation.llm_adapter import (
    LLMAdapter,
    LLMError,
    LLMResponse,
    get_llm_adapter,
)
from app.services.tarot.interpretation import (
    SAFETY_DISCLAIMER as TAROT_SAFETY_DISCLAIMER,
    TarotInterpretationError,
)
from app.services.palm_analysis.catalog import get_palm_lines_catalog, get_palm_mounts_catalog

ENGINE_NAME = "AIInterpretationEngine"
ENGINE_VERSION = "1.0.0"
MODEL_NAME = "palmistry-ai-1.0.0"
MODEL_VERSION = "1.0.0"

LLM_SAFETY_DISCLAIMER = (
    "All palmistry, tarot, health, career, and life-trend insights presented in this "
    "interpretation are offered strictly for interpretive guidance, entertainment, "
    "and self-reflection. They do not constitute medical advice, legal counsel, or "
    "guaranteed financial forecasts (Spec §49.19)."
)


class InterpretationError(Exception):
    """Interpretation engine failure mapped to the standard error envelope (§49.14)."""

    def __init__(self, message: str, *, code: str = "INTERPRETATION_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class InterpretationNotReady(InterpretationError):
    def __init__(self, message: str = "Interpretation data is not ready for AI processing."):
        super().__init__(message, code="INTERPRETATION_NOT_READY", status_code=422)


def _load_context_data() -> Dict[str, Any]:
    """Load reference catalogs for retrieval-grounded interpretation."""
    lines_catalog = get_palm_lines_catalog()
    mounts_catalog = get_palm_mounts_catalog()
    return {
        "lines": lines_catalog,
        "mounts": mounts_catalog,
    }


def _extract_palm_signals(palm_data: Dict[str, Any]) -> str:
    """Extract interpretive signals from palm analysis for prompt construction."""
    signals: List[str] = []
    palm_shape = palm_data.get("palm_shape", {})
    element = palm_shape.get("element", "Unknown")
    signals.append(f"Elemental hand type: {element}")

    lines = palm_data.get("lines", [])
    if isinstance(lines, list):
        for line in lines:
            if isinstance(line, dict):
                name = line.get("name", line.get("line_id", ""))
                conf = line.get("confidence", 0.0)
                variation = line.get("variation_type", "standard")
                interpretation = line.get("interpretation", "")
                signals.append(f"{name}: confidence={conf:.0%}, pattern={variation}, meaning={interpretation}")

    mounts = palm_data.get("mounts", [])
    if isinstance(mounts, list):
        prominent = [m for m in mounts if isinstance(m, dict) and m.get("prominence") == "prominent"]
        if prominent:
            names = ", ".join(m.get("name", "") for m in prominent)
            signals.append(f"Prominent mounts: {names}")

    metadata = palm_data.get("metadata", {})
    overall_conf = metadata.get("overall_confidence", 0.0)
    signals.append(f"Overall analysis confidence: {overall_conf:.0%}")

    finger = palm_data.get("finger_structure", {})
    digit_ratio = finger.get("digit_ratio_2d_4d", 0.0)
    signals.append(f"Digit ratio (2D:4D): {digit_ratio:.3f}")

    return "; ".join(signals)


def _extract_tarot_signals(tarot_data: Dict[str, Any]) -> str:
    """Extract interpretive signals from tarot interpretation for prompt construction."""
    signals: List[str] = []
    spread_name = tarot_data.get("spread_name", "Unknown")
    card_count = tarot_data.get("card_count", 0)
    signals.append(f"Spread: {spread_name} ({card_count} cards)")

    domain = tarot_data.get("domain_focus")
    if domain:
        signals.append(f"Domain focus: {domain}")

    cards = tarot_data.get("cards", [])
    if isinstance(cards, list):
        for card in cards[:5]:
            if isinstance(card, dict):
                name = card.get("card_name", "")
                orientation = card.get("orientation", "upright")
                arcana = card.get("arcana", "")
                signals.append(f"{name} ({arcana}, {orientation})")

    narrative = tarot_data.get("narrative", {})
    if isinstance(narrative, dict):
        summary = narrative.get("summary", "")
        if summary:
            signals.append(f"Narrative summary: {summary}")

    analysis = tarot_data.get("analysis", {})
    if isinstance(analysis, dict):
        arcana_balance = analysis.get("arcana_balance", {})
        if arcana_balance:
            major = arcana_balance.get("major_arcana", 0)
            signals.append(f"Major Arcana count: {major}")

    metadata = tarot_data.get("metadata", {})
    if isinstance(metadata, dict):
        rule_based = metadata.get("rule_based", True)
        signals.append(f"Tarot engine rule_based={rule_based}")

    return "; ".join(signals)


def _build_palm_prompt(
    palm_data: Dict[str, Any],
    question: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Construct a structured prompt for palm interpretation."""
    signals = _extract_palm_signals(palm_data)
    element = palm_data.get("palm_shape", {}).get("element", "Unknown")
    lines = palm_data.get("lines", [])
    mounts = palm_data.get("mounts", [])

    prompt_lines: List[str] = [
        "You are a wise palmistry interpreter. Analyze the following palm data and generate a personalized, insightful interpretation.",
        "",
        "Palm Analysis Data:",
        f"Elemental hand type: {element}",
        f"Analysis confidence: {palm_data.get('metadata', {}).get('overall_confidence', 0.0):.0%}",
        "",
        "Lines detected:",
    ]
    if isinstance(lines, list):
        for line in lines:
            if isinstance(line, dict):
                name = line.get("name", line.get("line_id", ""))
                conf = line.get("confidence", 0.0)
                variation = line.get("variation_type", "standard")
                interpretation = line.get("interpretation", "")
                prompt_lines.append(f"  - {name}: confidence={conf:.0%}, pattern={variation}")
                if interpretation:
                    prompt_lines.append(f"    Meaning: {interpretation}")

    prompt_lines.append("")
    prompt_lines.append("Mounts:")
    if isinstance(mounts, list):
        for mount in mounts:
            if isinstance(mount, dict):
                name = mount.get("name", mount.get("mount_id", ""))
                prominence = mount.get("prominence", "balanced")
                score = mount.get("score", 0.5)
                meaning = mount.get("meaning", "")
                prompt_lines.append(f"  - {name}: prominence={prominence} (score={score:.0%})")
                if meaning:
                    prompt_lines.append(f"    Meaning: {meaning}")

    prompt_lines.append("")
    prompt_lines.append(f"Additional signals: {signals}")

    if question:
        prompt_lines.append("")
        prompt_lines.append(f"The user's question is: '{question}'")
        prompt_lines.append("Please address the question directly within your interpretation.")

    prompt_lines.append("")
    prompt_lines.append("Generate a personalized palm interpretation that:")
    prompt_lines.append("1. Describes what the palm reveals about the person's character and life path")
    prompt_lines.append("2. Offers actionable guidance based on the elemental hand type and line patterns")
    prompt_lines.append("3. Provides domain-specific insights (love, career, or spiritual) if a question is given")
    prompt_lines.append("4. Maintains the ethical disclaimer tone")
    prompt_lines.append("")
    prompt_lines.append("Return the interpretation as a JSON object with keys:")
    prompt_lines.append("- 'summary': a concise one-line summary of the palm reading")
    prompt_lines.append("- 'body': a detailed paragraph of interpretation")
    prompt_lines.append("- 'guidance': a list of 2-4 personalized guidance points")
    prompt_lines.append("- 'domain_insights': a dict mapping domain names to insight paragraphs")

    return "\n".join(prompt_lines)


def _build_tarot_prompt(
    tarot_data: Dict[str, Any],
    question: Optional[str] = None,
) -> str:
    """Construct a structured prompt for enhanced tarot interpretation."""
    signals = _extract_tarot_signals(tarot_data)
    spread_name = tarot_data.get("spread_name", "Unknown")
    card_count = tarot_data.get("card_count", 0)
    narrative = tarot_data.get("narrative", {})
    domain = tarot_data.get("domain_focus")

    prompt_lines: List[str] = [
        "You are a master tarot interpreter. Enhance and deepen the following tarot reading with AI-powered insights.",
        "",
        "Tarot Reading Data:",
        f"Spread: {spread_name} ({card_count} cards)",
    ]
    if domain:
        prompt_lines.append(f"Domain focus: {domain}")

    cards = tarot_data.get("cards", [])
    if isinstance(cards, list):
        for card in cards[:10]:
            if isinstance(card, dict):
                name = card.get("card_name", "")
                orientation = card.get("orientation", "upright")
                position_name = card.get("position_name", "")
                keywords = card.get("keywords", [])
                core_meaning = card.get("core_meaning", "")
                domain_guidance = card.get("domain_guidance", [])
                prompt_lines.append(f"  - {name} [{orientation}] in '{position_name}'")
                if keywords:
                    prompt_lines.append(f"    Keywords: {', '.join(keywords[:3])}")
                if core_meaning:
                    prompt_lines.append(f"    Core meaning: {core_meaning[:100]}")
                if domain_guidance:
                    dg_texts = [g.get("text", "") for g in domain_guidance if isinstance(g, dict) and g.get("text")]
                    if dg_texts:
                        prompt_lines.append(f"    Domain guidance: {'; '.join(dg_texts[:2])}")

    if isinstance(narrative, dict):
        opening = narrative.get("opening", "")
        closing = narrative.get("closing", "")
        if opening:
            prompt_lines.append(f"\nNarrative opening: {opening}")
        if closing:
            prompt_lines.append(f"\nNarrative closing: {closing}")

    prompt_lines.append(f"\nAdditional signals: {signals}")

    if question:
        prompt_lines.append(f"\nThe user's question is: '{question}'")

    prompt_lines.append("")
    prompt_lines.append("Enhance this reading by providing:")
    prompt_lines.append("1. A deeper narrative that weaves the cards together with psychological and spiritual insight")
    prompt_lines.append("2. Contextual guidance that addresses the user's question directly")
    prompt_lines.append("3. A 'wisdom_points' list of 3-5 concise takeaways")
    prompt_lines.append("4. An 'action_plan' with 3 actionable steps")
    prompt_lines.append("")
    prompt_lines.append("Return the enhancement as a JSON object with keys:")
    prompt_lines.append("- 'deep_narrative': enriched narrative text")
    prompt_lines.append("- 'wisdom_points': list of concise takeaways")
    prompt_lines.append("- 'action_plan': list of actionable steps")
    prompt_lines.append("- 'contextual_insight': paragraph connecting the reading to the user's life context")

    return "\n".join(prompt_lines)


def _build_synthesis_prompt(
    palm_data: Dict[str, Any],
    tarot_data: Dict[str, Any],
    question: Optional[str] = None,
) -> str:
    """Construct a structured prompt for reading synthesis (palm + tarot)."""
    palm_signals = _extract_palm_signals(palm_data)
    tarot_signals = _extract_tarot_signals(tarot_data)

    prompt_lines: List[str] = [
        "You are a holistic spiritual interpreter. Synthesize a palm reading and a tarot reading into a unified, coherent life narrative.",
        "",
        "=== PALM READING ===",
        f"Elemental hand: {palm_data.get('palm_shape', {}).get('element', 'Unknown')}",
        f"Confidence: {palm_data.get('metadata', {}).get('overall_confidence', 0.0):.0%}",
        f"Palm signals: {palm_signals}",
        "",
        "=== TAROT READING ===",
        f"Spread: {tarot_data.get('spread_name', 'Unknown')} ({tarot_data.get('card_count', 0)} cards)",
        f"Domain: {tarot_data.get('domain_focus', 'General')}",
        f"Tarot signals: {tarot_signals}",
    ]

    if question:
        prompt_lines.append(f"\nUser's question: '{question}'")

    prompt_lines.append("")
    prompt_lines.append("Synthesize these two readings into:")
    prompt_lines.append("1. A unified 'life_narrative' paragraph that weaves palm and tarot themes together")
    prompt_lines.append("2. 'cross_references': a list of connections between palm and tarot symbols")
    prompt_lines.append("3. 'integrated_guidance': 3-5 holistic guidance points that address both readings")
    prompt_lines.append("4. 'growth_areas': areas for personal development highlighted by both readings")
    prompt_lines.append("5. 'overall_confidence': a holistic confidence score (0-100) based on both readings")
    prompt_lines.append("")
    prompt_lines.append("Return as a JSON object.")

    return "\n".join(prompt_lines)


def generate_palm_interpretation(
    palm_data: Dict[str, Any],
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate AI-powered palm interpretation (FR-017)."""
    if not palm_data or not isinstance(palm_data, dict):
        raise InterpretationNotReady("Palm analysis data is required for interpretation.")

    adapter = get_llm_adapter()
    context_data = _load_context_data()
    prompt = _build_palm_prompt(palm_data, question=question, context_data=context_data)

    system_prompt = (
        "You are a wise, compassionate palmistry interpreter grounded in the "
        "Rider-Waite-Smith symbolic tradition. Your interpretations are "
        "analytical yet accessible. Never present interpretations as guaranteed "
        "facts. Always include the ethical disclaimer in your guidance."
    )

    response = adapter.complete(
        prompt=prompt,
        system=system_prompt,
        max_tokens=1500,
        temperature=0.7,
        json_mode=True,
    )

    return _parse_interpretation_response(response, palm_data)


def generate_tarot_interpretation(
    tarot_data: Dict[str, Any],
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate AI-powered tarot interpretation enhancement."""
    if not tarot_data or not isinstance(tarot_data, dict):
        raise InterpretationNotReady("Tarot interpretation data is required for AI enhancement.")

    adapter = get_llm_adapter()
    prompt = _build_tarot_prompt(tarot_data, question=question)

    system_prompt = (
        "You are a master tarot interpreter who deepens rule-based readings with "
        "psychological and spiritual insight. Enhance the existing interpretation "
        "without contradicting it. Never present insights as guaranteed facts."
    )

    response = adapter.complete(
        prompt=prompt,
        system=system_prompt,
        max_tokens=2000,
        temperature=0.7,
        json_mode=True,
    )

    return _parse_tarot_enhancement(response, tarot_data)


def generate_reading_synthesis(
    palm_data: Dict[str, Any],
    tarot_data: Dict[str, Any],
    question: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a unified synthesis of palm and tarot readings."""
    if not palm_data or not isinstance(palm_data, dict):
        raise InterpretationNotReady("Palm analysis data is required for synthesis.")
    if not tarot_data or not isinstance(tarot_data, dict):
        raise InterpretationNotReady("Tarot interpretation data is required for synthesis.")

    adapter = get_llm_adapter()
    prompt = _build_synthesis_prompt(palm_data, tarot_data, question=question)

    system_prompt = (
        "You are a holistic spiritual interpreter who synthesizes palm and tarot "
        "readings into a unified narrative. Respect both modalities equally. "
        "Highlight meaningful connections between the two systems. "
        "Never present synthesis as guaranteed fact."
    )

    response = adapter.complete(
        prompt=prompt,
        system=system_prompt,
        max_tokens=2500,
        temperature=0.7,
        json_mode=True,
    )

    return _parse_synthesis_response(response, palm_data, tarot_data)


def _clean_json_str(raw: str) -> str:
    """Strip markdown backticks (```json ... ```) or whitespace from LLM text."""
    text = raw.strip()
    if text.startswith("```"):
        # Strip ```json or ```
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _parse_interpretation_response(response: LLMResponse, palm_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the LLM response into a structured interpretation result."""
    try:
        content = _clean_json_str(response.content)
        # Try to find JSON in the response
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(content[json_start:json_end])
        else:
            parsed = {"summary": "", "body": content, "guidance": [], "domain_insights": {}}
    except (json.JSONDecodeError, ValueError):
        parsed = {"summary": "", "body": response.content, "guidance": [], "domain_insights": {}}

    meta = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": LLM_SAFETY_DISCLAIMER,
    }

    return {
        "interpretation_type": "palm",
        "summary": parsed.get("summary", "A palm interpretation was generated."),
        "body": parsed.get("body", response.content),
        "guidance": parsed.get("guidance", []),
        "domain_insights": parsed.get("domain_insights", {}),
        "element": palm_data.get("palm_shape", {}).get("element", "Unknown"),
        "confidence": palm_data.get("metadata", {}).get("overall_confidence", 0.0),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": meta["timestamp"],
        "disclaimer": LLM_SAFETY_DISCLAIMER,
        "metadata": meta,
    }


def _parse_tarot_enhancement(response: LLMResponse, tarot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the LLM enhancement response into structured enhancement data."""
    try:
        content = _clean_json_str(response.content)
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(content[json_start:json_end])
        else:
            parsed = {"deep_narrative": "", "wisdom_points": [], "action_plan": []}
    except (json.JSONDecodeError, ValueError):
        parsed = {"deep_narrative": response.content, "wisdom_points": [], "action_plan": []}

    meta = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": TAROT_SAFETY_DISCLAIMER,
    }

    return {
        "interpretation_type": "tarot_enhancement",
        "spread_name": tarot_data.get("spread_name", "Unknown"),
        "deep_narrative": parsed.get("deep_narrative", ""),
        "wisdom_points": parsed.get("wisdom_points", []),
        "action_plan": parsed.get("action_plan", []),
        "contextual_insight": parsed.get("contextual_insight", ""),
        "domain_focus": tarot_data.get("domain_focus"),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": meta["timestamp"],
        "disclaimer": TAROT_SAFETY_DISCLAIMER,
        "metadata": meta,
    }


def _parse_synthesis_response(
    response: LLMResponse, palm_data: Dict[str, Any], tarot_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Parse the synthesis response into a unified reading result."""
    try:
        content = _clean_json_str(response.content)
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            parsed = json.loads(content[json_start:json_end])
        else:
            parsed = {"life_narrative": "", "cross_references": [], "integrated_guidance": []}
    except (json.JSONDecodeError, ValueError):
        parsed = {"life_narrative": response.content, "cross_references": [], "integrated_guidance": []}

    palm_conf = palm_data.get("metadata", {}).get("overall_confidence", 0.5)
    tarot_conf = tarot_data.get("metadata", {}).get("overall_relevance", 0.5)
    overall_conf = round((palm_conf * 0.3 + tarot_conf * 0.25 + 0.45) * 100, 1)

    meta = {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "disclaimer": LLM_SAFETY_DISCLAIMER,
    }

    return {
        "interpretation_type": "synthesis",
        "life_narrative": parsed.get("life_narrative", "A unified interpretation was generated."),
        "cross_references": parsed.get("cross_references", []),
        "integrated_guidance": parsed.get("integrated_guidance", []),
        "growth_areas": parsed.get("growth_areas", []),
        "overall_confidence": overall_conf,
        "palm_element": palm_data.get("palm_shape", {}).get("element", "Unknown"),
        "tarot_domain": tarot_data.get("domain_focus", "General"),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "model": response.model,
        "provider": response.provider,
        "rule_based": response.rule_based,
        "timestamp": meta["timestamp"],
        "disclaimer": LLM_SAFETY_DISCLAIMER,
        "metadata": meta,
    }

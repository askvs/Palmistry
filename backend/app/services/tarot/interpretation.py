"""Tarot card interpretation engine (Spec FR-016, TASK-007)."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.services.tarot.catalog import (
    draw_spread,
    get_card_by_id,
    get_spread_by_id,
    get_tarot_deck,
    get_tarot_spreads,
)

ENGINE_NAME = "TarotInterpretationEngine"
ENGINE_VERSION = "1.0.0"
MODEL_NAME = "rider-waite-rulebook"
MODEL_VERSION = "1.0.0"

SAFETY_DISCLAIMER = (
    "Tarot interpretations are offered as interpretive guidance for self-reflection "
    "and entertainment. They are never medical diagnoses, legal facts, or guaranteed "
    "financial advice (Spec \u00a749.19)."
)

SUIT_ELEMENTS = {"wands": "Fire", "cups": "Water", "swords": "Air", "pentacles": "Earth"}
CLASSICAL_ELEMENTS = ("Fire", "Water", "Air", "Earth")

DOMINANT_ELEMENT_TONE = {
    "Fire": "drive, ambition, creative passion, and bold action",
    "Water": "emotion, intuition, relationships, and inner flow",
    "Air": "thought, communication, intellect, and decision-making",
    "Earth": "material stability, health, finances, and grounded effort",
}
MISSING_ELEMENT_HINT = {
    "Fire": "momentum and passion may need conscious ignition",
    "Water": "feelings may be under-expressed and deserve more attention",
    "Air": "clarity and honest communication may be lacking",
    "Earth": "practical grounding and material planning may need reinforcement",
}

SPREAD_CATEGORY_DOMAIN = {
    "interpersonal": "love",
    "professional": "career",
    "spiritual_evolution": "spiritual",
}
DOMAIN_LABELS = {
    "love": "Love & Relationships",
    "career": "Career & Ambition",
    "spiritual": "Spiritual Growth",
}
DOMAIN_KEYS = {
    "love": ("love", "love_reversed"),
    "career": ("career", "career_reversed"),
    "spiritual": ("spiritual", "spiritual_reversed"),
}

QUESTION_HINTS = {
    "love": (
        "love", "romance", "relationship", "partner", "marriage", "crush",
        "dating", "heart", "soulmate", "ex",
    ),
    "career": (
        "career", "job", "work", "business", "money", "finance", "promotion",
        "office", "profession", "salary", "project",
    ),
    "spiritual": (
        "spiritual", "soul", "purpose", "path", "growth", "meditation",
        "karma", "enlighten", "destiny", "universe",
    ),
}

NUMBER_MEANINGS = {
    0: "infinite potential and the Fool's leap of faith",
    1: "new beginnings and raw potential",
    2: "balance, choice, and partnership",
    3: "growth, creativity, and collaboration",
    4: "stability, structure, and solid foundations",
    5: "change, challenge, and healthy disruption",
    6: "harmony, reciprocity, and adjustment",
    7: "reflection, strategy, and inner assessment",
    8: "mastery, movement, and personal power",
    9: "culmination, wisdom, and near-completion",
    10: "completion, cycles closing, and renewal",
}


class TarotInterpretationError(Exception):
    """Interpretation failure mapped to the standard error envelope (§49.14)."""

    def __init__(self, message: str, *, code: str = "TAROT_INTERPRETATION_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _resolve_spread(spread_ref: str) -> dict[str, Any] | None:
    spread = get_spread_by_id(spread_ref)
    if spread:
        return spread
    wanted = _normalize(spread_ref)
    if not wanted:
        return None
    for candidate in get_tarot_spreads():
        if _normalize(candidate["id"]) == wanted:
            return candidate
        name_variants = {_normalize(candidate["name"])}
        base_name = candidate["name"].split(" (")[0]
        name_variants.add(_normalize(base_name))
        if wanted in name_variants or (len(wanted) >= 4 and _normalize(base_name).startswith(wanted)):
            return candidate
    return None


def _synthetic_spread(spread_ref: str, count: int) -> dict[str, Any]:
    safe_count = max(1, count)
    return {
        "id": _normalize(spread_ref) or "custom",
        "name": spread_ref or "Custom Spread",
        "spec_requirement": None,
        "card_count": safe_count,
        "category": "custom",
        "description": "Free-form spread resolved from the provided card selection.",
        "positions": [
            {
                "position": i + 1,
                "name": f"Card {i + 1}",
                "description": "Free-form card placement carrying its own significance.",
                "layout_coordinate": {"x": (i + 1) / (safe_count + 1), "y": 0.5},
            }
            for i in range(safe_count)
        ],
        "interpretation_order": list(range(1, safe_count + 1)),
    }


def _resolve_card(card_ref: str) -> dict[str, Any] | None:
    card = get_card_by_id(card_ref)
    if card:
        return card
    wanted = _normalize(card_ref)
    if not wanted:
        return None
    for candidate in get_tarot_deck("rider_waite_smith")["cards"]:
        if _normalize(candidate["name"]) == wanted:
            return candidate
    return None


def _element_of(card: dict[str, Any]) -> str | None:
    if card.get("suit") in SUIT_ELEMENTS:
        return SUIT_ELEMENTS[card["suit"]]
    return card.get("element")


def _detect_question_domain(question: str | None) -> str | None:
    if not question:
        return None
    lowered = question.lower()
    scores = {domain: sum(1 for hint in hints if hint in lowered) for domain, hints in QUESTION_HINTS.items()}
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else None


def _domain_guidance(card: dict[str, Any], is_reversed: bool, domain: str | None) -> list[dict[str, str]]:
    domains = card.get("domains", {})
    if domain:
        keys = DOMAIN_KEYS[domain]
        text = domains.get(keys[1] if is_reversed else keys[0]) or domains.get(keys[0])
        if text:
            return [{"domain": domain, "label": DOMAIN_LABELS[domain], "text": text}]
        return []
    guidance = []
    for domain_key, (upright_key, reversed_key) in DOMAIN_KEYS.items():
        text = domains.get(reversed_key if is_reversed else upright_key) or domains.get(upright_key)
        if text:
            guidance.append({"domain": domain_key, "label": DOMAIN_LABELS[domain_key], "text": text})
    return guidance


def _card_relevance(card: dict[str, Any], domain_guidance: list[dict[str, str]]) -> float:
    checks = [
        bool(card.get("upright_meaning")),
        bool(card.get("reversed_meaning")),
        bool(card.get("keywords_upright")),
        bool(card.get("keywords_reversed")),
        bool(card.get("fortune_telling")),
        bool(card.get("meanings_light")),
        bool(card.get("meanings_shadow")),
        bool(domain_guidance),
    ]
    return round(sum(checks) / len(checks), 3)


def interpret_card(
    card: dict[str, Any],
    position: dict[str, Any],
    is_reversed: bool,
    domain: str | None = None,
) -> dict[str, Any]:
    """Produce a position-aware, orientation-aware interpretation for one card."""
    keywords = card["keywords_reversed"] if is_reversed else card["keywords_upright"]
    core_meaning = card["reversed_meaning"] if is_reversed else card["upright_meaning"]
    guidance = _domain_guidance(card, is_reversed, domain)
    keyword_preview = ", ".join(keywords[:3]) if keywords else core_meaning
    if is_reversed:
        position_context = (
            f"Positioned as '{position['name']}', the reversed {card['name']} asks you to "
            f"re-examine {keyword_preview} within this area of your inquiry."
        )
    else:
        position_context = (
            f"Positioned as '{position['name']}', {card['name']} channels "
            f"{keyword_preview} into this area of your inquiry."
        )

    expanded = card.get("meanings_shadow") if is_reversed else card.get("meanings_light")

    return {
        "position": position["position"],
        "position_name": position["name"],
        "position_description": position["description"],
        "card_id": card["id"],
        "card_name": card["name"],
        "number": card["number"],
        "arcana": card["arcana"],
        "suit": card.get("suit"),
        "element": _element_of(card),
        "is_reversed": is_reversed,
        "orientation": "reversed" if is_reversed else "upright",
        "keywords": keywords,
        "core_meaning": core_meaning,
        "position_context": position_context,
        "domain_guidance": guidance,
        "fortune_telling": card.get("fortune_telling", []),
        "expanded_meanings": list(expanded[:3]) if expanded else [],
        "image_path": card.get("image_path"),
        "relevance": _card_relevance(card, guidance),
    }


def _arcana_balance(card_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(card_results)
    major = sum(1 for c in card_results if c["arcana"] == "major")
    minor = total - major
    share = major / total if total else 0.0
    if major == total:
        narrative = (
            "The draw is composed entirely of Major Arcana: powerful, fated forces "
            "are at work, and the situation reaches beyond everyday control."
        )
    elif share >= 0.5:
        narrative = (
            f"Major Arcana lead this spread ({major} of {total}): significant life themes "
            "and karmic momentum dominate the situation."
        )
    elif major > 0:
        narrative = (
            f"A few Major Arcana appear ({major} of {total}): practical matters prevail, "
            "but key turning points carry deeper significance."
        )
    else:
        narrative = (
            "No Major Arcana appear: the situation is governed by everyday choices, "
            "practical energies, and personal agency."
        )
    return {
        "major_arcana": major,
        "minor_arcana": minor,
        "major_ratio": round(share, 3),
        "narrative": narrative,
    }


def _elemental_balance(card_results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(e for c in card_results if (e := c.get("element")) in CLASSICAL_ELEMENTS)
    dominant = max(CLASSICAL_ELEMENTS, key=lambda e: counts.get(e, 0)) if counts else None
    missing = [e for e in CLASSICAL_ELEMENTS if counts.get(e, 0) == 0]

    parts: list[str] = []
    if dominant and counts.get(dominant, 0) > 0:
        parts.append(
            f"{dominant} energy dominates ({counts[dominant]} of {len(card_results)} cards), "
            f"coloring the reading with {DOMINANT_ELEMENT_TONE[dominant]}."
        )
    else:
        parts.append("The four classical elements are thinly represented, suggesting an unsettled mix of energies.")
    for element in missing:
        parts.append(f"The absence of {element} suggests that {MISSING_ELEMENT_HINT[element]}.")
    return {
        "counts": {element: counts.get(element, 0) for element in CLASSICAL_ELEMENTS},
        "dominant_element": dominant,
        "missing_elements": missing,
        "narrative": " ".join(parts),
    }


def _reversal_analysis(card_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(card_results)
    reversed_count = sum(1 for c in card_results if c["is_reversed"])
    ratio = reversed_count / total if total else 0.0
    if total and reversed_count == 0:
        narrative = "All cards are upright: energies flow outward with clarity and forward momentum."
    elif ratio > 0.5:
        narrative = (
            f"More than half the cards are reversed ({reversed_count} of {total}): much of the "
            "current work is inward, through reflection, release, and integration."
        )
    else:
        narrative = (
            f"A minority of cards are reversed ({reversed_count} of {total}): movement is mostly "
            "forward, with a few areas inviting inner review."
        )
    return {
        "reversed_count": reversed_count,
        "upright_count": total - reversed_count,
        "reversal_ratio": round(ratio, 3),
        "narrative": narrative,
    }


def _numerology_analysis(card_results: list[dict[str, Any]]) -> dict[str, Any]:
    number_counts = Counter(c["number"] for c in card_results)
    repeats = [
        {
            "number": number,
            "count": count,
            "cards": [c["card_name"] for c in card_results if c["number"] == number],
            "meaning": NUMBER_MEANINGS.get(number, f"a shared energetic tone of the number {number}"),
        }
        for number, count in sorted(number_counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]
    if repeats:
        tone = "; ".join(f"{r['count']}x number {r['number']} - {r['meaning']}" for r in repeats)
        narrative = f"Repeating numerological tones amplify key themes: {tone}."
    else:
        narrative = "No repeating numerological tones: each card contributes a distinct vibration."
    return {"repeats": repeats, "narrative": narrative}


def _guidance_lines(card_results: list[dict[str, Any]]) -> list[str]:
    lines = []
    for card in card_results:
        fortune = card.get("fortune_telling") or []
        if fortune:
            lines.append(f"{card['card_name']}: {fortune[0]}")
        elif card["keywords"]:
            lines.append(f"{card['card_name']}: lean into {card['keywords'][0]}.")
    return lines[:4]


def _compose_narrative(
    spread: dict[str, Any],
    card_results: list[dict[str, Any]],
    question: str | None,
    domain: str | None,
    arcana: dict[str, Any],
    elemental: dict[str, Any],
    reversal: dict[str, Any],
    numerology: dict[str, Any],
) -> dict[str, Any]:
    total = len(card_results)
    if question:
        opening = f"You asked: '{question}' Your {spread['name']} ({total} cards) responds below."
    else:
        opening = f"Your {spread['name']} of {total} cards offers the following guidance."

    body = [card["position_context"] for card in card_results]

    if domain:
        focus = []
        for card in card_results:
            for item in card["domain_guidance"]:
                if item["domain"] == domain:
                    focus.append(f"{card['card_name']} brings {item['text']}")
        if focus:
            body.append(f"Focused on {DOMAIN_LABELS[domain].lower()}: " + "; ".join(focus) + ".")

    closing = " ".join([arcana["narrative"], elemental["narrative"], reversal["narrative"], numerology["narrative"]])

    dominant_bits = []
    if arcana["major_arcana"] > 0:
        dominant_bits.append(f"{arcana['major_arcana']} Major Arcana")
    if elemental["dominant_element"]:
        dominant_bits.append(f"{elemental['dominant_element']} dominant")
    if reversal["reversed_count"] > 0:
        dominant_bits.append(f"{reversal['reversed_count']} reversed")
    summary = f"{total}-card {spread['name']}: " + ", ".join(dominant_bits) + "." if dominant_bits else (
        f"{total}-card {spread['name']} drawn."
    )

    return {"opening": opening, "body": body, "closing": closing, "summary": summary[:280]}


def interpret_spread(
    spread: dict[str, Any],
    card_results: list[dict[str, Any]],
    *,
    question: str | None = None,
    deck_id: str = "rider_waite_smith",
    seed: int | None = None,
) -> dict[str, Any]:
    """Assemble the full spread interpretation payload from interpreted cards."""
    domain = _detect_question_domain(question) or SPREAD_CATEGORY_DOMAIN.get(spread.get("category"))
    arcana = _arcana_balance(card_results)
    elemental = _elemental_balance(card_results)
    reversal = _reversal_analysis(card_results)
    numerology = _numerology_analysis(card_results)
    narrative = _compose_narrative(spread, card_results, question, domain, arcana, elemental, reversal, numerology)

    ordered = sorted(card_results, key=lambda c: c["position"])
    relevance = round(sum(c["relevance"] for c in card_results) / len(card_results), 3) if card_results else 0.0

    return {
        "spread_id": spread["id"],
        "spread_name": spread["name"],
        "spread_category": spread.get("category"),
        "card_count": len(card_results),
        "deck_id": deck_id,
        "question": question,
        "domain_focus": domain,
        "cards": ordered,
        "analysis": {
            "arcana_balance": arcana,
            "elemental_balance": elemental,
            "reversal_analysis": reversal,
            "numerology": numerology,
        },
        "narrative": narrative,
        "guidance": _guidance_lines(card_results),
        "disclaimer": SAFETY_DISCLAIMER,
        "metadata": {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "rule_based": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_relevance": relevance,
        },
        "seed": seed,
    }


def interpret_draw(
    *,
    spread_id: str,
    deck_id: str = "rider_waite_smith",
    question: str | None = None,
    allow_reversals: bool = True,
    seed: int | None = None,
    spread_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shuffle, draw, and interpret a spread in one step (FR-013..FR-016)."""
    spread = spread_override or _resolve_spread(spread_id)
    if spread is None:
        raise TarotInterpretationError(
            f"Unknown tarot spread: '{spread_id}'", code="TAROT_UNKNOWN_SPREAD", status_code=400
        )
    try:
        draw = draw_spread(
            spread["id"],
            deck_id=deck_id,
            seed=seed,
            allow_reversals=allow_reversals,
            spread_override=spread if spread_override else None,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise TarotInterpretationError(str(exc), code="TAROT_DRAW_FAILED", status_code=400) from exc

    card_results = []
    domain = _detect_question_domain(question) or SPREAD_CATEGORY_DOMAIN.get(spread.get("category"))
    for index, drawn in enumerate(draw["cards"]):
        card = get_card_by_id(drawn["card_id"], deck_id)
        if card is None:
            raise TarotInterpretationError(
                f"Card '{drawn['card_id']}' missing from deck catalog",
                code="TAROT_UNKNOWN_CARD",
                status_code=400,
            )
        position = {
            "position": index + 1,
            "name": drawn["position_name"],
            "description": drawn["position_description"],
        }
        card_results.append(interpret_card(card, position, drawn["is_reversed"], domain))

    return interpret_spread(spread, card_results, question=question, deck_id=deck_id, seed=seed)


def interpret_explicit_cards(
    *,
    spread_ref: str,
    selections: list[str | dict[str, Any]],
    question: str | None = None,
    deck_id: str = "rider_waite_smith",
    spread_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Interpret a user-selected card sequence (FR-014 card selection workflow)."""
    if not selections:
        raise TarotInterpretationError(
            "At least one card selection is required", code="TAROT_NO_CARDS", status_code=400
        )

    normalized: list[dict[str, Any]] = []
    for item in selections:
        if isinstance(item, str):
            normalized.append({"card": item, "is_reversed": False})
        elif isinstance(item, dict) and isinstance(item.get("card"), str):
            normalized.append({"card": item["card"], "is_reversed": bool(item.get("is_reversed", False))})
        else:
            raise TarotInterpretationError(
                "Each card selection must be a card id/name or {card, is_reversed}",
                code="TAROT_INVALID_SELECTION",
                status_code=400,
            )

    spread = spread_override or _resolve_spread(spread_ref) or _synthetic_spread(spread_ref, len(normalized))
    domain = _detect_question_domain(question) or SPREAD_CATEGORY_DOMAIN.get(spread.get("category"))

    card_results = []
    for index, selection in enumerate(normalized):
        card = _resolve_card(selection["card"])
        if card is None:
            raise TarotInterpretationError(
                f"Unknown tarot card: '{selection['card']}'", code="TAROT_UNKNOWN_CARD", status_code=400
            )
        position = (
            spread["positions"][index]
            if index < len(spread["positions"])
            else _synthetic_spread(spread_ref, len(normalized))["positions"][index]
        )
        card_results.append(interpret_card(card, position, selection["is_reversed"], domain))

    return interpret_spread(spread, card_results, question=question, deck_id=deck_id, seed=None)


def list_decks() -> list[dict[str, Any]]:
    """Summarize available decks for deck selection (FR-012)."""
    deck = get_tarot_deck("rider_waite_smith")
    return [
        {
            "deck_id": deck["deck_id"],
            "name": deck["name"],
            "author": deck.get("author"),
            "description": deck.get("description"),
            "total_cards": deck.get("total_cards"),
            "major_arcana_count": deck.get("major_arcana_count"),
            "minor_arcana_count": deck.get("minor_arcana_count"),
            "suits": deck.get("suits", []),
            "is_default": True,
        }
    ]

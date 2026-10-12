"""Reading report generator (FR-057, FR-058, Spec §49.9, §49.19)."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.models.reading import Reading, ReadingType
from app.models.user import User

REPORT_ENGINE_VERSION = "1.3.0"
ETHICAL_DISCLAIMER = (
    "All palmistry, tarot, health, career, and life-trend insights presented in this report "
    "are offered strictly for interpretive guidance, entertainment, and self-reflection. "
    "They do not constitute medical advice, legal counsel, or guaranteed financial forecasts."
)


def _score_label(score: float) -> str:
    """Score label mapping per Spec §49.9 (0-39 Low, 40-69 Moderate, 70-84 High, 85-100 Very High)."""
    if score < 40:
        return "Low"
    elif score < 70:
        return "Moderate"
    elif score < 85:
        return "High"
    return "Very High"


def build_reading_report(reading: Reading, user: User | None = None) -> Dict[str, Any]:
    """Compile a full reading report dictionary from a Reading database model."""
    created_str = (
        reading.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if getattr(reading, "created_at", None)
        else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    if user and getattr(user, "full_name", None):
        user_name = user.full_name
    elif user and getattr(user, "email", None):
        user_name = user.email
    else:
        user_name = "Seeker"

    result_data = reading.result or {}

    if reading.type == ReadingType.palm or reading.type == "palm":
        return _build_palm_report(reading, user_name, created_str, result_data)
    else:
        return _build_tarot_report(reading, user_name, created_str, result_data)


def _iter_entries(value: Any) -> list[tuple[str | None, dict]]:
    """Normalize the two stored shapes of lines/mounts."""
    if isinstance(value, dict):
        return [(key, val) for key, val in value.items() if isinstance(val, dict)]
    if isinstance(value, list):
        return [(None, entry) for entry in value if isinstance(entry, dict)]
    return []


def _fallback_key(val: dict, fallback: str) -> str:
    key = val.get("line_id") or val.get("mount_id") or val.get("key")
    if key:
        return str(key)
    name = val.get("name")
    if name:
        return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or fallback
    return fallback


def _line_interpretation(name: str, val: dict) -> str:
    # Prefer the pipeline's own interpretation when present.
    if val.get("interpretation"):
        return str(val.get("interpretation"))
    continuity = val.get("continuity")
    variation = val.get("variation_description") or val.get("variation_type")
    significance = val.get("significance")
    parts = [f"The {str(name).lower()} is traced with {continuity} continuity, indicating how steadily its associated energy flows through the seeker's life."] if continuity else [f"Clear formation of the {str(name).lower()} indicating stable vitality."]
    if variation:
        parts.append(f"Observed variation: {variation}.")
    if significance:
        parts.append(str(significance))
    return " ".join(parts)


def _detected_hand(result_data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Prefer a human-readable hand string from any of the stored shapes."""
    hand = result_data.get("hand")
    if isinstance(hand, dict):
        hand = hand.get("preferred_hand") or hand.get("detected_handedness")
    hand = hand or metadata.get("hand")
    if isinstance(hand, str) and hand.strip():
        return hand.strip().title()
    return "Right"


def _reading_common(reading: Reading) -> Dict[str, Any]:
    """Fields shared by every report type: review state, notes, status."""
    reviewed_by = getattr(reading, "reviewed_by", None)
    return {
        "reading_status": str(getattr(getattr(reading, "status", ""), "value", getattr(reading, "status", "")) or ""),
        "reading_notes": getattr(reading, "notes", None) or "",
        "reviewed": reviewed_by is not None,
        "reviewed_by": str(reviewed_by) if reviewed_by else None,
    }


def _palm_guidance(element: str, lines_list: List[Dict[str, Any]], traits: List[str], shape_desc: str) -> List[str]:
    guidance = [
        f"Embrace the grounded strengths of your {element} hand structure in decision making — {shape_desc[:140]}".rstrip(),
        "Channel your mental clarity into structured long-term objectives: pick one measurable goal for the next 30 days.",
        "Maintain balance across creative and practical pursuits; schedule both deep work and restorative reflection.",
    ]
    low_lines = [ln for ln in lines_list if (ln.get("confidence") or 0) < 55 or ln.get("detected") is False]
    if low_lines:
        names = ", ".join(ln.get("name", "") for ln in low_lines[:3])
        guidance.append(
            f"Lines with lower clarity ({names}) are shown honestly rather than guessed — re-scan in soft daylight with the palm flat for a sharper trace."
        )
    if traits:
        guidance.append(f"Your hand traits ({', '.join(traits[:4])}) suggest leaning into collaborative, reflective routines this cycle.")
    guidance.append("Revisit this report after 2–4 weeks of journaling and compare which themes held steady.")
    # Deduplicate while preserving order, cap at 6.
    seen: List[str] = []
    for item in guidance:
        if item not in seen:
            seen.append(item)
    return seen[:6]


def _build_palm_report(
    reading: Reading, user_name: str, created_str: str, result_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate structured Palmistry report (FR-057)."""
    metadata = result_data.get("metadata", {}) or {}
    palm_shape = result_data.get("palm_shape", {}) or {}
    finger_structure = result_data.get("finger_structure", {}) or {}
    hand_block = result_data.get("hand", {}) or {}
    lines = result_data.get("lines", [])
    mounts = result_data.get("mounts", [])
    ai_block = result_data.get("ai_interpretation") or {}
    summary_text = reading.summary or "Palm feature extraction and line biometric analysis."

    overall_conf = float(metadata.get("overall_confidence", 0.85))
    score_100 = round(overall_conf * 100, 1)

    # Standardize lines (dict- or list-shaped source data), preserving CV detail.
    lines_list = []
    for line_key, line_val in _iter_entries(lines):
        key = line_key or _fallback_key(line_val, f"line_{len(lines_list) + 1}")
        name = line_val.get("name") or key.replace("_", " ").title()
        confidence = float(line_val.get("confidence", overall_conf))
        lines_list.append({
            "key": key,
            "name": name,
            "classical_name": line_val.get("classical_name", ""),
            "length": line_val.get("length", "Medium"),
            "length_normalized": line_val.get("length_normalized"),
            "clarity": line_val.get("clarity") or line_val.get("depth_clarity") or ("Visible" if confidence >= 0.5 else "Faint"),
            "depth_clarity": line_val.get("depth_clarity", ""),
            "curve": line_val.get("curve", "Gentle"),
            "curvature": line_val.get("curvature"),
            "continuity": line_val.get("continuity", ""),
            "variation_type": line_val.get("variation_type", ""),
            "variation_description": line_val.get("variation_description", ""),
            "detected": line_val.get("detected", True),
            "confidence": round(confidence * 100, 1),
            "interpretation": line_val.get("interpretation") or _line_interpretation(name, line_val),
            "significance": line_val.get("significance", ""),
        })

    # Standardize mounts (dict- or list-shaped source data), preserving CV detail.
    mounts_list = []
    for mount_key, mount_val in _iter_entries(mounts):
        key = mount_key or _fallback_key(mount_val, f"mount_{len(mounts_list) + 1}")
        m_score = float(mount_val.get("prominence_score", mount_val.get("score", 0.5)))
        mounts_list.append({
            "key": key,
            "name": mount_val.get("name") or key.replace("_", " ").title(),
            "prominence": mount_val.get("prominence", "Normal"),
            "score": round(m_score * 100, 1),
            "element": mount_val.get("element", ""),
            "planetary_ruler": mount_val.get("planetary_ruler", ""),
            "meaning": mount_val.get("meaning", "Balanced development of qualities."),
            "core_attributes": mount_val.get("core_attributes", []) or [],
        })

    element = palm_shape.get("element", "Earth")
    shape_desc = palm_shape.get("description", f"A well-grounded {element} hand indicating pragmatism and stability.")
    traits = palm_shape.get("traits", []) or []

    hand_detail = hand_block if isinstance(hand_block, dict) else {}

    common = _reading_common(reading)

    return {
        "report_id": str(uuid.uuid4()),
        "reading_id": str(reading.id),
        "report_type": "palmistry",
        "title": reading.title or f"Palmistry Biometric Report ({element} Hand)",
        "user_name": user_name,
        "created_at": created_str,
        "summary": summary_text,
        "confidence": {
            "score": score_100,
            "label": _score_label(score_100),
            "raw_confidence": overall_conf,
        },
        "palm_features": {
            "element": element,
            "shape_description": shape_desc,
            "traits": traits,
            "palm_length_to_width": palm_shape.get("palm_ratio", palm_shape.get("aspect_ratio", 1.05)),
            "finger_to_palm_ratio": palm_shape.get("finger_ratio", palm_shape.get("finger_to_palm_ratio", 0.82)),
            "palm_width": palm_shape.get("palm_width"),
            "palm_height": palm_shape.get("palm_height"),
            "aspect_ratio": palm_shape.get("aspect_ratio"),
            "hand_detected": _detected_hand(result_data, metadata),
            "handedness_confidence": hand_detail.get("handedness_confidence"),
            "is_palmar": hand_detail.get("is_palmar", True),
            "landmarks_count": metadata.get("landmarks_count", hand_detail.get("landmarks_count", 21)),
        },
        "finger_structure": {
            "digit_ratio_2d_4d": finger_structure.get("digit_ratio_2d_4d"),
            "digit_ratio_interpretation": finger_structure.get("digit_ratio_interpretation", ""),
            "thumb_angle_degrees": finger_structure.get("thumb_angle_degrees"),
            "thumb_flexibility": finger_structure.get("thumb_flexibility", ""),
            "pinky_trait": finger_structure.get("pinky_trait") or finger_structure.get("pinky_communication_trait", ""),
            "fingers": finger_structure.get("fingers", {}) or {},
        },
        "lines": lines_list,
        "mounts": mounts_list,
        "ai_interpretation": {
            "summary": ai_block.get("summary", "") if isinstance(ai_block, dict) else "",
            "narrative": ai_block.get("narrative", "") if isinstance(ai_block, dict) else "",
            "confidence": ai_block.get("confidence") if isinstance(ai_block, dict) else None,
        } if ai_block else None,
        "actionable_guidance": _palm_guidance(element, lines_list, traits, shape_desc),
        "disclaimer": ETHICAL_DISCLAIMER,
        "engine_metadata": {
            "engine": metadata.get("engine", metadata.get("model_name", "PalmBiometricsCV")),
            "version": metadata.get("model_version", REPORT_ENGINE_VERSION),
            "timestamp_utc": metadata.get("timestamp", datetime.now(timezone.utc).isoformat()),
        },
        **common,
    }


def _normalize_domain_guidance(value: Any) -> List[Dict[str, str]]:
    """Accept the engine's list shape, a legacy dict shape, or nothing."""
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, dict):
                out.append({
                    "domain": str(item.get("domain", "")),
                    "label": str(item.get("label", item.get("domain", ""))),
                    "text": str(item.get("text", "")),
                })
        return out
    if isinstance(value, dict):
        return [{"domain": str(k), "label": str(k).title(), "text": str(v)} for k, v in value.items()]
    return []


def _build_tarot_report(
    reading: Reading, user_name: str, created_str: str, result_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate structured Tarot report (FR-058)."""
    spread_name = result_data.get("spread_name") or reading.title or "Tarot Spread Reading"
    question = result_data.get("question") or "General Life Guidance"
    cards_data = result_data.get("cards") or []
    analysis = result_data.get("analysis") or {}
    synthesis_legacy = result_data.get("synthesis") or {}
    narrative = result_data.get("narrative") or {}
    guidance = result_data.get("guidance") or []
    meta = result_data.get("metadata") or {}
    ai_block = result_data.get("ai_interpretation") or {}

    # Normalize cards: support the full engine shape, the curated shape, and plain strings.
    normalized_cards = []
    for idx, card in enumerate(cards_data):
        if isinstance(card, dict):
            c_name = card.get("card_name") or card.get("name") or f"Card {idx+1}"
            is_rev = bool(card.get("is_reversed", False)) or card.get("orientation") == "reversed"
            pos_info = card.get("position") or {}
            if isinstance(pos_info, dict):
                pos_name = card.get("position_name") or pos_info.get("name") or f"Position {idx+1}"
                pos_meaning = (
                    card.get("position_description")
                    or card.get("position_meaning")
                    or pos_info.get("description")
                    or pos_info.get("meaning")
                    or "Current influence"
                )
            else:
                pos_name = card.get("position_name") or str(pos_info or f"Position {idx+1}")
                pos_meaning = card.get("position_description") or card.get("position_meaning") or "Current influence"
            interpretation = (
                card.get("position_context")
                or card.get("core_meaning")
                or card.get("interpretation")
                or card.get("meaning")
                or ""
            )
            keywords = card.get("keywords") or card.get("keywords_upright") or []
            domain_advice = _normalize_domain_guidance(card.get("domain_guidance"))

            normalized_cards.append({
                "index": card.get("position", idx + 1) if isinstance(card.get("position"), int) else idx + 1,
                "card_id": card.get("card_id") or card.get("id") or f"card-{idx}",
                "name": c_name,
                "number": card.get("number"),
                "arcana": card.get("arcana", "Major Arcana"),
                "suit": card.get("suit", "None"),
                "element": card.get("element", ""),
                "orientation": "Reversed" if is_rev else "Upright",
                "is_reversed": is_rev,
                "position_name": pos_name,
                "position_meaning": pos_meaning,
                "keywords": keywords if isinstance(keywords, list) else [str(keywords)],
                "interpretation": interpretation,
                "core_meaning": card.get("core_meaning", ""),
                "position_context": card.get("position_context", ""),
                "domain_guidance": domain_advice,
                "fortune_telling": card.get("fortune_telling", []) or [],
                "expanded_meanings": card.get("expanded_meanings", []) or [],
                "relevance": card.get("relevance"),
                "image_path": card.get("image_path"),
            })
        elif isinstance(card, str):
            is_rev = card.endswith("_rev") or card.endswith(" (Reversed)")
            clean_name = card.replace("_rev", "").replace(" (Reversed)", "").replace("_", " ").title()
            normalized_cards.append({
                "index": idx + 1,
                "card_id": card,
                "name": clean_name,
                "number": None,
                "arcana": "Major Arcana" if "arcana" in card.lower() else "Minor Arcana",
                "suit": "None",
                "element": "",
                "orientation": "Reversed" if is_rev else "Upright",
                "is_reversed": is_rev,
                "position_name": f"Position {idx+1}",
                "position_meaning": "Influencing factor",
                "keywords": ["Insight", "Reflection"],
                "interpretation": f"Symbolic archetypal resonance of {clean_name}.",
                "core_meaning": "",
                "position_context": "",
                "domain_guidance": [],
                "fortune_telling": [],
                "expanded_meanings": [],
                "relevance": None,
                "image_path": None,
            })

    # Confidence calculation (§49.9)
    overall_conf = float(meta.get("confidence", meta.get("overall_relevance", 0.90)))
    if overall_conf > 1:
        overall_conf = overall_conf / 100.0
    score_100 = round(overall_conf * 100, 1)

    # Narrative: support both the engine shape (opening/body/closing/summary)
    if isinstance(narrative, dict):
        body_lines: List[str] = []
        raw_body = narrative.get("body", [])
        if isinstance(raw_body, list):
            body_lines = [str(x) for x in raw_body if str(x).strip()]
        elif isinstance(raw_body, str) and raw_body.strip():
            body_lines = [raw_body]
        summary_text = (
            narrative.get("summary")
            or (reading.summary or "Tarot symbolic archetypal reflection.")
        )
        narrative_out = {
            "opening": narrative.get("opening", ""),
            "theme": narrative.get("theme", "Spiritual Evolution"),
            "summary": summary_text,
            "body": body_lines,
            "closing": narrative.get("closing", ""),
            "full_text": narrative.get("full_text") or narrative.get("closing") or summary_text,
        }
    else:
        summary_text = reading.summary or "Tarot symbolic archetypal reflection."
        narrative_out = {
            "opening": "",
            "theme": "Spiritual Evolution",
            "summary": summary_text,
            "body": [],
            "closing": "",
            "full_text": summary_text,
        }

    # Synthesis: prefer the engine analysis block, fall back to legacy keys.
    arcana = analysis.get("arcana_balance", {}) if isinstance(analysis, dict) else {}
    elemental = analysis.get("elemental_balance", {}) if isinstance(analysis, dict) else {}
    reversal = analysis.get("reversal_analysis", {}) if isinstance(analysis, dict) else {}
    numerology = analysis.get("numerology", {}) if isinstance(analysis, dict) else {}
    reversals_count = int(
        reversal.get("reversed_count", synthesis_legacy.get("reversals_count", sum(1 for c in normalized_cards if c.get("is_reversed"))))
    )

    action_items = guidance if isinstance(guidance, list) and guidance else [
        "Reflect on the archetypal invitations presented by your draw.",
        "Take intentional steps aligned with your inner clarity and intuition.",
    ]

    common = _reading_common(reading)

    return {
        "report_id": str(uuid.uuid4()),
        "reading_id": str(reading.id),
        "report_type": "tarot",
        "title": spread_name,
        "user_name": user_name,
        "created_at": created_str,
        "question": question,
        "domain_focus": result_data.get("domain_focus", ""),
        "summary": summary_text,
        "confidence": {
            "score": score_100,
            "label": _score_label(score_100),
            "raw_confidence": overall_conf,
        },
        "spread_details": {
            "spread_id": result_data.get("spread_id", "custom"),
            "spread_name": spread_name,
            "spread_category": result_data.get("spread_category", ""),
            "deck_id": result_data.get("deck_id", "rider-waite-smith"),
            "total_cards": len(normalized_cards),
        },
        "cards": normalized_cards,
        "synthesis": {
            "elemental_dominance": (
                (elemental.get("dominant_element") if isinstance(elemental, dict) else None)
                or synthesis_legacy.get("elemental_dominance", "Balanced")
            ),
            "elemental_counts": elemental.get("counts", {}) if isinstance(elemental, dict) else {},
            "elemental_narrative": elemental.get("narrative", "") if isinstance(elemental, dict) else "",
            "arcana_distribution": synthesis_legacy.get("arcana_distribution") or {
                "major": arcana.get("major_arcana", 0) if isinstance(arcana, dict) else 0,
                "minor": arcana.get("minor_arcana", 0) if isinstance(arcana, dict) else 0,
            },
            "arcana_narrative": arcana.get("narrative", "") if isinstance(arcana, dict) else "",
            "reversals_count": reversals_count,
            "reversal_narrative": reversal.get("narrative", "") if isinstance(reversal, dict) else "",
            "numerology_profile": synthesis_legacy.get("numerology_profile") or numerology if isinstance(numerology, dict) else {},
            "numerology_narrative": numerology.get("narrative", "") if isinstance(numerology, dict) else "",
        },
        "narrative": narrative_out,
        "actionable_guidance": action_items,
        "ai_interpretation": ai_block or None,
        "disclaimer": result_data.get("disclaimer") or ETHICAL_DISCLAIMER,
        "engine_metadata": {
            "engine": meta.get("engine", "TarotInterpretationRuleEngine"),
            "version": meta.get("engine_version", meta.get("model_version", REPORT_ENGINE_VERSION)),
            "model": meta.get("model_name", "rider-waite-rulebook"),
            "timestamp_utc": meta.get("timestamp", datetime.now(timezone.utc).isoformat()),
        },
        **common,
    }

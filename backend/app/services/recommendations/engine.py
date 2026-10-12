"""LLM-powered recommendation engine (Module 9, FR-034, TASK-012)."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.services.interpretation.llm_adapter import LLMAdapter, get_llm_adapter

logger = logging.getLogger(__name__)

ENGINE_NAME = "LLMRecommendationEngine"
ENGINE_VERSION = "2.0.0"
MODEL_NAME = "groq-llm-recommender"
MODEL_VERSION = "2.0.0"

RECOMMENDATION_DISCLAIMER = (
    "Recommendations are interpretive guidance for self-reflection and "
    "entertainment only — not professional, medical, financial, or psychological "
    "advice (Spec §49.19)."
)

REC_TYPES: Tuple[str, ...] = (
    "personal_growth",
    "relationship",
    "career",
    "goal_alignment",
    "spiritual_development",
)

ELEMENTS: Tuple[str, ...] = ("Fire", "Water", "Air", "Earth")

VALID_EFFORTS: Tuple[str, ...] = ("low", "medium", "high")
VALID_HORIZONS: Tuple[str, ...] = ("daily", "weekly", "monthly", "quarterly", "as_needed")
VALID_PRIORITIES: Tuple[str, ...] = ("low", "medium", "high")

MAX_TITLE_LEN = 120
MAX_TEXT_LEN = 600
MAX_TAGS = 6
MAX_REASONS = 4
LLM_TEMPERATURE = 0.6
LLM_MAX_TOKENS = 2800

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]+")

# Goal keyword patterns for heuristic fallback.
GOAL_CATEGORY_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "career": ("career", "job", "work", "profession", "business", "promot", "employ"),
    "relationships": ("relationship", "partner", "friend", "family", "love", "marriage", "social", "date"),
    "health_wellness": ("health", "fitness", "wellness", "sleep", "weight", "energy", "stress", "habit"),
    "spiritual_growth": ("spiritual", "meditat", "soul", "mindful", "tarot", "psychic", "inner peace"),
    "finances": ("money", "financ", "saving", "invest", "debt", "wealth", "budget"),
    "creativity": ("creat", "art", "music", "write", "paint", "imagin"),
    "education": ("learn", "study", "course", "school", "skill", "read", "exam"),
    "self_discipline": ("disciplin", "focus", "routine", "habit", "productiv", "organis", "organiz", "consistent"),
    "emotional_balance": ("calm", "anxiety", "emotion", "mood", "anger", "peace", "balance"),
    "leadership": ("lead", "manager", "team", "confiden", "influence", "speak"),
}


def _tokens(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


class RecommendationEngineError(Exception):
    """Engine failure mapped to the standard error envelope (§49.14)."""

    def __init__(
        self,
        message: str = "Recommendation engine failed",
        *,
        code: str = "RECOMMENDATION_ERROR",
        status_code: int = 400,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


# Catalog (grounding context for the LLM + source for the offline fallback)

@dataclass(frozen=True)
class CatalogItem:
    id: str
    type: str
    title: str
    text: str
    tags: Tuple[str, ...]
    elements: Tuple[str, ...]
    addresses: Tuple[str, ...]
    leverages: Tuple[str, ...]
    goal_categories: Tuple[str, ...]
    effort: str
    horizon: str
    priority_base: str

    @property
    def document(self) -> str:
        """Flat text used by the heuristic fallback's keyword overlap."""
        parts = [self.title, self.text, self.type.replace("_", " ")]
        parts.extend(self.tags)
        parts.extend(self.addresses)
        parts.extend(self.leverages)
        parts.extend(self.goal_categories)
        return " ".join(parts)


@dataclass
class Catalog:
    items: List[CatalogItem]
    fingerprint: str
    schema_version: str = "1.0.0"

    @classmethod
    def load(cls, path: Path) -> "Catalog":
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        items: List[CatalogItem] = []
        for idx, raw_item in enumerate(data.get("items", [])):
            try:
                items.append(
                    CatalogItem(
                        id=str(raw_item["id"]),
                        type=str(raw_item["type"]),
                        title=str(raw_item["title"]),
                        text=str(raw_item["text"]),
                        tags=tuple(str(t).strip().lower() for t in raw_item.get("tags", [])),
                        elements=tuple(str(e) for e in raw_item.get("elements", [])),
                        addresses=tuple(str(a) for a in raw_item.get("addresses", [])),
                        leverages=tuple(str(l) for l in raw_item.get("leverages", [])),
                        goal_categories=tuple(str(g) for g in raw_item.get("goal_categories", [])),
                        effort=str(raw_item.get("effort", "low")),
                        horizon=str(raw_item.get("horizon", "weekly")),
                        priority_base=str(raw_item.get("priority_base", "medium")),
                    )
                )
            except KeyError as exc:
                raise RecommendationEngineError(
                    f"Catalog item {idx} is missing required field {exc}",
                    code="RECOMMENDATION_CATALOG_INVALID",
                ) from exc
        if not items:
            raise RecommendationEngineError(
                "Recommendation catalog is empty",
                code="RECOMMENDATION_CATALOG_EMPTY",
            )
        seen = {item.id for item in items}
        if len(seen) != len(items):
            raise RecommendationEngineError(
                "Recommendation catalog contains duplicate item ids",
                code="RECOMMENDATION_CATALOG_INVALID",
            )
        return cls(items=items, fingerprint=hashlib.sha256(raw).hexdigest())

    def digest(self, limit: int = 24) -> str:
        """Compact per-type digest that grounds the LLM prompt."""
        by_type: Dict[str, List[CatalogItem]] = {t: [] for t in REC_TYPES}
        for item in self.items:
            if item.type in by_type:
                by_type[item.type].append(item)
        lines: List[str] = []
        for rec_type, entries in by_type.items():
            sample = entries[: max(1, limit // len(by_type))]
            titles = "; ".join(f"'{e.title}' ({e.effort} effort, {e.horizon})" for e in sample)
            lines.append(f"- {rec_type}: {titles}")
        return "\n".join(lines)


def default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[4] / "data" / "recommendations" / "recommendations_catalog.json"


# User context

@dataclass
class UserContext:
    dominant_element: str = "Unknown"
    secondary_element: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    behaviors: List[str] = field(default_factory=list)
    question: str = ""
    tarot_summary: str = ""
    sources: List[str] = field(default_factory=list)

    @property
    def document(self) -> str:
        parts: List[str] = [self.dominant_element, "element"]
        if self.secondary_element:
            parts.append(self.secondary_element)
        parts.extend(self.strengths)
        parts.extend(self.weaknesses)
        parts.extend(self.weaknesses)  # weight growth areas double — they drive recommendations
        parts.extend(self.interests)
        parts.extend(self.behaviors)
        if self.question:
            parts.append(self.question)
        if self.tarot_summary:
            parts.append(self.tarot_summary)
        return " ".join(parts)

    @property
    def goal_documents(self) -> List[str]:
        return [g for g in (goal.strip() for goal in self.goals) if g]


def context_from_dict(raw: Optional[Dict[str, Any]]) -> UserContext:
    """Build a UserContext from the heterogeneous personality/profile context dict."""
    raw = raw or {}

    def _extract(value: Any, key: str) -> List[str]:
        out: List[str] = []
        for entry in value or []:
            if isinstance(entry, dict):
                text = entry.get(key, "")
                if text:
                    out.append(str(text))
            elif isinstance(entry, str) and entry.strip():
                out.append(entry.strip())
        return out

    known_elements = {el.lower(): el for el in ELEMENTS}
    dominant_raw = str(raw.get("dominant_element") or raw.get("element") or "Unknown")
    dominant = known_elements.get(dominant_raw.lower(), dominant_raw)
    secondary_raw = raw.get("secondary_element")
    secondary = known_elements.get(str(secondary_raw).lower()) if secondary_raw else None

    return UserContext(
        dominant_element=dominant,
        secondary_element=secondary,
        strengths=_extract(raw.get("strengths"), "trait"),
        weaknesses=_extract(raw.get("weaknesses"), "area"),
        goals=[str(g) for g in raw.get("goals", []) if str(g).strip()],
        interests=[str(i) for i in raw.get("interests", []) if str(i).strip()],
        behaviors=_extract(raw.get("behaviors"), "insight"),
        question=str(raw.get("question") or "").strip(),
        tarot_summary=str(raw.get("tarot_summary") or "").strip(),
        sources=[str(s) for s in raw.get("sources", []) if str(s).strip()],
    )


# Engine

class LLMRecommendationEngine:
    """Generates personalised recommendations with an LLM (Groq-first adapter)."""

    def __init__(self, catalog: Optional[Catalog] = None, adapter: Optional[LLMAdapter] = None):
        self.catalog = catalog or Catalog.load(default_catalog_path())
        self._adapter = adapter
        self.generation_method: Optional[str] = None
        self.llm_tokens_last: int = 0

    @property
    def adapter(self) -> LLMAdapter:
        if self._adapter is None:
            self._adapter = get_llm_adapter()
        return self._adapter

    def set_adapter(self, adapter: Optional[LLMAdapter]) -> None:
        self._adapter = adapter

    # prompt construction

    def _build_system_prompt(self, types: Sequence[str]) -> str:
        return (
            "You are the Personalized Recommendation engine of a palmistry and tarot "
            "platform. You turn symbolic reading data (palm elemental profiles, tarot "
            "arcana patterns) plus the seeker's stated goals into concrete, kind, "
            "actionable guidance for self-reflection.\n"
            "Hard rules:\n"
            "1. Output ONLY valid JSON matching the requested schema. No markdown, no "
            "commentary outside the JSON.\n"
            "2. Every item's 'type' must be one of: " + ", ".join(types) + ".\n"
            "3. Guidance is interpretive and empowering — never medical, legal, or "
            "financial advice, never deterministic predictions, never judgmental.\n"
            "4. Personalise relentlessly: tie each item to the seeker's dominant "
            "element, strengths, growth areas, goals, interests, focus question, or "
            "recent tarot narrative where the data allows it.\n"
            "5. Respect feedback signals: avoid repeating dismissed themes; build on "
            "accepted and completed ones.\n"
            "6. Write in warm second person ('you'), specific and practical, one to "
            "three sentences per item.\n"
            "7. Scores are your calibrated confidence in [0, 1] — do not inflate."
        )

    def _build_user_prompt(
        self,
        ctx: UserContext,
        *,
        types: Sequence[str],
        max_total: int,
        per_type: int,
        feedback_summary: str = "",
        catalog_digest: str = "",
    ) -> str:
        def _bullets(values: Sequence[str], limit: int = 6) -> str:
            cleaned = [str(v).strip() for v in values if str(v).strip()][:limit]
            return "\n".join(f"  - {v}" for v in cleaned) if cleaned else "  - (none provided)"

        parts: List[str] = [
            "## Seeker context",
            f"- Reading sources: {', '.join(ctx.sources) if ctx.sources else 'palm reading'}",
            f"- Dominant element: {ctx.dominant_element}"
            + (f" (secondary: {ctx.secondary_element})" if ctx.secondary_element else ""),
            f"- Focus question: {ctx.question or '(none)'}",
            "",
            "Strengths:",
            _bullets(ctx.strengths),
            "Growth areas:",
            _bullets(ctx.weaknesses),
            "Stated goals:",
            _bullets(ctx.goals),
            "Interests:",
            _bullets(ctx.interests),
            "Behavioural insights:",
            _bullets(ctx.behaviors),
            f"- Tarot narrative: {ctx.tarot_summary or '(none)'}",
        ]

        if feedback_summary:
            parts += ["", "## Recent recommendation feedback (steer accordingly)", feedback_summary]

        if catalog_digest:
            parts += [
                "",
                "## Catalog reference (tone and vocabulary examples only — craft NEW "
                "personalised guidance rather than copying these verbatim)",
                catalog_digest,
            ]

        parts += [
            "",
            "## Task",
            f"Generate between {min(3, max_total)} and {max_total} personalised recommendations: "
            f"at most {per_type} per type, covering these types: {', '.join(types)}.",
            "",
            "Return JSON of this exact shape:",
            '{"recommendations": [',
            "  {",
            '    "type": "personal_growth|relationship|career|goal_alignment|spiritual_development",',
            '    "title": "short imperative title (<= 10 words)",',
            '    "text": "1-3 sentences of personalised, actionable guidance",',
            '    "tags": ["3-6 lowercase topic tags"],',
            '    "elements": ["element(s) this guidance resonates with: Fire|Water|Air|Earth"],',
            '    "effort": "low|medium|high",',
            '    "horizon": "daily|weekly|monthly|quarterly|as_needed",',
            '    "priority": "low|medium|high",',
            '    "reasoning": ["1-3 short phrases: why THIS item fits THIS seeker"],',
            '    "scores": {"context_relevance": 0.0-1.0, "personalization": 0.0-1.0, "goal_alignment": 0.0-1.0}',
            "  }",
            "]}",
        ]
        return "\n".join(parts)

    # LLM call + validation

    def _generate_with_llm(
        self,
        ctx: UserContext,
        *,
        types: Sequence[str],
        max_total: int,
        per_type: int,
        feedback_summary: str = "",
    ) -> Optional[List[Dict[str, Any]]]:
        """Call the LLM and return normalised items, or None on any failure."""
        adapter = self.adapter
        if not adapter.is_online:
            return None

        prompt = self._build_user_prompt(
            ctx,
            types=types,
            max_total=max_total,
            per_type=per_type,
            feedback_summary=feedback_summary,
            catalog_digest=self.catalog.digest(),
        )
        try:
            response = adapter.complete(
                prompt=prompt,
                system=self._build_system_prompt(types),
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                json_mode=True,
            )
        except Exception as exc:
            logger.warning("LLM recommendation call failed (%s): %s", adapter.provider, exc)
            return None

        if response.rule_based:
            return None  # offline adapter fallback payload — not recommendation JSON

        self.llm_tokens_last = int(response.tokens or 0)
        raw_items = self._parse_llm_json(response.content)
        if raw_items is None:
            logger.warning("LLM recommendation output was not parseable JSON; falling back")
            return None

        allowed = set(types)
        seen_ids: set = set()
        validated: List[Dict[str, Any]] = []
        for raw in raw_items:
            item = self._validate_item(raw, allowed_types=allowed, seen_ids=seen_ids, ctx=ctx)
            if item is not None:
                validated.append(item)
        return validated or None

    def _parse_llm_json(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """Extract the recommendations list from an LLM completion."""
        if not content:
            return None
        text = content.strip()
        # Tolerate markdown fences and leading chatter around the JSON object.
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            raw_items = parsed.get("recommendations", parsed.get("items"))
        elif isinstance(parsed, list):
            raw_items = parsed
        else:
            return None
        if not isinstance(raw_items, list):
            return None
        return [r for r in raw_items if isinstance(r, dict)]

    def _validate_item(
        self,
        raw: Dict[str, Any],
        *,
        allowed_types: set,
        seen_ids: set,
        ctx: UserContext,
    ) -> Optional[Dict[str, Any]]:
        rec_type = str(raw.get("type", "")).strip()
        if rec_type not in allowed_types:
            return None

        title = str(raw.get("title", "")).strip()[:MAX_TITLE_LEN]
        text = str(raw.get("text", "")).strip()[:MAX_TEXT_LEN]
        if not title or not text:
            return None

        item_id = self._stable_id(rec_type, title, seen_ids)

        tags = [str(t).strip().lower() for t in raw.get("tags", []) if str(t).strip()][:MAX_TAGS]
        elements = [str(e).title() for e in raw.get("elements", []) if str(e).title() in ELEMENTS]
        effort = str(raw.get("effort", "medium")).lower()
        horizon = str(raw.get("horizon", "weekly")).lower()
        priority = str(raw.get("priority", "medium")).lower()

        reasoning = [str(r).strip() for r in raw.get("reasoning", []) if str(r).strip()][:MAX_REASONS]

        scores_raw = raw.get("scores", {})
        scores_raw = scores_raw if isinstance(scores_raw, dict) else {}
        context_relevance = _clamp01(scores_raw.get("context_relevance", 0.75))
        personalization = _clamp01(scores_raw.get("personalization", 0.7))
        goal_alignment = _clamp01(scores_raw.get("goal_alignment", 0.6))
        blended = round((context_relevance + personalization + goal_alignment) / 3.0, 4)

        element_affinity = next(
            (el for el in elements if el == ctx.dominant_element),
            None,
        )

        return {
            "id": item_id,
            "type": rec_type,
            "title": title,
            "text": text,
            "tags": tags,
            "elements": elements,
            "effort": effort if effort in VALID_EFFORTS else "medium",
            "horizon": horizon if horizon in VALID_HORIZONS else "weekly",
            "priority": priority if priority in VALID_PRIORITIES else "medium",
            "scores": {
                "context_relevance": round(context_relevance, 4),
                "personalization": round(personalization, 4),
                "goal_alignment": round(goal_alignment, 4),
                "blended": blended,
            },
            "matched_reasons": list(reasoning),
            "cluster": 0,
            "reasoning": reasoning or ["Generated by the LLM recommender from your reading context"],
            "confidence": blended,
            "element_affinity": element_affinity,
            "final_score": blended,
            "rank": 0,
        }

    @staticmethod
    def _stable_id(rec_type: str, title: str, seen_ids: set) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "item"
        item_id = f"llm_{rec_type[:4]}_{slug}"
        base = item_id
        n = 2
        while item_id in seen_ids:
            item_id = f"{base}_{n}"
            n += 1
        seen_ids.add(item_id)
        return item_id

    # heuristic fallback (no ML dependencies, no network)

    def _fallback_scores(
        self,
        item: CatalogItem,
        ctx: UserContext,
        feedback: Optional[Dict[str, float]],
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """Pure-Python relevance scoring of one catalog item for the user."""
        user_tokens = set(_tokens(ctx.document))
        goal_tokens = set(_tokens(" ".join(ctx.goal_documents)))
        item_tokens = set(_tokens(item.document))

        overlap = user_tokens & item_tokens
        context_relevance = min(1.0, len(overlap) / 12.0) if user_tokens else 0.3

        goal_overlap = goal_tokens & item_tokens if goal_tokens else set()
        goal_alignment = min(1.0, len(goal_overlap) / 5.0) if goal_tokens else 0.35
        stated_categories = {
            cat
            for goal in ctx.goal_documents
            for cat, patterns in GOAL_CATEGORY_PATTERNS.items()
            if any(p in goal.lower() for p in patterns)
        }
        if stated_categories and set(item.goal_categories) & stated_categories:
            goal_alignment = min(1.0, goal_alignment + 0.3)

        known = [el for el in item.elements if el in ELEMENTS]
        universal = len(known) == len(ELEMENTS)
        element_match = (
            ctx.dominant_element in known
            or (ctx.secondary_element in known if ctx.secondary_element else False)
            or universal
        )

        personalization = 0.3
        reasons: List[str] = []
        if ctx.dominant_element in known and not universal:
            personalization += 0.25
            reasons.append(f"matches your dominant {ctx.dominant_element} element")
        weakness_hits = {
            w
            for w in ctx.weaknesses
            if any(_tokens(w) and _tokens(w)[0] in _tokens(a.lower()) for a in item.addresses)
            or any(w.lower() in a.lower() or a.lower() in w.lower() for a in item.addresses)
        }
        if weakness_hits:
            personalization += min(0.3, 0.15 * len(weakness_hits))
            reasons.extend(f"addresses growth area: {hit}" for hit in sorted(weakness_hits)[:2])
        strength_hits = {
            s
            for s in ctx.strengths
            if any(s.lower() in l.lower() or l.lower() in s.lower() for l in item.leverages)
        }
        if strength_hits:
            personalization += min(0.15, 0.15 * len(strength_hits))
            reasons.extend(f"leverages your strength: {hit}" for hit in sorted(strength_hits)[:1])
        personalization = min(1.0, personalization)

        scores = {
            "context_relevance": round(context_relevance, 4),
            "personalization": round(personalization, 4),
            "goal_alignment": round(goal_alignment, 4),
        }
        blended = round(
            0.4 * scores["context_relevance"]
            + 0.35 * scores["personalization"]
            + 0.25 * scores["goal_alignment"],
            4,
        )
        # Feedback penalty/bonus replaces the old collaborative filter.
        if feedback:
            signal = feedback.get(item.id)
            if signal is not None:
                blended = round(max(0.0, min(1.0, blended + 0.1 * signal)), 4)
                if signal > 0:
                    reasons.append("similar to guidance you engaged with before")
                elif signal < 0:
                    blended = round(max(0.0, blended - 0.15), 4)

        return blended, scores, reasons or ["Selected from the curated catalog for your reading context"]

    def _fallback_select(
        self,
        ctx: UserContext,
        *,
        types: Sequence[str],
        max_total: int,
        per_type: int,
        feedback: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for item in self.catalog.items:
            if item.type not in types:
                continue
            blended, scores, reasons = self._fallback_scores(item, ctx, feedback)
            candidates.append(
                {
                    "id": item.id,
                    "type": item.type,
                    "title": item.title,
                    "text": item.text,
                    "tags": list(item.tags),
                    "elements": list(item.elements),
                    "effort": item.effort,
                    "horizon": item.horizon,
                    "priority": item.priority_base,
                    "scores": {**scores, "blended": blended},
                    "matched_reasons": list(reasons),
                    "cluster": 0,
                    "reasoning": list(reasons),
                    "confidence": blended,
                    "element_affinity": next(
                        (el for el in item.elements if el in ELEMENTS and el == ctx.dominant_element),
                        None,
                    ),
                    "final_score": blended,
                    "rank": 0,
                }
            )
        return candidates

    # selection

    @staticmethod
    def _select(
        candidates: List[Dict[str, Any]],
        *,
        types: Sequence[str],
        max_total: int,
        per_type: int,
    ) -> List[Dict[str, Any]]:
        """Round-robin per type over blended-score order, honouring quotas."""
        by_type: Dict[str, List[Dict[str, Any]]] = {t: [] for t in types}
        for cand in sorted(candidates, key=lambda c: c["scores"]["blended"], reverse=True):
            if cand["type"] in by_type:
                by_type[cand["type"]].append(cand)

        selected: List[Dict[str, Any]] = []
        target = min(max_total, len(types) * per_type)
        while len(selected) < target:
            placed = False
            for t in types:
                if len(selected) >= target:
                    break
                if len([s for s in selected if s["type"] == t]) >= per_type:
                    continue
                pool = by_type[t]
                # De-duplicate by id (LLM may repeat an item across rounds).
                while pool and any(s["id"] == pool[0]["id"] for s in selected):
                    pool.pop(0)
                if pool:
                    selected.append(pool.pop(0))
                    placed = True
            if not placed:
                break

        for rank, item in enumerate(selected, start=1):
            item["rank"] = rank
            item["final_score"] = item["scores"]["blended"]
        return selected

    # public API

    def generate(
        self,
        user_context: Optional[Dict[str, Any]] = None,
        *,
        requested_types: Optional[Sequence[str]] = None,
        max_total: int = 8,
        per_type: int = 2,
        feedback_summary: str = "",
        feedback_scores: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generate recommendations."""
        ctx = context_from_dict(user_context)
        types = [t for t in (requested_types or REC_TYPES) if t in REC_TYPES] or list(REC_TYPES)

        adapter = self.adapter
        self.generation_method = "heuristic_fallback"
        candidates: Optional[List[Dict[str, Any]]] = None

        try:
            candidates = self._generate_with_llm(
                ctx,
                types=types,
                max_total=max_total,
                per_type=per_type,
                feedback_summary=feedback_summary,
            )
        except Exception as exc:  # defensive: LLM path must never break serving
            logger.warning("LLM recommendation generation raised, using fallback: %s", exc)
            candidates = None

        if candidates is not None:
            self.generation_method = "llm"
        else:
            candidates = self._fallback_select(
                ctx, types=types, max_total=max_total, per_type=per_type, feedback=feedback_scores
            )

        selected = self._select(candidates, types=types, max_total=max_total, per_type=per_type)

        metadata = {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "model": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "provider": adapter.provider,
            "provider_model": adapter.model,
            "generation_method": self.generation_method,
            "llm_generated": self.generation_method == "llm",
            "llm_tokens": self.llm_tokens_last if self.generation_method == "llm" else 0,
            "catalog_fingerprint": self.catalog.fingerprint[:12],
            "catalog_size": len(self.catalog.items),
            "candidate_count": len(candidates),
            "feedback_signals": bool(feedback_summary or feedback_scores),
            "requested_types": list(types),
            "context_sources": ctx.sources,
            "disclaimer": RECOMMENDATION_DISCLAIMER,
        }
        return selected, metadata


# Module-level singleton (lazy)

_engine: Optional[LLMRecommendationEngine] = None


def get_engine() -> LLMRecommendationEngine:
    """Lazily build the process-wide engine singleton."""
    global _engine
    if _engine is None:
        _engine = LLMRecommendationEngine()
    return _engine


def reset_engine() -> None:
    """Drop the cached engine (used by tests)."""
    global _engine
    _engine = None


def _clamp01(value: Any, default: float = 0.5) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if num != num:  # NaN
        return default
    return max(0.0, min(1.0, num))

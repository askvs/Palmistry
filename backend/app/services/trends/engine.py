"""Life Trend Engine (Milestone 3 / FR-017)."""
from __future__ import annotations

import datetime as dt
import math
from typing import Any, Dict, List, Optional

ENGINE_NAME = "LifeTrendEngine"
ENGINE_VERSION = "1.0.0"
METHOD = "feature_based_trend_scoring"

ELEMENTS = ("Fire", "Water", "Air", "Earth")

DOMAIN_LABELS: Dict[str, str] = {
    "career": "Career & Purpose",
    "relationships": "Love & Relationships",
    "emotional": "Emotional Wellbeing",
    "growth": "Personal Growth",
    "vitality": "Health & Vitality",
    "creativity": "Creativity & Expression",
}

# Recency half-life in days for weighting readings (trend = recent behavior).
RECENCY_HALF_LIFE_DAYS = 90.0

# Per-reading signal extraction
# Every signal is a real value extracted from stored Reading.result JSONB,


def _clamp01(value: Any) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return max(0.0, min(1.0, v))


def _line_map(palm_result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        line.get("line_id"): line
        for line in palm_result.get("lines", []) or []
        if isinstance(line, dict) and line.get("line_id")
    }


def _line_strength(line: Dict[str, Any]) -> Optional[float]:
    """Blend a detected line's depth, continuity and confidence into 0..1."""
    parts = [
        p
        for p in (
            _clamp01(line.get("depth_clarity")),
            _clamp01(line.get("continuity")),
            _clamp01(line.get("confidence")),
        )
        if p is not None
    ]
    if not parts:
        return None
    return sum(parts) / len(parts)


def extract_reading_signals(reading_type: str, result: Dict[str, Any]) -> Dict[str, float]:
    """Extract normalized 0-1 signals from one reading's stored result."""
    signals: Dict[str, float] = {}
    if not isinstance(result, dict):
        return signals

    if reading_type == "palm":
        lines = _line_map(result)
        for line_id in ("life_line", "heart_line", "head_line", "fate_line", "sun_line"):
            line = lines.get(line_id)
            if line and line.get("detected"):
                strength = _line_strength(line)
                if strength is not None:
                    key = line_id.replace("_line", "")
                    signals[f"palm.{key}_line_strength"] = strength
                variation = str(line.get("variation_type") or "")
                if variation in ("broken", "chain", "faint_or_shallow", "faint_or_absent", "absent"):
                    signals["palm.growth_markers"] = max(
                        signals.get("palm.growth_markers", 0.0), 1.0
                    )

        mounts = [m for m in result.get("mounts", []) or [] if isinstance(m, dict)]
        if mounts:
            total = len(mounts)
            for element in ELEMENTS:
                prominent = [
                    m for m in mounts
                    if str(m.get("element")) == element and m.get("prominence") == "prominent"
                ]
                if prominent:
                    signals[f"palm.mount_{element.lower()}"] = len(prominent) / total

        shape = result.get("palm_shape") or {}
        element = str(shape.get("element") or "")
        if element in ELEMENTS:
            signals[f"palm.element_{element.lower()}"] = 1.0

        finger = result.get("finger_structure") or {}
        ratio = _clamp01(finger.get("digit_ratio_2d_4d"))
        if ratio is not None:
            # Normalize the physiological 2D:4D range (~0.85-1.05) to 0..1.
            signals["palm.digit_ratio_norm"] = max(0.0, min(1.0, (1.05 - ratio) / 0.20))

        metadata = result.get("metadata") or {}
        conf = _clamp01(metadata.get("overall_confidence"))
        if conf is not None:
            signals["palm.overall_confidence"] = conf

    elif reading_type == "tarot":
        # Tarot payloads vary by endpoint; normalize here.
        payload = result.get("interpretation")
        if not isinstance(payload, dict) or "cards" not in payload:
            payload = result

        cards = [c for c in payload.get("cards", []) or [] if isinstance(c, dict)]
        n_cards = len(cards)
        if n_cards:
            majors = sum(
                1 for c in cards if str(c.get("arcana", "")).lower().startswith("major")
            )
            reversed_cards = sum(1 for c in cards if c.get("orientation") == "reversed")
            court = sum(
                1 for c in cards
                if any(t in str(c.get("card_name", "")) for t in ("Page", "Knight", "Queen", "King"))
            )
            signals["tarot.major_ratio"] = majors / n_cards
            signals["tarot.reversal_ratio"] = reversed_cards / n_cards
            signals["tarot.court_ratio"] = court / n_cards

            for element in ELEMENTS:
                count = sum(1 for c in cards if c.get("element") == element)
                if count:
                    signals[f"tarot.element_{element.lower()}"] = count / n_cards

        domain = str(payload.get("domain_focus") or "")
        if domain:
            signals[f"tarot.domain_{domain}"] = 1.0

        metadata = payload.get("metadata") or {}
        relevance = _clamp01(metadata.get("overall_relevance"))
        if relevance is not None:
            signals["tarot.relevance"] = relevance

    return signals


# Domain scoring model
# Documented, fixed weights mapping signals to life domains.

DOMAIN_SIGNAL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "career": {
        "palm.fate_line_strength": 0.30,
        "palm.head_line_strength": 0.15,
        "palm.mount_earth": 0.10,
        "palm.element_fire": 0.10,
        "tarot.domain_career": 0.25,
        "tarot.element_fire": 0.10,
    },
    "relationships": {
        "palm.heart_line_strength": 0.30,
        "palm.mount_water": 0.20,
        "palm.element_water": 0.15,
        "tarot.domain_love": 0.25,
        "tarot.element_water": 0.10,
    },
    "emotional": {
        "palm.head_line_strength": 0.15,
        "tarot.reversal_ratio": 0.20,
        "palm.element_water": 0.20,
        "palm.mount_water": 0.15,
        "tarot.element_water": 0.20,
        "tarot.relevance": 0.10,
    },
    "growth": {
        "palm.life_line_strength": 0.25,
        "palm.growth_markers": 0.15,
        "tarot.major_ratio": 0.25,
        "tarot.domain_spiritual": 0.20,
        "palm.element_air": 0.15,
    },
    "vitality": {
        "palm.life_line_strength": 0.35,
        "palm.mount_earth": 0.20,
        "palm.element_earth": 0.25,
        "palm.growth_markers": 0.20,
    },
    "creativity": {
        "palm.sun_line_strength": 0.30,
        "palm.mount_fire": 0.20,
        "tarot.court_ratio": 0.15,
        "tarot.element_air": 0.20,
        "palm.element_air": 0.15,
    },
}

# Goal text keywords -> domain (personalization from ProfileGoal.text).
GOAL_DOMAIN_KEYWORDS: Dict[str, tuple] = {
    "career": ("career", "job", "work", "business", "promotion", "study", "exam", "money", "finance"),
    "relationships": ("love", "relationship", "partner", "marriage", "family", "friend"),
    "emotional": ("calm", "anxiety", "stress", "emotion", "peace", "mental"),
    "growth": ("grow", "growth", "habit", "learn", "discipline", "spiritual", "purpose"),
    "vitality": ("health", "fitness", "sleep", "energy", "diet"),
    "creativity": ("creative", "art", "music", "write", "paint", "express"),
}

DIRECTION_BAND = 0.08  # |delta| below this = stable


def _recency_weight(created_at: dt.datetime, now: dt.datetime) -> float:
    age_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def score_reading_domains(signals: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """Score every domain for one reading from its signals."""
    out: Dict[str, Dict[str, float]] = {}
    for domain, weights in DOMAIN_SIGNAL_WEIGHTS.items():
        num = 0.0
        den = 0.0
        used: Dict[str, float] = {}
        for signal, weight in weights.items():
            value = signals.get(signal)
            if value is None:
                continue
            num += weight * value
            den += weight
            used[signal] = value
        out[domain] = {
            "score": (num / den) if den > 0 else 0.0,
            "coverage": den / sum(weights.values()),
            "signals": used,
        }
    return out


class LifeTrendEngine:
    """Aggregates per-reading signals into life trend results."""

    def __init__(
        self,
        readings: List[Dict[str, Any]],
        goals: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        now: Optional[dt.datetime] = None,
    ) -> None:
        """`readings` items: {type: 'palm'|'tarot', result: dict, created_at: datetime}."""
        self.now = now or dt.datetime.now(dt.timezone.utc)
        self.goals = [g for g in (goals or []) if isinstance(g, str) and g.strip()]
        self.interests = [i for i in (interests or []) if isinstance(i, str) and i.strip()]
        self.readings = sorted(
            (r for r in readings if isinstance(r, dict) and r.get("created_at")),
            key=lambda r: r["created_at"],
        )
        self._prepared = self._prepare()

    # preparation

    def _prepare(self) -> List[Dict[str, Any]]:
        prepared = []
        for reading in self.readings:
            created_at = reading["created_at"]
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=dt.timezone.utc)
            signals = extract_reading_signals(
                str(reading.get("type") or ""), reading.get("result") or {}
            )
            prepared.append(
                {
                    "type": reading.get("type"),
                    "created_at": created_at,
                    "signals": signals,
                    "domains": score_reading_domains(signals),
                }
            )
        return prepared

    def _goal_alignment(self) -> Dict[str, Dict[str, Any]]:
        """Map user goal/interest text onto domains (personalization signal)."""
        alignment: Dict[str, Dict[str, Any]] = {}
        texts = [t.lower() for t in self.goals + self.interests]
        for domain, keywords in GOAL_DOMAIN_KEYWORDS.items():
            matched = [t for t in texts if any(k in t for k in keywords)]
            if matched:
                alignment[domain] = {
                    "boost": min(0.15, 0.075 * len(matched)),
                    "source": matched[0],
                }
        return alignment

    # aggregation

    def compute(self) -> Dict[str, Any]:
        """Compute the full life trend analysis."""
        n = len(self._prepared)
        palm_count = sum(1 for r in self._prepared if r["type"] == "palm")
        tarot_count = n - palm_count

        history = [
            {
                "date": r["created_at"].isoformat(),
                "type": r["type"],
                "overall_signal": round(
                    sum(d["score"] for d in r["domains"].values()) / len(r["domains"]), 3
                )
                if r["domains"]
                else 0.0,
                "domains": {k: round(v["score"], 3) for k, v in r["domains"].items()},
            }
            for r in self._prepared
        ]

        if n == 0:
            return self._empty_result(history)

        goal_alignment = self._goal_alignment()
        domain_trends = self._domain_trends(goal_alignment)
        growth_potential = self._growth_potential(domain_trends)
        life_path = self._life_path(domain_trends, goal_alignment)
        opportunities = self._opportunities(domain_trends)
        challenges = self._challenges(domain_trends)
        explanation = self._explanation(domain_trends, goal_alignment, growth_potential)

        completeness = min(1.0, n / 6.0) * 0.5 + (
            min(1.0, palm_count / 2.0) * 0.25 + min(1.0, tarot_count / 2.0) * 0.25
        )

        return {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "method": METHOD,
            "life_path": life_path,
            "current_trends": domain_trends,
            "opportunities": opportunities,
            "challenges": challenges,
            "growth_potential": growth_potential,
            "explanation": explanation,
            "history": history,
            "data_coverage": {
                "readings_analyzed": n,
                "palm_readings": palm_count,
                "tarot_readings": tarot_count,
                "completeness": round(completeness, 2),
                "goals_used": len(self.goals),
            },
            "feature_vector": self._feature_vector(domain_trends),
        }

    def _domain_trends(self, goal_alignment: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recency-weighted per-domain trend scores with direction and confidence."""
        trends: List[Dict[str, Any]] = []
        n = len(self._prepared)
        weights = [
            _recency_weight(r["created_at"], self.now) or 1e-6 for r in self._prepared
        ]
        weight_sum = sum(weights)

        for domain, weights_map in DOMAIN_SIGNAL_WEIGHTS.items():
            total_weight = sum(weights_map.values())
            weighted_score = 0.0
            covered_weight = 0.0
            coverage_acc = 0.0
            signal_values: Dict[str, List[float]] = {}
            for r, w in zip(self._prepared, weights):
                d = r["domains"].get(domain)
                if not d or d["coverage"] <= 0:
                    continue
                weighted_score += w * d["score"]
                covered_weight += w
                coverage_acc += w * d["coverage"]
                for sig, val in d["signals"].items():
                    signal_values.setdefault(sig, []).append(val)
            # Average only over readings with evidence.
            score = weighted_score / covered_weight if covered_weight > 0 else 0.0
            coverage = coverage_acc / weight_sum

            # Direction: recent half vs older half (by recency weight order).
            recent, baseline = self._split_recent_baseline(domain)
            delta = recent - baseline
            if delta > DIRECTION_BAND:
                direction = "rising"
            elif delta < -DIRECTION_BAND:
                direction = "declining"
            else:
                direction = "stable"

            # Goal alignment boost (user-declared intent is direct evidence).
            boost_info = goal_alignment.get(domain)
            goal_signals: List[str] = []
            if boost_info:
                score = min(1.0, score + boost_info["boost"])
                goal_signals.append(
                    f"User goal: \"{boost_info['source']}\" (self-declared focus)"
                )

            evidence = min(1.0, len(signal_values) / 3.0)
            strength = round(min(1.0, 0.6 * evidence + 0.4 * coverage), 2)
            confidence = round(
                min(0.9, 0.25 + 0.10 * min(n, 5) + 0.15 * coverage), 2
            )

            trends.append(
                {
                    "name": DOMAIN_LABELS[domain],
                    "domain": domain,
                    "score": round(score, 3),
                    "direction": direction,
                    "momentum": round(max(-1.0, min(1.0, delta * 4.0)), 2),
                    "strength": strength,
                    "confidence": confidence,
                    "explanation": self._trend_explanation(
                        domain, score, direction, signal_values
                    ),
                    "signals": self._signal_descriptions(signal_values) + goal_signals,
                }
            )

        trends.sort(key=lambda t: t["score"] * t["strength"], reverse=True)
        return trends

    def _split_recent_baseline(self, domain: str) -> tuple:
        """Mean score of the most recent half of readings vs the older half."""
        scored = [
            (r["created_at"], r["domains"].get(domain, {}).get("score", 0.0))
            for r in self._prepared
            if r["domains"].get(domain, {}).get("coverage", 0) > 0
        ]
        if len(scored) < 2:
            return 0.0, 0.0
        scored.sort(key=lambda x: x[0])
        split = max(1, len(scored) // 2)
        baseline = [s for _, s in scored[:split]]
        recent = [s for _, s in scored[split:]]
        return sum(recent) / len(recent), sum(baseline) / len(baseline)

    def _signal_descriptions(self, signal_values: Dict[str, List[float]]) -> List[str]:
        SIGNAL_LABELS = {
            "palm.life_line_strength": "Life line depth & continuity",
            "palm.heart_line_strength": "Heart line depth & clarity",
            "palm.head_line_strength": "Head line depth & clarity",
            "palm.fate_line_strength": "Fate line strength",
            "palm.sun_line_strength": "Sun line strength",
            "palm.growth_markers": "Line variations (faint/absent)",
            "palm.mount_water": "Mount of Venus/Moon prominence",
            "palm.mount_earth": "Mount of Saturn prominence",
            "palm.mount_fire": "Mount of Jupiter/Apollo prominence",
            "palm.element_water": "Water hand shape",
            "palm.element_earth": "Earth hand shape",
            "palm.element_fire": "Fire hand shape",
            "palm.element_air": "Air hand shape",
            "tarot.major_ratio": "Major Arcana ratio in spreads",
            "tarot.reversal_ratio": "Reversed card ratio",
            "tarot.court_ratio": "Court card ratio",
            "tarot.element_water": "Water suit presence in tarot",
            "tarot.element_fire": "Fire suit presence in tarot",
            "tarot.element_air": "Air suit presence in tarot",
            "tarot.domain_career": "Career-focused readings",
            "tarot.domain_love": "Love-focused readings",
            "tarot.domain_spiritual": "Spiritual-growth readings",
            "tarot.relevance": "Card-spread relevance score",
        }
        descriptions = []
        for signal, values in sorted(signal_values.items()):
            label = SIGNAL_LABELS.get(signal, signal)
            mean = sum(values) / len(values)
            descriptions.append(
                f"{label}: {mean:.2f} avg across {len(values)} reading(s)"
            )
        return descriptions

    def _trend_explanation(
        self,
        domain: str,
        score: float,
        direction: str,
        signal_values: Dict[str, List[float]],
    ) -> str:
        level = "strong" if score >= 0.65 else "moderate" if score >= 0.4 else "emerging"
        direction_text = {
            "rising": "and rising across your recent readings",
            "declining": "and softening compared with earlier readings",
            "stable": "and holding steady across your readings",
        }[direction]
        n_signals = len(signal_values)
        evidence = (
            f"Based on {n_signals} distinct signal(s) in your reading history."
            if n_signals
            else "Only limited evidence is available so far — more readings will sharpen this."
        )
        return (
            f"{DOMAIN_LABELS[domain]} shows a {level} signal ({direction_text}). {evidence}"
        )

    def _growth_potential(self, trends: List[Dict[str, Any]]) -> float:
        """Composite growth potential from balance, level, momentum and evidence."""
        if not trends:
            return 0.5
        scores = [t["score"] for t in trends]
        strengths = [t["strength"] for t in trends]
        mean_level = sum(scores) / len(scores)
        spread = max(scores) - min(scores)
        balance = max(0.0, 1.0 - spread)  # balanced profiles have more room to grow evenly
        momentum = sum(max(0.0, t["momentum"]) for t in trends) / len(trends)
        evidence = sum(strengths) / len(strengths)
        potential = 0.40 * mean_level + 0.25 * balance + 0.20 * momentum + 0.15 * evidence
        return round(max(0.0, min(1.0, potential)), 3)

    def _life_path(
        self,
        trends: List[Dict[str, Any]],
        goal_alignment: Dict[str, Dict[str, Any]],
    ) -> str:
        if not trends:
            return "Your path is still taking shape — begin with a palm or tarot reading."
        top = trends[0]
        element = self._dominant_element()
        parts = [
            f"A {element.lower()}-natured path currently centred on {top['name'].lower()}"
        ]
        if self.goals:
            parts.append(f", guided by your goal: \"{self.goals[0]}\"")
        direction_note = {
            "rising": "with momentum building in recent readings",
            "declining": "where recent readings suggest a pause for reflection",
            "stable": "with steady, consistent energy",
        }[top["direction"]]
        return f"{parts[0]}{parts[1] if len(parts) > 1 else ''}, {direction_note}."

    def _dominant_element(self) -> str:
        """Dominant element from the most recent palm reading, else tarot suits."""
        for r in reversed(self._prepared):
            signals = r["signals"]
            for element in ELEMENTS:
                if signals.get(f"palm.element_{element.lower()}"):
                    return element
            element_counts = {
                el: signals.get(f"tarot.element_{el.lower()}", 0.0) for el in ELEMENTS
            }
            best = max(element_counts, key=lambda el: element_counts[el])
            if element_counts[best] > 0:
                return best
        return "seeker"

    def _opportunities(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Top domains weighted by score & strength; rising domains first."""
        ranked = sorted(
            trends, key=lambda t: (t["direction"] == "rising", t["score"] * t["strength"]),
            reverse=True,
        )
        opportunities = []
        for trend in ranked[:3]:
            if trend["score"] < 0.3 and trend["direction"] != "rising":
                continue
            lead = {
                "rising": f"Momentum is building in {trend['name']} — this is the right moment to invest energy here.",
                "stable": f"{trend['name']} is a steady foundation — deepen it for compounding returns.",
                "declining": f"{trend['name']} has a strong base from earlier readings — renewed attention could revive it.",
            }[trend["direction"]]
            opportunities.append(
                {
                    "title": f"Opportunity: {trend['name']}",
                    "explanation": lead + " " + trend["explanation"],
                    "signals": trend["signals"][:3],
                    "confidence": trend["confidence"],
                }
            )
        return opportunities

    def _challenges(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Lowest-scoring / declining domains, framed as interpretive challenges."""
        ranked = sorted(
            trends,
            key=lambda t: (t["direction"] == "declining", -(t["score"] * t["strength"])),
        )
        challenges = []
        for trend in ranked[:3]:
            if trend["score"] > 0.65 and trend["direction"] != "declining":
                continue
            frame = {
                "declining": f"Recent readings show {trend['name'].lower()} softening — worth conscious attention.",
                "stable": f"{trend['name']} shows only a weak signal so far — evidence is limited, not necessarily negative.",
                "rising": f"{trend['name']} is rising from a low base — early-stage friction is normal.",
            }[trend["direction"]]
            challenges.append(
                {
                    "title": f"Challenge: {trend['name']}",
                    "explanation": frame + " " + trend["explanation"],
                    "signals": trend["signals"][:3],
                    "confidence": trend["confidence"],
                }
            )
        return challenges

    def _explanation(
        self,
        trends: List[Dict[str, Any]],
        goal_alignment: Dict[str, Dict[str, Any]],
        growth_potential: float,
    ) -> str:
        top = trends[0] if trends else None
        rising = [t["name"].lower() for t in trends if t["direction"] == "rising"]
        declining = [t["name"].lower() for t in trends if t["direction"] == "declining"]
        coverage = self.data_completeness()
        parts = [
            f"This analysis is a transparent, feature-based interpretation of your "
            f"{self.data_coverage['readings_analyzed']} stored reading(s) "
            f"({self.data_coverage['palm_readings']} palm, {self.data_coverage['tarot_readings']} tarot) — "
            f"not a prediction of future events."
        ]
        if top:
            parts.append(
                f"Your strongest current signal is {top['name']} "
                f"(score {top['score']:.2f}, {top['direction']})."
            )
        if rising:
            parts.append(f"Rising areas: {', '.join(rising)}.")
        if declining:
            parts.append(f"Softening areas: {', '.join(declining)}.")
        if goal_alignment:
            parts.append(
                f"Your profile goals and interests ({', '.join(a['source'] for a in goal_alignment.values())}) "
                f"were used as self-declared focus signals."
            )
        if coverage < 0.5:
            parts.append(
                "Data coverage is still limited, so treat these trends as early indications — "
                "additional readings will make them more reliable."
            )
        parts.append(f"Composite growth potential: {growth_potential:.2f}.")
        return " ".join(parts)

    def data_completeness(self) -> float:
        n = max(1, len(self._prepared))
        palm = sum(1 for r in self._prepared if r["type"] == "palm")
        tarot = n - palm
        return min(1.0, n / 6.0) * 0.5 + (
            min(1.0, palm / 2.0) * 0.25 + min(1.0, tarot / 2.0) * 0.25
        )

    @property
    def data_coverage(self) -> Dict[str, int]:
        n = len(self._prepared)
        palm = sum(1 for r in self._prepared if r["type"] == "palm")
        return {
            "readings_analyzed": n,
            "palm_readings": palm,
            "tarot_readings": n - palm,
            "goals_used": len(self.goals),
        }

    def _feature_vector(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Flattened feature vector — the training input shape for a future."""
        vector: Dict[str, Any] = {
            "n_readings": len(self._prepared),
            "palm_readings": self.data_coverage["palm_readings"],
            "tarot_readings": self.data_coverage["tarot_readings"],
            "n_goals": len(self.goals),
        }
        for trend in trends:
            d = trend["domain"]
            vector[f"domain_{d}_score"] = trend["score"]
            vector[f"domain_{d}_strength"] = trend["strength"]
            vector[f"domain_{d}_momentum"] = trend["momentum"]
        for r in self._prepared:
            for signal, value in r["signals"].items():
                key = signal.replace(".", "_")
                values = vector.setdefault(f"{key}_series", [])
                values.append(round(value, 3))
        return vector

    # empty state

    def _empty_result(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "method": METHOD,
            "life_path": "Your path is still taking shape — begin with a palm or tarot reading.",
            "current_trends": [],
            "opportunities": [],
            "challenges": [],
            "growth_potential": 0.5,
            "explanation": (
                "There are no completed readings to analyze yet. Once you complete a palm "
                "or tarot reading, this section will compute real trend signals from your "
                "own data. Nothing is predicted or assumed without evidence."
            ),
            "history": history,
            "data_coverage": {
                "readings_analyzed": 0,
                "palm_readings": 0,
                "tarot_readings": 0,
                "completeness": 0.0,
                "goals_used": len(self.goals),
            },
            "feature_vector": {"n_readings": 0, "n_goals": len(self.goals)},
        }

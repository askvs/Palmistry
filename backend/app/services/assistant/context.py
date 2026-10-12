"""Dashboard AI Assistant — role-scoped context builder."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.reading import ReadingStatus, ReadingType
from app.models.user import User, UserRole
from app.services import admin as admin_service
from app.services import consultation as consultation_service
from app.services import reading as reading_service
from app.services import recommendations as recommendation_service

ENGINE_NAME = "DashboardAssistant"
ENGINE_VERSION = "1.0.0"

DISCLAIMER = (
    "This analysis is grounded in your live platform data and is offered strictly for "
    "interpretive guidance, entertainment, and self-reflection. It is not medical, legal, "
    "psychological, or financial advice (Spec §49.19)."
)

ROLE_LABELS: Dict[str, str] = {
    UserRole.user.value: "Seeker",
    UserRole.tarot_reader.value: "Tarot Reader",
    UserRole.spiritual_consultant.value: "Spiritual Consultant",
    UserRole.admin.value: "Administrator",
}

# Recent-item window used for the highlight notes and the prompt digest.
_RECENT_LIMIT = 20

# Suggested questions are the fastest way into the assistant for each role.
_SUGGESTED_QUESTIONS: Dict[str, List[str]] = {
    UserRole.user.value: [
        "Give me an overall analysis of my readings",
        "What patterns repeat across my palm and tarot readings?",
        "Which life area needs the most attention right now?",
        "How is my spiritual journey trending?",
    ],
    UserRole.tarot_reader.value: [
        "Give me an overall analysis of the reading queue",
        "How much review work is waiting for me?",
        "What is the busiest reading type on the platform?",
        "How has divination activity moved this week?",
    ],
    UserRole.spiritual_consultant.value: [
        "Give me an overall analysis of my guidance queue",
        "What themes do seekers ask about most?",
        "How is my resolution rate and response time?",
        "Which threads are still waiting on my reply?",
    ],
    UserRole.admin.value: [
        "Give me an overall analysis of the platform",
        "How is user growth and engagement trending?",
        "Which role needs the most onboarding support?",
        "What should I look at first as an administrator?",
    ],
}


def _role_value(user: User) -> str:
    role = getattr(user, "role", None)
    return role.value if hasattr(role, "value") else str(role or UserRole.user.value)


def _by_key(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    """Collapse a [{key, count}] aggregate into a plain lookup."""
    out: Dict[str, int] = {}
    for row in rows or []:
        if isinstance(row, dict) and row.get(key) is not None:
            out[str(row[key])] = int(row.get("count") or 0)
    return out


def _pct(part: int, whole: int) -> int:
    return round((part / whole) * 100) if whole else 0


def _fmt_dt(value: Optional[datetime]) -> str:
    if not value:
        return "unknown"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _metric(label: str, value: Any, hint: Optional[str] = None) -> Dict[str, str]:
    return {"label": label, "value": str(value), "hint": hint}


# Seeker


def _seeker_snapshot(db: Session, user: User) -> Dict[str, Any]:
    analytics = reading_service.reading_analytics(db, user_id=user.id)
    readings, _ = reading_service.list_for_user(db, user.id, limit=_RECENT_LIMIT)
    consultations, _ = consultation_service.list_for_user(db, user.id)
    recommendations = recommendation_service.list_recommendations(
        db, user=user, limit=_RECENT_LIMIT
    )

    by_type = _by_key(analytics.get("by_type"), "type")
    by_status = _by_key(analytics.get("by_status"), "status")
    palm_count = by_type.get(ReadingType.palm.value, 0)
    tarot_count = by_type.get(ReadingType.tarot.value, 0)
    completed = by_status.get(ReadingStatus.completed.value, 0)

    latest_palm = next((r for r in readings if r.type == ReadingType.palm), None)
    palm_element = None
    if latest_palm:
        palm_element = (latest_palm.result or {}).get("palm_shape", {}).get("element")

    spreads = [
        (r.result or {}).get("spread") or r.title
        for r in readings
        if r.type == ReadingType.tarot
    ]
    spread_mix = sorted({s for s in spreads if s})

    interpreted = sum(
        1 for r in readings if (r.result or {}).get("ai_interpretation")
    )

    consultation_status = {}
    for c in consultations:
        status = getattr(c.status, "value", str(c.status))
        consultation_status[status] = consultation_status.get(status, 0) + 1

    open_threads = consultation_status.get("open", 0) + consultation_status.get("in_review", 0)

    metrics = [
        _metric("Total readings", analytics.get("total", 0), "Palm scans and tarot rituals"),
        _metric("Palm scans", palm_count, "Chirognomy & line analysis"),
        _metric("Tarot readings", tarot_count, "Spreads you have drawn"),
        _metric("Interpreted by AI", f"{_pct(interpreted, len(readings))}%", "Share with an AI narrative"),
        _metric("Open guidance threads", open_threads, "Waiting on a reader or consultant"),
        _metric("Recommendations", recommendations.get("total", 0), "Personalised suggestions on file"),
    ]

    highlights: List[Dict[str, str]] = [
        {
            "label": "Divination balance",
            "detail": (
                f"{palm_count} palm scan(s) and {tarot_count} tarot reading(s) — "
                f"{'palm-led' if palm_count > tarot_count else 'tarot-led' if tarot_count > palm_count else 'evenly split'}."
            ),
        },
        {
            "label": "Completion",
            "detail": f"{completed} of {analytics.get('total', 0)} reading(s) marked completed.",
        },
    ]
    if palm_element:
        highlights.append(
            {"label": "Dominant element", "detail": f"{palm_element} hand in your latest palm scan."}
        )
    if spread_mix:
        highlights.append(
            {"label": "Spreads drawn", "detail": ", ".join(spread_mix[:5])}
        )
    if recommendations.get("items"):
        top = recommendations["items"][0]
        highlights.append(
            {
                "label": "Top recommendation",
                "detail": f"{top.get('title', 'Untitled')} — {top.get('rec_type', 'general').replace('_', ' ')}.",
            }
        )
    if not readings:
        highlights.append(
            {
                "label": "Getting started",
                "detail": "No readings yet — your first palm scan or tarot ritual unlocks the analysis.",
            }
        )

    facts = [
        f"Seeker profile: {user.email}, member since {_fmt_dt(user.created_at)}.",
        f"Readings: total={analytics.get('total', 0)}, completed={completed}, palm={palm_count}, tarot={tarot_count}.",
    ]
    if palm_element:
        facts.append(f"Latest palm scan element: {palm_element}.")
    if spread_mix:
        facts.append(f"Tarot spreads drawn: {', '.join(spread_mix)}.")
    facts.append(
        f"Consultations: {consultation_status.get('open', 0)} open, "
        f"{consultation_status.get('in_review', 0)} in review, "
        f"{consultation_status.get('resolved', 0)} resolved."
    )
    facts.append(f"Personalised recommendations on file: {recommendations.get('total', 0)}.")
    facts.append(f"Readings with an AI interpretation: {interpreted} of {len(readings)} recent.")

    return {
        "scope": "your own readings, recommendations, and guidance threads",
        "headline": "Your personal divination and guidance picture",
        "metrics": metrics,
        "highlights": highlights,
        "facts": facts,
    }


# Tarot reader


def _reader_snapshot(db: Session, user: User) -> Dict[str, Any]:
    analytics = reading_service.reading_analytics(db)
    readings, _ = reading_service.list_for_user(db, None, limit=_RECENT_LIMIT)

    by_type = _by_key(analytics.get("by_type"), "type")
    by_status = _by_key(analytics.get("by_status"), "status")
    pending = by_status.get(ReadingStatus.pending.value, 0)
    completed = by_status.get(ReadingStatus.completed.value, 0)
    reviewed = sum(1 for r in readings if r.reviewed_by)

    metrics = [
        _metric("Platform readings", analytics.get("total", 0), "Across every account"),
        _metric("Pending review", pending, "Awaiting certification"),
        _metric("Certified", completed, "Marked completed by a reader"),
        _metric("Palm / Tarot split", f"{by_type.get('palm', 0)} / {by_type.get('tarot', 0)}", "By reading type"),
        _metric("Activity last 7 days", sum(d.get("count", 0) for d in analytics.get("per_day", [])), "Rolling week"),
    ]

    highlights = [
        {
            "label": "Review backlog",
            "detail": f"{pending} reading(s) waiting, {reviewed} of the {len(readings)} most recent already reviewed.",
        },
        {
            "label": "Reading mix",
            "detail": (
                f"{by_type.get('palm', 0)} palm and {by_type.get('tarot', 0)} tarot — "
                f"{'palm-heavy' if by_type.get('palm', 0) > by_type.get('tarot', 0) else 'tarot-heavy' if by_type.get('tarot', 0) > by_type.get('palm', 0) else 'balanced'}."
            ),
        },
    ]
    if not readings:
        highlights.append(
            {"label": "Queue empty", "detail": "No platform readings yet — the queue fills as seekers divine."}
        )

    facts = [
        f"Reader console scope: every reading on the platform (reader/admin RBAC).",
        f"Readings: total={analytics.get('total', 0)}, pending={pending}, completed={completed}.",
        f"Type split: palm={by_type.get('palm', 0)}, tarot={by_type.get('tarot', 0)}.",
        f"Readings in the last 7 days: {sum(d.get('count', 0) for d in analytics.get('per_day', []))}.",
        f"Recent batch: {reviewed} of {len(readings)} already certified.",
    ]

    return {
        "scope": "every reading on the platform, newest first",
        "headline": "The querent reading queue at a glance",
        "metrics": metrics,
        "highlights": highlights,
        "facts": facts,
    }


# Spiritual consultant


def _consultant_snapshot(db: Session, user: User) -> Dict[str, Any]:
    queue, queue_total = consultation_service.list_queue(db)
    effectiveness = consultation_service.effectiveness(db)
    insights = consultation_service.insights(db)

    by_status = _by_key(insights.get("by_status"), "status")
    top_topics = insights.get("top_topics") or []
    awaiting = effectiveness.get("awaiting_reply", 0)

    metrics = [
        _metric("Guidance threads", queue_total, "All seeker inquiries"),
        _metric("Open", by_status.get("open", 0), "Not yet picked up"),
        _metric("In review", by_status.get("in_review", 0), "Being worked on"),
        _metric("Resolved", by_status.get("resolved", 0), "Counsel dispatched"),
        _metric("Awaiting your reply", awaiting, "Seeker spoke last"),
        _metric(
            "Resolution rate",
            f"{round((effectiveness.get('resolution_rate') or 0) * 100)}%",
            "Threads with dispatched counsel",
        ),
    ]

    highlights = [
        {
            "label": "Queue shape",
            "detail": (
                f"{by_status.get('open', 0)} open, {by_status.get('in_review', 0)} in review, "
                f"{by_status.get('resolved', 0)} resolved of {queue_total}."
            ),
        },
        {
            "label": "Your responsiveness",
            "detail": (
                f"{awaiting} thread(s) waiting on you; average first response "
                f"{_minutes(effectiveness.get('avg_first_response_minutes'))}."
            ),
        },
    ]
    if top_topics:
        highlights.append(
            {
                "label": "Dominant themes",
                "detail": ", ".join(f"{t.get('topic')} ({t.get('count')})" for t in top_topics[:5]),
            }
        )
    if not queue:
        highlights.append(
            {"label": "Queue clear", "detail": "Every seeker inquiry has received counsel."}
        )

    facts = [
        "Consultant console scope: every guidance thread on the platform.",
        f"Threads: total={queue_total}, open={by_status.get('open', 0)}, "
        f"in_review={by_status.get('in_review', 0)}, resolved={by_status.get('resolved', 0)}.",
        f"Resolution rate: {round((effectiveness.get('resolution_rate') or 0) * 100)}%.",
        f"Awaiting your reply: {awaiting}; average first response "
        f"{_minutes(effectiveness.get('avg_first_response_minutes'))}.",
        f"Top inquiry themes: "
        + (", ".join(f"{t.get('topic')} ({t.get('count')})" for t in top_topics) or "none recorded"),
    ]

    return {
        "scope": "every seeker guidance thread and its outcome",
        "headline": "Your guidance queue and effectiveness",
        "metrics": metrics,
        "highlights": highlights,
        "facts": facts,
    }


def _minutes(value: Optional[float]) -> str:
    if value is None:
        return "not measured"
    if value < 60:
        return f"{round(value)} min"
    return f"{(value / 60):.1f} h"


# Administrator


def _admin_snapshot(db: Session, user: User) -> Dict[str, Any]:
    platform = admin_service.platform_analytics(db, days=7)
    readings = admin_service.reading_statistics(db, days=30)
    audit, audit_total = admin_service.list_audit_logs(db, limit=1)
    _ = audit  # only the total is surfaced; the trail itself lives in the admin console

    users_by_role = platform.get("users_by_role") or []
    engagement = platform.get("engagement") or {}
    signups = sum(d.get("count", 0) for d in platform.get("signups_per_day", []))
    readings_in_period = sum(d.get("count", 0) for d in readings.get("per_day", []))

    role_mix = {r.get("role"): r.get("count", 0) for r in users_by_role}
    seekers = role_mix.get(UserRole.user.value, 0)
    staff = sum(v for k, v in role_mix.items() if k != UserRole.user.value)

    ai_configured = bool(settings.GROQ_API_KEY or settings.OPENAI_API_KEY)

    metrics = [
        _metric("Registered users", platform.get("users_total", 0), f"+{signups} in 7 days"),
        _metric("Active users", platform.get("users_active", 0), "Non-suspended accounts"),
        _metric("Total readings", platform.get("readings_total", 0), f"{readings_in_period} in 30 days"),
        _metric("Consultations", platform.get("consultations_total", 0), "Guidance inquiries"),
        _metric("Seekers / staff", f"{seekers} / {staff}", "Role distribution"),
        _metric("Audit entries", audit_total, "Administrative actions logged"),
    ]

    activated = engagement.get("users_with_readings", 0)
    returning = engagement.get("users_with_multiple_readings", 0)
    highlights = [
        {
            "label": "Engagement",
            "detail": (
                f"{activated} of {platform.get('users_total', 0)} account(s) have run a reading; "
                f"{returning} came back for more."
            ),
        },
        {
            "label": "Growth",
            "detail": f"{signups} new account(s) in the last 7 days, {readings_in_period} reading(s) in 30 days.",
        },
        {
            "label": "AI engine",
            "detail": (
                "Online provider configured." if ai_configured else "Running the deterministic rule engine (no provider key)."
            ),
        },
    ]

    facts = [
        "Admin console scope: platform-wide governance, analytics, and the audit trail.",
        f"Users: total={platform.get('users_total', 0)}, active={platform.get('users_active', 0)}, "
        f"signups_last_7d={signups}.",
        f"Role mix: " + (", ".join(f"{k}={v}" for k, v in role_mix.items()) or "none"),
        f"Readings: total={platform.get('readings_total', 0)}, last_30d={readings_in_period}.",
        f"Consultations: total={platform.get('consultations_total', 0)}.",
        f"Engagement: activated={activated}, returning={returning} of {platform.get('users_total', 0)}.",
        f"Audit entries logged: {audit_total}.",
        f"AI provider configured: {ai_configured}.",
    ]

    return {
        "scope": "platform-wide analytics, governance, and the audit trail",
        "headline": "Platform health, growth, and governance",
        "metrics": metrics,
        "highlights": highlights,
        "facts": facts,
    }


_SNAPSHOT_BUILDERS = {
    UserRole.user.value: _seeker_snapshot,
    UserRole.tarot_reader.value: _reader_snapshot,
    UserRole.spiritual_consultant.value: _consultant_snapshot,
    UserRole.admin.value: _admin_snapshot,
}


def build_context(db: Session, user: User) -> Dict[str, Any]:
    """Assemble the assistant's role-scoped view of the caller's data."""
    role = _role_value(user)
    builder = _SNAPSHOT_BUILDERS.get(role, _seeker_snapshot)
    snapshot = builder(db, user)
    snapshot.update(
        {
            "role": role,
            "role_label": ROLE_LABELS.get(role, "Seeker"),
            "suggested_questions": _SUGGESTED_QUESTIONS.get(role, _SUGGESTED_QUESTIONS[UserRole.user.value]),
            "disclaimer": DISCLAIMER,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return snapshot

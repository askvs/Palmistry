"""Consultation service (FR-006)."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation, ConsultationMessage, ConsultationStatus
from app.models.reading import Reading
from app.models.user import UserRole


STAFF_ROLES = (UserRole.tarot_reader, UserRole.spiritual_consultant, UserRole.admin)


class ConsultationError(Exception):
    code = "CONSULTATION_ERROR"
    status_code = 400

    def __init__(self, message: str = "Consultation operation failed"):
        self.message = message
        super().__init__(message)


class ConsultationNotFound(ConsultationError):
    code = "CONSULTATION_NOT_FOUND"
    status_code = 404


def _get(db: Session, consultation_id: uuid.UUID) -> Consultation:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ConsultationNotFound("Consultation not found")
    return consultation


def create_request(db: Session, user, *, topic: str, message: str) -> Consultation:
    consultation = Consultation(user_id=user.id, topic=topic, message=message)
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation


def list_for_user(db: Session, user_id: uuid.UUID) -> tuple[list[Consultation], int]:
    items = db.scalars(
        select(Consultation)
        .where(Consultation.user_id == user_id)
        .order_by(Consultation.created_at.desc())
    ).all()
    return list(items), len(items)


def list_queue(db: Session) -> tuple[list[Consultation], int]:
    items = db.scalars(
        select(Consultation).order_by(Consultation.created_at.desc()).limit(200)
    ).all()
    return list(items), len(items)


def get_any(db: Session, consultation_id: uuid.UUID) -> Consultation:
    return _get(db, consultation_id)


def get_owned(db: Session, consultation_id: uuid.UUID, user_id: uuid.UUID) -> Consultation:
    consultation = _get(db, consultation_id)
    if consultation.user_id != user_id:
        raise ConsultationNotFound("Consultation not found")
    return consultation


def ensure_participant(consultation: Consultation, user) -> None:
    """Only the seeker who opened the thread or a responsible role may read/write it."""
    is_seeker = consultation.user_id == user.id
    is_staff = user.role in STAFF_ROLES or consultation.consultant_id == user.id
    if not (is_seeker or is_staff):
        raise ConsultationNotFound("Consultation not found")


def list_messages(db: Session, consultation_id: uuid.UUID) -> list[ConsultationMessage]:
    from sqlalchemy.orm import selectinload

    return list(
        db.scalars(
            select(ConsultationMessage)
            .where(ConsultationMessage.consultation_id == consultation_id)
            .options(selectinload(ConsultationMessage.sender))
            .order_by(ConsultationMessage.created_at)
        ).all()
    )


def post_message(
    db: Session, consultation: Consultation, user, *, body: str
) -> ConsultationMessage:
    """Append a message to the thread and move the consultation along."""
    is_seeker = consultation.user_id == user.id
    message = ConsultationMessage(
        consultation_id=consultation.id, sender_id=user.id, body=body
    )
    if is_seeker:
        if consultation.status == ConsultationStatus.resolved:
            consultation.status = ConsultationStatus.open
    else:
        if consultation.consultant_id is None:
            consultation.consultant_id = user.id
        if consultation.status == ConsultationStatus.open:
            consultation.status = ConsultationStatus.in_review
    db.add(message)
    db.commit()
    db.refresh(message)
    db.refresh(consultation)
    return message


def provide_guidance(
    db: Session, consultation: Consultation, consultant, *, guidance: str, status: ConsultationStatus | None
) -> Consultation:
    consultation.guidance = guidance
    consultation.consultant_id = consultant.id
    consultation.status = status or ConsultationStatus.resolved
    db.commit()
    db.refresh(consultation)
    return consultation


def assign(db: Session, consultation: Consultation, consultant_id: uuid.UUID | None) -> Consultation:
    consultation.consultant_id = consultant_id
    if consultant_id is not None and consultation.status == ConsultationStatus.open:
        consultation.status = ConsultationStatus.in_review
    db.commit()
    db.refresh(consultation)
    return consultation


def update_status(db: Session, consultation: Consultation, status: ConsultationStatus) -> Consultation:
    consultation.status = status
    db.commit()
    db.refresh(consultation)
    return consultation


def effectiveness(db: Session) -> dict:
    total_guidance = db.scalar(
        select(func.count())
        .select_from(Reading)
        .where(Reading.reviewed_by.is_not(None))
    ) or 0
    consultations = db.scalars(select(Consultation)).all()
    with_guidance = sum(1 for c in consultations if c.guidance)

    # Thread activity metrics from the message log.
    from app.models.user import User

    sender_rows = db.execute(
        select(
            ConsultationMessage.consultation_id,
            ConsultationMessage.created_at,
            User.role,
        )
        .join(User, ConsultationMessage.sender_id == User.id, isouter=True)
        .order_by(ConsultationMessage.created_at.asc())
    ).all()

    first_staff_reply: dict[uuid.UUID, datetime] = {}
    last_sender_is_staff: dict[uuid.UUID, bool] = {}
    for consultation_id, created_at, role in sender_rows:
        is_staff = role in STAFF_ROLES
        last_sender_is_staff[consultation_id] = is_staff
        if is_staff and consultation_id not in first_staff_reply:
            first_staff_reply[consultation_id] = created_at

    response_minutes = [
        (first_staff_reply[c.id] - c.created_at).total_seconds() / 60.0
        for c in consultations
        if c.id in first_staff_reply
    ]
    avg_first_response = (
        sum(response_minutes) / len(response_minutes) if response_minutes else None
    )

    # Count threads awaiting a reply.
    awaiting_reply = 0
    for c in consultations:
        if c.status == ConsultationStatus.resolved:
            continue
        if c.id in last_sender_is_staff:
            if not last_sender_is_staff[c.id]:
                awaiting_reply += 1
        elif c.guidance is None:
            awaiting_reply += 1

    return {
        "total_guidance": int(total_guidance),
        "with_guidance": with_guidance,
        "avg_user_rating": None,
        "ratings_count": 0,
        "resolution_rate": (with_guidance / len(consultations)) if consultations else 0.0,
        "avg_first_response_minutes": avg_first_response,
        "awaiting_reply": awaiting_reply,
    }


def insights(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(Consultation)) or 0
    by_status_rows = db.execute(
        select(Consultation.status, func.count()).group_by(Consultation.status)
    ).all()
    top_topics_rows = db.execute(
        select(Consultation.topic, func.count().label("count"))
        .group_by(Consultation.topic)
        .order_by(func.count().desc())
        .limit(5)
    ).all()
    return {
        "total_requests": int(total),
        "by_status": [{"status": row[0].value, "count": row[1]} for row in by_status_rows],
        "top_topics": [{"topic": row[0], "count": row[1]} for row in top_topics_rows],
    }


def user_trends(db: Session) -> dict:
    from app.models.user import User

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    active_users = db.scalar(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    ) or 0

    readings_rows = db.execute(
        select(
            func.date_trunc("day", Reading.created_at).label("day"),
            func.count().label("count"),
        )
        .where(Reading.created_at >= week_ago)
        .group_by("day")
        .order_by("day")
    ).all()
    consultation_rows = db.execute(
        select(
            func.date_trunc("day", Consultation.created_at).label("day"),
            func.count().label("count"),
        )
        .where(Consultation.created_at >= week_ago)
        .group_by("day")
        .order_by("day")
    ).all()

    return {
        "total_users": int(total_users),
        "active_users": int(active_users),
        "readings_per_day": [
            {"day": row[0].strftime("%Y-%m-%d"), "count": row[1]} for row in readings_rows
        ],
        "consultations_per_day": [
            {"day": row[0].strftime("%Y-%m-%d"), "count": row[1]} for row in consultation_rows
        ],
    }


# Client roster (consultant workspace)


def list_clients(db: Session, *, user_id: uuid.UUID | None = None) -> list[dict]:
    """Live client roster for the consultant workspace."""
    from app.models.profile import Profile
    from app.models.user import User

    now = datetime.now(timezone.utc)
    month_start = now - timedelta(days=30)

    # One grouped aggregate per table, joined to the roster of thread authors.
    threads = (
        select(
            Consultation.user_id.label("user_id"),
            func.count().label("threads"),
            func.count()
            .filter(Consultation.status == ConsultationStatus.resolved)
            .label("resolved"),
            func.max(Consultation.updated_at).label("last_thread_at"),
        )
        .group_by(Consultation.user_id)
        .subquery()
    )
    readings = (
        select(
            Reading.user_id.label("user_id"),
            func.count().label("readings"),
            func.count().filter(Reading.created_at >= month_start).label("recent"),
            func.max(Reading.created_at).label("last_reading_at"),
        )
        .group_by(Reading.user_id)
        .subquery()
    )

    query = (
        select(
            User,
            threads.c.threads,
            threads.c.resolved,
            threads.c.last_thread_at,
            func.coalesce(readings.c.readings, 0),
            func.coalesce(readings.c.recent, 0),
            readings.c.last_reading_at,
        )
        .join(threads, threads.c.user_id == User.id)
        .outerjoin(readings, readings.c.user_id == User.id)
        .order_by(threads.c.last_thread_at.desc())
    )
    if user_id is not None:
        query = query.where(User.id == user_id)

    rows = db.execute(query).all()
    # Batch-load profiles; roster stays small.
    profiles = {}
    if rows:
        profile_ids = [row[0].id for row in rows]
        profiles = {
            profile.user_id: profile
            for profile in db.scalars(
                select(Profile).where(Profile.user_id.in_(profile_ids))
            ).all()
        }

    clients = []
    for user, thread_count, resolved, last_thread_at, reading_count, recent, last_reading_at in rows:
        profile = profiles.get(user.id)
        clients.append(
            {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "age_group": profile.age_group if profile else None,
                "interests": sorted(i.interest for i in profile.interests) if profile else [],
                "goals": [g.text for g in profile.goals] if profile else [],
                "engagement": {
                    "threads": int(thread_count or 0),
                    "resolved_threads": int(resolved or 0),
                    "readings": int(reading_count or 0),
                    "readings_last_30_days": int(recent or 0),
                    "last_reading_at": last_reading_at,
                    "last_thread_at": last_thread_at,
                },
            }
        )
    return clients

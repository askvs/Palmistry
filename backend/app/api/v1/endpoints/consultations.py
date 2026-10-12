"""Spiritual Consultant endpoints (FR-006)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user, require_spiritual_consultant
from app.db.session import get_db
from app.models.user import User
from app.services.notifications import notify_consultation_message, notify_new_question
from app.utils.logging import logger
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationGuidanceUpdate,
    ConsultationInsights,
    ConsultationListOut,
    ConsultationMessageCreate,
    ConsultationMessageListOut,
    ConsultationMessageOut,
    ConsultationOut,
    GuidanceEffectiveness,
    UserTrends,
)
from app.services import consultation as consultation_service

STAFF_ROLE_VALUES = {role.value for role in consultation_service.STAFF_ROLES}

router = APIRouter(dependencies=[Depends(get_current_user)])

consultant_router = APIRouter(
    prefix="/consultant",
    dependencies=[Depends(require_spiritual_consultant)],
)


# User: request and view consultations (FR-006)


@router.post("/consultations", response_model=ConsultationOut, status_code=201)
async def create_consultation(
    payload: ConsultationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consultation = consultation_service.create_request(
        db, user, topic=payload.topic, message=payload.message
    )
    try:
        notify_new_question(
            consultation_id=consultation.id,
            asker_id=user.id,
            asker_name=user.full_name or user.email,
            topic=consultation.topic,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to notify consultants of consultation %s: %s", consultation.id, exc)
    return ConsultationOut.model_validate(consultation)


@router.get("/consultations", response_model=ConsultationListOut)
async def list_my_consultations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = consultation_service.list_for_user(db, user.id)
    return ConsultationListOut(
        items=[ConsultationOut.model_validate(c) for c in items],
        total=total,
    )


def _message_out(message) -> ConsultationMessageOut:
    sender = message.sender
    role = sender.role.value if sender is not None else None
    return ConsultationMessageOut(
        id=message.id,
        consultation_id=message.consultation_id,
        sender_id=message.sender_id,
        sender_name=sender.full_name if sender is not None else None,
        sender_role=role,
        is_staff=role in STAFF_ROLE_VALUES,
        body=message.body,
        created_at=message.created_at,
    )


@router.get(
    "/consultations/{consultation_id}/messages",
    response_model=ConsultationMessageListOut,
)
async def list_consultation_messages(
    consultation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consultation = consultation_service.get_any(db, consultation_id)
    consultation_service.ensure_participant(consultation, user)
    items = consultation_service.list_messages(db, consultation_id)
    return ConsultationMessageListOut(
        items=[_message_out(m) for m in items], total=len(items)
    )


@router.post(
    "/consultations/{consultation_id}/messages",
    response_model=ConsultationMessageOut,
    status_code=201,
)
async def post_consultation_message(
    consultation_id: uuid.UUID,
    payload: ConsultationMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consultation = consultation_service.get_any(db, consultation_id)
    consultation_service.ensure_participant(consultation, user)
    message = consultation_service.post_message(
        db, consultation, user, body=payload.body
    )
    try:
        sender_is_staff = user.role.value in STAFF_ROLE_VALUES
        notify_consultation_message(
            message_id=message.id,
            consultation_id=consultation.id,
            owner_id=consultation.user_id,
            sender_is_staff=sender_is_staff,
            sender_id=user.id,
            sender_name=user.full_name or user.email,
            body_snippet=(message.body or "")[:80],
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to notify consultation message %s: %s", message.id, exc)
    return _message_out(message)


@consultant_router.get("/consultations", response_model=ConsultationListOut)
async def list_consultations(db: Session = Depends(get_db)):
    items, total = consultation_service.list_queue(db)
    return ConsultationListOut(
        items=[ConsultationOut.model_validate(c) for c in items],
        total=total,
    )


@consultant_router.post(
    "/consultations/{consultation_id}/guidance", response_model=ConsultationOut
)
async def provide_guidance(
    consultation_id: uuid.UUID,
    payload: ConsultationGuidanceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consultation = consultation_service.get_any(db, consultation_id)
    consultation = consultation_service.provide_guidance(
        db,
        consultation,
        user,
        guidance=payload.guidance,
        status=payload.status,
    )
    return ConsultationOut.model_validate(consultation)


@consultant_router.get("/clients")
async def list_clients(db: Session = Depends(get_db)):
    """Live client roster: every seeker with an active guidance thread."""
    items = consultation_service.list_clients(db)
    return {"items": items, "total": len(items)}


@consultant_router.get("/insights/effectiveness", response_model=GuidanceEffectiveness)
async def guidance_effectiveness(db: Session = Depends(get_db)):
    return GuidanceEffectiveness(**consultation_service.effectiveness(db))


@consultant_router.get("/insights/trends", response_model=UserTrends)
async def user_trends(db: Session = Depends(get_db)):
    return UserTrends(**consultation_service.user_trends(db))


@consultant_router.get("/insights/consultations", response_model=ConsultationInsights)
async def consultation_insights(db: Session = Depends(get_db)):
    return ConsultationInsights(**consultation_service.insights(db))

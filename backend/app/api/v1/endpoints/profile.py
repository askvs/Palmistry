"""User profile endpoints (TASK-004 / FR-005, WF-02)."""

import uuid

from fastapi import APIRouter, Depends, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.auth.rbac import get_current_user
from app.config import settings
from app.db.session import get_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import (
    GoalCreate,
    GoalOut,
    GoalUpdate,
    InterestsUpdate,
    ProfileOut,
    ProfileUpdate,
)
from app.services.profile import service
from app.services.profile.errors import AvatarNotFound

router = APIRouter(dependencies=[Depends(get_current_user)])


def _profile_out(profile: Profile) -> ProfileOut:
    """Build the response while the DB session is still open."""
    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        age_group=profile.age_group,
        avatar_key=profile.avatar_key,
        default_deck=profile.default_deck,
        favorite_spread=profile.favorite_spread,
        tone=profile.tone,
        notify_daily_guidance=profile.notify_daily_guidance,
        notify_reminders=profile.notify_reminders,
        notify_sms=profile.notify_sms,
        interests=[item.interest for item in profile.interests],
        goals=[GoalOut.model_validate(goal) for goal in profile.goals],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    return _profile_out(profile)


@router.patch("/profile", response_model=ProfileOut)
async def patch_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    profile = service.update_profile(db, user, updates)
    return _profile_out(profile)


@router.put("/profile/interests", response_model=ProfileOut)
async def put_interests(
    payload: InterestsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    service.replace_interests(db, profile, payload.interests)
    return _profile_out(profile)


@router.get("/profile/goals", response_model=list[GoalOut])
async def list_goals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    return [GoalOut.model_validate(goal) for goal in profile.goals]


@router.post("/profile/goals", response_model=GoalOut, status_code=201)
async def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    goal = service.create_goal(db, profile, payload.text.strip())
    return GoalOut.model_validate(goal)


@router.patch("/profile/goals/{goal_id}", response_model=GoalOut)
async def patch_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    goal = service.update_goal(db, profile, goal_id, payload.text.strip())
    return GoalOut.model_validate(goal)


@router.delete("/profile/goals/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    service.delete_goal(db, profile, goal_id)


@router.put("/profile/avatar", response_model=ProfileOut)
async def put_avatar(
    avatar: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await avatar.read(settings.AVATAR_MAX_SIZE_MB * 1024 * 1024 + 1)
    profile = service.get_or_create_profile(db, user)
    service.store_avatar(db, profile, data)
    return _profile_out(profile)


@router.delete("/profile/avatar", response_model=ProfileOut)
async def delete_avatar(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    service.delete_avatar(db, profile)
    return _profile_out(profile)


@router.get("/profile/avatar")
async def get_avatar(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = service.get_or_create_profile(db, user)
    stored = service.read_avatar(profile)
    if stored is None:
        raise AvatarNotFound("No avatar has been uploaded")
    content, media_type = stored
    etag = f'"{int(profile.updated_at.timestamp())}"'
    headers = {"ETag": etag, "Cache-Control": "private, max-age=31536000"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=content, media_type=media_type, headers=headers)

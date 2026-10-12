"""Profile management service (TASK-004 / FR-005)."""

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.profile import Profile, ProfileGoal, ProfileInterest
from app.models.user import User
from app.services.profile.catalog import (
    AVATAR_CONTENT_TYPES,
    AVATAR_MAGIC,
    MAX_GOALS_PER_PROFILE,
)
from app.services.profile.errors import (
    AvatarTooLarge,
    GoalLimitReached,
    GoalNotFound,
    UnsupportedAvatarFormat,
)
from app.utils.logging import logger


def get_or_create_profile(db: Session, user: User) -> Profile:
    """Return the user's profile, creating it on first access."""
    profile = db.scalars(select(Profile).where(Profile.user_id == user.id)).first()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info("profile created user_id=%s profile_id=%s", user.id, profile.id)
    return profile


def update_profile(db: Session, user: User, updates: dict) -> Profile:
    """Apply partial profile updates; `full_name` is mirrored onto users."""
    full_name = updates.pop("full_name", None)
    if full_name is not None:
        user.full_name = full_name

    profile = get_or_create_profile(db, user)
    if "age_group" in updates:
        profile.age_group = updates["age_group"]
    for field in ("default_deck", "favorite_spread", "tone"):
        if updates.get(field) is not None:
            setattr(profile, field, updates[field])
    for field in ("notify_daily_guidance", "notify_reminders", "notify_sms"):
        if updates.get(field) is not None:
            setattr(profile, field, updates[field])
    db.commit()
    db.refresh(profile)
    return profile


def replace_interests(db: Session, profile: Profile, interests: list[str]) -> Profile:
    """Replace the profile's interest list with the desired one."""
    desired: list[str] = list(dict.fromkeys(interests))
    existing = {item.interest: item for item in profile.interests}
    profile.interests = [existing.get(name) or ProfileInterest(interest=name) for name in desired]
    db.commit()
    db.refresh(profile)
    return profile


def create_goal(db: Session, profile: Profile, text: str) -> ProfileGoal:
    count = db.scalar(
        select(func.count()).select_from(ProfileGoal).where(ProfileGoal.profile_id == profile.id)
    )
    if count is not None and count >= MAX_GOALS_PER_PROFILE:
        raise GoalLimitReached(f"A profile can hold at most {MAX_GOALS_PER_PROFILE} goals")
    goal = ProfileGoal(profile_id=profile.id, text=text)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, profile: Profile, goal_id: uuid.UUID, text: str) -> ProfileGoal:
    goal = _get_owned_goal(db, profile, goal_id)
    goal.text = text
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, profile: Profile, goal_id: uuid.UUID) -> None:
    goal = _get_owned_goal(db, profile, goal_id)
    db.delete(goal)
    db.commit()


def _get_owned_goal(db: Session, profile: Profile, goal_id: uuid.UUID) -> ProfileGoal:
    goal = db.scalars(
        select(ProfileGoal).where(
            ProfileGoal.id == goal_id, ProfileGoal.profile_id == profile.id
        )
    ).first()
    if goal is None:
        raise GoalNotFound("Goal not found")
    return goal


def _avatar_dir() -> Path:
    path = Path(settings.UPLOAD_DIR) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def detect_avatar_content_type(data: bytes) -> str:
    for magic, content_type in AVATAR_MAGIC:
        if data.startswith(magic):
            return content_type
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise UnsupportedAvatarFormat("Avatar must be a JPG, PNG, or WEBP image")


def store_avatar(db: Session, profile: Profile, data: bytes) -> Profile:
    """Validate, persist, and record an avatar image; replaces any previous one."""
    limit = settings.AVATAR_MAX_SIZE_MB * 1024 * 1024
    if len(data) > limit:
        raise AvatarTooLarge(f"Avatar must be {settings.AVATAR_MAX_SIZE_MB} MB or smaller")
    if not data:
        raise UnsupportedAvatarFormat("Avatar file is empty")
    content_type = detect_avatar_content_type(data)
    extension = AVATAR_CONTENT_TYPES[content_type]

    avatar_key = f"{profile.id}{extension}"
    (_avatar_dir() / avatar_key).write_bytes(data)
    if profile.avatar_key and profile.avatar_key != avatar_key:
        _delete_avatar_file(profile.avatar_key)

    profile.avatar_key = avatar_key
    db.commit()
    db.refresh(profile)
    logger.info("avatar stored profile_id=%s key=%s", profile.id, avatar_key)
    return profile


def read_avatar(profile: Profile) -> tuple[bytes, str] | None:
    """Return (bytes, content_type) for the stored avatar, or None."""
    if profile.avatar_key is None:
        return None
    path = _avatar_dir() / profile.avatar_key
    if not path.is_file():
        return None
    content_type = "application/octet-stream"
    for candidate, extension in AVATAR_CONTENT_TYPES.items():
        if profile.avatar_key.endswith(extension):
            content_type = candidate
            break
    return path.read_bytes(), content_type


def delete_avatar(db: Session, profile: Profile) -> Profile:
    if profile.avatar_key is None:
        return profile
    _delete_avatar_file(profile.avatar_key)
    profile.avatar_key = None
    db.commit()
    db.refresh(profile)
    logger.info("avatar deleted profile_id=%s", profile.id)
    return profile


def _delete_avatar_file(avatar_key: str) -> None:
    path = _avatar_dir() / avatar_key
    if path.is_file():
        path.unlink()

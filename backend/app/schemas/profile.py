import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.profile.catalog import (
    AGE_GROUPS,
    DECKS,
    GOAL_TEXT_MAX_LENGTH,
    INTERESTS,
    MAX_INTERESTS,
    SPREADS,
    TONES,
)


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    created_at: datetime
    updated_at: datetime


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    age_group: str | None
    avatar_key: str | None
    default_deck: str
    favorite_spread: str
    tone: str
    notify_daily_guidance: bool
    notify_reminders: bool
    notify_sms: bool
    interests: list[str]
    goals: list[GoalOut]
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    age_group: str | None = None
    default_deck: str | None = None
    favorite_spread: str | None = None
    tone: str | None = None
    notify_daily_guidance: bool | None = None
    notify_reminders: bool | None = None
    notify_sms: bool | None = None

    @field_validator("age_group")
    @classmethod
    def _valid_age_group(cls, value: str | None) -> str | None:
        if value is not None and value not in AGE_GROUPS:
            raise ValueError(f"age_group must be one of: {', '.join(AGE_GROUPS)}")
        return value

    @field_validator("default_deck")
    @classmethod
    def _valid_deck(cls, value: str | None) -> str | None:
        if value is not None and value not in DECKS:
            raise ValueError(f"default_deck must be one of: {', '.join(DECKS)}")
        return value

    @field_validator("favorite_spread")
    @classmethod
    def _valid_spread(cls, value: str | None) -> str | None:
        if value is not None and value not in SPREADS:
            raise ValueError(f"favorite_spread must be one of: {', '.join(SPREADS)}")
        return value

    @field_validator("tone")
    @classmethod
    def _valid_tone(cls, value: str | None) -> str | None:
        if value is not None and value not in TONES:
            raise ValueError(f"tone must be one of: {', '.join(TONES)}")
        return value


class InterestsUpdate(BaseModel):
    interests: list[str] = Field(default_factory=list)

    @field_validator("interests")
    @classmethod
    def _valid_interests(cls, value: list[str]) -> list[str]:
        unique: list[str] = list(dict.fromkeys(value))
        unknown = [item for item in unique if item not in INTERESTS]
        if unknown:
            raise ValueError(
                f"Unknown interests: {', '.join(unknown)}. Allowed: {', '.join(INTERESTS)}"
            )
        if len(unique) > MAX_INTERESTS:
            raise ValueError(f"At most {MAX_INTERESTS} interests can be selected")
        return unique


class GoalCreate(BaseModel):
    text: str = Field(min_length=1, max_length=GOAL_TEXT_MAX_LENGTH)


class GoalUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=GOAL_TEXT_MAX_LENGTH)

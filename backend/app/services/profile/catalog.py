"""Controlled vocabularies for user profiles (FR-005)."""

AGE_GROUPS: tuple[str, ...] = (
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55-64",
    "65+",
)

INTERESTS: tuple[str, ...] = (
    "Tarot",
    "Palmistry",
    "Numerology",
    "Meditation",
    "Astrology",
    "Crystal Healing",
    "Energy Work",
    "Manifestation",
    "Dream Interpretation",
    "Runes",
    "Chakras",
    "Mindfulness",
)

MAX_INTERESTS = 10

DECKS: tuple[str, ...] = (
    "Rider-Waite-Smith",
)

DEFAULT_DECK = "Rider-Waite-Smith"

SPREADS: tuple[str, ...] = (
    "Single Card",
    "Three Card",
    "Relationship",
    "Career",
    "Celtic Cross",
    "Life Path",
)

DEFAULT_SPREAD = "Three Card"

TONES: tuple[str, ...] = ("Gentle", "Direct", "Balanced")

DEFAULT_TONE = "Gentle"

MAX_GOALS_PER_PROFILE = 25
GOAL_TEXT_MAX_LENGTH = 500

AVATAR_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

AVATAR_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)
# WEBP is RIFF-prefixed with "WEBP" at bytes 8..12; checked separately.

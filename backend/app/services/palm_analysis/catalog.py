"""Palmistry reference catalog service (Spec §49.5, FR-009, FR-011, TASK-005)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
PALM_DATA_DIR = ROOT_DIR / "data" / "palmistry"
LANDMARKS_DATA_DIR = ROOT_DIR / "data" / "landmarks"

_CACHED_LINES: dict[str, Any] | None = None
_CACHED_MOUNTS: dict[str, Any] | None = None
_CACHED_LANDMARKS: dict[str, Any] | None = None


def get_palm_lines_catalog() -> list[dict[str, Any]]:
    """Load and return the 5 primary palm lines catalog."""
    global _CACHED_LINES
    if _CACHED_LINES is not None:
        return _CACHED_LINES["lines"]

    path = PALM_DATA_DIR / "lines_catalog.json"
    if not path.exists():
        raise FileNotFoundError(f"Palm lines catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHED_LINES = data
    return data["lines"]


def get_palm_line_by_id(line_id: str) -> dict[str, Any] | None:
    """Retrieve a palm line definition by ID (life_line, head_line, heart_line, fate_line, sun_line)."""
    lines = get_palm_lines_catalog()
    for line in lines:
        if line["id"] == line_id:
            return line
    return None


def get_palm_mounts_catalog() -> list[dict[str, Any]]:
    """Load and return the 6 traditional palm mounts catalog."""
    global _CACHED_MOUNTS
    if _CACHED_MOUNTS is not None:
        return _CACHED_MOUNTS["mounts"]

    path = PALM_DATA_DIR / "mounts_catalog.json"
    if not path.exists():
        raise FileNotFoundError(f"Palm mounts catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHED_MOUNTS = data
    return data["mounts"]


def get_palm_mount_by_id(mount_id: str) -> dict[str, Any] | None:
    """Retrieve a palm mount definition by ID."""
    mounts = get_palm_mounts_catalog()
    for mount in mounts:
        if mount["id"] == mount_id:
            return mount
    return None


def get_hand_landmarks_schema() -> dict[str, Any]:
    """Load and return the MediaPipe 21 hand landmarks reference schema."""
    global _CACHED_LANDMARKS
    if _CACHED_LANDMARKS is not None:
        return _CACHED_LANDMARKS

    path = LANDMARKS_DATA_DIR / "hand_landmarks_schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Hand landmarks schema not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHED_LANDMARKS = data
    return data


def get_landmark_by_index(index: int) -> dict[str, Any] | None:
    """Retrieve a specific landmark by MediaPipe index (0 to 20)."""
    schema = get_hand_landmarks_schema()
    for lm in schema.get("landmarks", []):
        if lm["index"] == index:
            return lm
    return None

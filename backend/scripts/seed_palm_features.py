"""Seed and validate Palmistry lines, mounts, and landmark reference catalogs (TASK-005, Spec §49.5).

Usage (from backend/):
    python -m scripts.seed_palm_features
"""
import sys
from pathlib import Path

from app.services.palm_analysis.catalog import (
    get_palm_lines_catalog,
    get_palm_mounts_catalog,
    get_hand_landmarks_schema,
)


def seed_palm_features() -> None:
    print("Seeding & validating Palmistry reference datasets...")

    # Validate lines
    lines = get_palm_lines_catalog()
    if len(lines) != 5:
        raise ValueError(f"Expected 5 palm lines, found {len(lines)}")

    required_lines = {"life_line", "head_line", "heart_line", "fate_line", "sun_line"}
    found_lines = {line["id"] for line in lines}
    missing_lines = required_lines - found_lines
    if missing_lines:
        raise ValueError(f"Missing required palm lines: {missing_lines}")

    for line in lines:
        assert line["name"], f"Missing name for {line['id']}"
        assert line["description"], f"Missing description for {line['id']}"
        assert len(line["significance"]) > 0, f"Missing significance for {line['id']}"
        assert len(line["variations"]) > 0, f"Missing variations for {line['id']}"
        print(f"  [OK] Palm line valid: {line['name']} ({len(line['variations'])} variations)")

    # Validate mounts
    mounts = get_palm_mounts_catalog()
    if len(mounts) != 6:
        raise ValueError(f"Expected 6 mounts, found {len(mounts)}")

    for mount in mounts:
        assert mount["name"], f"Missing name for {mount['id']}"
        assert mount["anatomical_anchor"]["landmark_name"], f"Missing anchor for {mount['id']}"
        assert len(mount["core_attributes"]) > 0, f"Missing attributes for {mount['id']}"
        print(f"  [OK] Palm mount valid: {mount['name']} (Anchor: {mount['anatomical_anchor']['landmark_name']})")

    # Validate landmarks
    schema = get_hand_landmarks_schema()
    landmarks = schema.get("landmarks", [])
    if len(landmarks) != 21:
        raise ValueError(f"Expected 21 MediaPipe landmarks, found {len(landmarks)}")

    indices = [lm["index"] for lm in landmarks]
    assert indices == list(range(21)), f"Landmark indices out of sequence: {indices}"
    print(f"  [OK] MediaPipe hand landmark topology valid: {len(landmarks)} points, {len(schema.get('connections', []))} connections")

    print("Palmistry reference datasets verified and ready.")


if __name__ == "__main__":
    try:
        seed_palm_features()
    except Exception as exc:
        print(f"seed_palm_features failed: {exc}", file=sys.stderr)
        sys.exit(1)

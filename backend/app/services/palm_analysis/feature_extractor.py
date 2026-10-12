"""Palm feature extraction service (Spec §49.5, FR-008, FR-011)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from app.services.palm_analysis.catalog import get_palm_mounts_catalog
from app.services.palm_analysis.hand_landmarker import HandLandmarkResult, LandmarkPoint


@dataclass
class PalmShapeResult:
    element: str               # 'Earth', 'Air', 'Fire', 'Water'
    palm_width: float          # Normalized
    palm_height: float         # Normalized
    aspect_ratio: float        # width / height
    finger_to_palm_ratio: float
    description: str
    traits: List[str]


@dataclass
class FingerDetail:
    name: str
    length: float
    ratio_to_middle: float


@dataclass
class FingerStructureResult:
    fingers: Dict[str, FingerDetail]
    digit_ratio_2d_4d: float   # Index to Ring ratio
    digit_ratio_interpretation: str
    pinky_reaches_ring_dip: bool
    pinky_communication_trait: str
    thumb_angle_degrees: float
    thumb_flexibility: str


@dataclass
class MountDetail:
    mount_id: str
    name: str
    planetary_ruler: str
    element: str
    prominence: str            # 'underdeveloped', 'balanced', 'prominent'
    score: float               # 0.0 to 1.0
    meaning: str
    core_attributes: List[str]
    center: Tuple[float, float] = (0.5, 0.5)  # Normalized (x, y)


def _euclidean_distance(p1: LandmarkPoint, p2: LandmarkPoint) -> float:
    """Calculate Euclidean distance between two landmarks in normalized coordinates."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def _angle_between(p_origin: LandmarkPoint, p1: LandmarkPoint, p2: LandmarkPoint) -> float:
    """Calculate angle in degrees between vectors (origin -> p1) and (origin -> p2)."""
    v1 = (p1.x - p_origin.x, p1.y - p_origin.y)
    v2 = (p2.x - p_origin.x, p2.y - p_origin.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    if mag1 * mag2 == 0:
        return 0.0
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def extract_palm_shape(landmarks: List[LandmarkPoint]) -> PalmShapeResult:
    """Classify the elemental hand shape (Earth, Air, Fire, Water)."""
    lms = {lm.index: lm for lm in landmarks}

    # Palm Width: Index MCP (5) to Pinky MCP (17)
    palm_width = _euclidean_distance(lms[5], lms[17])

    # Palm Height: Wrist (0) to Middle MCP (9)
    palm_height = _euclidean_distance(lms[0], lms[9])
    if palm_height <= 0:
        palm_height = 0.001

    aspect_ratio = palm_width / palm_height

    # Middle Finger Length: Middle MCP (9) to Middle Tip (12)
    middle_finger_len = _euclidean_distance(lms[9], lms[12])
    finger_to_palm_ratio = middle_finger_len / palm_height

    # Elemental Hand Shape Matrix:
    is_square_palm = 0.82 <= aspect_ratio <= 1.18
    is_long_fingers = finger_to_palm_ratio >= 0.80

    if is_square_palm:
        if is_long_fingers:
            element = "Air"
            desc = "Air Hand: Square palm with elegant, long fingers. Signifies analytical intellect, curiosity, and verbal dexterity."
            traits = ["intellectual", "curious", "analytical", "communicative", "objective"]
        else:
            element = "Earth"
            desc = "Earth Hand: Solid, square palm with practical, sturdy fingers. Signifies grounded reliability, honesty, and pragmatism."
            traits = ["practical", "grounded", "reliable", "steadfast", "realistic"]
    else:
        if is_long_fingers:
            element = "Water"
            desc = "Water Hand: Rectangular palm with long, graceful fingers. Signifies profound empathy, intuitive sensitivity, and rich creative imagination."
            traits = ["intuitive", "empathetic", "creative", "sensitive", "receptive"]
        else:
            element = "Fire"
            desc = "Fire Hand: Long, vibrant rectangular palm with agile, compact fingers. Signifies dynamic passion, charismatic enthusiasm, and pioneering leadership."
            traits = ["passionate", "energetic", "bold", "charismatic", "action-oriented"]

    return PalmShapeResult(
        element=element,
        palm_width=round(palm_width, 4),
        palm_height=round(palm_height, 4),
        aspect_ratio=round(aspect_ratio, 3),
        finger_to_palm_ratio=round(finger_to_palm_ratio, 3),
        description=desc,
        traits=traits,
    )


def extract_finger_structure(landmarks: List[LandmarkPoint]) -> FingerStructureResult:
    """Analyze finger proportions, digit ratios, and thumb dynamics."""
    lms = {lm.index: lm for lm in landmarks}

    thumb_len = _euclidean_distance(lms[1], lms[4])
    index_len = _euclidean_distance(lms[5], lms[8])
    middle_len = _euclidean_distance(lms[9], lms[12])
    ring_len = _euclidean_distance(lms[13], lms[16])
    pinky_len = _euclidean_distance(lms[17], lms[20])

    m_len = max(middle_len, 0.001)

    fingers = {
        "thumb": FingerDetail(name="Thumb", length=round(thumb_len, 4), ratio_to_middle=round(thumb_len / m_len, 3)),
        "index": FingerDetail(name="Index (Jupiter)", length=round(index_len, 4), ratio_to_middle=round(index_len / m_len, 3)),
        "middle": FingerDetail(name="Middle (Saturn)", length=round(middle_len, 4), ratio_to_middle=1.0),
        "ring": FingerDetail(name="Ring (Apollo)", length=round(ring_len, 4), ratio_to_middle=round(ring_len / m_len, 3)),
        "pinky": FingerDetail(name="Pinky (Mercury)", length=round(pinky_len, 4), ratio_to_middle=round(pinky_len / m_len, 3)),
    }

    # Digit Ratio 2D:4D (Index to Ring)
    r_len = max(ring_len, 0.001)
    digit_ratio_2d_4d = round(index_len / r_len, 3)

    if digit_ratio_2d_4d > 1.02:
        digit_interp = "High 2D:4D ratio: Strong Jupiter emphasis indicating pronounced leadership aspiration, social authority, and proactive ambition."
    elif digit_ratio_2d_4d < 0.96:
        digit_interp = "Low 2D:4D ratio: Strong Apollo emphasis reflecting natural creative instinct, spatial awareness, competitive drive, and artistic flair."
    else:
        digit_interp = "Balanced 2D:4D ratio: Harmonious equilibrium between leadership ambition and creative self-expression."

    # Pinky reach relative to Ring DIP joint (Landmark 15)
    pinky_reaches_dip = lms[20].y <= lms[15].y
    if pinky_reaches_dip:
        pinky_trait = "Long Mercury finger reaching past the ring DIP joint: Excellent communication fluency, sharp negotiating skills, and natural persuasion."
    else:
        pinky_trait = "Mercury finger slightly modest: Prefers concise, straightforward communication over ornate rhetoric; values sincere clarity."

    # Thumb spread angle between Thumb MCP (2) and Index MCP (5) from Wrist (0)
    thumb_angle = round(_angle_between(lms[0], lms[2], lms[5]), 1)
    if thumb_angle > 55:
        thumb_flex = "Wide thumb spread: High independent initiative, generous mindset, and bold freedom of thought."
    elif thumb_angle < 35:
        thumb_flex = "Close thumb posture: Cautious, discreet, conservative steward of energy and material resources."
    else:
        thumb_flex = "Balanced thumb spread: Practical balance between autonomy, adaptability, and measured judgment."

    return FingerStructureResult(
        fingers=fingers,
        digit_ratio_2d_4d=digit_ratio_2d_4d,
        digit_ratio_interpretation=digit_interp,
        pinky_reaches_ring_dip=pinky_reaches_dip,
        pinky_communication_trait=pinky_trait,
        thumb_angle_degrees=thumb_angle,
        thumb_flexibility=thumb_flex,
    )


def extract_mounts(
    landmarks: List[LandmarkPoint],
    clahe_image: np.ndarray,
) -> List[MountDetail]:
    """Estimate mount prominence (Jupiter, Saturn, Apollo, Mercury, Venus, Moon)."""
    mounts_catalog = get_palm_mounts_catalog()
    lms = {lm.index: lm for lm in landmarks}
    h, w = clahe_image.shape[:2]

    results: List[MountDetail] = []

    # Mapping each mount to landmark center and sampling radius
    sample_centers = {
        "mount_of_jupiter": (lms[5].px, lms[5].py + int(h * 0.04)),
        "mount_of_saturn": (lms[9].px, lms[9].py + int(h * 0.04)),
        "mount_of_apollo": (lms[13].px, lms[13].py + int(h * 0.04)),
        "mount_of_mercury": (lms[17].px, lms[17].py + int(h * 0.04)),
        "mount_of_venus": (int((lms[1].px + lms[2].px) / 2), int((lms[1].py + lms[2].py) / 2)),
        "mount_of_moon": (int(lms[0].px + (lms[17].px - lms[0].px) * 0.7), int(lms[0].py - h * 0.1)),
    }

    radius = max(8, int(min(h, w) * 0.035))

    for mount_def in mounts_catalog:
        m_id = mount_def["id"]
        center = sample_centers.get(m_id, (lms[0].px, lms[0].py))
        cx, cy = center

        # Sample local patch
        y1, y2 = max(0, cy - radius), min(h, cy + radius)
        x1, x2 = max(0, cx - radius), min(w, cx + radius)

        if y2 > y1 and x2 > x1:
            patch = clahe_image[y1:y2, x1:x2]
            mean_intensity = float(np.mean(patch))
            variance = float(np.var(patch))
        else:
            mean_intensity = 128.0
            variance = 50.0

        # Normalized score based on texture intensity and clarity
        raw_score = (mean_intensity / 255.0) * 0.6 + (min(variance, 400.0) / 400.0) * 0.4
        score = round(max(0.2, min(0.95, raw_score)), 2)

        if score > 0.72:
            prominence = "prominent"
        elif score < 0.42:
            prominence = "underdeveloped"
        else:
            prominence = "balanced"

        meaning = mount_def.get("prominence_meanings", {}).get(prominence, "")
        norm_center = (round(cx / max(w, 1), 4), round(cy / max(h, 1), 4))

        results.append(
            MountDetail(
                mount_id=m_id,
                name=mount_def["name"],
                planetary_ruler=mount_def["planetary_ruler"],
                element=mount_def["element"],
                prominence=prominence,
                score=score,
                meaning=meaning,
                core_attributes=mount_def["core_attributes"],
                center=norm_center,
            )
        )

    return results

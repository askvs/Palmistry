"""Palm line detection and geometric extraction engine (Spec §49.5, FR-009)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from app.services.palm_analysis.catalog import get_palm_lines_catalog
from app.services.palm_analysis.hand_landmarker import HandLandmarkResult, LandmarkPoint


@dataclass
class LinePoint:
    x: float  # Normalized [0, 1]
    y: float  # Normalized [0, 1]


@dataclass
class PalmLineResult:
    line_id: str
    name: str
    classical_name: str
    detected: bool
    confidence: float
    length_normalized: float
    curvature: float
    depth_clarity: float
    continuity: str          # 'unbroken', 'intermittent', 'chained', 'forked'
    variation_type: str
    variation_description: str
    interpretation: str
    significance: List[str]
    coordinates: List[Tuple[float, float]]  # List of normalized (x, y)


def _distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _sample_crease_corridor(
    crease_map: np.ndarray,
    start_pt: Tuple[int, int],
    end_pt: Tuple[int, int],
    steps: int = 15,
    search_radius: int = 12,
    curve_bias: float = 0.0,
) -> Tuple[List[Tuple[float, float]], float, float]:
    """Sample points along an anatomical line corridor, tracing local crease peaks."""
    h, w = crease_map.shape[:2]
    pts: List[Tuple[float, float]] = []
    intensities: List[float] = []

    dx = end_pt[0] - start_pt[0]
    dy = end_pt[1] - start_pt[1]
    norm_dist = math.sqrt(dx * dx + dy * dy)
    if norm_dist == 0:
        norm_dist = 1.0

    # Normal vector to corridor for perpendicular peak search
    perp_x = -dy / norm_dist
    perp_y = dx / norm_dist

    detected_crease_count = 0

    for s in range(steps + 1):
        t = s / float(steps)
        # Linear base point with parabolic curve bias
        curv_offset = math.sin(t * math.pi) * curve_bias
        base_x = start_pt[0] + t * dx + perp_x * curv_offset
        base_y = start_pt[1] + t * dy + perp_y * curv_offset

        best_x, best_y = base_x, base_y
        max_val = -1.0

        # Search perpendicular window for crease peak
        for r in range(-search_radius, search_radius + 1, 2):
            sx = int(base_x + perp_x * r)
            sy = int(base_y + perp_y * r)
            if 0 <= sx < w and 0 <= sy < h:
                val = float(crease_map[sy, sx])
                if val > max_val:
                    max_val = val
                    best_x, best_y = sx, sy

        if max_val > 30.0:
            detected_crease_count += 1

        intensities.append(max(0.0, max_val))
        pts.append((round(best_x / w, 4), round(best_y / h, 4)))

    mean_intensity = min(1.0, float(np.mean(intensities)) / 180.0) if intensities else 0.5
    continuity = detected_crease_count / float(steps + 1)
    return pts, mean_intensity, continuity


def detect_palm_lines(
    landmarks_res: HandLandmarkResult,
    crease_map: np.ndarray,
    clahe_image: np.ndarray,
) -> List[PalmLineResult]:
    """Detect all 5 required palm lines using landmark-anchored corridor tracing."""
    lines_catalog = get_palm_lines_catalog()
    catalog_by_id = {line["id"]: line for line in lines_catalog}

    lms = {lm.index: lm for lm in landmarks_res.landmarks}
    h, w = crease_map.shape[:2]
    handedness = landmarks_res.handedness

    # Key landmark pixel points:
    wrist_px = (lms[0].px, lms[0].py)
    thumb_cmc_px = (lms[1].px, lms[1].py)
    thumb_mcp_px = (lms[2].px, lms[2].py)
    index_mcp_px = (lms[5].px, lms[5].py)
    middle_mcp_px = (lms[9].px, lms[9].py)
    ring_mcp_px = (lms[13].px, lms[13].py)
    pinky_mcp_px = (lms[17].px, lms[17].py)

    # Lateral sign: +1 for Left hand palmar, -1 for Right hand palmar
    sign = 1 if handedness == "Left" else -1

    # True Euclidean scale of the palm (invariant to hand rotation)
    palm_h_px = max(10, int(math.hypot(wrist_px[0] - middle_mcp_px[0], wrist_px[1] - middle_mcp_px[1])))

    results: List[PalmLineResult] = []

    # 1. LIFE LINE
    life_start = (int((index_mcp_px[0] + thumb_mcp_px[0]) / 2), int((index_mcp_px[1] + thumb_mcp_px[1]) / 2))
    life_end = (int(wrist_px[0] + sign * (thumb_cmc_px[0] - wrist_px[0]) * 0.3), int(wrist_px[1] - palm_h_px * 0.05))
    life_pts, life_clarity, life_cont = _sample_crease_corridor(
        crease_map, life_start, life_end, steps=16, search_radius=14, curve_bias=sign * palm_h_px * 0.22
    )
    life_chord = _distance_2d(life_pts[0], life_pts[-1])
    life_len = sum(_distance_2d(life_pts[i], life_pts[i + 1]) for i in range(len(life_pts) - 1))
    life_curv = round(life_len / max(0.001, life_chord), 2)
    life_conf = round(min(0.98, max(0.60, 0.45 + life_clarity * 0.35 + life_cont * 0.2)), 2)
    # Honest detection: a crease was actually traceable along the corridor.
    life_detected = life_cont >= 0.35 and life_clarity >= 0.12

    if life_curv > 1.25:
        life_var = "wide_arc"
        life_var_desc = "Broad sweeping arc around Mount of Venus."
        life_interp = "Vibrant, adventurous enthusiasm, warm generosity, strong physical vitality."
    elif life_conf > 0.8:
        life_var = "long_and_deep"
        life_var_desc = "Long, well-etched, steady line."
        life_interp = "Exceptional vitality, grounded resilience, robust endurance throughout life."
    else:
        life_var = "close_to_thumb"
        life_var_desc = "Line stays moderately enclosed near the thumb base."
        life_interp = "Measured pacing, careful steward of physical stamina, values quiet security."

    cat_life = catalog_by_id.get("life_line", {})
    results.append(
        PalmLineResult(
            line_id="life_line",
            name=cat_life.get("name", "Life Line"),
            classical_name=cat_life.get("classical_name", "Linea Vitae"),
            detected=life_detected,
            confidence=life_conf,
            length_normalized=round(life_len, 3),
            curvature=life_curv,
            depth_clarity=round(life_clarity, 2),
            continuity="unbroken" if life_cont > 0.6 else "intermittent",
            variation_type=life_var,
            variation_description=life_var_desc,
            interpretation=life_interp,
            significance=cat_life.get("significance", []),
            coordinates=life_pts,
        )
    )

    # 2. HEAD LINE
    head_start = life_start
    head_end = (int(pinky_mcp_px[0] + sign * (wrist_px[0] - pinky_mcp_px[0]) * 0.3), int(pinky_mcp_px[1] + palm_h_px * 0.38))
    head_pts, head_clarity, head_cont = _sample_crease_corridor(
        crease_map, head_start, head_end, steps=14, search_radius=12, curve_bias=-sign * palm_h_px * 0.08
    )
    head_chord = _distance_2d(head_pts[0], head_pts[-1])
    head_len = sum(_distance_2d(head_pts[i], head_pts[i + 1]) for i in range(len(head_pts) - 1))
    head_curv = round(head_len / max(0.001, head_chord), 2)
    head_conf = round(min(0.96, max(0.60, 0.45 + head_clarity * 0.35 + head_cont * 0.2)), 2)
    head_detected = head_cont >= 0.35 and head_clarity >= 0.12

    # Check slope towards Moon (lower palm) vs straight across
    y_drop = head_pts[-1][1] - head_pts[0][1]
    if y_drop > 0.12:
        head_var = "sloping_toward_moon"
        head_var_desc = "Gently slanting downward toward the intuitive Mount of Moon."
        head_interp = "Rich creative imagination, intuitive intellect, literary and aesthetic talent."
    elif head_curv > 1.12:
        head_var = "writers_fork"
        head_var_desc = "Creative bifurcation near termination (Writer's Fork)."
        head_interp = "Rare balance of sharp practical pragmatism and visionary creative genius."
    else:
        head_var = "straight_and_horizontal"
        head_var_desc = "Straight, clear trajectory across upper percussion."
        head_interp = "Clear logical focus, analytical precision, objective problem solving, realistic."

    cat_head = catalog_by_id.get("head_line", {})
    results.append(
        PalmLineResult(
            line_id="head_line",
            name=cat_head.get("name", "Head Line"),
            classical_name=cat_head.get("classical_name", "Linea Capitis"),
            detected=head_detected,
            confidence=head_conf,
            length_normalized=round(head_len, 3),
            curvature=head_curv,
            depth_clarity=round(head_clarity, 2),
            continuity="unbroken" if head_cont > 0.6 else "intermittent",
            variation_type=head_var,
            variation_description=head_var_desc,
            interpretation=head_interp,
            significance=cat_head.get("significance", []),
            coordinates=head_pts,
        )
    )

    # 3. HEART LINE
    heart_start = (int(pinky_mcp_px[0]), int(pinky_mcp_px[1] + palm_h_px * 0.18))
    heart_end = (int(index_mcp_px[0] + (middle_mcp_px[0] - index_mcp_px[0]) * 0.4), int(index_mcp_px[1] + palm_h_px * 0.08))
    heart_pts, heart_clarity, heart_cont = _sample_crease_corridor(
        crease_map, heart_start, heart_end, steps=14, search_radius=12, curve_bias=-palm_h_px * 0.14
    )
    heart_chord = _distance_2d(heart_pts[0], heart_pts[-1])
    heart_len = sum(_distance_2d(heart_pts[i], heart_pts[i + 1]) for i in range(len(heart_pts) - 1))
    heart_curv = round(heart_len / max(0.001, heart_chord), 2)
    heart_conf = round(min(0.97, max(0.60, 0.48 + heart_clarity * 0.32 + heart_cont * 0.2)), 2)
    heart_detected = heart_cont >= 0.35 and heart_clarity >= 0.12

    # Termination position check: closer to index (Jupiter) or middle (Saturn)
    dist_to_jupiter = _distance_2d(heart_pts[-1], (lms[5].x, lms[5].y))
    dist_to_saturn = _distance_2d(heart_pts[-1], (lms[9].x, lms[9].y))

    if dist_to_jupiter < dist_to_saturn * 0.85:
        heart_var = "curved_to_jupiter"
        heart_var_desc = "Curving upward into Mount of Jupiter."
        heart_interp = "Idealistic in love, affectionate, deeply loyal, noble romantic expectations."
    elif dist_to_saturn < dist_to_jupiter * 0.85:
        heart_var = "straight_and_terminating_at_saturn"
        heart_var_desc = "Terminates under Mount of Saturn."
        heart_interp = "Pragmatic, emotionally self-reliant, values practical action over dramatic words."
    else:
        heart_var = "ending_between_jupiter_and_saturn"
        heart_var_desc = "Balanced termination between index and middle fingers."
        heart_interp = "Harmonious emotional balance: warm-hearted affection guided by healthy boundaries."

    cat_heart = catalog_by_id.get("heart_line", {})
    results.append(
        PalmLineResult(
            line_id="heart_line",
            name=cat_heart.get("name", "Heart Line"),
            classical_name=cat_heart.get("classical_name", "Linea Mensalis"),
            detected=heart_detected,
            confidence=heart_conf,
            length_normalized=round(heart_len, 3),
            curvature=heart_curv,
            depth_clarity=round(heart_clarity, 2),
            continuity="unbroken" if heart_cont > 0.6 else "intermittent",
            variation_type=heart_var,
            variation_description=heart_var_desc,
            interpretation=heart_interp,
            significance=cat_heart.get("significance", []),
            coordinates=heart_pts,
        )
    )

    # 4. FATE LINE (Destiny Line)
    fate_start = (int(wrist_px[0] + (middle_mcp_px[0] - wrist_px[0]) * 0.2), int(wrist_px[1] - palm_h_px * 0.08))
    fate_end = (int(middle_mcp_px[0]), int(middle_mcp_px[1] + palm_h_px * 0.15))
    fate_pts, fate_clarity, fate_cont = _sample_crease_corridor(
        crease_map, fate_start, fate_end, steps=12, search_radius=10, curve_bias=0.0
    )
    fate_chord = _distance_2d(fate_pts[0], fate_pts[-1])
    fate_len = sum(_distance_2d(fate_pts[i], fate_pts[i + 1]) for i in range(len(fate_pts) - 1))
    fate_curv = round(fate_len / max(0.001, fate_chord), 2)
    fate_conf = round(min(0.92, max(0.52, 0.40 + fate_clarity * 0.35 + fate_cont * 0.25)), 2)
    fate_detected = fate_cont >= 0.35 and fate_clarity >= 0.12

    if fate_conf > 0.72:
        fate_var = "deep_and_straight"
        fate_var_desc = "Clear vertical ascent towards Mount of Saturn."
        fate_interp = "Strong sense of vocational clarity, self-directed career ambition, high persistence."
    elif fate_conf > 0.55:
        fate_var = "rising_from_life_line"
        fate_var_desc = "Ascends supported by foundational personal grit."
        fate_interp = "Self-made professional success: career breakthroughs won through disciplined personal initiative."
    else:
        fate_var = "faint_or_absent"
        fate_var_desc = "Flexible, adaptable vertical crease."
        fate_interp = "Self-authored destiny: open to diverse career transitions and entrepreneurial fluidity."

    cat_fate = catalog_by_id.get("fate_line", {})
    results.append(
        PalmLineResult(
            line_id="fate_line",
            name=cat_fate.get("name", "Fate Line"),
            classical_name=cat_fate.get("classical_name", "Linea Saturni"),
            detected=fate_detected,
            confidence=fate_conf,
            length_normalized=round(fate_len, 3),
            curvature=fate_curv,
            depth_clarity=round(fate_clarity, 2),
            continuity="unbroken" if fate_cont > 0.55 else "intermittent",
            variation_type=fate_var,
            variation_description=fate_var_desc,
            interpretation=fate_interp,
            significance=cat_fate.get("significance", []),
            coordinates=fate_pts,
        )
    )

    # 5. SUN LINE (Apollo Line)
    sun_start = (int(wrist_px[0] + (ring_mcp_px[0] - wrist_px[0]) * 0.35), int(wrist_px[1] - palm_h_px * 0.22))
    sun_end = (int(ring_mcp_px[0]), int(ring_mcp_px[1] + palm_h_px * 0.12))
    sun_pts, sun_clarity, sun_cont = _sample_crease_corridor(
        crease_map, sun_start, sun_end, steps=10, search_radius=10, curve_bias=0.0
    )
    sun_chord = _distance_2d(sun_pts[0], sun_pts[-1])
    sun_len = sum(_distance_2d(sun_pts[i], sun_pts[i + 1]) for i in range(len(sun_pts) - 1))
    sun_curv = round(sun_len / max(0.001, sun_chord), 2)
    sun_conf = round(min(0.90, max(0.50, 0.38 + sun_clarity * 0.35 + sun_cont * 0.27)), 2)
    sun_detected = sun_cont >= 0.35 and sun_clarity >= 0.12

    if sun_conf > 0.68:
        sun_var = "strong_and_unbroken"
        sun_var_desc = "Distinct solar ridge ascending toward ring finger."
        sun_interp = "Public creative recognition, charismatic magnetism, acknowledged artistic flair."
    elif sun_conf > 0.55:
        sun_var = "rising_from_heart_line"
        sun_var_desc = "Upper solar branch rising from Heart Line."
        sun_interp = "Late-blooming brilliance: greatest recognition and creative fulfillment achieved in maturity."
    else:
        sun_var = "absent"
        sun_var_desc = "Modest or subtle solar ridge."
        sun_interp = "Quiet personal fulfillment: contentment achieved through steady inner mastery rather than fame."

    cat_sun = catalog_by_id.get("sun_line", {})
    results.append(
        PalmLineResult(
            line_id="sun_line",
            name=cat_sun.get("name", "Sun Line"),
            classical_name=cat_sun.get("classical_name", "Linea Solaris"),
            detected=sun_detected,
            confidence=sun_conf,
            length_normalized=round(sun_len, 3),
            curvature=sun_curv,
            depth_clarity=round(sun_clarity, 2),
            continuity="unbroken" if sun_cont > 0.55 else "intermittent",
            variation_type=sun_var,
            variation_description=sun_var_desc,
            interpretation=sun_interp,
            significance=cat_sun.get("significance", []),
            coordinates=sun_pts,
        )
    )

    return results

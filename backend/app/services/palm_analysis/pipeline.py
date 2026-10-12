"""Palm analysis orchestrator pipeline (Spec §27.1, §49.4, §49.5, Module 3)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np

from app.services.palm_analysis.feature_extractor import (
    extract_finger_structure,
    extract_mounts,
    extract_palm_shape,
)
from app.services.palm_analysis.hand_landmarker import extract_hand_landmarks
from app.services.palm_analysis.line_detector import detect_palm_lines
from app.services.palm_analysis.preprocessor import (
    PalmValidationError,
    preprocess_palm_image,
)

MODEL_NAME = "MediaPipe HandLandmarker + OpenCV Crease Pipeline"
MODEL_VERSION = "1.0.0"


def analyze_palm_image(
    image_bytes: bytes,
    preferred_hand: Optional[str] = None,
    enforce_palmar: bool = True,
) -> Dict[str, Any]:
    """Execute end-to-end palm analysis pipeline on raw image bytes."""
    start_time = datetime.now(timezone.utc)

    # 1. Preprocess & Validate
    preprocessed = preprocess_palm_image(image_bytes)

    # 2. Extract MediaPipe Hand Landmarks & Validate Orientation
    landmark_res = extract_hand_landmarks(
        preprocessed.rgb,
        enforce_palmar=enforce_palmar,
    )

    # 3. Extract Elemental Palm Shape
    shape_res = extract_palm_shape(landmark_res.landmarks)

    # 4. Extract Finger Structure & Digit Ratios
    finger_res = extract_finger_structure(landmark_res.landmarks)

    # 5. Extract Mount Prominence
    mounts_res = extract_mounts(landmark_res.landmarks, preprocessed.clahe)

    # 6. Detect & Quantify 5 Primary Lines (Life, Head, Heart, Fate, Sun)
    lines_res = detect_palm_lines(
        landmark_res,
        preprocessed.creases,
        preprocessed.clahe,
    )

    # 7. Compute Overall Analysis Confidence
    line_confs = [l.confidence for l in lines_res]
    mount_confs = [m.score for m in mounts_res]
    overall_confidence = round(
        (np.mean(line_confs) * 0.6 + np.mean(mount_confs) * 0.2 + landmark_res.handedness_confidence * 0.2),
        2,
    )

    # 8. Assemble Full Payload
    return {
        "metadata": {
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "timestamp": start_time.isoformat(),
            "overall_confidence": float(overall_confidence),
            "original_resolution": {
                "width": preprocessed.original_size[0],
                "height": preprocessed.original_size[1],
            },
            "analyzed_resolution": {
                "width": preprocessed.normalized_size[0],
                "height": preprocessed.normalized_size[1],
            },
        },
        "hand": {
            "detected_handedness": landmark_res.handedness,
            "handedness_confidence": round(landmark_res.handedness_confidence, 3),
            "preferred_hand": preferred_hand or landmark_res.handedness,
            "is_palmar": landmark_res.is_palmar,
            "landmarks_count": len(landmark_res.landmarks),
            "palm_bounding_box": {
                "min_x": landmark_res.palm_bbox[0],
                "min_y": landmark_res.palm_bbox[1],
                "max_x": landmark_res.palm_bbox[2],
                "max_y": landmark_res.palm_bbox[3],
            },
            "landmarks": [
                {
                    "index": lm.index,
                    "name": lm.name,
                    "x": round(lm.x, 4),
                    "y": round(lm.y, 4),
                    "z": round(lm.z, 4),
                }
                for lm in landmark_res.landmarks
            ],
        },
        "palm_shape": {
            "element": shape_res.element,
            "palm_width": shape_res.palm_width,
            "palm_height": shape_res.palm_height,
            "aspect_ratio": shape_res.aspect_ratio,
            "finger_to_palm_ratio": shape_res.finger_to_palm_ratio,
            "description": shape_res.description,
            "traits": shape_res.traits,
        },
        "finger_structure": {
            "digit_ratio_2d_4d": finger_res.digit_ratio_2d_4d,
            "digit_ratio_interpretation": finger_res.digit_ratio_interpretation,
            "pinky_reaches_ring_dip": finger_res.pinky_reaches_ring_dip,
            "pinky_trait": finger_res.pinky_communication_trait,
            "thumb_angle_degrees": finger_res.thumb_angle_degrees,
            "thumb_flexibility": finger_res.thumb_flexibility,
            "fingers": {
                k: {
                    "name": v.name,
                    "length": v.length,
                    "ratio_to_middle": v.ratio_to_middle,
                }
                for k, v in finger_res.fingers.items()
            },
        },
        "mounts": [
            {
                "mount_id": m.mount_id,
                "name": m.name,
                "planetary_ruler": m.planetary_ruler,
                "element": m.element,
                "prominence": m.prominence,
                "score": m.score,
                "meaning": m.meaning,
                "core_attributes": m.core_attributes,
                "center": {
                    "x": m.center[0],
                    "y": m.center[1],
                },
            }
            for m in mounts_res
        ],
        "lines": [
            {
                "line_id": l.line_id,
                "name": l.name,
                "classical_name": l.classical_name,
                "detected": l.detected,
                "confidence": l.confidence,
                "length_normalized": l.length_normalized,
                "curvature": l.curvature,
                "depth_clarity": l.depth_clarity,
                "continuity": l.continuity,
                "variation_type": l.variation_type,
                "variation_description": l.variation_description,
                "interpretation": l.interpretation,
                "significance": l.significance,
                "coordinates": [{"x": pt[0], "y": pt[1]} for pt in l.coordinates],
            }
            for l in lines_res
        ],
    }

"""MediaPipe Hand Landmarker service (Spec §49.5, FR-007, FR-008)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from app.services.palm_analysis.preprocessor import PalmValidationError

ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_PATH = ROOT_DIR / "models" / "hand_landmarker.task"

_DETECTOR: vision.HandLandmarker | None = None


@dataclass
class LandmarkPoint:
    index: int
    name: str
    x: float          # Normalized [0, 1]
    y: float          # Normalized [0, 1]
    z: float          # Depth relative to wrist
    px: int           # Pixel x coordinate
    py: int           # Pixel y coordinate


@dataclass
class HandLandmarkResult:
    landmarks: List[LandmarkPoint]
    handedness: str            # 'Left' or 'Right'
    handedness_confidence: float
    is_palmar: bool
    palm_polygon_pixels: List[Tuple[int, int]]
    palm_bbox: Tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)
    hand_presence_score: float


LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP",
    "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP",
    "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
]

PALM_HULL_INDICES = [0, 1, 2, 5, 9, 13, 17]


def get_detector() -> vision.HandLandmarker:
    """Initialize and cache MediaPipe HandLandmarker instance."""
    global _DETECTOR
    if _DETECTOR is not None:
        return _DETECTOR

    if not DEFAULT_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"MediaPipe hand landmarker model not found at {DEFAULT_MODEL_PATH}. Run build setup first."
        )

    base_options = python.BaseOptions(model_asset_path=str(DEFAULT_MODEL_PATH))
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    _DETECTOR = vision.HandLandmarker.create_from_options(options)
    return _DETECTOR


def extract_hand_landmarks(
    rgb_image: np.ndarray,
    enforce_palmar: bool = True,
) -> HandLandmarkResult:
    """Detect hand landmarks from an RGB numpy image array."""
    detector = get_detector()
    height, width = rgb_image.shape[:2]

    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    detection = detector.detect(mp_img)

    if not detection.hand_landmarks:
        # Check if the image contains rich skin texture/creases without the full hand outline (extreme close-up)
        gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY) if rgb_image.ndim == 3 else rgb_image
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))

        if lap_var > 6.0 and std_val > 15.0 and 40.0 < mean_val < 225.0:
            raise PalmValidationError(
                "CLOSE_UP_HAND_DETECTED",
                "No hand outline detected. This image appears to be an extreme close-up of palm creases without the wrist or fingers. Please step back to capture your full hand (wrist, palm, and all fingertips visible) against a plain background.",
                400,
            )

        raise PalmValidationError(
            "NO_HAND_DETECTED",
            "No hand detected in the uploaded image. Please ensure your palm is clearly visible against a plain background with adequate lighting.",
            400,
        )

    raw_lms = detection.hand_landmarks[0]
    handedness_category = detection.handedness[0][0]
    handedness = handedness_category.category_name
    confidence = handedness_category.score

    landmarks: List[LandmarkPoint] = []
    for idx, lm in enumerate(raw_lms):
        px = max(0, min(width - 1, int(lm.x * width)))
        py = max(0, min(height - 1, int(lm.y * height)))
        landmarks.append(
            LandmarkPoint(
                index=idx,
                name=LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"POINT_{idx}",
                x=float(lm.x),
                y=float(lm.y),
                z=float(lm.z),
                px=px,
                py=py,
            )
        )

    # Rotation-invariant Palmar vs Dorsal Verification
    ux = raw_lms[9].x - raw_lms[0].x
    uy = raw_lms[9].y - raw_lms[0].y
    vx = raw_lms[17].x - raw_lms[5].x
    vy = raw_lms[17].y - raw_lms[5].y
    cross_2d = ux * vy - uy * vx
    sign = 1.0 if handedness == "Left" else -1.0
    is_palmar = (sign * cross_2d) > 0.0

    if enforce_palmar and not is_palmar:
        raise PalmValidationError(
            "DORSAL_HAND_DETECTED",
            "The back of your hand was detected. Please turn your hand around so the palm side with creases is facing the camera.",
            400,
        )

    # Compute palm polygon from palm hull indices
    polygon = [(landmarks[i].px, landmarks[i].py) for i in PALM_HULL_INDICES]

    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    bbox = (min(xs), min(ys), max(xs), max(ys))

    return HandLandmarkResult(
        landmarks=landmarks,
        handedness=handedness,
        handedness_confidence=confidence,
        is_palmar=is_palmar,
        palm_polygon_pixels=polygon,
        palm_bbox=bbox,
        hand_presence_score=confidence,
    )


def check_hand_presence(rgb_image: np.ndarray) -> Dict[str, Any]:
    """Lightweight hand presence and palmar orientation check for real-time video frames (<15ms)."""
    detector = get_detector()
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    detection = detector.detect(mp_img)

    if not detection.hand_landmarks:
        return {
            "hand_detected": False,
            "is_palmar": False,
            "handedness": None,
            "confidence": 0.0,
            "landmarks_count": 0,
        }

    raw_lms = detection.hand_landmarks[0]
    handedness_category = detection.handedness[0][0]
    handedness = handedness_category.category_name
    confidence = float(handedness_category.score)

    ux = raw_lms[9].x - raw_lms[0].x
    uy = raw_lms[9].y - raw_lms[0].y
    vx = raw_lms[17].x - raw_lms[5].x
    vy = raw_lms[17].y - raw_lms[5].y
    cross_2d = ux * vy - uy * vx
    sign = 1.0 if handedness == "Left" else -1.0
    is_palmar = bool((sign * cross_2d) > 0.0)

    return {
        "hand_detected": True,
        "is_palmar": is_palmar,
        "handedness": handedness,
        "confidence": round(confidence, 3),
        "landmarks_count": len(raw_lms),
    }


def check_hand_presence_from_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """Decode image bytes and run fast hand presence & palmar orientation check."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        return {
            "hand_detected": False,
            "is_palmar": False,
            "handedness": None,
            "confidence": 0.0,
            "landmarks_count": 0,
        }

    h, w = img.shape[:2]
    if max(h, w) > 480:
        scale = 480 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return check_hand_presence(rgb)


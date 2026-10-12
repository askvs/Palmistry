"""Pydantic schemas for Palm Analysis API (Spec §49.5, FR-006..FR-011)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PalmCoordinate(BaseModel):
    x: float
    y: float


class PalmLineDetail(BaseModel):
    line_id: str
    name: str
    classical_name: str
    detected: bool
    confidence: float
    length_normalized: float
    curvature: float
    depth_clarity: float
    continuity: str
    variation_type: str
    variation_description: str
    interpretation: str
    significance: List[str]
    coordinates: List[PalmCoordinate]


class PalmMountDetail(BaseModel):
    mount_id: str
    name: str
    planetary_ruler: str
    element: str
    prominence: str
    score: float
    meaning: str
    core_attributes: List[str]
    center: Optional[PalmCoordinate] = None


class PalmShapeDetail(BaseModel):
    element: str
    palm_width: float
    palm_height: float
    aspect_ratio: float
    finger_to_palm_ratio: float
    description: str
    traits: List[str]


class FingerMeasurement(BaseModel):
    name: str
    length: float
    ratio_to_middle: float


class FingerStructureDetail(BaseModel):
    digit_ratio_2d_4d: float
    digit_ratio_interpretation: str
    pinky_reaches_ring_dip: bool
    pinky_trait: str
    thumb_angle_degrees: float
    thumb_flexibility: str
    fingers: Dict[str, FingerMeasurement]


class PalmMetadata(BaseModel):
    model_name: str
    model_version: str
    timestamp: str
    overall_confidence: float
    original_resolution: Dict[str, int]
    analyzed_resolution: Dict[str, int]


class HandMetadata(BaseModel):
    detected_handedness: str
    handedness_confidence: float
    preferred_hand: str
    is_palmar: bool
    landmarks_count: int
    palm_bounding_box: Dict[str, int]
    landmarks: Optional[List[Dict[str, Any]]] = None


class PalmAnalysisResponse(BaseModel):
    reading_id: Optional[str] = None
    metadata: PalmMetadata
    hand: HandMetadata
    palm_shape: PalmShapeDetail
    finger_structure: FingerStructureDetail
    mounts: List[PalmMountDetail]
    lines: List[PalmLineDetail]

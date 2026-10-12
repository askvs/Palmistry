"""Palm Analysis API Endpoints (Spec §49.4, §49.5, FR-006..FR-011)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.rbac import get_optional_current_user
from app.config import settings
from app.db.session import get_db
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User
from app.schemas.palm import (
    PalmAnalysisResponse,
    PalmMountDetail,
    PalmLineDetail,
)
from app.services.palm_analysis.catalog import (
    get_palm_lines_catalog,
    get_palm_mounts_catalog,
)
from app.services.palm_analysis.hand_landmarker import check_hand_presence_from_bytes
from app.services.palm_analysis.pipeline import analyze_palm_image
from app.services.palm_analysis.preprocessor import PalmValidationError

router = APIRouter(prefix="/palm", tags=["palm"])


@router.post(
    "/analyze",
    response_model=PalmAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze palm image with CV pipeline",
)
async def analyze_palm(
    file: UploadFile = File(..., description="Palm image file (JPG, PNG, WEBP <= 10 MB)"),
    hand: Optional[str] = Form(None, description="Preferred hand ('Left' or 'Right')"),
    user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Upload a palm photo for full computer vision and biometric analysis."""
    data = await file.read(11 * 1024 * 1024)
    if not data:
        raise PalmValidationError("EMPTY_FILE", "The uploaded file is empty.", 400)

    # Run analysis pipeline
    analysis = analyze_palm_image(
        image_bytes=data,
        preferred_hand=hand,
        enforce_palmar=True,
    )

    reading_id_str: Optional[str] = None

    # If user is authenticated, persist reading record
    if user is not None:
        shape_elem = analysis.get("palm_shape", {}).get("element", "Hand")
        conf_pct = int(analysis.get("metadata", {}).get("overall_confidence", 0.0) * 100)
        detected_count = sum(1 for ln in analysis.get("lines", []) if ln.get("detected"))
        reading = Reading(
            user_id=user.id,
            type=ReadingType.palm,
            status=ReadingStatus.completed,
            title=f"Palm Analysis ({shape_elem} Hand)",
            summary=f"Detected {shape_elem} hand with {detected_count} of 5 primary lines detected ({conf_pct}% confidence).",
            result=analysis,
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        reading_id_str = str(reading.id)

    analysis["reading_id"] = reading_id_str
    analysis["ai_interpretation"] = None

    return analysis


@router.get(
    "/lines",
    summary="Get reference catalog of 5 primary palm lines",
)
def get_lines() -> List[Dict[str, Any]]:
    """Return reference definitions of Life, Head, Heart, Fate, and Sun lines."""
    return get_palm_lines_catalog()


@router.get(
    "/mounts",
    summary="Get reference catalog of 6 palm mounts",
)
def get_mounts() -> List[Dict[str, Any]]:
    """Return reference definitions of Jupiter, Saturn, Apollo, Mercury, Venus, and Moon mounts."""
    return get_palm_mounts_catalog()


@router.post(
    "/check-frame",
    summary="Fast hand presence & orientation check for live camera feed (<15ms)",
)
async def check_frame(
    file: UploadFile = File(..., description="Webcam video frame (JPEG/PNG)"),
) -> Dict[str, Any]:
    """Lightweight real-time check to verify hand is in focus and facing camera."""
    data = await file.read(2 * 1024 * 1024)
    if not data:
        return {
            "hand_detected": False,
            "is_palmar": False,
            "handedness": None,
            "confidence": 0.0,
            "landmarks_count": 0,
        }
    return check_hand_presence_from_bytes(data)


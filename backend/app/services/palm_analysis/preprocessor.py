"""Palm image preprocessor (Spec §49.4, §49.5, FR-006, FR-007)."""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB per §49.4
TARGET_SIZE = (1024, 1024)


class PalmValidationError(Exception):
    """Raised when an uploaded image fails validation (MIME, magic bytes, dimensions, aspect)."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass
class PreprocessedPalmImage:
    rgb: np.ndarray             # Normalized RGB image (H, W, 3)
    gray: np.ndarray            # Grayscale image (H, W)
    clahe: np.ndarray           # High-contrast CLAHE enhanced grayscale (H, W)
    creases: np.ndarray         # Morphological Black-Hat crease map (H, W)
    original_size: Tuple[int, int]  # (width, height)
    normalized_size: Tuple[int, int]  # (width, height)


def validate_image_bytes(data: bytes) -> str:
    """Validate binary file signature and file size."""
    if not data:
        raise PalmValidationError("EMPTY_FILE", "The uploaded image file is empty.", 400)

    if len(data) > MAX_IMAGE_BYTES:
        raise PalmValidationError(
            "IMAGE_TOO_LARGE",
            f"Image size exceeds the 10 MB limit ({len(data) / (1024*1024):.1f} MB).",
            413,
        )

    # Magic bytes check
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
        return "image/webp"

    raise PalmValidationError(
        "INVALID_IMAGE_FORMAT",
        "Unsupported image format. Please upload a valid JPG, PNG, or WEBP image.",
        415,
    )


def preprocess_palm_image(
    image_bytes: bytes,
    target_dim: int = 1024,
) -> PreprocessedPalmImage:
    """Execute complete image validation and preprocessing pipeline."""
    # 1. Signature & size validation
    validate_image_bytes(image_bytes)

    # 2. Decode via PIL with EXIF orientation correction
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)
        orig_w, orig_h = pil_img.size
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
    except Exception as exc:
        raise PalmValidationError(
            "CORRUPTED_IMAGE",
            f"Unable to decode image file: {str(exc)}. Please re-take or upload a clean photo.",
            400,
        ) from exc

    # Minimum dimension check
    if orig_w < 200 or orig_h < 200:
        raise PalmValidationError(
            "IMAGE_RESOLUTION_TOO_LOW",
            f"Image resolution ({orig_w}x{orig_h}) is too small for accurate palm reading. Minimum required is 200x200.",
            400,
        )

    # 3. Dimensional normalization preserving aspect ratio
    scale = target_dim / max(orig_w, orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    rgb_array = np.array(pil_img)

    # 4. Grayscale conversion & edge-preserving smoothing
    gray = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 5. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe_op = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    clahe_img = clahe_op.apply(denoised)

    # 6. Morphological Black-Hat filtering for dark crease accentuation
    h_n, w_n = denoised.shape[:2]
    base_k = max(9, (min(h_n, w_n) // 64) | 1)
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (base_k, base_k))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (base_k * 2 + 1, base_k * 2 + 1))
    bh1 = cv2.morphologyEx(denoised, cv2.MORPH_BLACKHAT, k1)
    bh2 = cv2.morphologyEx(denoised, cv2.MORPH_BLACKHAT, k2)
    blackhat = cv2.max(bh1, bh2)

    # Robust normalization preserves crease contrast.
    scale = max(float(np.percentile(blackhat, 99.5)), 1.0)
    creases = np.clip(blackhat / scale * 255.0, 0, 255).astype(np.uint8)

    return PreprocessedPalmImage(
        rgb=rgb_array,
        gray=denoised,
        clahe=clahe_img,
        creases=creases,
        original_size=(orig_w, orig_h),
        normalized_size=(new_w, new_h),
    )

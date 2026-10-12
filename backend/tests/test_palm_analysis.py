# Palm analysis engine: validation, preprocessing, landmarks, mounts, lines, endpoints.
from pathlib import Path
import io
import pytest
from PIL import Image

from app.services.palm_analysis.preprocessor import (
    PalmValidationError,
    validate_image_bytes,
    preprocess_palm_image,
)
from app.services.palm_analysis.hand_landmarker import (
    extract_hand_landmarks,
    HandLandmarkResult,
)
from app.services.palm_analysis.feature_extractor import (
    extract_palm_shape,
    extract_finger_structure,
    extract_mounts,
)
from app.services.palm_analysis.line_detector import detect_palm_lines
from app.services.palm_analysis.pipeline import analyze_palm_image
from app.models.reading import Reading, ReadingType, ReadingStatus
from app.auth.password import hash_password
from app.models.user import User, UserRole

ROOT_DIR = Path(__file__).resolve().parents[2]
PALMAR_SAMPLE = ROOT_DIR / "dataset" / "Hands and palm images dataset" / "Hands" / "Hands" / "Hand_0000038.jpg"
DORSAL_SAMPLE = ROOT_DIR / "dataset" / "Hands and palm images dataset" / "Hands" / "Hands" / "Hand_0000002.jpg"
HORIZONTAL_PALMAR_SAMPLE = ROOT_DIR / "dataset" / "palmline" / "Palm Line Detection.v2i.yolov5pytorch" / "train" / "images" / "istockphoto-3_PNG.rf.8bb7def428b681284a2d62198d51f359.jpg"


class TestPalmValidationAndPreprocessing:
    def test_validate_image_bytes_formats(self):
        # Valid JPEG
        jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        assert validate_image_bytes(jpeg_bytes) == "image/jpeg"

        # Valid PNG
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert validate_image_bytes(png_bytes) == "image/png"

        # Valid WEBP
        webp_bytes = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 100
        assert validate_image_bytes(webp_bytes) == "image/webp"

    def test_validate_image_bytes_rejections(self):
        # Empty
        with pytest.raises(PalmValidationError) as exc:
            validate_image_bytes(b"")
        assert exc.value.status_code == 400
        assert exc.value.code == "EMPTY_FILE"

        # Invalid format / text
        with pytest.raises(PalmValidationError) as exc:
            validate_image_bytes(b"This is definitely not an image.")
        assert exc.value.status_code == 415
        assert exc.value.code == "INVALID_IMAGE_FORMAT"

        # Oversized
        oversized = b"\xff\xd8\xff" + b"\x00" * (11 * 1024 * 1024)
        with pytest.raises(PalmValidationError) as exc:
            validate_image_bytes(oversized)
        assert exc.value.status_code == 413
        assert exc.value.code == "IMAGE_TOO_LARGE"

    def test_preprocess_palm_image_on_sample(self):
        assert PALMAR_SAMPLE.exists(), f"Sample image missing: {PALMAR_SAMPLE}"
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        res = preprocess_palm_image(data)
        assert res.rgb.shape[2] == 3
        assert res.gray.ndim == 2
        assert res.clahe.ndim == 2
        assert res.creases.ndim == 2
        assert max(res.normalized_size) == 1024


class TestMediaPipeAndFeatureExtraction:
    def test_landmark_extraction_on_palmar_image(self):
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=True)

        assert len(lms.landmarks) == 21
        assert lms.is_palmar is True
        assert lms.handedness == "Left"
        assert lms.landmarks[0].name == "WRIST"
        assert len(lms.palm_polygon_pixels) == 7
        assert lms.hand_presence_score > 0.8

    def test_dorsal_image_rejection(self):
        assert DORSAL_SAMPLE.exists(), f"Sample image missing: {DORSAL_SAMPLE}"
        with open(DORSAL_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        with pytest.raises(PalmValidationError) as exc:
            extract_hand_landmarks(prep.rgb, enforce_palmar=True)

        assert exc.value.status_code == 400
        assert exc.value.code == "DORSAL_HAND_DETECTED"
        assert "palm" in exc.value.message.lower()

    def test_horizontal_rotated_palmar_image_accepted(self):
        assert HORIZONTAL_PALMAR_SAMPLE.exists(), f"Sample missing: {HORIZONTAL_PALMAR_SAMPLE}"
        with open(HORIZONTAL_PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=True)
        assert lms.is_palmar is True
        assert lms.handedness == "Right"

    def test_palm_shape_classification(self):
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=False)
        shape = extract_palm_shape(lms.landmarks)

        assert shape.element in ("Earth", "Air", "Fire", "Water")
        assert shape.aspect_ratio > 0.0
        assert shape.finger_to_palm_ratio > 0.0
        assert len(shape.traits) >= 3

    def test_finger_structure_analysis(self):
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=False)
        fingers = extract_finger_structure(lms.landmarks)

        assert len(fingers.fingers) == 5
        assert "thumb" in fingers.fingers
        assert "middle" in fingers.fingers
        assert fingers.digit_ratio_2d_4d > 0.0
        assert fingers.thumb_angle_degrees > 0.0

    def test_mounts_extraction(self):
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=False)
        mounts = extract_mounts(lms.landmarks, prep.clahe)

        assert len(mounts) == 6
        mount_ids = {m.mount_id for m in mounts}
        assert mount_ids == {
            "mount_of_jupiter",
            "mount_of_saturn",
            "mount_of_apollo",
            "mount_of_mercury",
            "mount_of_venus",
            "mount_of_moon",
        }
        for m in mounts:
            assert m.prominence in ("underdeveloped", "balanced", "prominent")
            assert 0.0 <= m.score <= 1.0

    def test_line_detection_five_lines(self):
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()

        prep = preprocess_palm_image(data)
        lms = extract_hand_landmarks(prep.rgb, enforce_palmar=False)
        lines = detect_palm_lines(lms, prep.creases, prep.clahe)

        assert len(lines) == 5
        line_ids = {l.line_id for l in lines}
        assert line_ids == {"life_line", "head_line", "heart_line", "fate_line", "sun_line"}

        # Major creases must register on a clear palmar photo; faint lines
        # (fate/sun) may honestly report detected=False on some hands.
        detected_lines = [l for l in lines if l.detected]
        assert len(detected_lines) >= 3
        assert all(l.line_id in {"life_line", "head_line", "heart_line"} for l in detected_lines[:3])

        for line in lines:
            assert line.confidence >= 0.5
            assert len(line.coordinates) > 5
            assert line.variation_type
            assert line.interpretation


class TestPalmAnalysisAPI:
    def test_get_lines_catalog(self, client):
        res = client.get("/api/v1/palm/lines")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 5
        ids = {l["id"] for l in data}
        assert "life_line" in ids
        assert "sun_line" in ids

    def test_get_mounts_catalog(self, client):
        res = client.get("/api/v1/palm/mounts")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 6
        ids = {m["id"] for m in data}
        assert "mount_of_jupiter" in ids
        assert "mount_of_moon" in ids

    def test_analyze_palm_unsupported_format(self, client):
        files = {"file": ("test.txt", b"plain text", "text/plain")}
        res = client.post("/api/v1/palm/analyze", files=files)
        assert res.status_code == 415
        body = res.json()
        assert body["code"] == "INVALID_IMAGE_FORMAT"

    def test_analyze_palm_dorsal_rejected(self, client):
        with open(DORSAL_SAMPLE, "rb") as f:
            img_bytes = f.read()

        files = {"file": ("dorsal.jpg", img_bytes, "image/jpeg")}
        res = client.post("/api/v1/palm/analyze", files=files)
        assert res.status_code == 400
        body = res.json()
        assert body["code"] == "DORSAL_HAND_DETECTED"
        assert "palm" in body["message"].lower()

    def test_analyze_palm_success_guest(self, client):
        with open(PALMAR_SAMPLE, "rb") as f:
            img_bytes = f.read()

        files = {"file": ("palm.jpg", img_bytes, "image/jpeg")}
        res = client.post("/api/v1/palm/analyze", files=files)
        assert res.status_code == 200
        data = res.json()

        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["overall_confidence"] > 0.5
        assert "palm_shape" in data
        assert data["palm_shape"]["element"] in ("Earth", "Air", "Fire", "Water")

        # Check lines
        assert len(data["lines"]) == 5
        line_ids = [l["line_id"] for l in data["lines"]]
        assert line_ids == ["life_line", "head_line", "heart_line", "fate_line", "sun_line"]

        # Check mounts
        assert len(data["mounts"]) == 6

        # Guest has no reading_id
        assert data["reading_id"] is None

    def test_analyze_palm_success_authenticated_persists(self, client, test_engine):
        from sqlalchemy.orm import Session
        from app.auth import tokens

        # Create test user
        with Session(test_engine) as db:
            user = User(
                email="palm_tester@example.com",
                full_name="Palm Tester",
                role=UserRole.user,
                password_hash=hash_password("PalmTest123!"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = user.id

        token = tokens.create_access_token(user_id, UserRole.user)
        headers = {"Authorization": f"Bearer {token}"}

        with open(PALMAR_SAMPLE, "rb") as f:
            img_bytes = f.read()

        files = {"file": ("palm_auth.jpg", img_bytes, "image/jpeg")}
        res = client.post("/api/v1/palm/analyze", files=files, headers=headers)
        assert res.status_code == 200
        data = res.json()

        reading_id = data.get("reading_id")
        assert reading_id is not None

        import uuid
        with Session(test_engine) as db:
            saved = db.get(Reading, uuid.UUID(reading_id))
            assert saved is not None
            assert saved.type == ReadingType.palm
            assert saved.status == ReadingStatus.completed
            assert "Hand" in saved.title
            assert saved.user_id == user_id
            assert "lines" in saved.result

    def test_close_up_crop_rejection_with_actionable_guidance(self, client):
        close_up = ROOT_DIR / "dataset" / "palmline" / "PalmLinesDetection.v3i.yolov5-obb" / "test" / "images" / "Hand_0011575_jpg.rf.7304eef80c17c2506910d4a01bdca240.jpg"
        if not close_up.exists():
            pytest.skip("Close up sample not found on disk")

        with open(close_up, "rb") as f:
            data = f.read()

        files = {"file": ("close_up.jpg", data, "image/jpeg")}
        res = client.post("/api/v1/palm/analyze", files=files)
        assert res.status_code == 400
        body = res.json()
        assert body["code"] == "CLOSE_UP_HAND_DETECTED"
        assert "extreme close-up" in body["message"]
        assert "wrist" in body["message"]

    def test_check_frame_palmar_vs_dorsal_vs_empty(self, client):
        # 1. Palmar hand
        with open(PALMAR_SAMPLE, "rb") as f:
            data = f.read()
        files = {"file": ("frame.jpg", data, "image/jpeg")}
        res = client.post("/api/v1/palm/check-frame", files=files)
        assert res.status_code == 200
        body = res.json()
        assert body["hand_detected"] is True
        assert body["is_palmar"] is True
        assert body["landmarks_count"] == 21

        # 2. Dorsal hand (back of hand)
        with open(DORSAL_SAMPLE, "rb") as f:
            data_d = f.read()
        files = {"file": ("frame.jpg", data_d, "image/jpeg")}
        res = client.post("/api/v1/palm/check-frame", files=files)
        assert res.status_code == 200
        body = res.json()
        assert body["hand_detected"] is True
        assert body["is_palmar"] is False

        # 3. Empty / non-hand
        files = {"file": ("frame.jpg", b"", "image/jpeg")}
        res = client.post("/api/v1/palm/check-frame", files=files)
        assert res.status_code == 200
        body = res.json()
        assert body["hand_detected"] is False

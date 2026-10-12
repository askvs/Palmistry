# Unified reading workflow: palm/tarot create, list, access control, notes, analytics.
import uuid
from pathlib import Path

import pytest

from app.auth.password import hash_password
from app.auth.tokens import create_access_token
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User, UserRole

ROOT_DIR = Path(__file__).resolve().parents[2]
PALMAR_SAMPLE = ROOT_DIR / "dataset" / "Hands and palm images dataset" / "Hands" / "Hands" / "Hand_0000038.jpg"
DORSAL_SAMPLE = ROOT_DIR / "dataset" / "Hands and palm images dataset" / "Hands" / "Hands" / "Hand_0000002.jpg"


def _create_user(test_engine, *, email: str, role: UserRole) -> User:
    from sqlalchemy.orm import Session

    with Session(test_engine) as session:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password("ReadingTest123!"),
            full_name=email.split("@")[0].title(),
            role=role,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


@pytest.fixture
def seeker(test_engine):
    return _create_user(test_engine, email="seeker@example.com", role=UserRole.user)


@pytest.fixture
def stranger(test_engine):
    return _create_user(test_engine, email="stranger@example.com", role=UserRole.user)


@pytest.fixture
def reader(test_engine):
    return _create_user(test_engine, email="reader@example.com", role=UserRole.tarot_reader)


@pytest.fixture
def admin(test_engine):
    return _create_user(test_engine, email="admin@example.com", role=UserRole.admin)


class TestPalmReadingEndpoint:
    def test_create_palm_reading_runs_real_cv(self, client, seeker):
        if not PALMAR_SAMPLE.exists():
            pytest.skip("Palmar sample image not available on disk")
        headers = _auth(seeker)
        with open(PALMAR_SAMPLE, "rb") as f:
            files = {"image": ("palm.jpg", f.read(), "image/jpeg")}
        res = client.post("/api/v1/readings/palm", files=files, headers=headers)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["type"] == "palm"
        assert body["status"] == "completed"
        assert body["user_id"] == str(seeker.id)

        result = body["result"]
        assert result["metadata"]["overall_confidence"] > 0.5
        assert result["palm_shape"]["element"] in ("Earth", "Air", "Fire", "Water")
        assert "lines" in result
        assert "mounts" in result

        # The reading is now persisted and fetchable by its ID
        get_res = client.get(f"/api/v1/readings/{body['id']}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["summary"] == body["summary"]

    def test_create_palm_reading_empty_file_rejected(self, client, seeker):
        headers = _auth(seeker)
        files = {"image": ("empty.jpg", b"", "image/jpeg")}
        res = client.post("/api/v1/readings/palm", files=files, headers=headers)
        assert res.status_code == 400
        assert res.json()["code"] == "PALM_IMAGE_EMPTY"

    def test_create_palm_reading_dorsal_rejected(self, client, seeker):
        if not DORSAL_SAMPLE.exists():
            pytest.skip("Dorsal sample image not available on disk")
        headers = _auth(seeker)
        with open(DORSAL_SAMPLE, "rb") as f:
            files = {"image": ("back.jpg", f.read(), "image/jpeg")}
        res = client.post("/api/v1/readings/palm", files=files, headers=headers)
        assert res.status_code in (400, 422)
        assert "code" in res.json()

    def test_create_palm_reading_requires_auth(self, client):
        files = {"image": ("palm.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 50, "image/jpeg")}
        res = client.post("/api/v1/readings/palm", files=files)
        assert res.status_code == 401


class TestTarotReadingEndpoint:
    def test_create_tarot_reading_from_explicit_cards(self, client, seeker):
        res = client.post(
            "/api/v1/readings/tarot",
            json={
                "spread": "Three Card",
                "cards": ["The Fool", "The Magician", "The Star"],
                "question": "What is guiding my professional transition?",
            },
            headers=_auth(seeker),
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["type"] == "tarot"
        assert body["status"] == "completed"
        assert body["summary"]
        assert len(body["result"]["cards"]) == 3

    def test_create_tarot_reading_unknown_card_rejected(self, client, seeker):
        res = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Three Card", "cards": ["Not A Real Card"]},
            headers=_auth(seeker),
        )
        assert res.status_code == 400
        assert res.json()["code"] == "TAROT_UNKNOWN_CARD"


class TestReadingLifecycle:
    def test_list_and_filters(self, client, seeker):
        headers = _auth(seeker)
        tarot = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Single Card", "cards": ["The Sun"]},
            headers=headers,
        ).json()
        client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Three Card", "cards": ["The Fool", "The Moon", "The World"]},
            headers=headers,
        )

        res = client.get("/api/v1/readings", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

        filtered = client.get("/api/v1/readings?type=tarot&status=completed", headers=headers).json()
        assert filtered["total"] == 2

        empty_filter = client.get("/api/v1/readings?type=palm", headers=headers).json()
        assert empty_filter["total"] == 0

        page = client.get("/api/v1/readings?limit=1", headers=headers).json()
        assert len(page["items"]) == 1
        assert page["total"] == 2

        paged_ids = {i["id"] for i in page["items"]}
        second = client.get("/api/v1/readings?limit=1&offset=1", headers=headers).json()
        assert {i["id"] for i in second["items"]}.isdisjoint(paged_ids)

    def test_get_access_control(self, client, seeker, stranger, reader, admin):
        tarot = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Single Card", "cards": ["The High Priestess"]},
            headers=_auth(seeker),
        ).json()
        rid = tarot["id"]

        assert client.get(f"/api/v1/readings/{rid}", headers=_auth(seeker)).status_code == 200
        assert client.get(f"/api/v1/readings/{rid}", headers=_auth(reader)).status_code == 200
        assert client.get(f"/api/v1/readings/{rid}", headers=_auth(admin)).status_code == 200

        forbidden = client.get(f"/api/v1/readings/{rid}", headers=_auth(stranger))
        assert forbidden.status_code == 404
        assert forbidden.json()["code"] == "READING_NOT_FOUND"

        assert client.get(f"/api/v1/readings/{rid}").status_code == 401

    def test_update_notes_and_delete(self, client, seeker, stranger):
        headers = _auth(seeker)
        rid = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Single Card", "cards": ["The Hermit"], "question": "Solitude?"},
            headers=headers,
        ).json()["id"]

        patch = client.patch(
            f"/api/v1/readings/{rid}",
            json={"notes": "Reflected on the Hermit card guidance.", "title": "My Hermit Reading"},
            headers=headers,
        )
        assert patch.status_code == 200
        assert patch.json()["notes"].startswith("Reflected")
        assert patch.json()["title"] == "My Hermit Reading"

        # Strangers cannot delete other users' readings
        assert client.delete(f"/api/v1/readings/{rid}", headers=_auth(stranger)).status_code == 404

        assert client.delete(f"/api/v1/readings/{rid}", headers=headers).status_code == 204
        assert client.get(f"/api/v1/readings/{rid}", headers=headers).status_code == 404

    def test_user_analytics(self, client, seeker):
        headers = _auth(seeker)
        client.post(
            "/api/v1/readings/tarot",
            json={"spread": "Single Card", "cards": ["Wheel of Fortune"]},
            headers=headers,
        )
        res = client.get("/api/v1/readings/analytics/me", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 1
        assert {"type": "tarot", "count": 1} in body["by_type"]
        assert any(s["status"] == "completed" for s in body["by_status"])

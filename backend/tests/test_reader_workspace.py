# Reader workspace: custom spreads, reading reports, and engagement insights.
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole

PASSWORD = "TestPass123!"


def _register(client, email, full_name, role="user"):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name, "role": role},
    )
    assert resp.status_code == 201, resp.text
    return resp


def _login(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(test_engine, email, role):
    Session = sessionmaker(bind=test_engine)
    with Session() as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


@pytest.fixture()
def reader(client, test_engine):
    email = f"reader-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Reader One", role="tarot_reader")
    return _login(client, email)


@pytest.fixture()
def other_reader(client, test_engine):
    email = f"reader-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Reader Two", role="tarot_reader")
    return _login(client, email)


@pytest.fixture()
def seeker(client):
    email = f"querent-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Querent One")
    return _login(client, email)


SAMPLE_POSITIONS = [
    {"name": "The Question", "description": "What the seeker asks."},
    {"name": "The Block", "description": "What stands in the way."},
    {"name": "The Way Through", "description": "How to move forward."},
]


class TestCustomSpreadAuthoring:
    def test_create_and_list(self, client, reader):
        created = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={"name": "Three Doors", "positions": SAMPLE_POSITIONS, "category": "choice"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["name"] == "Three Doors"
        assert body["card_count"] == 3
        assert body["visibility"] == "private"
        assert [p["position"] for p in body["positions"]] == [1, 2, 3]

        listing = client.get("/api/v1/reader/spreads", headers=reader).json()
        assert [s["id"] for s in listing["standard"]] == [
            "single_card",
            "three_card",
            "relationship",
            "career",
            "celtic_cross",
            "life_path",
        ]
        assert any(s["id"] == body["id"] and s["source"] == "custom" for s in listing["custom"])

    def test_update_and_retire(self, client, reader):
        spread_id = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={"name": "Original", "positions": SAMPLE_POSITIONS},
        ).json()["id"]

        updated = client.patch(
            f"/api/v1/reader/spreads/{spread_id}",
            headers=reader,
            json={"name": "Renamed", "visibility": "shared"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Renamed"
        assert updated.json()["visibility"] == "shared"

        assert (
            client.delete(f"/api/v1/reader/spreads/{spread_id}", headers=reader).status_code == 204
        )

        listing = client.get("/api/v1/reader/spreads", headers=reader).json()
        assert all(s["id"] != spread_id for s in listing["custom"])

    def test_duplicate_name_rejected(self, client, reader):
        for _ in range(2):
            resp = client.post(
                "/api/v1/reader/spreads",
                headers=reader,
                json={"name": "Same Name", "positions": SAMPLE_POSITIONS},
            )
            if resp.status_code == 201:
                continue
            assert resp.status_code == 409
            assert resp.json()["code"] == "SPREAD_NAME_TAKEN"
            break
        else:
            pytest.fail("expected the second create to be rejected")

    def test_positions_are_validated(self, client, reader):
        too_many = [{"name": f"Card {i}"} for i in range(11)]
        assert (
            client.post(
                "/api/v1/reader/spreads", headers=reader, json={"name": "Too Many", "positions": too_many}
            ).status_code
            == 422
        )

        assert (
            client.post(
                "/api/v1/reader/spreads", headers=reader, json={"name": "Empty", "positions": []}
            ).status_code
            == 422
        )

    def test_reader_cannot_edit_another_readers_spread(self, client, reader, other_reader):
        spread_id = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={"name": "Private Work", "positions": SAMPLE_POSITIONS},
        ).json()["id"]

        resp = client.patch(
            f"/api/v1/reader/spreads/{spread_id}",
            headers=other_reader,
            json={"name": "Hijacked"},
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "SPREAD_NOT_FOUND"

    def test_seeker_cannot_author_spreads(self, client, seeker):
        resp = client.post(
            "/api/v1/reader/spreads",
            headers=seeker,
            json={"name": "Nope", "positions": SAMPLE_POSITIONS},
        )
        assert resp.status_code == 403

    def test_unauthenticated_rejected(self, client):
        assert client.get("/api/v1/reader/spreads").status_code == 401
        assert client.post("/api/v1/reader/spreads", json={"name": "x", "positions": []}).status_code == 401


class TestReadingsWithCustomSpreads:
    def test_draw_with_a_custom_spread(self, client, reader):
        spread = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={
                "name": "Body / Mind / Spirit",
                "positions": [
                    {"name": "Body", "description": "The physical layer."},
                    {"name": "Mind", "description": "The mental layer."},
                    {"name": "Spirit", "description": "The spiritual layer."},
                ],
            },
        ).json()

        resp = client.post(
            "/api/v1/tarot/draw",
            headers=reader,
            json={"spread_id": spread["id"], "question": "Where should I focus?", "seed": 7},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["spread_id"] == spread["id"]
        assert body["spread_name"] == "Body / Mind / Spirit"
        assert body["card_count"] == 3
        assert [c["position_name"] for c in body["cards"]] == ["Body", "Mind", "Spirit"]
        assert body["reading_id"]

        stored = client.get(f"/api/v1/readings/{body['reading_id']}", headers=reader).json()
        assert stored["title"] == "Body / Mind / Spirit"

    def test_interpret_an_explicit_selection_on_a_custom_spread(self, client, reader):
        spread = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={
                "name": "Single Window",
                "positions": [{"name": "The Answer", "description": "The direct answer."}],
            },
        ).json()

        resp = client.post(
            "/api/v1/tarot/interpret",
            headers=reader,
            json={"spread_id": spread["id"], "cards": [{"card": "The Star"}]},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["spread_name"] == "Single Window"
        assert resp.json()["cards"][0]["card_name"] == "The Star"

    def test_shared_spread_is_usable_by_another_reader(self, client, reader, other_reader):
        spread = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={"name": "Open Layout", "visibility": "shared", "positions": SAMPLE_POSITIONS},
        ).json()

        resp = client.post(
            "/api/v1/tarot/draw",
            headers=other_reader,
            json={"spread_id": spread["id"], "seed": 3},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["spread_name"] == "Open Layout"

    def test_private_spread_is_not_usable_by_another_reader(self, client, reader, other_reader):
        spread = client.post(
            "/api/v1/reader/spreads",
            headers=reader,
            json={"name": "Secret Layout", "positions": SAMPLE_POSITIONS},
        ).json()

        resp = client.post(
            "/api/v1/tarot/draw",
            headers=other_reader,
            json={"spread_id": spread["id"], "seed": 3},
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == "SPREAD_NOT_ALLOWED"

    def test_unknown_spread_still_errors(self, client, reader):
        resp = client.post(
            "/api/v1/tarot/draw", headers=reader, json={"spread_id": "not-a-real-spread"}
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "TAROT_UNKNOWN_SPREAD"


class TestReadingReports:
    def test_lists_every_reading_with_its_owner(self, client, reader, seeker):
        client.post(
            "/api/v1/readings/tarot",
            headers=seeker,
            json={"spread": "Single Card", "cards": ["The Sun"]},
        )

        reports = client.get("/api/v1/reader/reports", headers=reader).json()
        assert reports["total"] >= 1
        row = next(r for r in reports["items"] if r["owner_email"] == seeker_email(seeker))
        assert row["type"] == "tarot"
        assert row["reviewed"] is False
        assert row["spread_name"]
        assert row["card_count"] == 1

    def test_filters_by_type_status_and_review_state(self, client, reader, seeker):
        for spread, cards in (("Single Card", ["The Sun"]), ("Single Card", ["The Moon"])):
            client.post(
                "/api/v1/readings/tarot", headers=seeker, json={"spread": spread, "cards": cards}
            )

        reviewed = client.get(
            "/api/v1/reader/reports", params={"reviewed": True}, headers=reader
        ).json()
        assert reviewed["items"] == []

        pending = client.get(
            "/api/v1/reader/reports", params={"reviewed": False}, headers=reader
        ).json()
        assert len(pending["items"]) >= 2

        assert (
            client.get("/api/v1/reader/reports", params={"type": "palm"}, headers=reader).json()[
                "items"
            ]
            == []
        )

    def test_filters_by_owner_and_search(self, client, reader, seeker):
        created = client.post(
            "/api/v1/readings/tarot",
            headers=seeker,
            json={"spread": "Three Card", "cards": ["The Fool", "The Magician", "The Star"]},
        ).json()

        by_owner = client.get(
            "/api/v1/reader/reports",
            params={"owner_email": seeker_email(seeker)},
            headers=reader,
        ).json()
        assert any(row["id"] == created["id"] for row in by_owner["items"])

        by_search = client.get(
            "/api/v1/reader/reports", params={"search": created["title"]}, headers=reader
        ).json()
        assert any(row["id"] == created["id"] for row in by_search["items"])

        by_search = client.get(
            "/api/v1/reader/reports", params={"search": "nothing-matches-this"}, headers=reader
        ).json()
        assert by_search["items"] == []

    def test_seeker_cannot_list_platform_reports(self, client, seeker):
        assert client.get("/api/v1/reader/reports", headers=seeker).status_code == 403


class TestReaderEngagement:
    def _two_readings(self, client, seeker):
        for cards in (["The Sun"], ["The Moon", "The Star"]):
            client.post(
                "/api/v1/readings/tarot", headers=seeker, json={"spread": "Single Card", "cards": cards}
            )

    def test_counts_querents_and_repeat_rate(self, client, reader, seeker):
        self._two_readings(client, seeker)

        body = client.get("/api/v1/reader/engagement", headers=reader).json()
        assert body["days"] == 30
        assert body["total_readings"] >= 2
        assert body["unique_querents"] >= 1
        assert body["readings_per_querent"] >= 2
        assert body["repeat_rate"] >= 1.0
        assert body["active_querents_in_window"] >= 1
        assert body["returning_querents_in_window"] >= 1
        assert body["review_rate"] == 0.0

    def test_reports_top_querents_and_popular_spreads(self, client, reader, seeker):
        self._two_readings(client, seeker)

        body = client.get("/api/v1/reader/engagement", headers=reader).json()
        assert body["top_querents"], "expected at least one querent row"
        top = body["top_querents"][0]
        assert top["reading_count"] >= 2
        assert top["email"] == seeker_email(seeker)
        assert top["last_reading_at"]

        assert body["popular_spreads"]
        assert body["popular_spreads"][0]["spread"] == "Single Card"
        assert body["popular_spreads"][0]["count"] >= 2

    def test_days_window_is_validated(self, client, reader):
        assert client.get("/api/v1/reader/engagement", params={"days": 0}, headers=reader).status_code == 422

    def test_seeker_cannot_read_engagement(self, client, seeker):
        assert client.get("/api/v1/reader/engagement", headers=seeker).status_code == 403


def seeker_email(headers) -> str:
    """Resolve the signed-in account's email from its bearer token."""
    import jwt

    token = headers["Authorization"].split(" ", 1)[1]
    from app.auth import tokens

    payload = tokens.decode_access_token(token)
    return payload["sub"] and _email_for(payload["sub"])


def _email_for(user_id: str) -> str:
    from app.db.session import get_db

    from app.models.user import User

    db = next(get_db())
    try:
        user = db.get(User, uuid.UUID(user_id))
        return user.email if user else ""
    finally:
        db.close()

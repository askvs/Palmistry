# Four-role capability matrix acceptance tests.
import uuid

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole

PASSWORD = "TestPass123!"


def _register(client, email, full_name):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client, email):
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _promote(test_engine, email, role):
    Session = sessionmaker(bind=test_engine)
    with Session() as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


@pytest.fixture()
def plain_user(client):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Plain User")
    return email


@pytest.fixture()
def reader_user(client, test_engine):
    email = f"reader-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Tarot Reader")
    _promote(test_engine, email, UserRole.tarot_reader)
    return email


@pytest.fixture()
def consultant_user(client, test_engine):
    email = f"consultant-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Spiritual Consultant")
    _promote(test_engine, email, UserRole.spiritual_consultant)
    return email


@pytest.fixture()
def admin_user(client, test_engine):
    email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Administrator")
    _promote(test_engine, email, UserRole.admin)
    return email


class TestRegistrationRole:
    def test_registration_defaults_to_user_role(self, client, plain_user):
        token_headers = _login(client, plain_user)
        resp = client.get("/api/v1/auth/me", headers=token_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "user"


class TestAuthWalls:
    def test_unauthenticated_gets_401(self, client):
        for path in (
            "/api/v1/readings",
            "/api/v1/reader/readings",
            "/api/v1/consultant/consultations",
            "/api/v1/admin/users",
        ):
            resp = client.get(path)
            assert resp.status_code == 401, path

    def test_plain_user_gets_403_on_role_endpoints(self, client, plain_user):
        headers = _login(client, plain_user)
        for path in (
            "/api/v1/reader/readings",
            "/api/v1/reader/readings/analytics",
            "/api/v1/consultant/consultations",
            "/api/v1/consultant/insights/trends",
            "/api/v1/admin/users",
            "/api/v1/admin/analytics/platform",
        ):
            resp = client.get(path, headers=headers)
            assert resp.status_code == 403, f"{path}: {resp.status_code}"


class TestUserRole:
    def test_user_tarot_reading_and_history(self, client, plain_user):
        headers = _login(client, plain_user)
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=headers,
            json={
                "spread": "Three Card",
                "cards": ["The Fool", "The Magician", "The Star"],
                "question": "What should I focus on?",
            },
        )
        assert resp.status_code == 201, resp.text
        reading = resp.json()

        resp = client.get("/api/v1/readings", headers=headers)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["items"][0]["id"] == reading["id"]
        assert payload["items"][0]["result"]["cards"] == [
            "The Fool",
            "The Magician",
            "The Star",
        ]

    def test_user_personal_analytics(self, client, plain_user):
        headers = _login(client, plain_user)
        resp = client.get("/api/v1/readings/analytics/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestReaderRole:
    def test_reader_reviews_user_reading(self, client, plain_user, reader_user):
        user_headers = _login(client, plain_user)
        created = client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={"spread": "Single Card", "cards": ["The Sun"]},
        ).json()

        reader_headers = _login(client, reader_user)
        resp = client.get("/api/v1/reader/readings", headers=reader_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.get("/api/v1/reader/readings/analytics", headers=reader_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.post(
            f"/api/v1/reader/readings/{created['id']}/review",
            headers=reader_headers,
            json={"status": "completed", "notes": "Strong Sun energy today."},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "completed"
        assert body["notes"] == "Strong Sun energy today."
        assert body["reviewed_by"] is not None

    def test_reader_cannot_access_admin(self, client, reader_user):
        headers = _login(client, reader_user)
        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 403


class TestConsultantRole:
    def test_consultant_provides_guidance(self, client, plain_user, consultant_user):
        user_headers = _login(client, plain_user)
        created = client.post(
            "/api/v1/consultations",
            headers=user_headers,
            json={"topic": "Stress", "message": "I feel overwhelmed lately."},
        )
        assert created.status_code == 201, created.text
        consultation = created.json()

        consultant_headers = _login(client, consultant_user)
        resp = client.get("/api/v1/consultant/consultations", headers=consultant_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.get("/api/v1/consultant/insights/trends", headers=consultant_headers)
        assert resp.status_code == 200
        assert resp.json()["total_users"] >= 2

        resp = client.get("/api/v1/consultant/insights/consultations", headers=consultant_headers)
        assert resp.status_code == 200
        assert resp.json()["total_requests"] >= 1

        resp = client.post(
            f"/api/v1/consultant/consultations/{consultation['id']}/guidance",
            headers=consultant_headers,
            json={"guidance": "Try a grounding breath practice each morning."},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["guidance"].startswith("Try a grounding")

        resp = client.get("/api/v1/consultations", headers=user_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any(c["guidance"] for c in items)


class TestAdminRole:
    def test_admin_manages_users_and_platform(self, client, plain_user, admin_user):
        admin_headers = _login(client, admin_user)

        resp = client.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

        user_headers = _login(client, plain_user)
        user_id = client.get("/api/v1/auth/me", headers=user_headers).json()["id"]

        resp = client.patch(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
            json={"role": "tarot_reader"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "tarot_reader"

        resp = client.patch(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        resp = client.get("/api/v1/admin/analytics/platform", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["users_total"] >= 2

        resp = client.get("/api/v1/admin/analytics/readings", headers=admin_headers)
        assert resp.status_code == 200

        resp = client.post("/api/v1/admin/reports/system", headers=admin_headers)
        assert resp.status_code == 201, resp.text
        report = resp.json()
        assert "platform" in report["payload"]

        resp = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        actions = [item["action"] for item in resp.json()["items"]]
        assert "user.update" in actions
        assert "report.generate" in actions

    def test_cannot_demote_last_admin(self, client, admin_user):
        admin_headers = _login(client, admin_user)
        admin_id = client.get("/api/v1/auth/me", headers=admin_headers).json()["id"]
        resp = client.patch(
            f"/api/v1/admin/users/{admin_id}",
            headers=admin_headers,
            json={"role": "user"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "LAST_ADMIN"

    def test_admin_change_persists_on_next_login(self, client, plain_user, admin_user):
        admin_headers = _login(client, admin_user)
        user_headers = _login(client, plain_user)
        user_id = client.get("/api/v1/auth/me", headers=user_headers).json()["id"]
        client.patch(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
            json={"role": "spiritual_consultant"},
        )
        fresh = _login(client, plain_user)
        resp = client.get("/api/v1/auth/me", headers=fresh)
        assert resp.json()["role"] == "spiritual_consultant"


class TestAdminPlatformReadings:
    """FR-007 reading oversight: admins audit every platform reading, not just their own."""

    def test_admin_sees_all_readings_with_owner_email(self, client, plain_user, admin_user):
        user_headers = _login(client, plain_user)
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={
                "spread": "Three Card",
                "cards": ["The Fool", "The Magician", "The Star"],
                "question": "What should I focus on?",
            },
        )
        assert resp.status_code == 201, resp.text
        reading_id = resp.json()["id"]

        admin_headers = _login(client, admin_user)
        resp = client.get("/api/v1/admin/readings", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["total"] >= 1
        item = next(i for i in payload["items"] if i["id"] == reading_id)
        assert item["owner_email"] == plain_user
        assert item["type"] == "tarot"
        assert item["status"] == "completed"

    def test_admin_readings_type_and_status_filters(self, client, plain_user, admin_user):
        user_headers = _login(client, plain_user)
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={
                "spread": "Single Card",
                "cards": ["The Star"],
            },
        )
        assert resp.status_code == 201, resp.text

        admin_headers = _login(client, admin_user)
        resp = client.get(
            "/api/v1/admin/readings?type=tarot&status=completed", headers=admin_headers
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] >= 1
        assert all(i["type"] == "tarot" for i in payload["items"])
        assert all(i["status"] == "completed" for i in payload["items"])

        resp = client.get("/api/v1/admin/readings?type=palm", headers=admin_headers)
        assert resp.status_code == 200
        assert all(i["type"] == "palm" for i in resp.json()["items"])

    def test_admin_with_no_own_readings_still_sees_platform(self, client, plain_user, admin_user):
        # The owner-scoped /readings list would be empty for the admin; the
        # oversight endpoint must not be.
        admin_headers = _login(client, admin_user)
        own = client.get("/api/v1/readings", headers=admin_headers)
        assert own.status_code == 200

        user_headers = _login(client, plain_user)
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={"spread": "Single Card", "cards": ["The Magician"]},
        )
        assert resp.status_code == 201, resp.text

        resp = client.get("/api/v1/admin/readings", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_non_admin_gets_403(self, client, plain_user, reader_user):
        for email in (plain_user, reader_user):
            headers = _login(client, email)
            resp = client.get("/api/v1/admin/readings", headers=headers)
            assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        resp = client.get("/api/v1/admin/readings")
        assert resp.status_code == 401


class TestAdminExecutiveAnalytics:
    """Milestone 4 executive analytics: time windows, engagement, per-type activity."""

    def test_platform_analytics_windows_and_engagement(self, client, plain_user, admin_user):
        user_headers = _login(client, plain_user)
        client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={"spread": "Single Card", "cards": ["The Star"]},
        )

        admin_headers = _login(client, admin_user)
        resp = client.get(
            "/api/v1/admin/analytics/platform?days=30", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["days"] == 30
        # Both fresh accounts signed up inside the requested window.
        assert body["signups_in_period"] >= 2
        assert body["signups_previous_period"] >= 0
        assert body["readings_in_period"] >= 1
        assert body["readings_previous_period"] >= 0
        assert len(body["signups_per_day"]) >= 1
        engagement = body["engagement"]
        assert engagement["users_with_readings"] >= 1
        assert engagement["users_with_multiple_readings"] >= 0

    def test_platform_analytics_days_validation(self, client, admin_user):
        admin_headers = _login(client, admin_user)
        resp = client.get("/api/v1/admin/analytics/platform?days=0", headers=admin_headers)
        assert resp.status_code == 422

    def test_reading_statistics_per_day_by_type(self, client, plain_user, admin_user):
        user_headers = _login(client, plain_user)
        resp = client.post(
            "/api/v1/readings/tarot",
            headers=user_headers,
            json={"spread": "Single Card", "cards": ["The Sun"]},
        )
        assert resp.status_code == 201, resp.text

        admin_headers = _login(client, admin_user)
        resp = client.get("/api/v1/admin/analytics/readings?days=7", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["days"] == 7
        assert body["total"] >= 1
        assert body["by_status"], "status distribution must be reported"
        tarot_rows = [r for r in body["per_day_by_type"] if r["type"] == "tarot"]
        assert tarot_rows, "expected at least one tarot day bucket in the window"
        assert all(set(r) >= {"day", "type", "count"} for r in tarot_rows)


class TestAdminAuditActor:
    """FR-007 audit trail: entries identify the acting account by email."""

    def test_audit_logs_include_actor_email(self, client, plain_user, admin_user):
        admin_headers = _login(client, admin_user)
        user_headers = _login(client, plain_user)
        user_id = client.get("/api/v1/auth/me", headers=user_headers).json()["id"]
        client.patch(
            f"/api/v1/admin/users/{user_id}",
            headers=admin_headers,
            json={"is_active": False},
        )

        resp = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        entries = [i for i in resp.json()["items"] if i["action"] == "user.update"]
        assert entries, "expected the user.update entry just written"
        entry = entries[0]
        assert entry["actor_email"] == admin_user

# Admin console: session oversight, permissions, auth, config, and monitoring.
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole

PASSWORD = "TestPass123!"

ADMIN_PATHS = (
    "/api/v1/admin/users",
    "/api/v1/admin/analytics/platform",
    "/api/v1/admin/analytics/readings",
    "/api/v1/admin/analytics/sessions",
    "/api/v1/admin/readings",
    "/api/v1/admin/consultations",
    "/api/v1/admin/audit-logs",
    "/api/v1/admin/permissions",
    "/api/v1/admin/settings/auth",
    "/api/v1/admin/settings/system",
    "/api/v1/admin/errors",
    "/api/v1/admin/errors/stats",
    "/api/v1/admin/system/performance",
)


def _register(client, email, full_name, role="user"):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": full_name,
            "role": role,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp


def _login(client, email):
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(test_engine, email, role):
    Session = sessionmaker(bind=test_engine)
    with Session() as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


@pytest.fixture()
def admin_headers(client, test_engine):
    email = f"console-admin-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Console Admin")
    _promote(test_engine, email, UserRole.admin)
    return _login(client, email)


@pytest.fixture()
def plain_headers(client):
    email = f"console-user-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Console User")
    return _login(client, email)


class TestAdminConsoleAccess:
    def test_every_console_endpoint_requires_admin(self, client, plain_headers):
        for path in ADMIN_PATHS:
            assert client.get(path).status_code == 401, path
            assert client.get(path, headers=plain_headers).status_code == 403, path

    def test_admin_reads_every_console_endpoint(self, client, admin_headers):
        for path in ADMIN_PATHS:
            resp = client.get(path, headers=admin_headers)
            assert resp.status_code == 200, f"{path}: {resp.status_code} {resp.text}"


class TestAdminLosesSessionAccess:
    """Admins govern the platform; they never host or attend sessions."""

    def _consultant(self, client):
        email = f"studio-reader-{uuid.uuid4().hex[:8]}@example.com"
        _register(client, email, "Studio Reader", role="tarot_reader")
        headers = _login(client, email)
        profile = client.put(
            "/api/v1/consultants/me/profile",
            json={
                "headline": "Tarot guidance",
                "session_rate": "40.00",
                "session_duration_minutes": 60,
                "timezone": "UTC",
            },
            headers=headers,
        )
        assert profile.status_code == 200, profile.text
        return headers, profile.json()

    def _admin(self, client, test_engine):
        email = f"no-session-admin-{uuid.uuid4().hex[:8]}@example.com"
        _register(client, email, "Governance Admin")
        _promote(test_engine, email, UserRole.admin)
        return _login(client, email)

    def test_admin_blocked_from_consultant_studio(self, client, test_engine):
        headers = self._admin(client, test_engine)
        for path in (
            "/api/v1/consultants/me/profile",
            "/api/v1/consultants/me/stats",
            "/api/v1/consultants/me/availability/rules",
            "/api/v1/consultants/me/bookings",
        ):
            resp = client.get(path, headers=headers)
            assert resp.status_code == 403, f"{path}: {resp.status_code}"

    def test_admin_blocked_from_the_seeker_session_hub(self, client, test_engine):
        headers = self._admin(client, test_engine)
        resp = client.get("/api/v1/bookings", headers=headers)
        assert resp.status_code == 403

    def test_admin_cannot_book_a_session(self, client, test_engine):
        _consultant_headers, profile = self._consultant(client)
        admin_headers = self._admin(client, test_engine)
        resp = client.post(
            f"/api/v1/consultants/{profile['id']}/bookings",
            json={"subject": "Admin trying to book"},
            headers=admin_headers,
        )
        assert resp.status_code == 403

    def test_admin_cannot_mutate_a_session(self, client, test_engine):
        """Even with a real booking id, an admin may not act on it."""
        consultant_headers, profile = self._consultant(client)
        seeker_email = f"real-seeker-{uuid.uuid4().hex[:8]}@example.com"
        _register(client, seeker_email, "Real Seeker")
        seeker_headers = _login(client, seeker_email)

        rule = client.post(
            "/api/v1/consultants/me/availability/rules",
            json={
                "weekday": (date.today() + timedelta(days=7)).weekday(),
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "slot_duration_minutes": 60,
                "buffer_minutes": 0,
                "timezone": "UTC",
                "effective_from": date.today().isoformat(),
            },
            headers=consultant_headers,
        )
        assert rule.status_code == 201, rule.text
        slots = client.get(
            f"/api/v1/consultants/{profile['id']}/slots",
            params={"date": (date.today() + timedelta(days=7)).isoformat()},
            headers=seeker_headers,
        ).json()["slots"]
        assert slots
        booking = client.post(
            f"/api/v1/consultants/{profile['id']}/bookings",
            json={"slot_id": slots[0]["id"], "subject": "Career guidance"},
            headers=seeker_headers,
        )
        assert booking.status_code == 201, booking.text
        booking_id = booking.json()["id"]

        admin_headers = self._admin(client, test_engine)
        for path, method in (
            (f"/api/v1/consultants/me/bookings/{booking_id}", "get"),
            (f"/api/v1/consultants/me/bookings/{booking_id}/accept", "post"),
            (f"/api/v1/bookings/{booking_id}", "get"),
            (f"/api/v1/bookings/{booking_id}/messages", "get"),
        ):
            resp = getattr(client, method)(path, headers=admin_headers)
            assert resp.status_code == 403, f"{method.upper()} {path}: {resp.status_code}"


class TestSessionOversight:
    def _booked_session(self, client):
        reader_email = f"oversight-reader-{uuid.uuid4().hex[:8]}@example.com"
        seeker_email = f"oversight-seeker-{uuid.uuid4().hex[:8]}@example.com"
        _register(client, reader_email, "Oversight Reader", role="tarot_reader")
        _register(client, seeker_email, "Oversight Seeker")

        reader_headers = _login(client, reader_email)
        seeker_headers = _login(client, seeker_email)

        profile = client.put(
            "/api/v1/consultants/me/profile",
            json={
                "headline": "Palm & tarot counsel",
                "session_rate": "55.00",
                "session_duration_minutes": 60,
                "timezone": "UTC",
            },
            headers=reader_headers,
        ).json()

        rule = client.post(
            "/api/v1/consultants/me/availability/rules",
            json={
                "weekday": (date.today() + timedelta(days=7)).weekday(),
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "slot_duration_minutes": 60,
                "buffer_minutes": 0,
                "timezone": "UTC",
                "effective_from": date.today().isoformat(),
            },
            headers=reader_headers,
        )
        assert rule.status_code == 201, rule.text
        target_day = date.today() + timedelta(days=7)
        slots = client.get(
            f"/api/v1/consultants/{profile['id']}/slots",
            params={"date": target_day.isoformat()},
            headers=seeker_headers,
        ).json()["slots"]
        assert slots
        booking = client.post(
            f"/api/v1/consultants/{profile['id']}/bookings",
            json={"slot_id": slots[0]["id"], "subject": "Relationship clarity"},
            headers=seeker_headers,
        )
        assert booking.status_code == 201, booking.text
        return profile, booking.json()

    def test_console_reports_scheduled_sessions(self, client, admin_headers):
        profile, booking = self._booked_session(client)
        resp = client.get(
            "/api/v1/admin/analytics/sessions", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["total"] == 1
        assert body["pending_requests"] == 1
        assert body["by_status"][0]["status"] == "pending"
        assert body["consultants_total"] == 1
        assert body["consultants_accepting"] == 1
        assert body["unique_seekers"] == 1
        assert body["days"] == 30

        row = body["upcoming_sessions"][0]
        assert row["subject"] == "Relationship clarity"
        assert row["status"] == "pending"
        assert row["consultant_name"] == "Oversight Reader"
        assert row["duration_minutes"] == 60

    def test_accepted_session_counts_as_upcoming(self, client, admin_headers):
        _profile, booking = self._booked_session(client)
        reader_email = (
            client.get("/api/v1/admin/users", headers=admin_headers)
            .json()["items"]
        )
        reader = next(u for u in reader_email if u["full_name"] == "Oversight Reader")
        # The reader accepts through the studio, not through the admin console.
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/accept",
            headers={"Authorization": f"Bearer {_reader_token(client, reader['email'])}"},
        )
        assert resp.status_code == 200, resp.text

        body = client.get("/api/v1/admin/analytics/sessions", headers=admin_headers).json()
        assert body["upcoming"] == 1
        assert body["pending_requests"] == 0
        assert body["upcoming_sessions"][0]["status"] == "accepted"

    def test_empty_platform_reports_zeroes(self, client, admin_headers):
        body = client.get(
            "/api/v1/admin/analytics/sessions", headers=admin_headers
        ).json()
        assert body["total"] == 0
        assert body["upcoming"] == 0
        assert body["pending_requests"] == 0
        assert body["upcoming_sessions"] == []
        assert body["avg_rating"] is None


def _reader_token(client, email):
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestPermissionMatrix:
    def test_matrix_lists_every_role(self, client, admin_headers):
        body = client.get("/api/v1/admin/permissions", headers=admin_headers).json()
        assert set(body["roles"]) == {"user", "tarot_reader", "spiritual_consultant", "admin"}
        names = {rule["name"] for rule in body["rules"]}
        assert {
            "require_user",
            "require_tarot_reader",
            "require_spiritual_consultant",
            "require_admin",
        } <= names
        admin_rule = next(r for r in body["rules"] if r["name"] == "require_admin")
        assert admin_rule["allowed"] == ["admin"]

    def test_admins_are_not_session_hosts(self, client, admin_headers):
        body = client.get("/api/v1/admin/permissions", headers=admin_headers).json()
        session_rules = [
            rule
            for rule in body["rules"]
            if rule["name"] in ("require_consultant_role", "require_session_role")
        ]
        assert session_rules, "session rules must be documented"
        for rule in session_rules:
            assert "admin" not in rule["allowed"], rule


class TestAuthSettings:
    def test_reports_real_policy_without_secrets(self, client, admin_headers):
        from app.auth import tokens
        from app.config import settings

        body = client.get("/api/v1/admin/settings/auth", headers=admin_headers).json()
        assert body["jwt_algorithm"] == tokens.JWT_ALGORITHM
        assert body["access_token_expire_minutes"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES
        assert body["refresh_token_expire_days"] == settings.REFRESH_TOKEN_EXPIRE_DAYS
        assert body["refresh_cookie_name"] == "palmistry_refresh"
        assert body["password_hashing"] == "argon2id"
        assert body["rate_limits"]["auth_requests_per_minute"] > 0
        assert body["cors_origins"] == list(settings.CORS_ORIGINS)
        assert body["admin_signup_requires_invite_code"] is True
        assert body["notes"]

    def test_never_leaks_secret_values(self, client, admin_headers):
        from app.config import settings

        body = client.get("/api/v1/admin/settings/auth", headers=admin_headers).json()
        flattened = json.dumps(body)
        # Compare the secret's own bytes, not a lowercased form: the response's
        # key names legitimately contain the word "admin".
        for secret in (
            settings.SECRET_KEY,
            settings.GROQ_API_KEY,
            settings.OPENAI_API_KEY,
            settings.ADMIN_SIGNUP_CODE,
            settings.EMAIL_SMTP_PASSWORD,
        ):
            if secret and len(secret) > 4:
                assert secret not in flattened, f"leaked secret: {secret[:3]}…"


class TestSystemConfig:
    def test_reports_environment_and_release(self, client, admin_headers):
        from app.config import settings

        body = client.get("/api/v1/admin/settings/system", headers=admin_headers).json()
        assert body["environment"] == settings.ENVIRONMENT
        assert body["version"] == settings.APP_VERSION
        assert body["api_prefix"] == settings.API_V1_PREFIX
        assert body["docs_url"].endswith("/docs")
        assert "palmistry" in body["database_target"]
        assert "postgres" not in body["database_target"].lower().replace("postgresql", "")
        # The revision must match the newest migration actually applied.
        # Read `alembic_version` directly rather than walking the script
        # directory: the suite already migrated the test DB to head, so this
        # asserts the endpoint reports reality rather than a hard-coded value.
        from sqlalchemy import text

        from app.db.session import get_engine

        with get_engine().connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
        assert body["migration_revision"] == (row[0] if row else None)
        assert body["uptime_seconds"] >= 0
        assert {s["name"] for s in body["schedulers"]} == {"notifications", "booking"}
        assert body["allowed_image_types"] == ["jpg", "jpeg", "png", "webp"]

    def test_database_target_hides_credentials(self, client, admin_headers):
        from app.config import settings

        from urllib.parse import urlparse

        password = urlparse(settings.DATABASE_URL).password
        body = client.get("/api/v1/admin/settings/system", headers=admin_headers).json()
        if password:
            assert password not in body["database_target"]


class TestErrorMonitoring:
    def _trigger_auth_failures(self, client, count=1):
        for index in range(count):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nobody@example.com",
                    "password": f"wrong-password-{index}",
                },
            )

    def _trigger_forbidden(self, client, plain_headers):
        client.get("/api/v1/admin/users", headers=plain_headers)

    def test_failures_are_recorded_and_counted(
        self, client, admin_headers, plain_headers
    ):
        from app.middleware.rate_limit import _buckets

        _buckets.clear()
        self._trigger_auth_failures(client, count=2)
        self._trigger_forbidden(client, plain_headers)

        stats = client.get("/api/v1/admin/errors/stats", headers=admin_headers).json()
        assert stats["total"] >= 2
        assert stats["unresolved"] >= 2
        assert stats["auth_failures_24h"] >= 1
        kinds = {row["kind"]: row["count"] for row in stats["by_kind"]}
        assert kinds.get("auth_failure", 0) >= 1
        assert kinds.get("forbidden", 0) >= 1

        listing = client.get("/api/v1/admin/errors", headers=admin_headers).json()
        assert listing["total"] >= 2
        assert listing["unresolved"] >= 2
        first = listing["items"][0]
        assert first["kind"] in {"auth_failure", "forbidden"}
        assert first["occurrences"] >= 1
        assert first["status_code"] in (401, 403)
        assert first["message"]

    def test_repeats_are_deduplicated(self, client, admin_headers, plain_headers):
        self._trigger_forbidden(client, plain_headers)
        self._trigger_forbidden(client, plain_headers)

        listing = client.get(
            "/api/v1/admin/errors",
            params={"kind": "forbidden", "unresolved_only": True},
            headers=admin_headers,
        ).json()
        rows = [i for i in listing["items"] if i["path"] == "/api/v1/admin/users"]
        assert rows
        assert rows[0]["occurrences"] >= 2

    def test_acknowledge_clears_unresolved_and_audits(
        self, client, admin_headers, plain_headers
    ):
        self._trigger_forbidden(client, plain_headers)
        listing = client.get("/api/v1/admin/errors", headers=admin_headers).json()
        target = listing["items"][0]

        resp = client.post(
            f"/api/v1/admin/errors/{target['id']}/acknowledge",
            headers=admin_headers,
        )
        assert resp.status_code == 204, resp.text

        after = client.get(
            "/api/v1/admin/errors",
            params={"unresolved_only": True},
            headers=admin_headers,
        ).json()
        assert all(item["id"] != target["id"] for item in after["items"])

        audit = client.get("/api/v1/admin/audit-logs", headers=admin_headers).json()
        assert any(a["action"] == "error.acknowledge" for a in audit["items"])

    def test_acknowledge_unknown_id_returns_404(self, client, admin_headers):
        resp = client.post(
            f"/api/v1/admin/errors/{uuid.uuid4()}/acknowledge", headers=admin_headers
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "ERROR_NOT_FOUND"

    def test_acknowledge_is_idempotent(self, client, admin_headers, plain_headers):
        self._trigger_forbidden(client, plain_headers)
        target = client.get("/api/v1/admin/errors", headers=admin_headers).json()["items"][0]
        path = f"/api/v1/admin/errors/{target['id']}/acknowledge"
        assert client.post(path, headers=admin_headers).status_code == 204
        assert client.post(path, headers=admin_headers).status_code == 204


class TestPerformanceSummary:
    def test_reports_latency_and_routes(self, client, admin_headers):
        body = client.get(
            "/api/v1/admin/system/performance", headers=admin_headers
        ).json()
        assert body["uptime_seconds"] >= 0
        assert body["requests_total"] > 0
        assert body["error_rate"] >= 0
        assert set(body["latency_ms"]) >= {"p50", "p95", "avg", "max"}
        assert isinstance(body["slowest_routes"], list)
        assert body["notes"]

    def test_health_probes_are_excluded(self, client, admin_headers):
        client.get("/api/v1/health")
        body = client.get(
            "/api/v1/admin/system/performance", headers=admin_headers
        ).json()
        assert all(row["path"] != "/api/v1/health" for row in body["slowest_routes"])

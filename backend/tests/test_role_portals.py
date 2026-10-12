# Per-role signup and login portal tests.
import uuid

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole

PASSWORD = "PortalPass123!"


def _register_via_portal(client, portal, email, extra=None):
    body = {"email": email, "password": PASSWORD, "full_name": "Portal Tester"}
    if extra:
        body.update(extra)
    return client.post(f"/api/v1/auth/{portal}/register", json=body)


def _login_via_portal(client, portal, email):
    return client.post(
        f"/api/v1/auth/{portal}/login", json={"email": email, "password": PASSWORD}
    )


def _login(client, email):
    return client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})


class TestPortalRegistration:
    @pytest.mark.parametrize(
        "portal,role",
        [
            ("user", "user"),
            ("tarot-reader", "tarot_reader"),
            ("spiritual-consultant", "spiritual_consultant"),
        ],
        ids=["user", "reader", "consultant"],
    )
    def test_portal_signup_creates_that_role(self, client, portal, role):
        email = f"{portal.replace('-', '')}-{uuid.uuid4().hex[:8]}@example.com"
        resp = _register_via_portal(client, portal, email)
        assert resp.status_code == 201, resp.text
        assert resp.json()["user"]["role"] == role

    def test_admin_portal_requires_invite_code(self, client):
        email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
        resp = _register_via_portal(client, "admin", email)
        assert resp.status_code == 403
        assert resp.json()["code"] == "ADMIN_SIGNUP_FORBIDDEN"

        resp = _register_via_portal(client, "admin", email, extra={"admin_invite_code": "wrong"})
        assert resp.status_code == 403

        resp = _register_via_portal(
            client, "admin", email, extra={"admin_invite_code": "ADMIN"}
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["user"]["role"] == "admin"

    def test_unknown_portal_rejected(self, client):
        email = f"{uuid.uuid4().hex[:8]}@example.com"
        resp = _register_via_portal(client, "wizard", email)
        # FastAPI path-param enum validation -> 422 with the error envelope.
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"


class TestPortalLogin:
    def test_login_on_matching_portal_succeeds(self, client):
        email = f"reader-{uuid.uuid4().hex[:8]}@example.com"
        _register_via_portal(client, "tarot-reader", email)
        resp = _login_via_portal(client, "tarot-reader", email)
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "tarot_reader"

    def test_login_on_wrong_portal_rejected(self, client):
        email = f"reader-{uuid.uuid4().hex[:8]}@example.com"
        _register_via_portal(client, "tarot-reader", email)
        resp = _login_via_portal(client, "user", email)
        assert resp.status_code == 403
        assert resp.json()["code"] == "WRONG_PORTAL"

    def test_shared_login_still_works_for_any_role(self, client):
        email = f"consult-{uuid.uuid4().hex[:8]}@example.com"
        _register_via_portal(client, "spiritual-consultant", email)
        resp = _login(client, email)
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "spiritual_consultant"


class TestLegacyRegisterKeepsRole:
    def test_generic_register_accepts_role(self, client):
        email = f"legacy-{uuid.uuid4().hex[:8]}@example.com"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": PASSWORD,
                "full_name": "Legacy",
                "role": "tarot_reader",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["user"]["role"] == "tarot_reader"

    def test_generic_register_defaults_to_user(self, client):
        email = f"legacy-{uuid.uuid4().hex[:8]}@example.com"
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": PASSWORD, "full_name": "Legacy"},
        )
        assert resp.status_code == 201
        assert resp.json()["user"]["role"] == "user"

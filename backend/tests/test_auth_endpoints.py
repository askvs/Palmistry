# Auth endpoints: register, login, refresh rotation, logout, /me.

import jwt
import pytest

from app.auth.tokens import JWT_ALGORITHM
from app.config import settings
from app.middleware.rate_limit import _buckets

pytestmark = pytest.mark.without_db if False else []


def _clear_rate_limit():
    _buckets.clear()


def _register(client, email="jane@example.com", password="passw0rd-long", name="Jane Doe"):
    _clear_rate_limit()
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )


def _login(client, email="jane@example.com", password="passw0rd-long"):
    _clear_rate_limit()
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


class TestRegister:
    def test_register_201_sets_refresh_cookie_and_jwt(self, client):
        resp = _register(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["user"]["email"] == "jane@example.com"
        assert body["user"]["role"] == "user"
        assert body["token_type"] == "bearer"
        assert body["access_token"].count(".") == 2
        assert "palmistry_refresh" in resp.cookies

    def test_register_duplicate_email_409_envelope(self, client):
        _register(client)
        _clear_rate_limit()
        resp = _register(client, email="jane@example.com")
        assert resp.status_code == 409
        body = resp.json()
        assert body["code"] == "EMAIL_ALREADY_REGISTERED"
        assert body["request_id"]

    def test_register_weak_password_422(self, client):
        _clear_rate_limit()
        resp = _register(client, password="short")
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    def test_register_invalid_email_422(self, client):
        _clear_rate_limit()
        resp = _register(client, email="not-an-email")
        assert resp.status_code == 422

    def test_register_normalizes_email_case(self, client):
        resp = _register(client, email="Jane@Example.COM")
        assert resp.status_code == 201
        assert resp.json()["user"]["email"] == "jane@example.com"


class TestLogin:
    def test_login_success_returns_access_token(self, client):
        _register(client)
        resp = _login(client)
        assert resp.status_code == 200
        assert resp.json()["access_token"].count(".") == 2
        assert "palmistry_refresh" in resp.cookies

    def test_login_wrong_password_401_auth_failed(self, client):
        _register(client)
        resp = _login(client, password="totally-wrong")
        assert resp.status_code == 401
        assert resp.json()["code"] == "AUTH_FAILED"

    def test_login_unknown_email_401(self, client):
        resp = _login(client, email="ghost@example.com")
        assert resp.status_code == 401
        assert resp.json()["code"] == "AUTH_FAILED"


class TestRefreshRotation:
    def test_refresh_returns_new_tokens_and_rotates_cookie(self, client):
        _register(client)
        old_cookie = client.cookies.get("palmistry_refresh")
        _clear_rate_limit()
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        assert resp.json()["access_token"]
        new_cookie = client.cookies.get("palmistry_refresh")
        assert new_cookie != old_cookie

    def test_refresh_with_revoked_old_token_reuses_detection(self, client):
        _register(client)
        old_cookie = client.cookies.get("palmistry_refresh")
        _clear_rate_limit()
        first = client.post("/api/v1/auth/refresh")
        assert first.status_code == 200
        second_cookie = client.cookies.get("palmistry_refresh")

        client.cookies.set("palmistry_refresh", old_cookie)
        _clear_rate_limit()
        reuse = client.post("/api/v1/auth/refresh")
        assert reuse.status_code == 401
        assert reuse.json()["code"] == "INVALID_REFRESH_TOKEN"

        client.cookies.set("palmistry_refresh", second_cookie)
        _clear_rate_limit()
        after = client.post("/api/v1/auth/refresh")
        assert after.status_code == 401, "reuse must revoke ALL user refresh tokens"

    def test_refresh_without_cookie_401(self, client):
        _clear_rate_limit()
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


class TestLogout:
    def test_logout_revokes_and_clears_cookie(self, client):
        _register(client)
        cookie = client.cookies.get("palmistry_refresh")
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

        client.cookies.set("palmistry_refresh", cookie)
        _clear_rate_limit()
        refresh = client.post("/api/v1/auth/refresh")
        assert refresh.status_code == 401


class TestMe:
    def test_me_with_valid_bearer_returns_user(self, client):
        resp = _register(client)
        token = resp.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "jane@example.com"

    def test_me_without_token_401(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_with_garbage_token_401(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
        assert resp.status_code == 401

    def test_me_with_expired_token_401(self, client):
        resp = _register(client)
        token = resp.json()["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        expired = jwt.encode(
            {**payload, "exp": payload["iat"] - 10}, settings.SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert me.status_code == 401

    def test_jwt_claims_shape(self, client):
        resp = _register(client)
        token = resp.json()["access_token"]
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert claims["role"] == "user"
        assert claims["type"] == "access"
        assert claims["sub"]
        assert claims["jti"]

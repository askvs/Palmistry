# Google OAuth2 adapter tests (mocked, no real provider calls).

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.errors import OAuthNotConfigured
from app.auth.oauth import google as google_oauth


class TestUnconfigured:
    def test_authorize_returns_503_when_not_configured(self, client):
        resp = client.get("/api/v1/auth/google/authorize", follow_redirects=False)
        assert resp.status_code == 503
        assert resp.json()["code"] == "OAUTH_NOT_CONFIGURED"

    def test_is_configured_false_by_default(self, monkeypatch):
        monkeypatch.setattr(google_oauth.settings, "GOOGLE_CLIENT_ID", "")
        monkeypatch.setattr(google_oauth.settings, "GOOGLE_CLIENT_SECRET", "")
        assert google_oauth.is_configured() is False


class TestAdapter:
    def test_extract_profile_normalizes_userinfo(self):
        token = {
            "userinfo": {"email": "Gmail.User@Example.com", "name": "Gmail User", "sub": "g-123"}
        }
        profile = google_oauth.extract_profile(token)
        assert profile == {
            "email": "Gmail.User@Example.com",
            "full_name": "Gmail User",
            "google_id": "g-123",
        }

    def test_extract_profile_falls_back_to_email_prefix(self):
        token = {"userinfo": {"email": "noname@example.com", "sub": "g-456"}}
        profile = google_oauth.extract_profile(token)
        assert profile["full_name"] == "noname"

    def test_extract_profile_requires_email(self):
        with pytest.raises(OAuthNotConfigured):
            google_oauth.extract_profile({"userinfo": {"name": "No Email"}})


class TestUpsertFlow:
    def test_oauth_only_user_has_null_password_hash(self, test_engine, monkeypatch):
        from app.auth import service
        from app.db.session import get_engine
        from app.models.user import UserRole
        from sqlalchemy.orm import Session

        db = Session(get_engine())
        try:
            user = service.upsert_oauth_user(
                db, email="New.OAuth@Example.com", full_name="New OAuth", google_id="g-789"
            )
            assert user.password_hash is None
            assert user.google_id == "g-789"
            assert user.role == UserRole.user
            assert user.email == "new.oauth@example.com"
        finally:
            db.close()

    def test_upsert_links_existing_email_to_google_id(self, test_engine):
        from app.auth import service
        from app.db.session import get_engine
        from sqlalchemy.orm import Session

        db = Session(get_engine())
        try:
            service.register_user(
                db, email="linked@example.com", password="passw0rd-long", full_name="Linked User"
            )
            user = service.upsert_oauth_user(
                db, email="LINKED@example.com", full_name="Linked User", google_id="g-link-1"
            )
            assert user.google_id == "g-link-1"
            assert user.password_hash is not None, "password login must survive linking"
        finally:
            db.close()

    def test_upsert_conflicting_google_id_rejected(self, test_engine):
        from app.auth import service
        from app.db.session import get_engine
        from sqlalchemy.orm import Session

        db = Session(get_engine())
        try:
            service.upsert_oauth_user(
                db, email="a@example.com", full_name="A", google_id="g-1"
            )
            with pytest.raises(Exception) as exc_info:
                service.upsert_oauth_user(
                    db, email="a@example.com", full_name="A", google_id="g-2"
                )
            assert "different Google account" in str(exc_info.value)
        finally:
            db.close()

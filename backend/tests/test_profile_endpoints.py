# Profile endpoints: get-or-create, preferences, interests, goals, avatar.

from pathlib import Path

import pytest

from app.config import settings
from app.middleware.rate_limit import _buckets

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBP_BODY = b"RIFF\x24\x00\x00\x00WEBPVP8 \x00\x00\x00\x00"


def _clear_rate_limit():
    _buckets.clear()


def _register(client, email="jane@example.com", password="passw0rd-long", name="Jane Doe"):
    _clear_rate_limit()
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    assert resp.status_code == 201
    return resp


def _auth_headers(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _get_profile(client, headers):
    return client.get("/api/v1/profile", headers=headers)


def _patch_profile(client, headers, payload):
    return client.patch("/api/v1/profile", json=payload, headers=headers)


class TestGetProfile:
    def test_get_profile_requires_auth_401(self, client):
        resp = client.get("/api/v1/profile")
        assert resp.status_code == 401
        assert resp.json()["code"] == "HTTP_401"

    def test_get_profile_creates_defaults(self, client):
        headers = _auth_headers(_register(client))
        resp = _get_profile(client, headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["age_group"] is None
        assert body["avatar_key"] is None
        assert body["default_deck"] == "Rider-Waite-Smith"
        assert body["favorite_spread"] == "Three Card"
        assert body["tone"] == "Gentle"
        assert body["notify_daily_guidance"] is True
        assert body["notify_reminders"] is True
        assert body["notify_sms"] is False
        assert body["interests"] == []
        assert body["goals"] == []
        assert body["user_id"]

    def test_get_profile_is_idempotent(self, client):
        headers = _auth_headers(_register(client))
        first = _get_profile(client, headers).json()
        second = _get_profile(client, headers).json()
        assert first["id"] == second["id"]
        assert first["user_id"] == second["user_id"]
        assert first["created_at"] == second["created_at"]

    def test_get_profile_with_garbage_token_401(self, client):
        resp = client.get(
            "/api/v1/profile", headers={"Authorization": "Bearer garbage.token.here"}
        )
        assert resp.status_code == 401


class TestUpdateProfile:
    def test_patch_full_name_mirrors_to_users(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"full_name": "Janet Dorian"})
        assert resp.status_code == 200
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.json()["full_name"] == "Janet Dorian"

    def test_patch_age_group(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"age_group": "25-34"})
        assert resp.status_code == 200
        assert resp.json()["age_group"] == "25-34"

    def test_patch_clears_age_group_with_null(self, client):
        headers = _auth_headers(_register(client))
        _patch_profile(client, headers, {"age_group": "25-34"})
        resp = _patch_profile(client, headers, {"age_group": None})
        assert resp.status_code == 200
        assert resp.json()["age_group"] is None

    def test_patch_preferences(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(
            client,
            headers,
            {
                "default_deck": "Rider-Waite-Smith",
                "favorite_spread": "Celtic Cross",
                "tone": "Direct",
                "notify_daily_guidance": False,
                "notify_reminders": False,
                "notify_sms": True,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["favorite_spread"] == "Celtic Cross"
        assert body["tone"] == "Direct"
        assert body["notify_daily_guidance"] is False
        assert body["notify_reminders"] is False
        assert body["notify_sms"] is True

    def test_patch_invalid_age_group_422(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"age_group": "900-999"})
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    def test_patch_invalid_tone_422(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"tone": "Sarcastic"})
        assert resp.status_code == 422

    def test_patch_invalid_deck_422(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"default_deck": "Thoth"})
        assert resp.status_code == 422

    def test_patch_invalid_spread_422(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"favorite_spread": "Horseshoe"})
        assert resp.status_code == 422

    def test_patch_empty_name_422(self, client):
        headers = _auth_headers(_register(client))
        resp = _patch_profile(client, headers, {"full_name": ""})
        assert resp.status_code == 422

    def test_patch_ignores_unset_fields(self, client):
        headers = _auth_headers(_register(client))
        _patch_profile(client, headers, {"tone": "Direct"})
        resp = _patch_profile(client, headers, {"notify_sms": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["tone"] == "Direct"
        assert body["notify_sms"] is True


class TestInterests:
    def test_put_interests_replaces_set(self, client):
        headers = _auth_headers(_register(client))
        resp = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Tarot", "Palmistry"]},
            headers=headers,
        )
        assert resp.status_code == 200
        assert sorted(resp.json()["interests"]) == ["Palmistry", "Tarot"]

    def test_put_interests_deduplicates(self, client):
        headers = _auth_headers(_register(client))
        resp = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Tarot", "Tarot", "Numerology"]},
            headers=headers,
        )
        assert resp.status_code == 200
        assert sorted(resp.json()["interests"]) == ["Numerology", "Tarot"]

    def test_put_interests_cumulative_update_with_overlap(self, client):
        # Regression: incremental UI updates overlap stored rows, so replace must tolerate that.
        headers = _auth_headers(_register(client))
        first = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Numerology"]},
            headers=headers,
        )
        assert first.status_code == 200
        assert first.json()["interests"] == ["Numerology"]

        second = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Numerology", "Astrology", "Meditation"]},
            headers=headers,
        )
        assert second.status_code == 200
        assert sorted(second.json()["interests"]) == ["Astrology", "Meditation", "Numerology"]

        # Removing one and swapping another must also succeed (partial overlap).
        third = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Astrology", "Dream Interpretation"]},
            headers=headers,
        )
        assert third.status_code == 200
        assert sorted(third.json()["interests"]) == ["Astrology", "Dream Interpretation"]

        # Persisted — a fresh GET reflects the final list.
        fetched = client.get("/api/v1/profile", headers=headers)
        assert sorted(fetched.json()["interests"]) == ["Astrology", "Dream Interpretation"]

    def test_put_interests_unknown_422(self, client):
        headers = _auth_headers(_register(client))
        resp = client.put(
            "/api/v1/profile/interests",
            json={"interests": ["Tarot", "Crypto Trading"]},
            headers=headers,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    def test_put_interests_over_limit_422(self, client):
        headers = _auth_headers(_register(client))
        too_many = ["Tarot", "Palmistry", "Numerology", "Meditation", "Astrology",
                    "Crystal Healing", "Energy Work", "Manifestation",
                    "Dream Interpretation", "Runes", "Chakras"]
        resp = client.put(
            "/api/v1/profile/interests", json={"interests": too_many}, headers=headers
        )
        assert resp.status_code == 422

    def test_put_interests_clears_with_empty_list(self, client):
        headers = _auth_headers(_register(client))
        client.put("/api/v1/profile/interests", json={"interests": ["Tarot"]}, headers=headers)
        resp = client.put("/api/v1/profile/interests", json={"interests": []}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["interests"] == []


class TestGoals:
    def test_create_goal_201_and_listed(self, client):
        headers = _auth_headers(_register(client))
        resp = client.post(
            "/api/v1/profile/goals",
            json={"text": "Build a daily reflection habit"},
            headers=headers,
        )
        assert resp.status_code == 201
        goal = resp.json()
        assert goal["text"] == "Build a daily reflection habit"
        profile = _get_profile(client, headers).json()
        assert [g["id"] for g in profile["goals"]] == [goal["id"]]

    def test_create_goal_blank_422(self, client):
        headers = _auth_headers(_register(client))
        resp = client.post("/api/v1/profile/goals", json={"text": ""}, headers=headers)
        assert resp.status_code == 422

    def test_create_goal_too_long_422(self, client):
        headers = _auth_headers(_register(client))
        resp = client.post(
            "/api/v1/profile/goals", json={"text": "x" * 501}, headers=headers
        )
        assert resp.status_code == 422

    def test_update_goal(self, client):
        headers = _auth_headers(_register(client))
        goal = client.post(
            "/api/v1/profile/goals", json={"text": "Meditate"}, headers=headers
        ).json()
        resp = client.patch(
            f"/api/v1/profile/goals/{goal['id']}",
            json={"text": "Meditate for 10 minutes"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "Meditate for 10 minutes"

    def test_delete_goal(self, client):
        headers = _auth_headers(_register(client))
        goal = client.post(
            "/api/v1/profile/goals", json={"text": "Meditate"}, headers=headers
        ).json()
        resp = client.delete(f"/api/v1/profile/goals/{goal['id']}", headers=headers)
        assert resp.status_code == 204
        profile = _get_profile(client, headers).json()
        assert profile["goals"] == []

    def test_goal_not_found_404(self, client):
        headers = _auth_headers(_register(client))
        resp = client.patch(
            "/api/v1/profile/goals/00000000-0000-0000-0000-000000000000",
            json={"text": "Nope"},
            headers=headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "GOAL_NOT_FOUND"

    def test_cannot_touch_another_users_goal_404(self, client):
        first = _auth_headers(_register(client, email="a@example.com"))
        goal = client.post(
            "/api/v1/profile/goals", json={"text": "Mine"}, headers=first
        ).json()
        second = _auth_headers(_register(client, email="b@example.com"))
        patch = client.patch(
            f"/api/v1/profile/goals/{goal['id']}", json={"text": "Hijack"}, headers=second
        )
        delete = client.delete(f"/api/v1/profile/goals/{goal['id']}", headers=second)
        assert patch.status_code == 404
        assert delete.status_code == 404

    def test_goal_limit_400(self, client):
        headers = _auth_headers(_register(client))
        for i in range(25):
            resp = client.post(
                "/api/v1/profile/goals", json={"text": f"Goal {i}"}, headers=headers
            )
            assert resp.status_code == 201
        resp = client.post(
            "/api/v1/profile/goals", json={"text": "One too many"}, headers=headers
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "GOAL_LIMIT_REACHED"

    def test_invalid_goal_id_422(self, client):
        headers = _auth_headers(_register(client))
        resp = client.delete("/api/v1/profile/goals/not-a-uuid", headers=headers)
        assert resp.status_code == 422


class TestAvatar:
    def _put_avatar(self, client, headers, data, filename="avatar.png", mime="image/png"):
        return client.put(
            "/api/v1/profile/avatar",
            files={"avatar": (filename, data, mime)},
            headers=headers,
        )

    def test_upload_requires_auth_401(self, client):
        resp = client.put(
            "/api/v1/profile/avatar",
            files={"avatar": ("avatar.png", PNG_MAGIC + b"pad", "image/png")},
        )
        assert resp.status_code == 401

    def test_upload_png_and_fetch(self, client):
        headers = _auth_headers(_register(client))
        resp = self._put_avatar(client, headers, PNG_MAGIC + b"pngdata")
        assert resp.status_code == 200
        body = resp.json()
        assert body["avatar_key"] is not None

        fetched = client.get("/api/v1/profile/avatar", headers=headers)
        assert fetched.status_code == 200
        assert fetched.headers["content-type"].startswith("image/png")
        assert fetched.content == PNG_MAGIC + b"pngdata"

    def test_upload_jpeg(self, client):
        headers = _auth_headers(_register(client))
        resp = self._put_avatar(
            client, headers, JPEG_MAGIC + b"jpegdata", "avatar.jpg", "image/jpeg"
        )
        assert resp.status_code == 200
        fetched = client.get("/api/v1/profile/avatar", headers=headers)
        assert fetched.headers["content-type"].startswith("image/jpeg")

    def test_upload_webp(self, client):
        headers = _auth_headers(_register(client))
        resp = self._put_avatar(client, headers, WEBP_BODY, "avatar.webp", "image/webp")
        assert resp.status_code == 200
        fetched = client.get("/api/v1/profile/avatar", headers=headers)
        assert fetched.headers["content-type"].startswith("image/webp")

    def test_upload_replaces_old_file(self, client):
        headers = _auth_headers(_register(client))
        first = self._put_avatar(client, headers, PNG_MAGIC + b"one").json()
        second = self._put_avatar(
            client, headers, JPEG_MAGIC + b"two", "avatar.jpg", "image/jpeg"
        ).json()
        assert first["avatar_key"] != second["avatar_key"]
        stale = Path(settings.UPLOAD_DIR) / "avatars" / first["avatar_key"]
        assert not stale.exists()
        current = Path(settings.UPLOAD_DIR) / "avatars" / second["avatar_key"]
        assert current.is_file()

    def test_upload_invalid_signature_415(self, client):
        headers = _auth_headers(_register(client))
        resp = self._put_avatar(client, headers, b"GIF89a-not-allowed", "avatar.gif", "image/gif")
        assert resp.status_code == 415
        assert resp.json()["code"] == "UNSUPPORTED_AVATAR_FORMAT"

    def test_upload_empty_415(self, client):
        headers = _auth_headers(_register(client))
        resp = self._put_avatar(client, headers, b"")
        assert resp.status_code == 415

    def test_upload_too_large_413(self, client, monkeypatch):
        monkeypatch.setattr(settings, "AVATAR_MAX_SIZE_MB", 1)
        headers = _auth_headers(_register(client))
        big = PNG_MAGIC + b"0" * (1 * 1024 * 1024)
        resp = self._put_avatar(client, headers, big)
        assert resp.status_code == 413
        assert resp.json()["code"] == "AVATAR_TOO_LARGE"

    def test_delete_avatar(self, client):
        headers = _auth_headers(_register(client))
        self._put_avatar(client, headers, PNG_MAGIC + b"data")
        resp = client.delete("/api/v1/profile/avatar", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["avatar_key"] is None
        fetched = client.get("/api/v1/profile/avatar", headers=headers)
        assert fetched.status_code == 404
        assert fetched.json()["code"] == "AVATAR_NOT_FOUND"

    def test_get_avatar_without_avatar_404(self, client):
        headers = _auth_headers(_register(client))
        resp = client.get("/api/v1/profile/avatar", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["code"] == "AVATAR_NOT_FOUND"


class TestRoleAccess:
    def test_all_registered_roles_have_own_profile_scope(self, client):
        headers = _auth_headers(_register(client, email="u@example.com"))
        assert _get_profile(client, headers).status_code == 200

    def test_second_user_gets_separate_profile(self, client):
        first = _auth_headers(_register(client, email="one@example.com"))
        second = _auth_headers(_register(client, email="two@example.com"))
        one = _get_profile(client, first).json()
        two = _get_profile(client, second).json()
        assert one["user_id"] != two["user_id"]

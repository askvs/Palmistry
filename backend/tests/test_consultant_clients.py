# Consultant client roster: live seekers with goals and activity.
import uuid

import pytest

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


@pytest.fixture()
def consultant(client):
    email = f"clients-consultant-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Consultant One", role="spiritual_consultant")
    return _login(client, email)


@pytest.fixture()
def seeker(client):
    email = f"clients-seeker-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Seeker One")
    return email, _login(client, email)


def _set_profile(client, headers, *, interests, goals, age_group):
    resp = client.patch("/api/v1/profile", headers=headers, json={"age_group": age_group})
    assert resp.status_code == 200, resp.text

    # `PUT /profile/interests` replaces the whole list, so send it in one call.
    if interests:
        added = client.put("/api/v1/profile/interests", headers=headers, json={"interests": interests})
        assert added.status_code == 200, added.text

    for goal in goals:
        created = client.post("/api/v1/profile/goals", headers=headers, json={"text": goal})
        assert created.status_code == 201, created.text
    return resp.json()


class TestClientRoster:
    def test_empty_until_a_thread_exists(self, client, consultant):
        body = client.get("/api/v1/consultant/clients", headers=consultant).json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_thread_author_becomes_a_client(self, client, consultant, seeker):
        email, headers = seeker
        _set_profile(
            client,
            headers,
            interests=["Tarot", "Meditation"],
            goals=["Build daily calm", "Read one spread a week"],
            age_group="25-34",
        )
        client.post(
            "/api/v1/consultations",
            headers=headers,
            json={"topic": "Career direction", "message": "I feel stuck at work."},
        )

        items = client.get("/api/v1/consultant/clients", headers=consultant).json()["items"]
        assert len(items) == 1
        client_row = items[0]
        assert client_row["email"] == email
        assert client_row["full_name"] == "Seeker One"
        assert client_row["age_group"] == "25-34"
        assert client_row["interests"] == ["Meditation", "Tarot"]
        assert client_row["goals"] == ["Build daily calm", "Read one spread a week"]
        assert client_row["engagement"]["threads"] == 1
        assert client_row["engagement"]["resolved_threads"] == 0

    def test_reading_activity_is_reported(self, client, consultant, seeker):
        _email, headers = seeker
        _set_profile(client, headers, interests=[], goals=[], age_group="35-44")
        for cards in (["The Sun"], ["The Moon"]):
            client.post(
                "/api/v1/readings/tarot", headers=headers, json={"spread": "Single Card", "cards": cards}
            )
        client.post(
            "/api/v1/consultations",
            headers=headers,
            json={"topic": "Focus", "message": "Help me focus."},
        )

        items = client.get("/api/v1/consultant/clients", headers=consultant).json()["items"]
        engagement = items[0]["engagement"]
        assert engagement["readings"] == 2
        assert engagement["readings_last_30_days"] == 2
        assert engagement["last_reading_at"]

    def test_resolved_threads_are_counted(self, client, consultant, seeker):
        _email, headers = seeker
        _set_profile(client, headers, interests=[], goals=[], age_group="18-24")
        created = client.post(
            "/api/v1/consultations",
            headers=headers,
            json={"topic": "Confidence", "message": "I want to feel steadier."},
        ).json()
        client.post(
            f"/api/v1/consultant/consultations/{created['id']}/guidance",
            headers=consultant,
            json={"guidance": "Try one grounding practice each morning.", "status": "resolved"},
        )

        items = client.get("/api/v1/consultant/clients", headers=consultant).json()["items"]
        engagement = items[0]["engagement"]
        assert engagement["threads"] == 1
        assert engagement["resolved_threads"] == 1

    def test_seekers_cannot_list_clients(self, client, seeker):
        _email, headers = seeker
        assert client.get("/api/v1/consultant/clients", headers=headers).status_code == 403

    def test_unauthenticated_rejected(self, client):
        assert client.get("/api/v1/consultant/clients").status_code == 401

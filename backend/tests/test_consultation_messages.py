# Two-way consultation threads: seekers ask, responsible roles respond.
import uuid

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
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(test_engine, email, role):
    Session = sessionmaker(bind=test_engine)
    with Session() as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


def _create_consultation(client, headers, topic="Career path", message="I feel lost at work."):
    resp = client.post(
        "/api/v1/consultations",
        json={"topic": topic, "message": message},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_seeker_can_message_and_read_own_thread(client):
    email = f"seeker-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Seeker One")
    headers = _login(client, email)

    consultation = _create_consultation(client, headers)
    cid = consultation["id"]

    resp = client.post(
        f"/api/v1/consultations/{cid}/messages",
        json={"body": "Any extra context that would help?"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    message = resp.json()
    assert message["body"] == "Any extra context that would help?"
    assert message["is_staff"] is False

    thread = client.get(f"/api/v1/consultations/{cid}/messages", headers=headers)
    assert thread.status_code == 200, thread.text
    items = thread.json()["items"]
    assert [m["body"] for m in items] == [
        "Any extra context that would help?"
    ]


def test_consultant_reply_claims_thread_and_marks_in_review(client, test_engine):
    seeker = f"seeker-{uuid.uuid4().hex[:8]}@example.com"
    consultant = f"consultant-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, seeker, "Seeker Two")
    _register(client, consultant, "Consultant Two")
    _promote(test_engine, consultant, UserRole.spiritual_consultant)

    seeker_headers = _login(client, seeker)
    consultation = _create_consultation(client, seeker_headers)
    cid = consultation["id"]
    assert consultation["status"] == "open"

    consultant_headers = _login(client, consultant)
    resp = client.post(
        f"/api/v1/consultations/{cid}/messages",
        json={"body": "Breathe. The path reveals itself in service."},
        headers=consultant_headers,
    )
    assert resp.status_code == 201, resp.text
    reply = resp.json()
    assert reply["is_staff"] is True
    assert reply["sender_role"] == "spiritual_consultant"

    after = client.get("/api/v1/consultations", headers=seeker_headers).json()
    assert after["items"][0]["status"] == "in_review"
    assert after["items"][0]["consultant_id"] is not None

    thread = client.get(f"/api/v1/consultations/{cid}/messages", headers=seeker_headers)
    assert thread.status_code == 200
    assert thread.json()["items"][-1]["sender_name"] == "Consultant Two"


def test_seeker_followup_on_resolved_reopens_thread(client, test_engine):
    seeker = f"seeker-{uuid.uuid4().hex[:8]}@example.com"
    consultant = f"consultant-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, seeker, "Seeker Three")
    _register(client, consultant, "Consultant Three")
    _promote(test_engine, consultant, UserRole.spiritual_consultant)

    seeker_headers = _login(client, seeker)
    consultation = _create_consultation(client, seeker_headers)
    cid = consultation["id"]

    consultant_headers = _login(client, consultant)
    resp = client.post(
        f"/api/v1/consultant/consultations/{cid}/guidance",
        json={"guidance": "Meditate on the Hermit's lamp."},
        headers=consultant_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "resolved"

    seeker_headers = _login(client, seeker)
    resp = client.post(
        f"/api/v1/consultations/{cid}/messages",
        json={"body": "What does the lamp symbolise exactly?"},
        headers=seeker_headers,
    )
    assert resp.status_code == 201, resp.text

    after = client.get("/api/v1/consultations", headers=seeker_headers).json()
    assert after["items"][0]["status"] == "open"


def test_outsider_cannot_read_or_write_thread(client):
    owner = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    outsider = f"outsider-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, owner, "Owner")
    _register(client, outsider, "Outsider")

    consultation = _create_consultation(client, _login(client, owner))
    cid = consultation["id"]

    outsider_headers = _login(client, outsider)
    assert (
        client.get(
            f"/api/v1/consultations/{cid}/messages", headers=outsider_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/consultations/{cid}/messages",
            json={"body": "sneaky"},
            headers=outsider_headers,
        ).status_code
        == 404
    )


def test_messages_require_auth_and_existing_thread(client):
    resp = client.post(
        f"/api/v1/consultations/{uuid.uuid4()}/messages",
        json={"body": "hi"},
    )
    assert resp.status_code in (401, 403)

    email = f"seeker-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Seeker Four")
    headers = _login(client, email)
    assert (
        client.get(
            f"/api/v1/consultations/{uuid.uuid4()}/messages", headers=headers
        ).status_code
        == 404
    )

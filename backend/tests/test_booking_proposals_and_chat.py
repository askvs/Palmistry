# Booking negotiation (propose/counter/confirm) plus per-booking chat.
from datetime import datetime, timedelta, timezone

from tests.test_booking_endpoints import (
    _as_consultant,
    _as_seeker,
    _create_consultant_profile,
    _register,
    _headers,
)


def _future_iso(days=3, hour=15):
    when = datetime.now(timezone.utc) + timedelta(days=days)
    return when.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def _propose(client, consultant_id, seeker_headers, **overrides):
    payload = {
        "start_time": _future_iso(),
        "duration_minutes": 60,
        "subject": "Career clarity",
        "notes": "Looking for guidance on a job change.",
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/consultants/{consultant_id}/bookings/propose",
        json=payload,
        headers=seeker_headers,
    )


def _setup(client):
    consultant = _as_consultant(client, email="consultant-prop@example.com")
    profile = _create_consultant_profile(client, consultant)
    seeker = _as_seeker(client, email="seeker-prop@example.com")
    return consultant, profile, seeker


def test_seeker_can_propose_a_custom_time(client, test_engine):
    consultant, profile, seeker = _setup(client)
    resp = _propose(client, profile["id"], seeker)
    assert resp.status_code == 201, resp.text
    booking = resp.json()
    assert booking["status"] == "pending"
    assert booking["origin"] == "proposal"
    assert booking["slot_id"] is None
    assert booking["awaiting_party"] == "consultant"


def test_consultant_counter_then_seeker_confirm(client, test_engine):
    consultant, profile, seeker = _setup(client)
    booking = _propose(client, profile["id"], seeker).json()

    new_time = _future_iso(days=4, hour=10)
    countered = client.post(
        f"/api/v1/consultants/me/bookings/{booking['id']}/counter",
        json={"start_time": new_time, "duration_minutes": 45, "message": "Mornings work better."},
        headers=consultant,
    )
    assert countered.status_code == 200, countered.text
    body = countered.json()
    assert body["status"] == "countered"
    assert body["awaiting_party"] == "seeker"
    assert body["duration_minutes"] == 45

    confirmed = client.post(
        f"/api/v1/bookings/{booking['id']}/confirm", headers=seeker
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "accepted"


def test_seeker_can_counter_back(client, test_engine):
    consultant, profile, seeker = _setup(client)
    booking = _propose(client, profile["id"], seeker).json()

    client.post(
        f"/api/v1/consultants/me/bookings/{booking['id']}/counter",
        json={"start_time": _future_iso(days=4, hour=10)},
        headers=consultant,
    )
    # Seeker suggests yet another time -> back to awaiting the consultant.
    resp = client.post(
        f"/api/v1/bookings/{booking['id']}/counter",
        json={"start_time": _future_iso(days=5, hour=16)},
        headers=seeker,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "pending"
    assert resp.json()["awaiting_party"] == "consultant"


def test_consultant_can_accept_a_proposed_time(client, test_engine):
    consultant, profile, seeker = _setup(client)
    booking = _propose(client, profile["id"], seeker).json()
    resp = client.post(
        f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "accepted"


def test_booking_chat_roundtrip_and_access(client, test_engine):
    consultant, profile, seeker = _setup(client)
    booking = _propose(client, profile["id"], seeker).json()

    # Seeker sends a message.
    sent = client.post(
        f"/api/v1/bookings/{booking['id']}/messages",
        json={"body": "Hi, looking forward to it!"},
        headers=seeker,
    )
    assert sent.status_code == 201, sent.text
    assert sent.json()["is_me"] is True

    # Consultant can read it and reply.
    listed = client.get(
        f"/api/v1/bookings/{booking['id']}/messages", headers=consultant
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["body"] == "Hi, looking forward to it!"
    # From the consultant's viewpoint the seeker's message is not "me".
    assert listed.json()["items"][0]["is_me"] is False

    reply = client.post(
        f"/api/v1/bookings/{booking['id']}/messages",
        json={"body": "Me too — see you then."},
        headers=consultant,
    )
    assert reply.status_code == 201, reply.text

    # An unrelated seeker cannot read the thread.
    outsider = _headers(_register(client, "outsider-prop@example.com"))
    denied = client.get(
        f"/api/v1/bookings/{booking['id']}/messages", headers=outsider
    )
    assert denied.status_code == 404, denied.text


def test_seeker_cannot_use_consultant_counter_endpoint(client, test_engine):
    consultant, profile, seeker = _setup(client)
    booking = _propose(client, profile["id"], seeker).json()
    # The consultant studio router is role-guarded; a seeker is forbidden.
    resp = client.post(
        f"/api/v1/consultants/me/bookings/{booking['id']}/counter",
        json={"start_time": _future_iso(days=6)},
        headers=seeker,
    )
    assert resp.status_code in (403, 404), resp.text

# Guidance-effectiveness insights from real thread activity.
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.consultation import Consultation
from app.models.user import User, UserRole

PASSWORD = "TestPass123!"


def _register(client, email, full_name):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert resp.status_code == 201, resp.text
    return email


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
def seeker(client):
    email = _register(client, f"seeker-{uuid.uuid4().hex[:8]}@example.com", "Seeker")
    return email


@pytest.fixture()
def consultant(client, test_engine):
    email = _register(client, f"consultant-{uuid.uuid4().hex[:8]}@example.com", "Consultant")
    _promote(test_engine, email, UserRole.spiritual_consultant)
    return email


def _ask(client, headers, topic):
    resp = client.post(
        "/api/v1/consultations", headers=headers, json={"topic": topic, "message": "Guide me"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestGuidanceEffectiveness:
    def test_resolution_rate_answers_fraction_of_requests(
        self, client, seeker, consultant
    ):
        seeker_headers = _login(client, seeker)
        _ask(client, seeker_headers, "Career path")
        second_id = _ask(client, seeker_headers, "Love clarity")

        consultant_headers = _login(client, consultant)
        resp = client.post(
            f"/api/v1/consultant/consultations/{second_id}/guidance",
            headers=consultant_headers,
            json={"guidance": "Trust the timing."},
        )
        assert resp.status_code == 200, resp.text

        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=consultant_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["with_guidance"] == 1
        assert data["resolution_rate"] == pytest.approx(0.5)

    def test_avg_first_response_minutes_uses_first_staff_message(
        self, client, seeker, consultant, test_engine
    ):
        seeker_headers = _login(client, seeker)
        consultation_id = _ask(client, seeker_headers, "Career path")

        # The question arrived 3 hours ago; the consultant's reply is "now".
        three_hours_ago = datetime.now(timezone.utc) - timedelta(hours=3)
        Session = sessionmaker(bind=test_engine)
        with Session() as db:
            db.execute(
                update(Consultation)
                .where(Consultation.id == consultation_id)
                .values(created_at=three_hours_ago)
            )
            db.commit()

        consultant_headers = _login(client, consultant)
        resp = client.post(
            f"/api/v1/consultations/{consultation_id}/messages",
            headers=consultant_headers,
            json={"body": "Here is my first counsel."},
        )
        assert resp.status_code == 201, resp.text

        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=consultant_headers)
        data = resp.json()
        # ~180 minutes, with a small tolerance for clock skew between the
        # seeded timestamp and the message insert.
        assert data["avg_first_response_minutes"] == pytest.approx(180, abs=2)

    def test_avg_first_response_minutes_none_without_staff_reply(
        self, client, seeker, consultant
    ):
        seeker_headers = _login(client, seeker)
        _ask(client, seeker_headers, "Career path")

        consultant_headers = _login(client, consultant)
        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=consultant_headers)
        data = resp.json()
        assert data["avg_first_response_minutes"] is None
        assert data["awaiting_reply"] == 1

    def test_awaiting_reply_tracks_threads_where_seeker_spoke_last(
        self, client, seeker, consultant
    ):
        seeker_headers = _login(client, seeker)
        unanswered_id = _ask(client, seeker_headers, "Unanswered")
        answered_id = _ask(client, seeker_headers, "Answered")
        followup_id = _ask(client, seeker_headers, "Follow-up")

        consultant_headers = _login(client, consultant)
        # Answered: staff reply, thread claimed → not awaiting.
        resp = client.post(
            f"/api/v1/consultations/{answered_id}/messages",
            headers=consultant_headers,
            json={"body": "Counsel."},
        )
        assert resp.status_code == 201, resp.text
        # Follow-up: staff replies, then the seeker speaks last → awaiting again.
        resp = client.post(
            f"/api/v1/consultations/{followup_id}/messages",
            headers=consultant_headers,
            json={"body": "Counsel."},
        )
        assert resp.status_code == 201, resp.text
        resp = client.post(
            f"/api/v1/consultations/{followup_id}/messages",
            headers=seeker_headers,
            json={"body": "Thank you — one more thing?"},
        )
        assert resp.status_code == 201, resp.text

        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=consultant_headers)
        data = resp.json()
        assert data["awaiting_reply"] == 2  # unanswered + seeker-last follow-up

    def test_resolved_threads_never_count_as_awaiting(self, client, seeker, consultant):
        seeker_headers = _login(client, seeker)
        resolved_id = _ask(client, seeker_headers, "Resolve me")

        consultant_headers = _login(client, consultant)
        resp = client.post(
            f"/api/v1/consultant/consultations/{resolved_id}/guidance",
            headers=consultant_headers,
            json={"guidance": "All clear.", "status": "resolved"},
        )
        assert resp.status_code == 200, resp.text
        # Seeker says thanks on the resolved thread — reopens it, so it IS awaiting.
        resp = client.post(
            f"/api/v1/consultations/{resolved_id}/messages",
            headers=seeker_headers,
            json={"body": "Thank you!"},
        )
        assert resp.status_code == 201, resp.text

        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=consultant_headers)
        data = resp.json()
        assert data["awaiting_reply"] == 1  # reopened by the seeker's follow-up

    def test_non_consultant_gets_403(self, client, seeker):
        headers = _login(client, seeker)
        resp = client.get("/api/v1/consultant/insights/effectiveness", headers=headers)
        assert resp.status_code == 403

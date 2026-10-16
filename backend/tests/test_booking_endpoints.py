# Booking lifecycle: profile, availability, booking, meeting link, dashboards, notifications.

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.db.session import get_db
from app.middleware.rate_limit import _buckets


def _session():
    """A session bound to the test engine the `client` fixture configured."""
    return next(get_db())


# Helpers


def _clear_rate_limit():
    _buckets.clear()


def _register(client, email, role="user", password="passw0rd-long", name=None):
    _clear_rate_limit()
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": name or email.split("@")[0].title(),
            "role": role,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp


def _headers(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _registered(client, email="viewer@example.com"):
    """Headers for a fresh signed-in account (used only to browse)."""
    return _headers(_register(client, email))


def _as_consultant(client, email="reader@example.com", role="tarot_reader", name="Reader One"):
    resp = _register(client, email, role=role, name=name)
    return _headers(resp)


def _as_seeker(client, email="seeker@example.com"):
    resp = _register(client, email, role="user", name="Seeker One")
    return _headers(resp)


def _create_consultant_profile(client, headers, **overrides):
    payload = {
        "headline": "Tarot & palm guidance",
        "bio": "Ten years of practice.",
        "specializations": ["tarot", "love"],
        "modalities": ["tarot"],
        "languages": ["English"],
        "years_experience": 10,
        "session_rate": "45.00",
        "currency": "USD",
        "session_duration_minutes": 60,
        "buffer_minutes": 15,
        "timezone": "UTC",
        "is_accepting_bookings": True,
    }
    payload.update(overrides)
    resp = client.put("/api/v1/consultants/me/profile", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _add_rule(client, headers, *, weekday=None, start="09:00:00", end="11:00:00", duration=60):
    if weekday is None:
        weekday = (date.today() + timedelta(days=7)).weekday()
    resp = client.post(
        "/api/v1/consultants/me/availability/rules",
        json={
            "weekday": weekday,
            "start_time": start,
            "end_time": end,
            "slot_duration_minutes": duration,
            "buffer_minutes": 0,
            "timezone": "UTC",
            "effective_from": date.today().isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _future_slot(client, consultant_id, headers, *, days=7):
    """The first open slot at least `days` from now."""
    target = date.today() + timedelta(days=days)
    resp = client.get(
        f"/api/v1/consultants/{consultant_id}/slots",
        params={"date": target.isoformat()},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    slots = resp.json()["slots"]
    assert slots, f"no slots for {target}: {resp.json()}"
    return slots[0]


# Phase 1 — consultant profiles + availability


class TestConsultantProfile:
    def test_profile_requires_authentication(self, client):
        assert client.get("/api/v1/consultants").status_code == 401

    def test_seeker_cannot_create_consultant_profile(self, client):
        headers = _as_seeker(client)
        resp = client.put(
            "/api/v1/consultants/me/profile",
            json={"headline": "I am not an consultant"},
            headers=headers,
        )
        # The router-level role guard answers first; the service layer's own
        # NOT_AN_CONSULTANT guard is exercised by GET /consultants/me/profile.
        assert resp.status_code == 403
        assert resp.json()["code"] in ("HTTP_403", "NOT_AN_CONSULTANT")

    def test_consultant_creates_profile(self, client):
        headers = _as_consultant(client)
        body = _create_consultant_profile(client, headers)
        assert body["headline"] == "Tarot & palm guidance"
        assert body["specializations"] == ["tarot", "love"]
        assert body["full_name"] == "Reader One"
        assert body["is_accepting_bookings"] is True

    def test_profile_is_idempotent_upsert(self, client):
        headers = _as_consultant(client)
        first = _create_consultant_profile(client, headers)
        second = _create_consultant_profile(client, headers, headline="Renamed")
        assert first["id"] == second["id"]
        assert second["headline"] == "Renamed"

    def test_profile_headline_required_to_create(self, client):
        headers = _as_consultant(client)
        resp = client.put(
            "/api/v1/consultants/me/profile", json={"bio": "no headline"}, headers=headers
        )
        assert resp.status_code == 422

    def test_consultant_listing_excludes_seekers(self, client):
        # A seeker and an consultant with no profile yet must not appear.
        _as_seeker(client, email="looker@example.com")
        _as_consultant(client, email="noprofile@example.com")
        _create_consultant_profile(client, _as_consultant(client, email="listed@example.com"))
        resp = client.get("/api/v1/consultants", headers=_registered(client))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["full_name"] == "Reader One"

    def test_non_accepting_consultants_hidden_by_default(self, client):
        headers = _as_consultant(client, email="busy@example.com")
        _create_consultant_profile(client, headers, is_accepting_bookings=False)
        seeker = _as_seeker(client, email="look@example.com")
        assert client.get("/api/v1/consultants", headers=seeker).json()["total"] == 0

    def test_consultant_search_and_price_filter(self, client):
        h1 = _as_consultant(client, email="a@example.com", name="Ada")
        h2 = _as_consultant(client, email="b@example.com", name="Boris")
        _create_consultant_profile(
            client,
            h1,
            headline="Tarot specialist",
            specializations=["tarot", "love"],
            session_rate="30.00",
        )
        _create_consultant_profile(
            client,
            h2,
            headline="Palm master",
            specializations=["palmistry"],
            session_rate="90.00",
        )
        seeker = _as_seeker(client, email="c@example.com")

        # Name + headline search.
        by_name = client.get(
            "/api/v1/consultants", params={"search": "tarot spec"}, headers=seeker
        ).json()
        assert by_name["total"] == 1
        assert by_name["items"][0]["session_rate"] == "30.00"

        # Search also matches the account name, not just the headline.
        by_name = client.get(
            "/api/v1/consultants", params={"search": "Ada"}, headers=seeker
        ).json()
        assert by_name["total"] == 1
        assert by_name["items"][0]["headline"] == "Tarot specialist"

        # Price ceiling.
        by_price = client.get(
            "/api/v1/consultants", params={"max_rate": 50}, headers=seeker
        ).json()
        assert by_price["total"] == 1
        assert by_price["items"][0]["headline"] == "Tarot specialist"

        # Specialisation (JSON containment).
        by_specialization = client.get(
            "/api/v1/consultants", params={"specialization": "love"}, headers=seeker
        ).json()
        assert by_specialization["total"] == 1
        assert by_specialization["items"][0]["headline"] == "Tarot specialist"

        by_specialization = client.get(
            "/api/v1/consultants", params={"specialization": "palmistry"}, headers=seeker
        ).json()
        assert by_specialization["total"] == 1
        assert by_specialization["items"][0]["headline"] == "Palm master"


class TestAvailability:
    def test_create_rule_materialises_slots(self, client):
        headers = _as_consultant(client)
        _create_consultant_profile(client, headers)
        weekday = (date.today() + timedelta(days=7)).weekday()
        body = _add_rule(client, headers, weekday=weekday, start="09:00:00", end="10:00:00")
        assert body["rule"]["weekday"] == weekday
        assert body["rule"]["weekday_name"]
        # The window falls inside the horizon, so at least one slot exists.
        assert body["slots_created"] >= 1

    def test_rule_rejects_inverted_window(self, client):
        headers = _as_consultant(client)
        _create_consultant_profile(client, headers)
        resp = client.post(
            "/api/v1/consultants/me/availability/rules",
            json={
                "weekday": 1,
                "start_time": "12:00:00",
                "end_time": "09:00:00",
                "effective_from": date.today().isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "AVAILABILITY_WINDOW_INVALID"

    def test_overlapping_rule_rejected(self, client):
        headers = _as_consultant(client)
        _create_consultant_profile(client, headers)
        weekday = (date.today() + timedelta(days=6)).weekday()
        _add_rule(client, headers, weekday=weekday, start="09:00:00", end="11:00:00")
        resp = client.post(
            "/api/v1/consultants/me/availability/rules",
            json={
                "weekday": weekday,
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "effective_from": date.today().isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "AVAILABILITY_RULE_OVERLAP"

    def test_rule_deletion_releases_free_slots(self, client):
        headers = _as_consultant(client)
        _create_consultant_profile(client, headers)
        rule = _add_rule(client, headers)
        profile_id = client.get("/api/v1/consultants/me/profile", headers=headers).json()["id"]

        before = client.get(
            "/api/v1/consultants/me/availability/slots", headers=headers
        ).json()["total"]
        assert before >= 1

        resp = client.delete(
            f"/api/v1/consultants/me/availability/rules/{rule['rule']['id']}", headers=headers
        )
        assert resp.status_code == 204
        after = client.get(
            "/api/v1/consultants/me/availability/slots", headers=headers
        ).json()["total"]
        assert after == 0

    def test_block_and_unblock_slot(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        slots = client.get(
            "/api/v1/consultants/me/availability/slots",
            params={"status": "available"},
            headers=consultant,
        ).json()["items"]
        assert slots
        slot_id = slots[0]["id"]

        blocked = client.post(
            f"/api/v1/consultants/me/availability/slots/{slot_id}/block", headers=consultant
        )
        assert blocked.status_code == 200
        assert blocked.json()["status"] == "blocked"

        unblocked = client.post(
            f"/api/v1/consultants/me/availability/slots/{slot_id}/unblock", headers=consultant
        )
        assert unblocked.status_code == 200
        assert unblocked.json()["status"] == "available"

    def test_booked_slot_cannot_be_blocked_or_deleted(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)

        booked = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Career clarity"},
            headers=seeker,
        )
        assert booked.status_code == 201

        assert (
            client.post(
                f"/api/v1/consultants/me/availability/slots/{slot['id']}/block",
                headers=consultant,
            ).status_code
            == 409
        )
        assert (
            client.delete(
                f"/api/v1/consultants/me/availability/slots/{slot['id']}", headers=consultant
            ).status_code
            == 409
        )

    def test_availability_calendar_and_day_slots(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        seeker = _as_seeker(client)

        target = date.today() + timedelta(days=7)
        cal = client.get(
            f"/api/v1/consultants/{consultant_id}/availability",
            params={"from": target.isoformat(), "to": target.isoformat()},
            headers=seeker,
        ).json()
        day = [d for d in cal["days"] if d["date"] == target.isoformat()][0]
        assert day["available_slots"] >= 1

        slots = client.get(
            f"/api/v1/consultants/{consultant_id}/slots",
            params={"date": target.isoformat()},
            headers=seeker,
        ).json()
        assert len(slots["slots"]) == day["available_slots"]

    def test_generate_slots_endpoint_is_idempotent(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant, start="20:00:00", end="22:00:00", duration=60)

        # Publishing the window already materialised the slots.
        slots = client.get(
            "/api/v1/consultants/me/availability/slots",
            params={"status": "available"},
            headers=consultant,
        ).json()
        assert slots["total"] >= 2

        # Asking again publishes nothing new.
        start = date.today()
        end = start + timedelta(days=14)
        resp = client.post(
            "/api/v1/consultants/me/availability/generate",
            json={"from_date": start.isoformat(), "to_date": end.isoformat()},
            headers=consultant,
        )
        assert resp.status_code == 200
        assert resp.json()["slots_created"] == 0

        # A blocked slot is not counted as open.
        client.post(
            f"/api/v1/consultants/me/availability/slots/{slots['items'][0]['id']}/block",
            headers=consultant,
        )
        open_slots = client.get(
            "/api/v1/consultants/me/availability/slots",
            params={"status": "available"},
            headers=consultant,
        ).json()
        assert open_slots["total"] == slots["total"] - 1


# Phase 2 — booking system + database


class TestBookingLifecycle:
    def test_seeker_books_slot_and_gets_pending(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)

        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Relationship clarity"},
            headers=seeker,
        )
        assert booking.status_code == 201, booking.text
        body = booking.json()
        assert body["status"] == "pending"
        assert body["meet_link"] is None
        assert body["consultant_name"] == "Reader One"
        assert body["seeker_name"] == "Seeker One"
        # Price is snapshotted from the consultant profile at booking time.
        assert body["price"] == "45.00"

    def test_slot_cannot_be_double_booked(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker_a = _as_seeker(client, email="a@example.com")
        seeker_b = _as_seeker(client, email="b@example.com")
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, seeker_a)

        first = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "First"},
            headers=seeker_a,
        )
        assert first.status_code == 201

        second = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Second"},
            headers=seeker_b,
        )
        assert second.status_code == 409
        assert second.json()["code"] == "SLOT_NOT_BOOKABLE"

    def test_consultant_cannot_book_own_session(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, consultant)
        resp = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Self"},
            headers=consultant,
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == "BOOKING_NOT_ALLOWED"

    def test_booking_in_the_past_window_rejected(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        # A rule that starts almost immediately still respects the lead time.
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slots = client.get(
            "/api/v1/consultants/me/availability/slots", headers=consultant
        ).json()["items"]
        soon = [s for s in slots if (datetime.fromisoformat(s["start_time"]) - datetime.now(timezone.utc)).total_seconds() < 5400]
        if not soon:
            pytest.skip("no slot within the minimum lead window in this run")
        resp = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": soon[0]["id"], "subject": "Too soon"},
            headers=seeker,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "BOOKING_TOO_SOON"

    def test_booking_blocks_far_future_slots(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        far = date.today() + timedelta(days=400)
        slots = client.get(
            f"/api/v1/consultants/{consultant_id}/slots", params={"date": far.isoformat()}, headers=seeker
        ).json()["slots"]
        if not slots:
            pytest.skip("the configured horizon does not reach that date")
        resp = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slots[0]["id"], "subject": "Way out"},
            headers=seeker,
        )
        assert resp.status_code == 409

    def test_seeker_cannot_access_someone_elses_booking(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker_a = _as_seeker(client, email="a@example.com")
        seeker_b = _as_seeker(client, email="b@example.com")
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, seeker_a)
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Private"},
            headers=seeker_a,
        ).json()
        resp = client.get(f"/api/v1/bookings/{booking['id']}", headers=seeker_b)
        assert resp.status_code == 404

    def test_my_bookings_scope_filters(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get("/api/v1/consultants/me/profile", headers=consultant).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Upcoming"},
            headers=seeker,
        )
        assert client.get("/api/v1/bookings?scope=upcoming", headers=seeker).json()["total"] == 1
        assert client.get("/api/v1/bookings?scope=past", headers=seeker).json()["total"] == 0


class TestBookingStatusFlow:
    def _book(self, client):
        consultant = _as_consultant(client)
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Life direction"},
            headers=seeker,
        ).json()
        return consultant, seeker, booking

    def test_pending_to_accepted(self, client):
        consultant, seeker, booking = self._book(client)
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["accepted_at"] is not None

    def test_pending_to_rejected_frees_slot(self, client):
        consultant, seeker, booking = self._book(client)
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/reject",
            json={"reason": "conflict"},
            headers=consultant,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
        assert resp.json()["cancellation_reason"] == "conflict"

        # Slot is bookable again.
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker, days=7)
        again = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Retry"},
            headers=seeker,
        )
        assert again.status_code == 201

    def test_seeker_cannot_accept_or_reject(self, client):
        consultant, seeker, booking = self._book(client)
        assert (
            client.post(
                f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=seeker
            ).status_code
            == 403
        )

    def test_accepted_can_complete(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/complete?force=true",
            headers=consultant,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_complete_requires_started_session(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/complete", headers=consultant
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "INVALID_BOOKING_TRANSITION"

    def test_invalid_transition_rejected(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/reject", headers=consultant)
        # A rejected booking is terminal.
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "INVALID_BOOKING_TRANSITION"

    def test_booking_event_history_recorded(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        detail = client.get(f"/api/v1/bookings/{booking['id']}", headers=seeker).json()
        types = [e["event_type"] for e in detail["events"]]
        assert types == ["booking_created", "booking_accepted"]
        assert detail["events"][0]["to_status"] == "pending"
        assert detail["events"][1]["from_status"] == "pending"
        assert detail["events"][1]["to_status"] == "accepted"

    def test_booking_unknown_id_404(self, client):
        seeker = _as_seeker(client)
        resp = client.get(f"/api/v1/bookings/{uuid.uuid4()}", headers=seeker)
        assert resp.status_code == 404
        assert resp.json()["code"] == "BOOKING_NOT_FOUND"


# Phase 3 — Meeting link


class TestMeetingLink:
    def _book(self, client, *, meeting_link=None):
        consultant = _as_consultant(client, email="meet@example.com")
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        payload = {"slot_id": slot["id"], "subject": "Meet link test"}
        if meeting_link is not None:
            payload["meeting_link"] = meeting_link
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json=payload,
            headers=seeker,
        ).json()
        return consultant, seeker, booking

    def test_consultant_sets_meeting_link(self, client):
        consultant, _seeker, booking = self._book(client)
        resp = client.patch(
            f"/api/v1/consultants/me/bookings/{booking['id']}/meeting-link",
            json={"meeting_link": "https://meet.google.com/abc-defg-hij"},
            headers=consultant,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meet_link"] == "https://meet.google.com/abc-defg-hij"

    def test_meeting_link_must_be_http_url(self, client):
        consultant, _seeker, booking = self._book(client)
        resp = client.patch(
            f"/api/v1/consultants/me/bookings/{booking['id']}/meeting-link",
            json={"meeting_link": "meet.google.com/abc-defg-hij"},
            headers=consultant,
        )
        assert resp.status_code == 422

    def test_meeting_link_can_be_cleared(self, client):
        consultant, _seeker, booking = self._book(
            client, meeting_link="https://meet.google.com/abc-defg-hij"
        )
        resp = client.patch(
            f"/api/v1/consultants/me/bookings/{booking['id']}/meeting-link",
            json={"meeting_link": None},
            headers=consultant,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meet_link"] is None

    def test_accept_keeps_provided_meeting_link(self, client):
        consultant, _seeker, booking = self._book(
            client, meeting_link="https://meet.google.com/seek-erli-nk1"
        )
        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/accept",
            headers=consultant,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meet_link"] == "https://meet.google.com/seek-erli-nk1"
        assert resp.json()["can_join_meet"] is False

    def test_meeting_link_rejected_on_closed_booking(self, client):
        consultant, _seeker, booking = self._book(client)
        rejected = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/reject",
            headers=consultant,
        )
        assert rejected.status_code == 200, rejected.text
        resp = client.patch(
            f"/api/v1/consultants/me/bookings/{booking['id']}/meeting-link",
            json={"meeting_link": "https://meet.google.com/abc-defg-hij"},
            headers=consultant,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "INVALID_BOOKING_TRANSITION"


# Phase 5 — notifications + reminders + cancellation


class TestNotificationsAndCancellation:
    def _book(self, client):
        consultant = _as_consultant(client, email="notify@example.com")
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Guidance"},
            headers=seeker,
        ).json()
        return consultant, seeker, booking

    def test_consultant_gets_request_notification(self, client):
        consultant, seeker, booking = self._book(client)
        notifs = client.get("/api/v1/notifications", headers=consultant).json()
        assert any(n["type"] == "booking_requested" for n in notifs)

    def test_seeker_gets_acceptance_notification(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        notifs = client.get("/api/v1/notifications", headers=seeker).json()
        assert any(n["type"] == "booking_accepted" for n in notifs)

    def test_reminder_dispatch_is_idempotent(self, client):
        from app.services.booking.scheduler import run_session_reminders

        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        booking_id = booking["id"]

        # Move the session into the reminder window.
        from app.models.booking import Booking

        db = _session()
        target = datetime.now(timezone.utc) + timedelta(minutes=10)
        row = db.get(Booking, uuid.UUID(booking_id))
        assert row is not None
        row.start_time = target
        row.end_time = target + timedelta(hours=1)
        db.commit()

        first = run_session_reminders(db)
        assert first >= 1
        db.refresh(row)
        assert row.short_reminder_sent_at is not None

        second = run_session_reminders(db)
        assert second == 0
        db.close()

    def test_seeker_can_cancel_within_window(self, client):
        consultant, seeker, booking = self._book(client)
        resp = client.post(
            f"/api/v1/bookings/{booking['id']}/cancel",
            json={"reason": "Plans changed"},
            headers=seeker,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        assert resp.json()["cancellation_reason"] == "Plans changed"

    def test_cancel_outside_window_blocked(self, client, monkeypatch):
        from app.config import settings
        from app.models.booking import Booking

        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)

        db = _session()
        row = db.get(Booking, uuid.UUID(booking["id"]))
        now = datetime.now(timezone.utc)
        row.start_time = now + timedelta(hours=2)
        row.end_time = now + timedelta(hours=3)
        db.commit()
        db.close()

        resp = client.post(
            f"/api/v1/bookings/{booking['id']}/cancel", headers=seeker
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "BOOKING_CANCELLATION_CLOSED"

    def test_consultant_can_cancel_anytime(self, client):
        from app.models.booking import Booking

        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant)
        db = _session()
        row = db.get(Booking, uuid.UUID(booking["id"]))
        now = datetime.now(timezone.utc)
        row.start_time = now + timedelta(hours=2)
        row.end_time = now + timedelta(hours=3)
        db.commit()
        db.close()

        resp = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/cancel",
            json={"reason": "Emergency"},
            headers=consultant,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

        # The seeker-side route refuses the same booking outside their window
        # (by then it is already cancelled, which is also a terminal state).
        blocked = client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=seeker)
        assert blocked.status_code in (404, 409)

    def test_cancel_notifies_other_party(self, client):
        consultant, seeker, booking = self._book(client)
        client.post(f"/api/v1/bookings/{booking['id']}/cancel", headers=seeker)
        notifs = client.get("/api/v1/notifications", headers=consultant).json()
        assert any(n["type"] == "booking_cancelled" for n in notifs)


# Phase 6 — session history, notes and feedback


class TestNotesAndFeedback:
    def _completed(self, client):
        consultant = _as_consultant(client, email="notes@example.com")
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Deep dive"},
            headers=seeker,
        ).json()
        client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/accept", headers=consultant
        )
        client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/complete?force=true",
            headers=consultant,
        )
        return consultant, seeker, booking

    def test_consultant_adds_shared_note_visible_to_seeker(self, client):
        consultant, seeker, booking = self._completed(client)
        note = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/notes",
            json={"body": "Strong intuition around career.", "visibility": "shared"},
            headers=consultant,
        )
        assert note.status_code == 201
        body = note.json()
        assert body["visibility"] == "shared"
        assert body["author_name"] == "Reader One"

        detail = client.get(f"/api/v1/bookings/{booking['id']}", headers=seeker).json()
        assert [n["body"] for n in detail["session_notes"]] == [
            "Strong intuition around career."
        ]

    def test_private_note_hidden_from_seeker(self, client):
        consultant, seeker, booking = self._completed(client)
        client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/notes",
            json={"body": "Private observation", "visibility": "private"},
            headers=consultant,
        )
        for headers in (seeker, consultant):
            detail = client.get(
                f"/api/v1/bookings/{booking['id']}"
                if headers is seeker
                else f"/api/v1/consultants/me/bookings/{booking['id']}",
                headers=headers,
            ).json()
            if headers is consultant:
                assert [n["body"] for n in detail["session_notes"]] == [
                    "Private observation"
                ]
            else:
                assert detail["session_notes"] == []

    def test_update_and_delete_note(self, client):
        consultant, seeker, booking = self._completed(client)
        note = client.post(
            f"/api/v1/consultants/me/bookings/{booking['id']}/notes",
            json={"body": "Draft"},
            headers=consultant,
        ).json()
        updated = client.patch(
            f"/api/v1/consultants/me/notes/{note['id']}",
            json={"body": "Polished", "visibility": "shared"},
            headers=consultant,
        )
        assert updated.status_code == 200
        assert updated.json()["body"] == "Polished"
        assert updated.json()["visibility"] == "shared"

        assert (
            client.delete(
                f"/api/v1/consultants/me/notes/{note['id']}", headers=consultant
            ).status_code
            == 204
        )

    def test_seeker_leaves_feedback_after_completion(self, client):
        consultant, seeker, booking = self._completed(client)
        resp = client.post(
            f"/api/v1/bookings/{booking['id']}/feedback",
            json={"rating": 5, "review": "Wonderful session"},
            headers=seeker,
        )
        assert resp.status_code == 201
        assert resp.json()["rating"] == 5

        profile = client.get(
            f"/api/v1/consultants/{booking['consultant_id']}", headers=seeker
        ).json()
        assert float(profile["avg_rating"]) == 5.0
        assert profile["review_count"] == 1

    def test_feedback_requires_completed_booking(self, client):
        consultant = _as_consultant(client, email="nofb@example.com")
        _create_consultant_profile(client, consultant)
        _add_rule(client, consultant)
        seeker = _as_seeker(client)
        consultant_id = client.get(
            "/api/v1/consultants/me/profile", headers=consultant
        ).json()["id"]
        slot = _future_slot(client, consultant_id, seeker)
        booking = client.post(
            f"/api/v1/consultants/{consultant_id}/bookings",
            json={"slot_id": slot["id"], "subject": "Pending"},
            headers=seeker,
        ).json()
        resp = client.post(
            f"/api/v1/bookings/{booking['id']}/feedback",
            json={"rating": 4},
            headers=seeker,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "FEEDBACK_NOT_ALLOWED"

    def test_feedback_is_unique_per_booking(self, client):
        consultant, seeker, booking = self._completed(client)
        client.post(
            f"/api/v1/bookings/{booking['id']}/feedback", json={"rating": 4}, headers=seeker
        )
        resp = client.post(
            f"/api/v1/bookings/{booking['id']}/feedback", json={"rating": 5}, headers=seeker
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "FEEDBACK_EXISTS"

    def test_public_reviews_listed(self, client):
        consultant, seeker, booking = self._completed(client)
        client.post(
            f"/api/v1/bookings/{booking['id']}/feedback",
            json={"rating": 4, "review": "Great"},
            headers=seeker,
        )
        reviews = client.get(
            f"/api/v1/consultants/{booking['consultant_id']}/reviews", headers=seeker
        ).json()
        assert reviews["total"] == 1
        assert reviews["items"][0]["review"] == "Great"
        assert reviews["items"][0]["author_name"] == "Seeker One"

    def test_consultant_stats_and_dashboard_scopes(self, client):
        consultant, seeker, booking = self._completed(client)
        stats = client.get("/api/v1/consultants/me/stats", headers=consultant).json()
        assert stats["completed_sessions"] == 1
        assert stats["upcoming_sessions"] == 0
        assert stats["review_count"] == 0

        consultant_bookings = client.get(
            "/api/v1/consultants/me/bookings?scope=past", headers=consultant
        ).json()
        assert consultant_bookings["total"] == 1

        seeker_bookings = client.get(
            "/api/v1/bookings?scope=past", headers=seeker
        ).json()
        assert seeker_bookings["total"] == 1

    def test_autocomplete_job_marks_past_sessions(self, client):
        from app.models.booking import Booking
        from app.services.booking.scheduler import run_booking_autocomplete

        consultant, seeker, booking = self._completed(client)
        db = _session()
        row = db.get(Booking, uuid.UUID(booking["id"]))
        row.status = "accepted"
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        row.start_time = past
        row.end_time = past + timedelta(hours=1)
        db.commit()
        assert run_booking_autocomplete(db) == 1
        db.refresh(row)
        assert row.status.value == "completed"
        db.close()

# Smoke-check role endpoints against a live backend (stdlib only).
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("API_BASE", "http://localhost:8000/api/v1")
PASSWORD = "TestPass123!"
RUN = str(int(time.time()))[-6:]

RESULTS = []


def check(label, ok, detail=""):
    RESULTS.append((label, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f" - {detail}" if detail else ""))


def _request(method, path, payload=None, headers=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            return exc.code, json.loads(body or b"null")
        except json.JSONDecodeError:
            return exc.code, {}


def token_for(email, role=None):
    # Register, sign in, and optionally promote to a staff role.
    _request(
        "POST",
        "/auth/register",
        {"email": email, "password": PASSWORD, "full_name": email.split("@")[0].title()},
    )
    if role:
        from sqlalchemy import create_engine, text

        from app.config import settings

        engine = create_engine(settings.DATABASE_URL)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE users SET role = :role WHERE email = :email"),
                    {"role": role, "email": email},
                )
        finally:
            engine.dispose()
    _status, body = _request("POST", "/auth/login", {"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {body['access_token']}"}


def main():
    seeker = token_for(f"smoke-seeker-{RUN}@example.com")
    reader = token_for(f"smoke-reader-{RUN}@example.com", role="tarot_reader")
    admin = token_for(f"smoke-admin-{RUN}@example.com", role="admin")

    # --- Administrator: no session access ----------------------------------
    for path in ("/consultants/me/profile", "/consultants/me/bookings", "/bookings"):
        status, _ = _request("GET", path, headers=admin)
        check(f"admin blocked from {path}", status == 403, f"status {status}")

    status, body = _request("GET", "/admin/users", headers=admin)
    check("admin lists user accounts", status == 200, f"status {status}")

    # Promote the *seeker* (never the admin itself — `items[0]` is the newest
    # account, which is the admin we are signed in as).
    _status, seeker_me = _request("GET", "/auth/me", headers=seeker)
    status, updated = _request(
        "PATCH", f"/admin/users/{seeker_me['id']}", {"role": "tarot_reader"}, admin
    )
    check(
        "admin assigns a role",
        status == 200 and updated.get("role") == "tarot_reader",
        f"status {status} role={updated.get('role')}",
    )
    # Put the seeker back so the journey checks below still read as a seeker.
    _request("PATCH", f"/admin/users/{seeker_me['id']}", {"role": "user"}, admin)
    seeker = token_for(f"smoke-seeker-{RUN}@example.com")

    status, body = _request("GET", "/admin/analytics/sessions", headers=admin)
    check(
        "admin sees read-only session oversight",
        status == 200 and "upcoming_sessions" in body,
        f"status {status} total={body.get('total')}",
    )

    for path, keys in (
        ("/admin/permissions", ["roles", "rules"]),
        ("/admin/settings/auth", ["jwt_algorithm", "password_hashing"]),
        ("/admin/settings/system", ["environment", "version", "migration_revision"]),
        ("/admin/errors", ["items", "total", "unresolved"]),
        ("/admin/errors/stats", ["total", "unresolved"]),
        ("/admin/system/performance", ["latency_ms", "slowest_routes"]),
        ("/admin/analytics/platform", ["users_total", "engagement"]),
        ("/admin/analytics/readings", ["total", "by_type"]),
    ):
        status, body = _request("GET", path, headers=admin)
        check(f"admin reads {path}", status == 200 and all(k in body for k in keys), f"status {status}")

    _request("POST", "/auth/login", {"email": "nobody@example.com", "password": "nope"})
    status, body = _request("GET", "/admin/errors", headers=admin)
    check("rejected sign-in is recorded", any(i["kind"] == "auth_failure" for i in body["items"]))

    pending = [i for i in body["items"] if not i["acknowledged_at"]]
    if pending:
        status, _ = _request("POST", f"/admin/errors/{pending[0]['id']}/acknowledge", headers=admin)
        check("admin triages an error entry", status == 204, f"status {status}")

    status, _ = _request("POST", "/admin/reports/system", headers=admin)
    check("admin generates a system report", status == 201, f"status {status}")

    # --- Tarot Reader: spreads, reports, engagement -------------------------
    status, spread = _request(
        "POST",
        "/reader/spreads",
        {
            "name": "Smoke Layout",
            "positions": [
                {"name": "Now", "description": "The present."},
                {"name": "Next", "description": "What follows."},
            ],
        },
        reader,
    )
    check("reader authors a spread", status == 201, f"status {status}")

    status, body = _request("GET", "/reader/spreads", headers=reader)
    check(
        "reader sees 6 standard + own spreads",
        status == 200 and len(body["standard"]) == 6,
        f"status {status}",
    )

    status, drawn = _request(
        "POST",
        "/tarot/draw",
        {"spread_id": spread["id"], "question": "What now?", "seed": 11},
        reader,
    )
    check(
        "a reading runs on the custom spread",
        status == 200 and drawn.get("spread_name") == "Smoke Layout",
        f"status {status}",
    )

    _request("POST", "/readings/tarot", {"spread": "Single Card", "cards": ["The Sun"]}, seeker)
    status, body = _request("GET", "/reader/reports", headers=reader)
    check(
        "reader report management lists readings",
        status == 200 and body["total"] >= 1,
        f"status {status} total={body.get('total')}",
    )

    status, body = _request("GET", "/reader/engagement", headers=reader)
    check(
        "reader engagement insights",
        status == 200 and "unique_querents" in body,
        f"status {status}",
    )

    status, _ = _request("GET", "/admin/users", headers=reader)
    check("reader cannot reach admin", status == 403, f"status {status}")

    # --- Spiritual Consultant: live client roster ---------------------------
    _request("PATCH", "/profile", {"age_group": "25-34"}, seeker)
    _request("PUT", "/profile/interests", {"interests": ["tarot", "calm"]}, seeker)
    _request("POST", "/profile/goals", {"text": "Feel steadier"}, seeker)
    _request(
        "POST",
        "/consultations",
        {"topic": "Confidence", "message": "I want to feel steadier."},
        seeker,
    )

    consultant_email = f"smoke-consultant-{RUN}@example.com"
    consultant = token_for(consultant_email, role="spiritual_consultant")

    status, body = _request("GET", "/consultant/clients", headers=consultant)
    check(
        "consultant reads a live client roster",
        status == 200 and body["total"] >= 1,
        f"status {status} total={body.get('total')}",
    )

    status, _ = _request("GET", "/consultant/consultations", headers=consultant)
    check("consultant reads the guidance queue", status == 200, f"status {status}")

    # --- Seeker: the core journey still works -------------------------------
    status, _ = _request("POST", "/readings/tarot", {"spread": "Single Card", "cards": ["The Star"]}, seeker)
    check("seeker runs a tarot reading", status == 201, f"status {status}")
    status, _ = _request("GET", "/readings", headers=seeker)
    check("seeker views reading history", status == 200, f"status {status}")
    status, _ = _request("GET", "/profile", headers=seeker)
    check("seeker manages their profile", status == 200, f"status {status}")

    failed = [label for label, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("failed: " + "; ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

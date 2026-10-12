# Rate limiter: 429 envelope after window exceeded.

from app.middleware.rate_limit import _buckets


def test_login_rate_limit_429_after_limit(client):
    _buckets.clear()
    for _ in range(10):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "anyone@example.com", "password": "whatever-long"},
        )
        assert resp.status_code == 401  # auth failure, but not rate limited yet
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "anyone@example.com", "password": "whatever-long"},
    )
    assert resp.status_code == 429
    body = resp.json()
    assert body["code"] == "HTTP_429"
    assert body["request_id"]


def test_register_rate_limit_429_after_limit(client):
    _buckets.clear()
    statuses = []
    for i in range(11):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user{i}@example.com",
                "password": "passw0rd-long",
                "full_name": "User",
            },
        )
        statuses.append(resp.status_code)
    assert statuses[:-1] == [201] * 10
    assert statuses[-1] == 429


def test_scopes_are_independent(client):
    _buckets.clear()
    for _ in range(10):
        client.post(
            "/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}
        )
    assert (
        client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}).status_code
        == 429
    )
    assert (
        client.post("/api/v1/auth/refresh").status_code == 401
    ), "refresh scope must have its own bucket"

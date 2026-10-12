def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["environment"]
    assert body["version"]
    # Real checks reported for the admin console's system-status panel.
    assert body["database"] == "ok"
    assert body["ai_provider"] in {"configured", "not_configured"}


def test_request_id_header_present(client):
    response = client.get("/api/v1/health")
    assert "x-request-id" in response.headers


def test_root_health_probe(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_returns_error_envelope(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert set(["code", "message", "request_id"]).issubset(body.keys())


def test_openapi_schema_available(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "Palmistry" in response.json()["info"]["title"]

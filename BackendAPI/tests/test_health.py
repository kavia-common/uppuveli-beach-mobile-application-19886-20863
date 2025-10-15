def test_health_root_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    # Expected shape includes message and timestamp keys
    assert isinstance(body, dict)
    assert "message" in body
    # Accept a few variants in case message differs across environments
    assert str(body["message"]).lower() in ("healthy", "ok")
    assert "timestamp" in body


def test_openapi_docs_reachable(client):
    # Ensure OpenAPI schema is served
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "info" in data

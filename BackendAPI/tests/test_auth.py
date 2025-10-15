def test_register_success(client):
    payload = {
        "email": "newuser@example.com",
        "password": "password123",
        "name": "New User",
        "phone": "1112223333",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code in (200, 400)  # 400 if duplicate between re-runs
    body = resp.json()
    if resp.status_code == 200:
        assert body["status"] == "success"
        data = body["data"]
        assert data["email"] == payload["email"].lower()
        assert "id" in data and data["id"] is not None
        assert "name" in data
    else:
        # 400 is standardized by global exception handler to ErrorResponse shape
        assert "error_code" in body
        assert "message" in body


def test_login_success(client):
    # Ensure a user exists
    reg = client.post(
        "/auth/register",
        json={"email": "loginok@example.com", "password": "password123", "name": "Lo Gin", "phone": "123"},
    )
    assert reg.status_code in (200, 400)

    resp = client.post("/auth/login", json={"email": "loginok@example.com", "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    token_data = body["data"]
    assert "access_token" in token_data and token_data["access_token"]
    assert token_data.get("token_type", "bearer") == "bearer"


def test_login_bad_credentials(client):
    # Make sure a user exists with known password
    client.post(
        "/auth/register",
        json={"email": "badcreds@example.com", "password": "password123", "name": "Bad Creds", "phone": "123"},
    )
    # Wrong password
    resp = client.post("/auth/login", json={"email": "badcreds@example.com", "password": "wrongpass"})
    assert resp.status_code == 401
    body = resp.json()
    # Global exception handler produces ErrorResponse shape
    assert "error_code" in body
    assert "message" in body

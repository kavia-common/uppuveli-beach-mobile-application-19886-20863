from datetime import date, timedelta


def test_bookings_requires_auth(client):
    r = client.get("/bookings")
    assert r.status_code == 401
    body = r.json()
    assert "error_code" in body and "message" in body


def test_create_and_list_bookings_with_auth(client, auth_token):
    headers = {"Authorization": auth_token}
    today = date.today()
    # Create two bookings
    payload1 = {
        "room_id": "R-100",
        "guest_id": "IGNORED",  # should be set by server using token subject
        "check_in": today.isoformat(),
        "check_out": (today + timedelta(days=1)).isoformat(),
        "status": "confirmed",
    }
    payload2 = {
        "room_id": "R-200",
        "guest_id": "IGNORED",
        "check_in": (today + timedelta(days=3)).isoformat(),
        "check_out": (today + timedelta(days=5)).isoformat(),
        "status": "pending",
    }
    c1 = client.post("/bookings", json=payload1, headers=headers)
    assert c1.status_code == 200, c1.text
    body1 = c1.json()
    assert body1["status"] == "success"
    data1 = body1["data"]
    assert data1["room_id"] == "R-100"
    assert data1["guest_id"] is not None  # set by server
    assert data1["id"] is not None

    c2 = client.post("/bookings", json=payload2, headers=headers)
    assert c2.status_code == 200, c2.text

    # List with pagination
    l1 = client.get("/bookings?limit=1&offset=0", headers=headers)
    assert l1.status_code == 200
    body = l1.json()
    assert body["status"] == "success"
    data = body["data"]
    assert isinstance(data, list)
    assert len(data) == 1

    # Next page
    l2 = client.get("/bookings?limit=1&offset=1", headers=headers)
    assert l2.status_code == 200
    data2 = l2.json()["data"]
    assert isinstance(data2, list)
    assert len(data2) >= 1  # may have exactly 1

    # Combined should be at least two created
    combined = data + data2
    assert len(combined) >= 2
    # Ensure items include expected fields
    for item in combined:
        for key in ("id", "room_id", "guest_id", "check_in", "check_out", "status"):
            assert key in item


def test_create_booking_validation_error(client, auth_token):
    headers = {"Authorization": auth_token}
    today = date.today()
    # Invalid payload: check_out before check_in
    bad = {
        "room_id": "R-300",
        "guest_id": "IGNORED",
        "check_in": (today + timedelta(days=2)).isoformat(),
        "check_out": (today + timedelta(days=1)).isoformat(),
        "status": "pending",
    }
    r = client.post("/bookings", json=bad, headers=headers)
    assert r.status_code == 400
    body = r.json()
    assert "error_code" in body
    assert "message" in body

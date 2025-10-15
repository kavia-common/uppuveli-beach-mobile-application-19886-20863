from datetime import date, timedelta


def _create_booking(client, auth_token, room_id="R-PAY-1", start_days=1, duration_days=2):
    headers = {"Authorization": auth_token}
    today = date.today()
    payload = {
        "room_id": room_id,
        "guest_id": "IGNORED",
        "check_in": (today + timedelta(days=start_days)).isoformat(),
        "check_out": (today + timedelta(days=start_days + duration_days)).isoformat(),
        "status": "confirmed",
    }
    r = client.post("/bookings", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]


def test_payments_requires_auth(client):
    # POST without auth
    r = client.post("/payments", json={"booking_id": 1, "amount": 100.0, "method": "stripe"})
    assert r.status_code == 401
    # GET without auth
    r2 = client.get("/payments/1")
    assert r2.status_code == 401


def test_create_payment_success_and_list(client, auth_token):
    headers = {"Authorization": auth_token}
    booking = _create_booking(client, auth_token)
    # Create a payment
    pay_req = {"booking_id": booking["id"], "amount": 123.45, "method": "stripe"}
    r = client.post("/payments", json=pay_req, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["booking_id"] == booking["id"]
    assert data["amount"] == pay_req["amount"]
    assert data["method"] == "stripe"
    assert data["status"] in ("succeeded", "failed")
    assert "id" in data and data["id"] is not None

    # List for booking
    l = client.get(f"/payments/{booking['id']}", headers=headers)
    assert l.status_code == 200
    lbody = l.json()
    assert lbody["status"] == "success"
    items = lbody["data"]["items"]
    assert isinstance(items, list)
    assert len(items) >= 1
    # Ensure fields present
    for item in items:
        for key in ("id", "booking_id", "guest_id", "amount", "method", "status", "created_at", "updated_at"):
            assert key in item


def test_create_payment_forbidden_for_other_user(client, register_user):
    # Create user A, booking A
    u_a = register_user(email="payerA@example.com", password="password123", name="Payer A")
    tok_a_resp = client.post("/auth/login", json={"email": u_a["email"], "password": u_a["password"]})
    token_a = "Bearer " + tok_a_resp.json()["data"]["access_token"]
    booking_a = _create_booking(client, token_a, room_id="R-X-1")

    # Create user B, try to pay for A's booking
    u_b = register_user(email="payerB@example.com", password="password123", name="Payer B")
    tok_b_resp = client.post("/auth/login", json={"email": u_b["email"], "password": u_b["password"]})
    token_b = "Bearer " + tok_b_resp.json()["data"]["access_token"]

    r = client.post("/payments", json={"booking_id": booking_a["id"], "amount": 50, "method": "wallet"}, headers={"Authorization": token_b})
    assert r.status_code == 403
    body = r.json()
    assert "error_code" in body and "message" in body


def test_create_payment_not_found_booking(client, auth_token):
    headers = {"Authorization": auth_token}
    r = client.post("/payments", json={"booking_id": 999999, "amount": 10, "method": "paypal"}, headers=headers)
    assert r.status_code == 404
    body = r.json()
    assert "error_code" in body and "message" in body


def test_deterministic_failure_rule(client, auth_token):
    headers = {"Authorization": auth_token}
    # Create multiple bookings until we hit booking id divisible by 5, then expect failure
    failed_seen = False
    for i in range(1, 8):
        booking = _create_booking(client, auth_token, room_id=f"R-DF-{i}", start_days=i)
        resp = client.post("/payments", json={"booking_id": booking["id"], "amount": 10.0, "method": "stripe"}, headers=headers)
        assert resp.status_code == 200, resp.text
        status_val = resp.json()["data"]["status"]
        if booking["id"] % 5 == 0:
            assert status_val == "failed"
            failed_seen = True
            break
    assert failed_seen, "Expected at least one simulated failure for booking_id % 5 == 0"

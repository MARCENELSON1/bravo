"""End-to-end pay-from-the-table (Carta QR F3 Tanda B): the diner pays their table's
bill from the QR token. Tests run against the default ``manual`` gateway, which
confirms instantly (no real MercadoPago) → the order settles in one call."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _product(http, h, name, amount, category="Platos"):
    res = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": amount, "category": category},
        headers=h,
    )
    assert res.status_code == 201, res.text
    return res.json()["product_id"]


async def _qr_token(http, h, number):
    table = await http.post("/api/v1/tables", json={"number": number, "name": None}, headers=h)
    table_id = table.json()["table_id"]
    return (await http.get(f"/api/v1/tables/{table_id}/qr", headers=h)).json()["token"]


async def _enable_self_order(http, h):
    res = await http.put(
        "/api/v1/self-order/settings",
        json={"enabled": True, "requires_confirmation": True},
        headers=h,
    )
    assert res.status_code == 200, res.text


async def _enable_self_pay(http, h, *, tips_enabled=True):
    res = await http.put(
        "/api/v1/self-pay/settings",
        json={"enabled": True, "tips_enabled": tips_enabled},
        headers=h,
    )
    assert res.status_code == 200, res.text


async def _submit(http, token, pid, qty):
    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": qty}]},
    )
    assert res.status_code == 200, res.text
    return res.json()["order_id"]


async def test_self_pay_settings_default_and_toggle(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    got = await http.get("/api/v1/self-pay/settings", headers=h)
    assert got.status_code == 200, got.text
    # Default: pago desde la mesa apagado (paridad), propina ofrecida.
    assert got.json() == {"enabled": False, "tips_enabled": True}

    await _enable_self_pay(http, h, tips_enabled=False)
    got = await http.get("/api/v1/self-pay/settings", headers=h)
    assert got.json() == {"enabled": True, "tips_enabled": False}


async def test_pay_settles_the_whole_bill(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 5)
    order_id = await _submit(http, token, pid, 2)  # total 2_400_000

    pay = await http.post("/api/v1/public/table/pay", json={"token": token})
    assert pay.status_code == 200, pay.text
    body = pay.json()
    assert body["order_id"] == order_id
    assert body["amount"] == 2400000
    assert body["status"] == "CONFIRMED"  # manual gateway confirms at once
    assert body["checkout_url"] is None

    # The order is settled and the bill drops to zero.
    order = await http.get(f"/api/v1/orders/{order_id}", headers=h)
    assert order.json()["status"] == "PAID"
    bill = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert bill.json()["balance"] == 0


async def test_pay_with_a_tip(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 6)
    await _submit(http, token, pid, 1)

    pay = await http.post("/api/v1/public/table/pay", json={"token": token, "tip": 150000})
    assert pay.status_code == 200, pay.text
    payment_id = pay.json()["payment_id"]
    assert pay.json()["tip"] == 150000

    # The diner can poll the payment status by token.
    status = await http.get(
        f"/api/v1/public/table/payment/{payment_id}", params={"token": token}
    )
    assert status.status_code == 200, status.text
    assert status.json()["status"] == "CONFIRMED"
    assert status.json()["tip"] == 150000


async def test_tip_is_ignored_when_owner_disabled_tips(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h, tips_enabled=False)
    token = await _qr_token(http, h, 7)
    await _submit(http, token, pid, 1)

    pay = await http.post("/api/v1/public/table/pay", json={"token": token, "tip": 150000})
    assert pay.status_code == 200, pay.text
    assert pay.json()["tip"] == 0  # the owner turned tips off → never charged


async def test_pay_rejected_when_self_pay_disabled(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)  # ordering on, paying OFF
    token = await _qr_token(http, h, 8)
    await _submit(http, token, pid, 1)

    pay = await http.post("/api/v1/public/table/pay", json={"token": token})
    assert pay.status_code == 409
    assert pay.json()["code"] == "self_pay_disabled"


async def test_pay_nothing_to_pay_without_an_order(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 9)  # table with no order

    pay = await http.post("/api/v1/public/table/pay", json={"token": token})
    assert pay.status_code == 409
    assert pay.json()["code"] == "nothing_to_pay"


async def test_double_tap_charges_the_bill_once(client):
    """With the manual gateway the first tap settles the bill instantly, so a second
    tap finds nothing to pay — the table is charged exactly once. (The idempotency
    key replay for a still-PENDING online charge is unit-tested separately.)"""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 10)
    order_id = await _submit(http, token, pid, 1)

    key = "diner-intent-abc"
    first = await http.post(
        "/api/v1/public/table/pay", json={"token": token, "idempotency_key": key}
    )
    second = await http.post(
        "/api/v1/public/table/pay", json={"token": token, "idempotency_key": key}
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 409  # already settled → nothing left to pay
    assert second.json()["code"] == "nothing_to_pay"

    pays = await http.get(f"/api/v1/orders/{order_id}/payments", headers=h)
    assert len(pays.json()) == 1  # charged once


async def test_split_the_bill_two_partial_payments_settle_it(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 11)
    order_id = await _submit(http, token, pid, 2)  # total 2_000_000

    # Diner 1 pays their half.
    first = await http.post(
        "/api/v1/public/table/pay", json={"token": token, "amount": 1000000}
    )
    assert first.status_code == 200, first.text
    assert first.json()["amount"] == 1000000
    order = await http.get(f"/api/v1/orders/{order_id}", headers=h)
    assert order.json()["status"] != "PAID"  # still half owing
    bill = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert bill.json()["balance"] == 1000000

    # Diner 2 pays the rest → the order settles.
    second = await http.post(
        "/api/v1/public/table/pay", json={"token": token, "amount": 1000000}
    )
    assert second.status_code == 200, second.text
    order = await http.get(f"/api/v1/orders/{order_id}", headers=h)
    assert order.json()["status"] == "PAID"
    bill = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert bill.json()["balance"] == 0


async def test_split_amount_over_balance_is_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1000000)
    await _enable_self_order(http, h)
    await _enable_self_pay(http, h)
    token = await _qr_token(http, h, 12)
    await _submit(http, token, pid, 1)  # balance 1_000_000

    pay = await http.post(
        "/api/v1/public/table/pay", json={"token": token, "amount": 5000000}
    )
    assert pay.status_code == 422
    assert pay.json()["code"] == "invalid_payment_amount"


async def test_pay_rejects_a_bad_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    res = await http.post("/api/v1/public/table/pay", json={"token": "garbage.deadbeef"})
    assert res.status_code == 401
    assert res.json()["code"] == "invalid_table_qr_token"


async def test_public_endpoints_are_rate_limited(client):
    """A leaked/abused table token can't hammer the floor: call-waiter is capped
    per table (8/min) → the 9th within the window is 429."""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    token = await _qr_token(http, h, 13)

    for _ in range(8):
        ok = await http.post("/api/v1/public/table/call-waiter", json={"token": token})
        assert ok.status_code == 200, ok.text
    blocked = await http.post("/api/v1/public/table/call-waiter", json={"token": token})
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "rate_limited"

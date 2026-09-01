"""End-to-end table bill (Carta QR F3 Tanda A): the diner reads the running bill of
their table from the QR token — total/pagado/saldo, server-computed, read-only."""

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


async def _submit(http, token, pid, qty):
    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": qty}]},
    )
    assert res.status_code == 200, res.text
    return res.json()["order_id"]


async def test_bill_reflects_the_open_order(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable_self_order(http, h)
    token = await _qr_token(http, h, 5)
    await _submit(http, token, pid, 2)

    res = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert res.status_code == 200, res.text
    bill = res.json()
    assert bill["currency"] == "ARS"
    assert bill["total"] == 2400000
    assert bill["paid"] == 0
    assert bill["balance"] == 2400000
    assert len(bill["items"]) == 1
    assert bill["items"][0]["name"] == "Pizza"
    assert bill["items"][0]["quantity"] == 2
    assert bill["items"][0]["unit_price"] == 1200000
    # Self-pay off by default → no online pay; tips offered by default.
    assert bill["online_pay_available"] is False
    assert bill["tips_enabled"] is True


async def test_bill_is_empty_before_any_order(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    token = await _qr_token(http, h, 6)  # table with no session yet

    res = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert res.status_code == 200, res.text
    bill = res.json()
    assert bill["items"] == []
    assert bill["total"] == 0
    assert bill["balance"] == 0


async def test_bill_subtracts_a_confirmed_partial_payment(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable_self_order(http, h)
    token = await _qr_token(http, h, 7)
    order_id = await _submit(http, token, pid, 2)  # total 2_400_000

    # Cashier collects a partial payment (< total → order stays open, shows on the bill).
    pay = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 1000000},
        headers=h,
    )
    assert pay.status_code in (200, 201), pay.text

    res = await http.get("/api/v1/public/table/bill", params={"token": token})
    assert res.status_code == 200, res.text
    bill = res.json()
    assert bill["total"] == 2400000
    assert bill["paid"] == 1000000
    assert bill["balance"] == 1400000


async def test_bill_rejects_a_bad_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    res = await http.get("/api/v1/public/table/bill", params={"token": "garbage.deadbeef"})
    assert res.status_code == 401
    assert res.json()["code"] == "invalid_table_qr_token"


async def test_bill_is_isolated_per_table(client):
    """A token for table B never shows table A's order (token IS the scope)."""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable_self_order(http, h)
    token_a = await _qr_token(http, h, 8)
    token_b = await _qr_token(http, h, 9)
    await _submit(http, token_a, pid, 1)

    res = await http.get("/api/v1/public/table/bill", params={"token": token_b})
    assert res.status_code == 200, res.text
    assert res.json()["total"] == 0  # table B has no order

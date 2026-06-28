"""End-to-end caja / arqueo Z: abrir → cobrar → esperado → cerrar → diferencia."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_cash_session_arqueo_flow(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    # Open the register with a 50000 cash float.
    opened = await http.post(
        "/api/v1/cashier/session/open", json={"opening_float_amount": 50000}, headers=h
    )
    assert opened.status_code == 200, opened.text
    session_id = opened.json()["id"]
    assert opened.json()["status"] == "OPEN"

    # An order to charge against.
    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Lomo", "price_amount": 1000000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers=h,
    )

    # Two confirmed inflows during the session: CASH 30000 + CARD 20000.
    for method, amount in (("CASH", 30000), ("CARD", 20000)):
        paid = await http.post(
            f"/api/v1/orders/{order_id}/payments",
            json={"method": method, "amount": amount},
            headers=h,
        )
        assert paid.status_code == 201, paid.text

    # Live arqueo: CASH expected = float(50000) + 30000 = 80000; CARD = 20000.
    report = await http.get("/api/v1/cashier/session/current", headers=h)
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["status"] == "OPEN"
    by_method = {line["method"]: line for line in body["lines"]}
    assert by_method["CASH"]["expected"] == 80000
    assert by_method["CARD"]["expected"] == 20000
    assert by_method["CASH"]["counted"] is None  # still open
    assert body["expected_total"] == 100000

    # Close counting 79500 cash (500 short) and 20000 card (exact).
    closed = await http.post(
        f"/api/v1/cashier/session/{session_id}/close",
        json={"counted": {"CASH": 79500, "CARD": 20000}},
        headers=h,
    )
    assert closed.status_code == 200, closed.text
    cbody = closed.json()
    assert cbody["status"] == "CLOSED"
    closed_by_method = {line["method"]: line for line in cbody["lines"]}
    assert closed_by_method["CASH"]["difference"] == -500
    assert closed_by_method["CARD"]["difference"] == 0
    assert cbody["counted_total"] == 99500
    assert cbody["difference_total"] == -500

    # A second open is rejected while one is already open.
    again = await http.post(
        "/api/v1/cashier/session/open", json={"opening_float_amount": 0}, headers=h
    )
    assert again.status_code == 200  # the previous one is CLOSED now, so this opens fine
    assert again.json()["status"] == "OPEN"


async def test_refund_excludes_payment_from_arqueo(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    await http.post(
        "/api/v1/cashier/session/open", json={"opening_float_amount": 10000}, headers=h
    )
    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Lomo", "price_amount": 1000000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers=h,
    )
    payment_id = (
        await http.post(
            f"/api/v1/orders/{order_id}/payments",
            json={"method": "CASH", "amount": 30000},
            headers=h,
        )
    ).json()["id"]

    # Before the refund: CASH expected = float(10000) + 30000 = 40000.
    before = await http.get("/api/v1/cashier/session/current", headers=h)
    cash_before = next(
        ln for ln in before.json()["lines"] if ln["method"] == "CASH"
    )["expected"]
    assert cash_before == 40000

    # Refund the payment → it no longer counts in the arqueo.
    refunded = await http.post(f"/api/v1/payments/{payment_id}/refund", headers=h)
    assert refunded.status_code == 200, refunded.text
    assert refunded.json()["status"] == "REFUNDED"

    after = await http.get("/api/v1/cashier/session/current", headers=h)
    cash_after = next(ln for ln in after.json()["lines"] if ln["method"] == "CASH")["expected"]
    assert cash_after == 10000  # only the float remains

    # Refunding twice is rejected.
    again = await http.post(f"/api/v1/payments/{payment_id}/refund", headers=h)
    assert again.status_code == 409
    assert again.json()["code"] == "payment_not_refundable"


async def test_cannot_open_two_sessions_at_once(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    first = await http.post(
        "/api/v1/cashier/session/open", json={"opening_float_amount": 10000}, headers=h
    )
    assert first.status_code == 200
    second = await http.post(
        "/api/v1/cashier/session/open", json={"opening_float_amount": 10000}, headers=h
    )
    assert second.status_code == 409
    assert second.json()["code"] == "cash_session_already_open"


async def test_no_open_session_returns_null(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    report = await http.get("/api/v1/cashier/session/current", headers=h)
    assert report.status_code == 200
    assert report.json() is None

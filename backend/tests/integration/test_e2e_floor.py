"""End-to-end checks for the floor read model (derived table occupancy)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_floor_reflects_table_occupancy(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    table_id = (
        await http.post("/api/v1/tables", json={"number": 7, "name": "Patio"}, headers=h)
    ).json()["table_id"]

    # Free to start: no active order.
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["status"] == "FREE"
    assert row["active_order"] is None

    # Opening an order makes the table occupied, with the order embedded.
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["status"] == "OCCUPIED"
    assert row["active_order"]["id"] == order_id

    # Cancelling frees the table again (PAID/CANCELLED orders are not active).
    await http.post(f"/api/v1/orders/{order_id}/cancel", headers=h)
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["status"] == "FREE"
    assert row["active_order"] is None


def _row(response, table_id: str) -> dict:
    assert response.status_code == 200, response.text
    return next(r for r in response.json() if r["id"] == table_id)


async def test_floor_session_state_derives_from_orders(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="bar", email="owner@bar.com")
    h = _auth(tokens)

    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Pizza", "price_amount": 120000, "category": "Platos"},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 3, "name": None}, headers=h)
    ).json()["table_id"]

    # Free table → no session.
    assert _row(await http.get("/api/v1/floor", headers=h), table_id)["session"] is None

    # Opening an order implicitly opens the session (abierta = OPEN).
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["session"] is not None
    session_id = row["session"]["id"]
    assert row["session"]["state"] == "OPEN"
    assert row["session"]["waiter_name"]  # the owner's display name, not a UUID

    async def _state() -> str:
        return _row(await http.get("/api/v1/floor", headers=h), table_id)["session"]["state"]

    # Marched to the kitchen → en_cocina.
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers=h,
    )
    await http.post(f"/api/v1/orders/{order_id}/send", headers=h)
    assert await _state() == "IN_KITCHEN"

    # A ready dish → para_servir (máxima prioridad).
    await http.post(f"/api/v1/orders/{order_id}/preparing", headers=h)
    await http.post(f"/api/v1/orders/{order_id}/ready", headers=h)
    ts = _row(await http.get("/api/v1/floor", headers=h), table_id)["session"]
    assert ts["state"] == "TO_SERVE"
    assert ts["state_since"] is not None

    # Served + bill requested → a_cobrar.
    await http.post(f"/api/v1/orders/{order_id}/served", headers=h)
    assert await _state() == "SERVED"
    billed = await http.post(f"/api/v1/floor/sessions/{session_id}/bill", headers=h)
    assert billed.status_code == 200, billed.text
    assert await _state() == "TO_CHARGE"


async def test_floor_session_pax_and_reuse(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="caf", email="owner@caf.com")
    h = _auth(tokens)
    table_id = (
        await http.post("/api/v1/tables", json={"number": 9, "name": None}, headers=h)
    ).json()["table_id"]

    # Explicit open with pax; a second open is idempotent (same visit).
    opened = await http.post(
        "/api/v1/floor/sessions", json={"table_id": table_id, "pax": 4}, headers=h
    )
    assert opened.status_code == 200, opened.text
    session_id = opened.json()["id"]
    assert opened.json()["pax"] == 4
    again = await http.post(
        "/api/v1/floor/sessions", json={"table_id": table_id, "pax": 2}, headers=h
    )
    assert again.json()["id"] == session_id  # reused, not duplicated

    # An order on that table reuses the open session (no second one).
    order = await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    assert order.status_code == 201, order.text
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["session"]["id"] == session_id
    assert row["session"]["pax"] == 4

    # PAX can be corrected.
    patched = await http.patch(
        f"/api/v1/floor/sessions/{session_id}/pax", json={"pax": 6}, headers=h
    )
    assert patched.status_code == 200, patched.text
    assert _row(await http.get("/api/v1/floor", headers=h), table_id)["session"]["pax"] == 6

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

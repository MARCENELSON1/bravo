"""End-to-end comandas + KDS flow over HTTP against the real app + DB."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_order_lifecycle_and_kds(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    product = await http.post(
        "/api/v1/products",
        json={"name": "Milanesa", "price_amount": 150000, "category": "Platos"},
        headers=h,
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["product_id"]

    table = await http.post(
        "/api/v1/tables", json={"number": 5, "name": "Ventana"}, headers=h
    )
    assert table.status_code == 201, table.text
    table_id = table.json()["table_id"]

    created = await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    assert created.status_code == 201, created.text
    order_id = created.json()["order_id"]

    # Add a line item: price is snapshotted from the product (2 x 150000).
    added = await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 2},
        headers=h,
    )
    assert added.status_code == 200, added.text
    body = added.json()
    assert body["status"] == "OPEN"
    assert body["total_amount"] == 300000
    assert body["items"][0]["name"] == "Milanesa"

    sent = await http.post(f"/api/v1/orders/{order_id}/send", headers=h)
    assert sent.status_code == 200
    assert sent.json()["status"] == "SENT"

    # The KDS sees the SENT order.
    kds = await http.get("/api/v1/kds/orders", headers=h)
    assert kds.status_code == 200
    assert order_id in [o["id"] for o in kds.json()]

    assert (
        await http.post(f"/api/v1/orders/{order_id}/preparing", headers=h)
    ).json()["status"] == "PREPARING"
    assert (
        await http.post(f"/api/v1/orders/{order_id}/ready", headers=h)
    ).json()["status"] == "READY"
    assert (
        await http.post(f"/api/v1/orders/{order_id}/served", headers=h)
    ).json()["status"] == "SERVED"

    # A SERVED order leaves the KDS board.
    kds_after = await http.get("/api/v1/kds/orders", headers=h)
    assert order_id not in [o["id"] for o in kds_after.json()]


async def test_cannot_send_empty_order(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    table = await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    order = await http.post(
        "/api/v1/orders", json={"table_id": table.json()["table_id"]}, headers=h
    )
    sent = await http.post(f"/api/v1/orders/{order.json()['order_id']}/send", headers=h)
    assert sent.status_code == 422
    assert sent.json()["code"] == "empty_order"


async def test_tenant_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await http.post(
        "/api/v1/products",
        json={"name": "Lomo", "price_amount": 200000, "category": None},
        headers=_auth(t1),
    )

    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    listed = await http.get("/api/v1/products", headers=_auth(t2))
    assert listed.status_code == 200
    assert listed.json() == []  # tenant 2 sees none of tenant 1's products (RLS)

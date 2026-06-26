"""End-to-end comandas + KDS flow over HTTP against the real app + DB."""

from __future__ import annotations

from uuid import uuid4

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


async def test_client_ids_make_create_and_add_idempotent(client):
    """A retried create/add with the same client id is a no-op (no duplicates)."""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Milanesa", "price_amount": 150000, "category": "Platos"},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 5, "name": None}, headers=h)
    ).json()["table_id"]

    # Create with a client-supplied order id, twice → same order, created once.
    order_id = str(uuid4())
    first = await http.post(
        "/api/v1/orders", json={"table_id": table_id, "id": order_id}, headers=h
    )
    again = await http.post(
        "/api/v1/orders", json={"table_id": table_id, "id": order_id}, headers=h
    )
    assert first.json()["order_id"] == order_id
    assert again.json()["order_id"] == order_id
    assert len((await http.get("/api/v1/orders", headers=h)).json()) == 1

    # Add the same item id twice → only one line.
    item_id = str(uuid4())
    payload = {"product_id": product_id, "quantity": 1, "id": item_id}
    await http.post(f"/api/v1/orders/{order_id}/items", json=payload, headers=h)
    replayed = await http.post(
        f"/api/v1/orders/{order_id}/items", json=payload, headers=h
    )
    assert replayed.status_code == 200, replayed.text
    assert len(replayed.json()["items"]) == 1


async def test_batch_add_and_send_is_idempotent(client):
    """Batch adds N items (+send) in one call; replaying the same ids is a no-op."""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Lomo", "price_amount": 200000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 2, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]

    items = [
        {"product_id": product_id, "quantity": 1, "id": str(uuid4())},
        {"product_id": product_id, "quantity": 2, "id": str(uuid4())},
    ]
    batch = await http.post(
        f"/api/v1/orders/{order_id}/items/batch",
        json={"items": items, "send": True},
        headers=h,
    )
    assert batch.status_code == 200, batch.text
    body = batch.json()
    assert body["status"] == "SENT"
    assert len(body["items"]) == 2
    assert body["total_amount"] == 600000  # 1x200000 + 2x200000

    # Replaying the same batch ids does not duplicate (order already SENT).
    replay = await http.post(
        f"/api/v1/orders/{order_id}/items/batch",
        json={"items": items, "send": True},
        headers=h,
    )
    assert replay.status_code == 200, replay.text
    assert len(replay.json()["items"]) == 2


async def test_remove_and_edit_item_while_open(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Milanesa", "price_amount": 150000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 9, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    item_id = (
        await http.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product_id, "quantity": 1},
            headers=h,
        )
    ).json()["items"][0]["id"]

    # Edit quantity → total reflects it.
    patched = await http.patch(
        f"/api/v1/orders/{order_id}/items/{item_id}", json={"quantity": 3}, headers=h
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["items"][0]["quantity"] == 3
    assert patched.json()["total_amount"] == 450000

    # Remove → empty order.
    removed = await http.delete(f"/api/v1/orders/{order_id}/items/{item_id}", headers=h)
    assert removed.status_code == 200, removed.text
    assert removed.json()["items"] == []

    # Removing a non-existent item → 404.
    missing = await http.delete(f"/api/v1/orders/{order_id}/items/{item_id}", headers=h)
    assert missing.status_code == 404
    assert missing.json()["code"] == "item_not_found"


async def test_cannot_edit_item_after_sent(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)
    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Lomo", "price_amount": 200000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 3, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    item_id = (
        await http.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product_id, "quantity": 1},
            headers=h,
        )
    ).json()["items"][0]["id"]
    await http.post(f"/api/v1/orders/{order_id}/send", headers=h)

    res = await http.delete(f"/api/v1/orders/{order_id}/items/{item_id}", headers=h)
    assert res.status_code == 409
    assert res.json()["code"] == "invalid_order_transition"


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

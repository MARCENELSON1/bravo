"""End-to-end product modifiers (Carta QR F2 D): the owner defines choices on a
product → the public menu exposes them → the diner picks options and the price is
recomputed server-side (a tampered cart never changes the total)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _product(http, h, name, amount):
    res = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": amount, "category": "Platos"},
        headers=h,
    )
    assert res.status_code == 201, res.text
    return res.json()["product_id"]


async def _qr_token(http, h, number):
    table = await http.post("/api/v1/tables", json={"number": number, "name": None}, headers=h)
    table_id = table.json()["table_id"]
    return (await http.get(f"/api/v1/tables/{table_id}/qr", headers=h)).json()["token"]


_GROUP = {
    "name": "Cocción",
    "min_select": 1,
    "max_select": 1,
    "options": [
        {"name": "Jugosa", "price_delta": 0},
        {"name": "Con panceta", "price_delta": 300000},
    ],
}


async def test_owner_sets_and_reads_modifiers(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Bife", 1200000)

    put = await http.put(
        f"/api/v1/products/{pid}/modifiers", json={"groups": [_GROUP]}, headers=h
    )
    assert put.status_code == 200, put.text
    groups = put.json()["groups"]
    assert len(groups) == 1
    assert groups[0]["required"] is True  # min_select 1
    assert groups[0]["id"]
    assert {o["name"] for o in groups[0]["options"]} == {"Jugosa", "Con panceta"}
    assert all(o["id"] for o in groups[0]["options"])

    got = await http.get(f"/api/v1/products/{pid}/modifiers", headers=h)
    assert got.status_code == 200
    assert got.json()["groups"][0]["name"] == "Cocción"


async def test_bad_group_rules_are_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Bife", 1200000)
    bad = {"name": "X", "min_select": 2, "max_select": 1, "options": [{"name": "a"}]}
    res = await http.put(
        f"/api/v1/products/{pid}/modifiers", json={"groups": [bad]}, headers=h
    )
    assert res.status_code == 422
    assert res.json()["code"] == "invalid_modifier_group"


async def test_public_menu_exposes_modifiers(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Bife", 1200000)
    await http.put(f"/api/v1/products/{pid}/modifiers", json={"groups": [_GROUP]}, headers=h)
    token = await _qr_token(http, h, 3)

    menu = await http.get("/api/v1/public/menu", params={"token": token})
    item = menu.json()["categories"][0]["items"][0]
    assert item["modifier_groups"][0]["name"] == "Cocción"
    assert item["modifier_groups"][0]["required"] is True
    # Prices are exposed to the diner (deltas), never costs.
    assert {o["price_delta"] for o in item["modifier_groups"][0]["options"]} == {0, 300000}


async def test_customer_order_recomputes_price_and_snapshots_options(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Bife", 1200000)
    put = await http.put(
        f"/api/v1/products/{pid}/modifiers", json={"groups": [_GROUP]}, headers=h
    )
    bacon = next(
        o for o in put.json()["groups"][0]["options"] if o["name"] == "Con panceta"
    )
    await http.put(
        "/api/v1/self-order/settings",
        json={"enabled": True, "requires_confirmation": True},
        headers=h,
    )
    token = await _qr_token(http, h, 4)

    # The cart sends only ids — never the price. Server folds the +300000 delta in.
    res = await http.post(
        "/api/v1/public/table/order",
        json={
            "token": token,
            "lines": [{"product_id": pid, "quantity": 2, "option_ids": [bacon["id"]]}],
        },
    )
    assert res.status_code == 200, res.text
    order_id = res.json()["order_id"]

    order = await http.get(f"/api/v1/orders/{order_id}", headers=h)
    assert order.status_code == 200, order.text
    body = order.json()
    # (1200000 base + 300000 delta) × 2.
    assert body["total_amount"] == 3000000
    item = body["items"][0]
    assert item["unit_price_amount"] == 1500000
    assert item["selected_options"] == [
        {"option_id": bacon["id"], "name": "Con panceta", "price_delta": 300000}
    ]


async def test_missing_required_modifier_is_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Bife", 1200000)
    await http.put(f"/api/v1/products/{pid}/modifiers", json={"groups": [_GROUP]}, headers=h)
    await http.put(
        "/api/v1/self-order/settings",
        json={"enabled": True, "requires_confirmation": True},
        headers=h,
    )
    token = await _qr_token(http, h, 5)

    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},  # sin cocción
    )
    assert res.status_code == 422
    assert res.json()["code"] == "invalid_modifier_selection"

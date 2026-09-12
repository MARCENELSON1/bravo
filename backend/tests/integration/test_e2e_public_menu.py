"""End-to-end Carta QR (Fase 1, Tanda A): owner issues a table's QR token, a diner
(no auth) fetches the public menu with it. Covers isolation and bad tokens."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _table(http, h: dict, number: int) -> str:
    res = await http.post("/api/v1/tables", json={"number": number, "name": None}, headers=h)
    assert res.status_code == 201, res.text
    return res.json()["table_id"]


async def _product(http, h: dict, name: str, amount: int, category: str | None) -> None:
    res = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": amount, "category": category},
        headers=h,
    )
    assert res.status_code == 201, res.text


async def test_issue_qr_then_fetch_public_menu(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    table_id = await _table(http, h, 5)
    await _product(http, h, "Empanada", 1500, "Entradas")
    await _product(http, h, "Provoleta", 4000, "Entradas")
    await _product(http, h, "Pizza", 12000, "Platos")

    qr = await http.get(f"/api/v1/tables/{table_id}/qr", headers=h)
    assert qr.status_code == 200, qr.text
    token = qr.json()["token"]
    assert token
    assert qr.json()["url"].endswith(f"/carta/{token}")

    # The diner scans → no auth needed, the token carries the tenant.
    menu = await http.get("/api/v1/public/menu", params={"token": token})
    assert menu.status_code == 200, menu.text
    body = menu.json()
    assert body["tenant_name"]
    assert body["currency"] == "ARS"
    names = [c["name"] for c in body["categories"]]
    assert names == ["Entradas", "Platos"]
    entradas = body["categories"][0]["items"]
    assert [i["name"] for i in entradas] == ["Empanada", "Provoleta"]
    assert entradas[0]["price_amount"] == 1500
    # No cost/margin leaks to the public menu.
    assert "cost_amount" not in entradas[0]
    # Autopedido apagado por default (paridad): la carta no muestra carrito.
    assert body["self_order_enabled"] is False
    assert body["self_order_requires_confirmation"] is True


async def test_qr_endpoint_requires_owner_or_manager(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    table_id = await _table(http, h, 1)

    # Unauthenticated → 401 (no bearer).
    anon = await http.get(f"/api/v1/tables/{table_id}/qr")
    assert anon.status_code == 401


async def test_public_menu_rejects_bad_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")

    bad = await http.get("/api/v1/public/menu", params={"token": "garbage.deadbeef"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_table_qr_token"

    missing = await http.get("/api/v1/public/menu")
    assert missing.status_code == 422  # required query param absent


async def test_call_waiter_and_request_bill_accept_a_valid_token(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    table_id = await _table(http, h, 5)
    token = (await http.get(f"/api/v1/tables/{table_id}/qr", headers=h)).json()["token"]

    waiter = await http.post("/api/v1/public/table/call-waiter", json={"token": token})
    assert waiter.status_code == 200, waiter.text
    assert waiter.json()["status"] == "ok"

    bill = await http.post("/api/v1/public/table/request-bill", json={"token": token})
    assert bill.status_code == 200, bill.text


async def test_call_waiter_rejects_bad_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    bad = await http.post(
        "/api/v1/public/table/call-waiter", json={"token": "garbage.deadbeef"}
    )
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_table_qr_token"


async def test_qr_token_is_tenant_isolated(client):
    http, fake_email = client
    # Tenant A with a product.
    a = _auth(await _onboard_verify_login(http, fake_email, slug="aaa", email="o@aaa.com"))
    table_a = await _table(http, a, 1)
    await _product(http, a, "Solo-A", 999, "X")
    token_a = (await http.get(f"/api/v1/tables/{table_a}/qr", headers=a)).json()["token"]

    # Tenant B with a different product.
    b = _auth(await _onboard_verify_login(http, fake_email, slug="bbb", email="o@bbb.com"))
    await _product(http, b, "Solo-B", 111, "Y")

    # A's token only ever shows A's menu.
    menu = (await http.get("/api/v1/public/menu", params={"token": token_a})).json()
    all_items = [i["name"] for c in menu["categories"] for i in c["items"]]
    assert all_items == ["Solo-A"]

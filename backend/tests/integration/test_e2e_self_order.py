"""End-to-end self-order (Carta QR F2 Tanda B): the diner submits a cart from the
QR menu → a real Order lands (gate ON = PENDING/OPEN, gate OFF = marched/SENT)."""

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


async def _enable(http, h, *, requires_confirmation: bool):
    res = await http.put(
        "/api/v1/self-order/settings",
        json={"enabled": True, "requires_confirmation": requires_confirmation},
        headers=h,
    )
    assert res.status_code == 200, res.text


async def test_settings_default_off_and_toggle(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    got = await http.get("/api/v1/self-order/settings", headers=h)
    assert got.status_code == 200, got.text
    # Default: autopedido apagado, gate ON (paridad + rollout seguro).
    assert got.json() == {
        "enabled": False,
        "requires_confirmation": True,
        "prepay_required": False,
        "mode": "READ_ONLY",
    }


async def test_gate_on_leaves_order_pending(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=True)
    token = await _qr_token(http, h, 5)

    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 2}]},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "OPEN"  # PENDING, sin marchar → el mozo confirma
    assert body["requires_confirmation"] is True
    assert body["order_id"]


async def test_gate_off_auto_marches_to_kitchen(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=False)
    token = await _qr_token(http, h, 6)

    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "SENT"  # auto-marchado al KDS
    assert res.json()["requires_confirmation"] is False


async def test_disabled_self_order_is_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    token = await _qr_token(http, h, 7)  # settings default = disabled

    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},
    )
    assert res.status_code == 409
    assert res.json()["code"] == "self_order_disabled"


async def test_unavailable_product_is_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=True)
    # 86'd it.
    await http.put(
        f"/api/v1/products/{pid}/availability", json={"available_today": False}, headers=h
    )
    token = await _qr_token(http, h, 8)

    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},
    )
    assert res.status_code == 409
    assert res.json()["code"] == "product_unavailable"


async def _me(http, h) -> str:
    return (await http.get("/api/v1/me", headers=h)).json()["user_id"]


async def _qr_order(http, h, number, pid) -> str:
    token = await _qr_token(http, h, number)
    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},
    )
    assert res.status_code == 200, res.text
    return res.json()["order_id"]


async def test_pending_qr_tray_and_confirm_assigns(client):
    """Fase 2: un pedido QR OPEN aparece en la bandeja; al confirmarlo (marchar),
    la mesa queda a nombre del que confirma y sale de la bandeja."""
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    owner_id = await _me(http, h)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=True)
    order_id = await _qr_order(http, h, 9, pid)

    tray = await http.get("/api/v1/orders/pending-qr", headers=h)
    assert tray.status_code == 200, tray.text
    assert [o["id"] for o in tray.json()] == [order_id]
    assert tray.json()[0]["source"] == "CUSTOMER_QR"
    assert tray.json()[0]["waiter_id"] == "00000000-0000-0000-0000-000000000000"

    sent = await http.post(f"/api/v1/orders/{order_id}/send", headers=h)
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "SENT"
    # estampado en la orden → el aviso "listo" (Fase 1) le llega al confirmante
    assert sent.json()["waiter_id"] == owner_id

    assert (await http.get("/api/v1/orders/pending-qr", headers=h)).json() == []


async def test_claim_orphan_qr_table(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    owner_id = await _me(http, h)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=True)
    order_id = await _qr_order(http, h, 10, pid)

    claimed = await http.post(f"/api/v1/orders/{order_id}/claim", headers=h)
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["waiter_id"] == owner_id


async def test_manager_assign_waiter(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    owner_id = await _me(http, h)
    pid = await _product(http, h, "Pizza", 1200000)
    await _enable(http, h, requires_confirmation=True)
    order_id = await _qr_order(http, h, 11, pid)

    res = await http.post(
        f"/api/v1/orders/{order_id}/assign-waiter",
        json={"waiter_id": owner_id},
        headers=h,
    )
    assert res.status_code == 200, res.text
    assert res.json()["waiter_id"] == owner_id


async def test_order_endpoint_rejects_bad_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": "garbage.deadbeef", "lines": [{"product_id": "x", "quantity": 1}]},
    )
    assert res.status_code == 401
    assert res.json()["code"] == "invalid_table_qr_token"

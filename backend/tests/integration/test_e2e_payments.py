"""End-to-end cobro (ingresos) + egresos flow over HTTP against the real app + DB."""

from __future__ import annotations

from httpx import AsyncClient

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _make_order(http: AsyncClient, headers: dict) -> str:
    """Create a product + table + order with one item (total 300000)."""
    product = await http.post(
        "/api/v1/products",
        json={"name": "Milanesa", "price_amount": 150000, "category": None},
        headers=headers,
    )
    table = await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=headers)
    order = await http.post(
        "/api/v1/orders", json={"table_id": table.json()["table_id"]}, headers=headers
    )
    order_id = order.json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product.json()["product_id"], "quantity": 2},
        headers=headers,
    )
    return order_id


async def test_cobro_conciliacion_marca_pagada(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)

    # Pago parcial: la comanda NO queda pagada.
    r1 = await http.post(
        f"/api/v1/orders/{order_id}/payments", json={"method": "CASH", "amount": 100000}, headers=h
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["status"] == "CONFIRMED"
    assert r1.json()["direction"] == "INFLOW"
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] != "PAID"

    # Pago que completa el total → comanda PAID.
    r2 = await http.post(
        f"/api/v1/orders/{order_id}/payments", json={"method": "QR", "amount": 200000}, headers=h
    )
    assert r2.status_code == 201
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"

    pays = await http.get(f"/api/v1/orders/{order_id}/payments", headers=h)
    assert len(pays.json()) == 2


async def test_monto_invalido_rechazado(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)
    bad = await http.post(
        f"/api/v1/orders/{order_id}/payments", json={"method": "CASH", "amount": 0}, headers=h
    )
    assert bad.status_code == 422


async def test_egreso_y_listado(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    expense = await http.post(
        "/api/v1/expenses",
        json={
            "method": "TRANSFER",
            "amount": 500000,
            "category": "Proveedores",
            "counterparty": "Frigorífico Sur",
            "description": "Carne",
        },
        headers=h,
    )
    assert expense.status_code == 201, expense.text
    assert expense.json()["direction"] == "OUTFLOW"
    listed = await http.get("/api/v1/expenses", headers=h)
    assert len(listed.json()) == 1


async def test_aislamiento_rls(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await http.post(
        "/api/v1/expenses",
        json={
            "method": "CASH",
            "amount": 1000,
            "category": None,
            "counterparty": None,
            "description": None,
        },
        headers=_auth(t1),
    )
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    assert (await http.get("/api/v1/expenses", headers=_auth(t2))).json() == []

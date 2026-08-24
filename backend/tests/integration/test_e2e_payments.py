"""End-to-end cobro (ingresos) + egresos flow over HTTP against the real app + DB."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

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


async def test_payment_records_tax_and_finance_reports_it(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="ustax", email="o@ustax.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)  # subtotal 300000

    # Cobro con sales tax incluido en amount (subtotal 300000 + tax 32250).
    r = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 332250, "tax": 32250},
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["tax_amount"] == 32250

    # El reporte de tax cobrado lo suma (lo que se le debe al fisco).
    tc = await http.get("/api/v1/finance/tax-collected", headers=h)
    assert tc.status_code == 200, tc.text
    assert tc.json()["amount"] == 32250


async def test_payment_tax_cannot_exceed_amount(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="ustax2", email="o@ustax2.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)
    r = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 100000, "tax": 200000},
        headers=h,
    )
    assert r.status_code >= 400, r.text


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


async def test_registerpayment_stamps_commission(client, admin_engine: AsyncEngine):
    """Comisiones (slice A): con una tasa por método cargada, el cobro congela
    fee_amount + net_amount; un método sin tasa → fee 0 y net == amount (paridad)."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # Tasa CARD 3% (300 bps) para el tenant único; CASH sin tasa.
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO payment_fee_rates (tenant_id, method, fee_bps) "
                "SELECT id, 'CARD', 300 FROM tenants"
            )
        )
    order_id = await _make_order(http, h)  # total 300000
    r_card = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CARD", "amount": 200000},
        headers=h,
    )
    assert r_card.status_code == 201, r_card.text
    r_cash = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 100000},
        headers=h,
    )
    assert r_cash.status_code == 201, r_cash.text
    async with admin_engine.begin() as conn:
        rows = (
            await conn.execute(
                text("SELECT method, amount, fee_amount, net_amount FROM payments")
            )
        ).all()
    by_method = {m: (amt, fee, net) for m, amt, fee, net in rows}
    # CARD 200000 @ 3% → fee 6000, net 194000.
    assert by_method["CARD"] == (200000, 6000, 194000)
    # CASH sin tasa → fee 0, net == amount (paridad).
    assert by_method["CASH"] == (100000, 0, 100000)

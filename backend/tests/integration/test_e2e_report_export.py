"""End-to-end: CSV exports for the accountant (ventas / gastos / libro IVA)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth, _make_order


async def test_export_sales_and_expenses_csv(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="rep", email="o@rep.com")
    h = _auth(tokens)

    # A paid order → sale_facts (total 300000).
    order_id = await _make_order(http, h)
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    # An itemized expense.
    await http.post(
        "/api/v1/expenses",
        json={
            "method": "CASH",
            "amount": 50000,
            "category": "Proveedores",
            "description": "Verdulería",
        },
        headers=h,
    )

    sales = await http.get("/api/v1/reports/export/sales.csv", headers=h)
    assert sales.status_code == 200, sales.text
    assert sales.headers["content-type"].startswith("text/csv")
    assert 'filename="ventas-por-dia.csv"' in sales.headers["content-disposition"]
    body = sales.content.decode("utf-8")
    assert body.startswith("﻿")  # BOM
    assert "Fecha;Órdenes;Unidades;Ventas;Costo de insumos" in body
    assert "3000,00" in body  # 300000 minor → AR decimal

    expenses = await http.get("/api/v1/reports/export/expenses.csv", headers=h)
    assert expenses.status_code == 200, expenses.text
    ebody = expenses.content.decode("utf-8")
    assert "Fecha;Rubro;Medio;Monto;Detalle" in ebody
    assert "Proveedores" in ebody
    assert "500,00" in ebody  # 50000 minor
    assert "Verdulería" in ebody


async def test_export_vat_sales_csv_headers_when_empty(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="iva", email="o@iva.com")
    h = _auth(tokens)
    r = await http.get("/api/v1/reports/export/vat_sales.csv", headers=h)
    assert r.status_code == 200, r.text
    assert 'filename="libro-iva-ventas.csv"' in r.headers["content-disposition"]
    body = r.content.decode("utf-8")
    assert "Tipo;Punto de venta;Número" in body  # cabecera del libro IVA

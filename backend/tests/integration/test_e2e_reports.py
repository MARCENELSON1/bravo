"""End-to-end dashboard summary over HTTP + DB."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth, _make_order


async def test_dashboard_summary(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    # Empty tenant → all zeros.
    empty = (await http.get("/api/v1/reports/dashboard", headers=h)).json()
    assert empty["sales"] == 0 and empty["active_orders"] == 0 and empty["paid_orders"] == 0

    # One order (total 300000) fully paid + one egreso.
    order_id = await _make_order(http, h)
    await http.post(
        f"/api/v1/orders/{order_id}/payments", json={"method": "CASH", "amount": 300000}, headers=h
    )
    await http.post(
        "/api/v1/expenses",
        json={
            "method": "CASH",
            "amount": 50000,
            "category": None,
            "counterparty": None,
            "description": None,
        },
        headers=h,
    )

    s = (await http.get("/api/v1/reports/dashboard", headers=h)).json()
    assert s["sales"] == 300000
    assert s["expenses"] == 50000
    assert s["net"] == 250000
    assert s["paid_orders"] == 1
    assert s["active_orders"] == 0  # the only order is PAID
    assert s["avg_ticket"] == 300000
    assert s["payment_count"] == 1
    assert s["currency"] == "ARS"

    # Guarda C: ventana por fecha — un 'from' futuro excluye los cobros/egresos.
    future = (
        await http.get("/api/v1/reports/dashboard?from=2999-01-01T00:00:00Z", headers=h)
    ).json()
    assert future["sales"] == 0
    assert future["expenses"] == 0
    assert future["net"] == 0
    assert future["payment_count"] == 0
    # Un 'from' pasado incluye todo (igual que sin filtro).
    past = (
        await http.get("/api/v1/reports/dashboard?from=2000-01-01T00:00:00Z", headers=h)
    ).json()
    assert past["sales"] == 300000
    assert past["expenses"] == 50000

"""End-to-end propinas por mozo: cobro con propina → reporte (ganado) →
liquidación como egreso → reporte (pagado/pendiente). Sobre HTTP + DB real."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _order_paid_with_tip(http, h, *, amount: int, tip: int) -> None:
    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Lomo", "price_amount": amount, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 1},
        headers=h,
    )
    paid = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": amount, "tip": tip},
        headers=h,
    )
    assert paid.status_code == 201, paid.text


async def test_tips_report_and_payout_flow(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com"))

    await _order_paid_with_tip(http, h, amount=30000, tip=5000)

    # Reporte: la propina se atribuye al mozo (el que abrió la orden = owner).
    report = (await http.get("/api/v1/cashier/tips/report", headers=h)).json()
    assert report["earned_total"] == 5000
    assert report["paid_total"] == 0
    assert report["pending_total"] == 5000
    assert len(report["rows"]) == 1
    row = report["rows"][0]
    assert row["earned"] == 5000 and row["paid"] == 0 and row["pending"] == 5000
    assert row["waiter_email"] == "owner@resto.com"
    waiter_id = row["waiter_id"]

    # Liquidar 5000 al mozo → egreso 'Propinas' a su nombre.
    payout = await http.post(
        "/api/v1/cashier/tips/payout",
        json={"waiter_id": waiter_id, "amount": 5000},
        headers=h,
    )
    assert payout.status_code == 200, payout.text
    body = payout.json()
    assert body["direction"] == "OUTFLOW"
    assert body["category"] == "Propinas"
    assert body["counterparty"] == waiter_id
    assert body["amount"] == 5000

    # Reporte de nuevo: ya quedó pagado, saldo 0.
    after = (await http.get("/api/v1/cashier/tips/report", headers=h)).json()
    assert after["earned_total"] == 5000
    assert after["paid_total"] == 5000
    assert after["pending_total"] == 0
    assert after["rows"][0]["pending"] == 0

    # El egreso aparece en la lista de egresos.
    expenses = (await http.get("/api/v1/expenses", headers=h)).json()
    assert any(e["category"] == "Propinas" and e["amount"] == 5000 for e in expenses)


async def test_tips_payout_to_unknown_waiter_404(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.post(
        "/api/v1/cashier/tips/payout",
        json={"waiter_id": missing, "amount": 1000},
        headers=h,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "user_not_found"


async def test_tips_report_empty_when_no_tips(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    report = (await http.get("/api/v1/cashier/tips/report", headers=h)).json()
    assert report["rows"] == []
    assert report["earned_total"] == 0 and report["pending_total"] == 0

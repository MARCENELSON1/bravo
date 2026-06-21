"""End-to-end staff report: hours + overtime crossed with PAID-order sales."""

from __future__ import annotations

from httpx import AsyncClient

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _make_paid_order(http: AsyncClient, headers: dict) -> None:
    """Product 150000 x2 = 300000, paid in full → order PAID, attributed to the
    logged-in user as waiter."""
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
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=headers,
    )


async def test_staff_report_hours_overtime_and_sales(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    # A shift adjusted to a known 9h span → 540 worked, 60 overtime (vs 480).
    cin = await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    await http.post("/api/v1/timeclock/clock-out", headers=h)
    await http.patch(
        f"/api/v1/timeclock/shifts/{cin.json()['id']}",
        json={
            "clock_in_at": "2026-06-21T09:00:00+00:00",
            "clock_out_at": "2026-06-21T18:00:00+00:00",
        },
        headers=h,
    )

    await _make_paid_order(http, h)

    report = await http.get("/api/v1/reports/staff", headers=h)
    assert report.status_code == 200, report.text
    rows = report.json()["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["email"] == "o@resto.com"
    assert row["worked_minutes"] == 540
    assert row["overtime_minutes"] == 60
    assert row["tables_served"] == 1
    assert row["sales_amount"] == 300000


async def test_staff_report_rls_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await _make_paid_order(http, _auth(t1))
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    assert (await http.get("/api/v1/reports/staff", headers=_auth(t2))).json()["rows"] == []

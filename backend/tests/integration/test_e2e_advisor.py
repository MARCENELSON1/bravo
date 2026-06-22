"""End-to-end advisor (Fase 9): deterministic KPIs + insights over the canonical
model, and the cost-profile settings. The LLM layer is off (template narrator)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _sell_with_recipe(http, h, *, price: int, qty: int, food_cost_per_kg: int) -> None:
    """A product with a 0.2 kg recipe, sold and paid in full → projected facts."""
    product = await http.post(
        "/api/v1/products",
        json={"name": "Milanesa", "price_amount": price, "category": "Cocina"},
        headers=h,
    )
    pid = product.json()["product_id"]
    ing = await http.post(
        "/api/v1/inventory/ingredients",
        json={
            "name": "Carne",
            "unit": "KG",
            "min_qty": 0,
            "unit_cost_amount": food_cost_per_kg,
            "stock_qty": 100000,
        },
        headers=h,
    )
    iid = ing.json()["ingredient_id"]
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},
        headers=h,
    )
    table = await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    order = await http.post(
        "/api/v1/orders", json={"table_id": table.json()["table_id"]}, headers=h
    )
    oid = order.json()["order_id"]
    await http.post(
        f"/api/v1/orders/{oid}/items",
        json={"product_id": pid, "quantity": qty},
        headers=h,
    )
    pay = await http.post(
        f"/api/v1/orders/{oid}/payments",
        json={"method": "CASH", "amount": price * qty},
        headers=h,
    )
    assert pay.status_code == 201, pay.text


def _codes(report: dict) -> set[str]:
    return {i["code"] for i in report["insights"]}


async def test_report_from_canonical_without_settings(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # 2 × 150000 = 300000 ventas ; food cost 0.2kg × 80000 × 2 = 32000
    await _sell_with_recipe(http, h, price=150000, qty=2, food_cost_per_kg=80000)

    report = (await http.get("/api/v1/advisor/report", headers=h)).json()
    kpis = report["kpis"]
    assert kpis["sales_amount"] == 300000
    assert kpis["food_cost_amount"] == 32000
    assert kpis["food_cost_ratio_bps"] == 1067  # ~10.7%
    assert kpis["configured"] is False
    assert report["llm_enabled"] is False
    assert "configure_costs" in _codes(report)
    assert "healthy_food_cost" in _codes(report)  # below the default 30% target


async def test_settings_roundtrip(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))

    put = await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 9_000_000,
            "monthly_other_fixed_costs": 6_000_000,
            "target_food_cost_bps": 3200,
        },
        headers=h,
    )
    assert put.status_code == 200, put.text
    assert put.json()["configured"] is True

    got = (await http.get("/api/v1/advisor/settings", headers=h)).json()
    assert got["monthly_labor_cost"] == 9_000_000
    assert got["monthly_other_fixed_costs"] == 6_000_000
    assert got["target_food_cost_bps"] == 3200
    assert got["configured"] is True
    assert got["currency"] == "ARS"


async def test_report_with_settings_detects_loss(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=2, food_cost_per_kg=80000)
    # Fixed costs dwarf the day's sales → losing money regardless of proration.
    await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 90_000_000,
            "monthly_other_fixed_costs": 60_000_000,
            "target_food_cost_bps": 3000,
        },
        headers=h,
    )

    report = (await http.get("/api/v1/advisor/report", headers=h)).json()
    kpis = report["kpis"]
    assert kpis["configured"] is True
    assert kpis["labor_cost_amount"] > 0
    assert kpis["break_even_amount"] > 0
    assert kpis["net_margin_amount"] < 0
    assert "losing_money" in _codes(report)


async def test_advisor_rls_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await _sell_with_recipe(http, _auth(t1), price=150000, qty=2, food_cost_per_kg=80000)

    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    report = (await http.get("/api/v1/advisor/report", headers=_auth(t2))).json()
    assert report["kpis"]["sales_amount"] == 0
    assert report["kpis"]["orders_count"] == 0

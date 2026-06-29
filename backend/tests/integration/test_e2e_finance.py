"""End-to-end Pantalla Finanzas: cobro con receta → /finance/overview con los
KPIs vitales, comparativo, diagnósticos y margen por producto."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _sell_with_recipe(http, h, *, price: int, qty: int, cost_per_kg: int) -> None:
    pid = (
        await http.post(
            "/api/v1/products", json={"name": "Milanesa", "price_amount": price}, headers=h
        )
    ).json()["product_id"]
    iid = (
        await http.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": "Carne", "unit": "KG", "min_qty": 0,
                "unit_cost_amount": cost_per_kg, "stock_qty": 100000,
            },
            headers=h,
        )
    ).json()["ingredient_id"]
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},  # 0.2 KG por unidad
        headers=h,
    )
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": pid, "quantity": qty},
        headers=h,
    )
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": price * qty},
        headers=h,
    )


async def test_finance_overview_returns_vital_kpis(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # Ventas 300000; food cost 80000×0.2×2 = 32000 → food cost ratio ≈ 10.67%.
    await _sell_with_recipe(http, h, price=150000, qty=2, cost_per_kg=80000)

    resp = await http.get("/api/v1/finance/overview", headers=h)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    kpis = {k["key"]: k for k in body["kpis"]}

    assert kpis["food_cost"]["kind"] == "ratio"
    assert kpis["food_cost"]["value"] == 1067  # round(32000/300000*10000)
    assert kpis["food_cost"]["status"] == "healthy"
    assert "prime_cost" in kpis and "labor_cost" in kpis and "net_margin" in kpis

    # Margen de contribución por producto (en pesos): 300000 − 32000.
    assert len(body["product_margins"]) == 1
    assert body["product_margins"][0]["margin_amount"] == 268000

    # Diagnósticos narrados presentes (food cost sano dispara healthy_food_cost).
    assert isinstance(body["diagnostics"], list)


async def test_finance_overview_empty_tenant_is_zeroed(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    body = (await http.get("/api/v1/finance/overview", headers=h)).json()
    kpis = {k["key"]: k for k in body["kpis"]}
    assert kpis["food_cost"]["value"] == 0  # sin ventas → 0, no crashea
    assert body["product_margins"] == []


async def test_finance_overview_requires_auth(client):
    http, _ = client
    # El endpoint exige OWNER/MANAGER; sin token → 401/403.
    nope = await http.get("/api/v1/finance/overview")
    assert nope.status_code in (401, 403)

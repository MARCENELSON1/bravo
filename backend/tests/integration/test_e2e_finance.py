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


async def test_finance_overview_revpash_and_turnover(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # Cargar asientos + horario (RevPASH) por la config del Asesor.
    settings = await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 0, "monthly_other_fixed_costs": 0,
            "target_food_cost_bps": 3000, "seats": 40, "daily_open_minutes": 480,
        },
        headers=h,
    )
    assert settings.status_code == 200, settings.text
    assert settings.json()["seats"] == 40

    await _sell_with_recipe(http, h, price=150000, qty=2, cost_per_kg=80000)

    kpis = {k["key"]: k for k in (await http.get("/api/v1/finance/overview", headers=h)).json()["kpis"]}
    # RevPASH: ventas 300000 / (40 asientos × 8h × días) > 0, en $ por asiento-hora.
    assert kpis["revpash"]["kind"] == "money"
    assert kpis["revpash"]["value"] > 0
    # Rotación presente y no negativa (con 100kg en stock vs 0,4kg vendidos redondea
    # a 0 en el período — el cálculo exacto está en el unit test).
    assert kpis["inventory_turnover"]["kind"] == "turnover"
    assert kpis["inventory_turnover"]["value"] >= 0


async def test_finance_overview_revpash_zero_without_seats(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="bar", email="o@bar.com"))
    await _sell_with_recipe(http, h, price=100000, qty=1, cost_per_kg=50000)
    kpis = {k["key"]: k for k in (await http.get("/api/v1/finance/overview", headers=h)).json()["kpis"]}
    assert kpis["revpash"]["value"] == 0  # sin asientos/horario cargados → 0, no crashea


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


async def test_product_drill_down_lists_sale_lines(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = (
        await http.post(
            "/api/v1/products", json={"name": "Lomo", "price_amount": 100000}, headers=h
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
        json={"product_id": pid, "quantity": 3},
        headers=h,
    )
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )

    detail = await http.get(f"/api/v1/finance/products/{pid}", headers=h)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["units_sold"] == 3
    assert body["sales_amount"] == 300000
    assert body["margin_amount"] == 300000  # sin receta → food cost 0
    assert len(body["lines"]) == 1
    assert body["lines"][0]["order_id"] == order_id


async def _expense(http, h, *, category: str, amount: int) -> None:
    resp = await http.post(
        "/api/v1/expenses",
        json={"method": "CASH", "category": category, "amount": amount},
        headers=h,
    )
    assert resp.status_code == 201, resp.text


async def test_expense_breakdown_groups_by_category(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _expense(http, h, category="Proveedores", amount=50000)
    await _expense(http, h, category="Proveedores", amount=30000)
    await _expense(http, h, category="Servicios", amount=18000)

    body = (await http.get("/api/v1/finance/expenses/breakdown", headers=h)).json()
    rows = {r["category"]: r for r in body["rows"]}
    assert rows["Proveedores"]["amount"] == 80000  # se suman las dos
    assert rows["Servicios"]["amount"] == 18000
    assert body["total"] == 98000
    assert body["rows"][0]["category"] == "Proveedores"  # ordenado por amount desc


async def test_recent_movements_lists_cobros_and_egresos(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=1, cost_per_kg=50000)  # cobro (IN)
    await _expense(http, h, category="Proveedores", amount=40000)  # egreso (OUT)

    movs = (await http.get("/api/v1/finance/movements", headers=h)).json()
    kinds = {m["kind"] for m in movs}
    assert "IN" in kinds and "OUT" in kinds
    assert any(m["amount"] == 40000 and m["kind"] == "OUT" for m in movs)


async def test_finance_v2_endpoints_rls_isolated(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await _expense(http, _auth(t1), category="Proveedores", amount=99000)
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    body = (await http.get("/api/v1/finance/expenses/breakdown", headers=_auth(t2))).json()
    assert body["total"] == 0 and body["rows"] == []

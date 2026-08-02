"""End-to-end Productos v2 Tanda B: log de precios, precios vs inflación, rotación.

El log de precios y sale_facts viven detrás de RLS; los backdates para simular
historia se hacen con el ``admin_engine`` (bypassea RLS), igual que analytics."""

from __future__ import annotations

from sqlalchemy import text

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _product(http, h, name: str, price: int) -> str:
    resp = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": price, "category": "Cocina"},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["product_id"]


async def _order_with(http, h, product_id: str, quantity: int) -> str:
    table = await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    order = await http.post(
        "/api/v1/orders", json={"table_id": table.json()["table_id"]}, headers=h
    )
    order_id = order.json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": quantity},
        headers=h,
    )
    return order_id


async def _pay(http, h, order_id: str, amount: int) -> None:
    resp = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": amount},
        headers=h,
    )
    assert resp.status_code == 201, resp.text


async def _set_inflation(http, h, bps: int) -> None:
    resp = await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 0,
            "monthly_other_fixed_costs": 0,
            "target_food_cost_bps": 3000,
            "monthly_inflation_bps": bps,
        },
        headers=h,
    )
    assert resp.status_code == 200, resp.text


# --- Log de precios (histórico real, base del simulador) ---------------------


async def test_create_seeds_baseline_price_change(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)

    history = (await http.get(f"/api/v1/products/{pid}/price-history", headers=h)).json()
    assert len(history["changes"]) == 1
    assert history["changes"][0]["old_price_amount"] is None
    assert history["changes"][0]["new_price_amount"] == 150000
    assert history["currency"] == "ARS"


async def test_update_price_logs_change_and_repricess(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)

    resp = await http.put(
        f"/api/v1/products/{pid}/price", json={"price_amount": 180000}, headers=h
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["price_amount"] == 180000

    # El catálogo refleja el nuevo precio.
    products = (await http.get("/api/v1/products", headers=h)).json()
    assert next(p for p in products if p["id"] == pid)["price_amount"] == 180000

    # El log tiene 2 entradas: baseline (old None) + el cambio (old = viejo precio).
    history = (await http.get(f"/api/v1/products/{pid}/price-history", headers=h)).json()
    assert len(history["changes"]) == 2
    assert history["changes"][1]["old_price_amount"] == 150000
    assert history["changes"][1]["new_price_amount"] == 180000


async def test_update_price_noop_is_not_logged(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)

    resp = await http.put(
        f"/api/v1/products/{pid}/price", json={"price_amount": 150000}, headers=h
    )
    assert resp.status_code == 200, resp.text
    history = (await http.get(f"/api/v1/products/{pid}/price-history", headers=h)).json()
    assert len(history["changes"]) == 1  # sin cambio real → no se loguea


# --- Precios vs inflación ("debería estar en $X") ----------------------------


async def test_pricing_flags_lagging_product(client, admin_engine):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 100000)
    await _set_inflation(http, h, 2000)  # 20% mensual

    # Backdate el precio 60 días para simular que quedó rezagado.
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE product_price_changes "
                "SET changed_at = now() - interval '60 days' WHERE product_id = :pid"
            ),
            {"pid": pid},
        )

    pricing = (await http.get("/api/v1/products/pricing", headers=h)).json()
    assert pricing["configured"] is True
    assert pricing["monthly_inflation_bps"] == 2000
    row = next(r for r in pricing["rows"] if r["product_id"] == pid)
    assert row["current_price_amount"] == 100000
    assert row["suggested_price_amount"] == 144000  # 100000 × 1.2^2
    assert row["days_since_change"] == 60
    assert row["lagging"] is True


async def test_pricing_without_inflation_is_not_configured(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _product(http, h, "Milanesa", 100000)

    pricing = (await http.get("/api/v1/products/pricing", headers=h)).json()
    assert pricing["configured"] is False
    assert pricing["rows"][0]["suggested_price_amount"] == 100000
    assert pricing["rows"][0]["lagging"] is False


# --- Rotación por día de semana ----------------------------------------------


async def test_rotation_buckets_sales_by_weekday(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)
    oid = await _order_with(http, h, pid, 2)
    await _pay(http, h, oid, 300000)

    rotation = (await http.get("/api/v1/products/rotation", headers=h)).json()
    assert len(rotation["rows"]) == 7  # Lun..Dom siempre
    active = [r for r in rotation["rows"] if r["units"] > 0]
    assert len(active) == 1  # una sola venta, un solo día
    assert active[0]["units"] == 2
    assert active[0]["sales_amount"] == 300000
    assert active[0]["top_product_name"] == "Milanesa"
    assert sum(r["units"] for r in rotation["rows"]) == 2


# --- Aislamiento multi-tenant ------------------------------------------------


async def test_pricing_and_history_are_tenant_isolated(client):
    http, fake_email = client
    t1 = _auth(await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com"))
    pid = await _product(http, t1, "Milanesa", 100000)

    t2 = _auth(await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com"))
    pricing = (await http.get("/api/v1/products/pricing", headers=t2)).json()
    assert pricing["rows"] == []  # t2 no ve productos de t1

    # t2 tampoco puede leer el histórico de un producto de t1.
    resp = await http.get(f"/api/v1/products/{pid}/price-history", headers=t2)
    assert resp.status_code == 404

"""End-to-end canonical model (Fase 8): sale_facts projection on PAID + KPIs.

The projection write is asserted via the admin engine (bypasses RLS) since the
read API lands in T2; the KPI endpoints are exercised over HTTP."""

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
    return resp.json()["product_id"]


async def _ingredient(http, h, name: str, **overrides) -> str:
    body = {"name": name, "unit": "KG", "min_qty": 0, "unit_cost_amount": 80000, "stock_qty": 5000}
    body.update(overrides)
    resp = await http.post("/api/v1/inventory/ingredients", json=body, headers=h)
    return resp.json()["ingredient_id"]


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


async def _facts(admin_engine, order_id: str) -> tuple[int, int, int | None]:
    """(row_count, total_line_amount, total_food_cost) for an order, via admin."""
    async with admin_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT count(*), coalesce(sum(line_amount),0), sum(food_cost_amount) "
                    "FROM sale_facts WHERE order_id = :oid"
                ),
                {"oid": order_id},
            )
        ).one()
    return int(row[0]), int(row[1]), (int(row[2]) if row[2] is not None else None)


async def test_paid_order_projects_sale_facts(client, admin_engine):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)
    order_id = await _order_with(http, h, pid, 2)

    await _pay(http, h, order_id, 300000)  # full → PAID
    count, total, food_cost = await _facts(admin_engine, order_id)
    assert count == 1  # one order line
    assert total == 300000  # 2 × 150000
    assert food_cost is None  # no recipe → no COGS snapshot


async def test_projection_is_idempotent(client, admin_engine):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)
    order_id = await _order_with(http, h, pid, 2)

    await _pay(http, h, order_id, 300000)
    # A second payment on an already-PAID order must NOT re-project.
    await _pay(http, h, order_id, 100000)
    count, _total, _fc = await _facts(admin_engine, order_id)
    assert count == 1


async def test_food_cost_snapshot_when_recipe(client, admin_engine):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Milanesa", 150000)
    iid = await _ingredient(http, h, "Carne", unit_cost_amount=80000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},  # 0.2 kg/unidad
        headers=h,
    )
    order_id = await _order_with(http, h, pid, 2)

    await _pay(http, h, order_id, 300000)
    count, total, food_cost = await _facts(admin_engine, order_id)
    assert count == 1
    assert total == 300000
    assert food_cost == 32000  # (80000 × 0.2) × 2

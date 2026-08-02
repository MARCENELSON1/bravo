"""End-to-end Productos v2 Tanda C (wiring): una preparación (receta madre)
alimenta el food cost de un plato al proyectar la venta.

La preparación y el ítem de receta que la referencia se insertan con el
``admin_engine`` (bypassea RLS) porque el CRUD de preparaciones es la tanda
siguiente; acá se valida que el MOTOR (projection) resuelve el costo multinivel."""

from __future__ import annotations

from uuid import uuid4

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


async def _ingredient(http, h, name: str, unit_cost_amount: int) -> str:
    resp = await http.post(
        "/api/v1/inventory/ingredients",
        json={
            "name": name,
            "unit": "KG",
            "min_qty": 0,
            "unit_cost_amount": unit_cost_amount,
            "stock_qty": 100000,
        },
        headers=h,
    )
    return resp.json()["ingredient_id"]


async def _order_and_pay(http, h, product_id: str, qty: int, amount: int) -> str:
    table = await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    order = await http.post(
        "/api/v1/orders", json={"table_id": table.json()["table_id"]}, headers=h
    )
    order_id = order.json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": qty},
        headers=h,
    )
    resp = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": amount},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    return order_id


async def test_preparation_feeds_product_food_cost_on_projection(client, admin_engine):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    pid = await _product(http, h, "Napolitana", 300000)
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)  # 1000/u base

    # Salsa fileto: 2.0 de tomate por tanda (= 2000 la tanda), rinde 2.0 → 1000/u.
    prep_id, ri_id, pi_id = str(uuid4()), str(uuid4()), str(uuid4())
    async with admin_engine.begin() as conn:
        tid = (
            await conn.execute(
                text("SELECT tenant_id FROM products WHERE id = :pid"), {"pid": pid}
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO preparations (id, tenant_id, name, yield_qty) "
                "VALUES (:id, :tid, 'Salsa fileto', 2000)"
            ),
            {"id": prep_id, "tid": tid},
        )
        await conn.execute(
            text(
                "INSERT INTO preparation_items (id, tenant_id, preparation_id, ingredient_id, qty) "
                "VALUES (:id, :tid, :pid, :ing, 2000)"
            ),
            {"id": pi_id, "tid": tid, "pid": prep_id, "ing": tomate},
        )
        await conn.execute(
            text("INSERT INTO recipes (product_id, tenant_id) VALUES (:pid, :tid)"),
            {"pid": pid, "tid": tid},
        )
        # La receta del plato usa 0.15 (150 milésimas) de la salsa → 150.
        await conn.execute(
            text(
                "INSERT INTO recipe_items (id, tenant_id, product_id, preparation_id, qty) "
                "VALUES (:id, :tid, :pid, :prep, 150)"
            ),
            {"id": ri_id, "tid": tid, "pid": pid, "prep": prep_id},
        )

    order_id = await _order_and_pay(http, h, pid, qty=1, amount=300000)

    async with admin_engine.connect() as conn:
        food_cost = (
            await conn.execute(
                text("SELECT food_cost_amount FROM sale_facts WHERE order_id = :oid"),
                {"oid": order_id},
            )
        ).scalar_one()
    assert food_cost == 150  # 0.15 × 1000 (costo/u de la salsa) × 1 unidad

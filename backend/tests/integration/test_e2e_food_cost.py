"""End-to-end stock consumption on sale (comanda → PAID) + food cost."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _ingredient(http, h, name: str, **overrides) -> str:
    body = {
        "name": name,
        "unit": "KG",
        "min_qty": 1000,
        "unit_cost_amount": 80000,
        "stock_qty": 5000,
    }
    body.update(overrides)
    resp = await http.post("/api/v1/inventory/ingredients", json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()["ingredient_id"]


async def _product(http, h, name: str, price: int) -> str:
    resp = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": price, "category": None},
        headers=h,
    )
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


async def _stock_of(http, h, ingredient_id: str) -> int:
    rows = (await http.get("/api/v1/inventory/ingredients", headers=h)).json()
    return next(r["stock_qty"] for r in rows if r["id"] == ingredient_id)


async def test_paid_order_discounts_stock_and_raises_alert(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    iid = await _ingredient(http, h, "Carne", stock_qty=1100, min_qty=1000)
    pid = await _product(http, h, "Milanesa", 150000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},
        headers=h,
    )
    order_id = await _order_with(http, h, pid, 2)  # consumes 2 × 200 = 400

    pay = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    assert pay.status_code == 201, pay.text
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"

    assert await _stock_of(http, h, iid) == 700  # 1100 - 400
    low = await http.get("/api/v1/inventory/low-stock", headers=h)
    assert any(r["id"] == iid for r in low.json())  # 700 <= 1000 → alert


async def test_resettle_does_not_double_discount(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    iid = await _ingredient(http, h, "Carne", stock_qty=5000)
    pid = await _product(http, h, "Milanesa", 150000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},
        headers=h,
    )
    order_id = await _order_with(http, h, pid, 2)  # consumes 400

    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    assert await _stock_of(http, h, iid) == 4600  # 5000 - 400

    # A second payment on an already-PAID order must NOT discount again.
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 100000},
        headers=h,
    )
    assert await _stock_of(http, h, iid) == 4600  # unchanged → idempotent


async def test_sale_without_recipe_leaves_stock(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    iid = await _ingredient(http, h, "Carne", stock_qty=5000)
    pid = await _product(http, h, "Gaseosa", 100000)  # no recipe set
    order_id = await _order_with(http, h, pid, 3)

    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"
    assert await _stock_of(http, h, iid) == 5000  # untouched


async def test_food_cost_and_margin(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    iid = await _ingredient(http, h, "Carne", unit_cost_amount=80000)  # 80000 / kg
    pid = await _product(http, h, "Milanesa", 150000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},  # 0.2 kg
        headers=h,
    )

    report = await http.get("/api/v1/inventory/food-cost", headers=h)
    assert report.status_code == 200, report.text
    rows = report.json()["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["product_id"] == pid
    assert row["food_cost_amount"] == 16000  # 80000 × 0.2
    assert row["price_amount"] == 150000
    assert row["margin_amount"] == 134000  # 150000 − 16000
    assert row["food_cost_ratio_bps"] == 1067  # round(16000 / 150000 × 10000)

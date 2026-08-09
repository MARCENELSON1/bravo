"""End-to-end Productos v2 Tanda C (capa usable): CRUD de preparaciones vía API,
receta que referencia una preparación, y **propagación** del costo multinivel al
food cost cuando cambia el costo de un insumo base."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


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


async def _product(http, h, name: str, price: int) -> str:
    resp = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": price, "category": "Cocina"},
        headers=h,
    )
    return resp.json()["product_id"]


async def _food_cost(http, h, product_id: str) -> int:
    report = (await http.get("/api/v1/inventory/food-cost", headers=h)).json()
    row = next(r for r in report["rows"] if r["product_id"] == product_id)
    return row["food_cost_amount"]


async def test_preparation_food_cost_propagates_on_ingredient_cost_change(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)  # 1000/u

    # Salsa fileto: 2.0 de tomate por tanda, rinde 2.0 → 1000/u.
    prep = await http.post(
        "/api/v1/inventory/preparations",
        json={
            "name": "Salsa fileto",
            "yield_qty": 2000,
            "items": [{"ingredient_id": tomate, "qty": 2000}],
        },
        headers=h,
    )
    assert prep.status_code == 201, prep.text
    salsa = prep.json()["preparation_id"]

    pid = await _product(http, h, "Napolitana", 300000)
    # La receta usa 0.15 de la salsa → food cost 150.
    r = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"preparation_id": salsa, "qty": 150}]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert await _food_cost(http, h, pid) == 150

    # Sube el costo del insumo base (compra a 2000/u) → se propaga: 0.15 × 2000 = 300.
    await http.post(
        f"/api/v1/inventory/ingredients/{tomate}/purchase",
        json={"qty": 1000, "unit_cost_amount": 2000},
        headers=h,
    )
    assert await _food_cost(http, h, pid) == 300


async def test_cycle_is_rejected_on_save(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)
    a = (
        await http.post(
            "/api/v1/inventory/preparations",
            json={
                "name": "A",
                "yield_qty": 1000,
                "items": [{"ingredient_id": tomate, "qty": 1000}],
            },
            headers=h,
        )
    ).json()["preparation_id"]
    b = (
        await http.post(
            "/api/v1/inventory/preparations",
            json={"name": "B", "yield_qty": 1000, "items": [{"preparation_id": a, "qty": 100}]},
            headers=h,
        )
    ).json()["preparation_id"]

    # A pasa a depender de B, que depende de A → ciclo → 409.
    resp = await http.put(
        f"/api/v1/inventory/preparations/{a}",
        json={"name": "A", "yield_qty": 1000, "items": [{"preparation_id": b, "qty": 100}]},
        headers=h,
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "recipe_cycle"


async def test_component_must_be_ingredient_xor_preparation(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)
    resp = await http.post(
        "/api/v1/inventory/preparations",
        json={
            "name": "Mala",
            "yield_qty": 1000,
            "items": [{"ingredient_id": tomate, "preparation_id": tomate, "qty": 100}],
        },
        headers=h,
    )
    assert resp.status_code == 422, resp.text


async def test_list_and_delete_preparations(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)
    salsa = (
        await http.post(
            "/api/v1/inventory/preparations",
            json={
                "name": "Salsa",
                "yield_qty": 1000,
                "items": [{"ingredient_id": tomate, "qty": 500}],
            },
            headers=h,
        )
    ).json()["preparation_id"]

    listed = (await http.get("/api/v1/inventory/preparations", headers=h)).json()
    assert [p["id"] for p in listed] == [salsa]
    assert listed[0]["yield_qty"] == 1000
    assert listed[0]["items"][0]["ingredient_id"] == tomate

    resp = await http.delete(f"/api/v1/inventory/preparations/{salsa}", headers=h)
    assert resp.status_code == 204
    assert (await http.get("/api/v1/inventory/preparations", headers=h)).json() == []


async def test_usage_count_reflects_products_using_the_preparation(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    tomate = await _ingredient(http, h, "Tomate", unit_cost_amount=1000)
    salsa = (
        await http.post(
            "/api/v1/inventory/preparations",
            json={
                "name": "Salsa",
                "yield_qty": 2000,
                "items": [{"ingredient_id": tomate, "qty": 2000}],
            },
            headers=h,
        )
    ).json()["preparation_id"]

    # Sin platos que la usen todavía.
    listed = (await http.get("/api/v1/inventory/preparations", headers=h)).json()
    assert listed[0]["used_in_products"] == 0

    pid = await _product(http, h, "Napolitana", 300000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"preparation_id": salsa, "qty": 150}]},
        headers=h,
    )

    listed = (await http.get("/api/v1/inventory/preparations", headers=h)).json()
    assert listed[0]["used_in_products"] == 1


async def test_preparations_are_tenant_isolated(client):
    http, fake_email = client
    t1 = _auth(await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com"))
    tomate = await _ingredient(http, t1, "Tomate", unit_cost_amount=1000)
    await http.post(
        "/api/v1/inventory/preparations",
        json={"name": "Salsa", "yield_qty": 1000, "items": [{"ingredient_id": tomate, "qty": 500}]},
        headers=t1,
    )

    t2 = _auth(await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com"))
    assert (await http.get("/api/v1/inventory/preparations", headers=t2)).json() == []


async def test_yield_pct_propagates_to_food_cost(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    carne = await _ingredient(http, h, "Carne", unit_cost_amount=1000)  # 1000/u, yield 100%
    pid = await _product(http, h, "Bife", 300000)
    r = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": carne, "qty": 200}]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert await _food_cost(http, h, pid) == 200  # 0.2 × 1000

    # Merma 80% (yield 8000) → costo efectivo 1250/u → food cost 250.
    patch = await http.patch(
        f"/api/v1/inventory/ingredients/{carne}",
        json={"yield_pct": 8000},
        headers=h,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["yield_pct"] == 8000
    assert await _food_cost(http, h, pid) == 250

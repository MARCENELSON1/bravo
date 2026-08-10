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
    return (await _food_cost_row(http, h, product_id))["food_cost_amount"]


async def _food_cost_row(http, h, product_id: str) -> dict:
    report = (await http.get("/api/v1/inventory/food-cost", headers=h)).json()
    return next(r for r in report["rows"] if r["product_id"] == product_id)


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


async def test_cost_includes_tax_nets_per_ingredient(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    # IVA global 21%.
    await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 0,
            "monthly_other_fixed_costs": 0,
            "target_food_cost_bps": 3000,
            "default_vat_bps": 2100,
        },
        headers=h,
    )

    async def _ing(name: str, cost: int, includes_tax: bool) -> str:
        resp = await http.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": name,
                "unit": "KG",
                "min_qty": 0,
                "unit_cost_amount": cost,
                "stock_qty": 100000,
                "price_includes_tax": includes_tax,
            },
            headers=h,
        )
        return resp.json()["ingredient_id"]

    con_iva = await _ing("ConIVA", 1210, True)  # 1210 con IVA → neto 1000
    sin_iva = await _ing("SinIVA", 1210, False)  # monotributo → queda 1210
    pa = await _product(http, h, "PlatoA", 300000)
    pb = await _product(http, h, "PlatoB", 300000)
    await http.put(
        f"/api/v1/products/{pa}/recipe",
        json={"items": [{"ingredient_id": con_iva, "qty": 1000}]},
        headers=h,
    )
    await http.put(
        f"/api/v1/products/{pb}/recipe",
        json={"items": [{"ingredient_id": sin_iva, "qty": 1000}]},
        headers=h,
    )
    # El food cost se MUESTRA bruto (COGS real) en ambos: 1210 (consistente con
    # Asesor/Finanzas). El neteo per-insumo se refleja en el MARGEN.
    row_a = await _food_cost_row(http, h, pa)
    row_b = await _food_cost_row(http, h, pb)
    assert row_a["food_cost_amount"] == 1210
    assert row_b["food_cost_amount"] == 1210
    # A netea su costo (incluye IVA → neto 1000), B no (monotributo → 1210). El
    # precio neto es igual para ambos → el margen de A supera al de B en 210.
    assert row_a["margin_amount"] - row_b["margin_amount"] == 210
    assert row_a["food_cost_ratio_bps"] < row_b["food_cost_ratio_bps"]


async def _sell(http, h, product_id: str, *, price: int, qty: int) -> None:
    """Vende un producto (mesa → orden → ítem → cobro) para que proyecte a
    sale_facts con el food cost bruto y neto snapshoteados."""
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]
    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": qty},
        headers=h,
    )
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": price * qty},
        headers=h,
    )


async def test_advisor_aggregate_uses_per_ingredient_net(client):
    """Solución 1 (F3): el agregado del Asesor/Finanzas usa el food neto
    per-insumo snapshoteado — NO re-netea el bruto global (que trataría al insumo
    monotributo como si incluyera IVA). Consistente con Productos per-plato."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await http.put(
        "/api/v1/advisor/settings",
        json={
            "monthly_labor_cost": 0,
            "monthly_other_fixed_costs": 0,
            "target_food_cost_bps": 3000,
            "default_vat_bps": 2100,
        },
        headers=h,
    )

    async def _ing(name: str, cost: int, includes_tax: bool) -> str:
        resp = await http.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": name,
                "unit": "KG",
                "min_qty": 0,
                "unit_cost_amount": cost,
                "stock_qty": 100000,
                "price_includes_tax": includes_tax,
            },
            headers=h,
        )
        return resp.json()["ingredient_id"]

    con_iva = await _ing("ConIVA", 121000, True)  # incluye IVA → neto 100000
    sin_iva = await _ing("SinIVA", 90000, False)  # monotributo → queda 90000
    pa = await _product(http, h, "PlatoA", 605000)  # neto de venta 500000
    pb = await _product(http, h, "PlatoB", 605000)
    for pid, ing in ((pa, con_iva), (pb, sin_iva)):
        await http.put(
            f"/api/v1/products/{pid}/recipe",
            json={"items": [{"ingredient_id": ing, "qty": 1000}]},
            headers=h,
        )
    await _sell(http, h, pa, price=605000, qty=1)
    await _sell(http, h, pb, price=605000, qty=1)

    body = (await http.get("/api/v1/finance/overview", headers=h)).json()
    kpis = {k["key"]: k for k in body["kpis"]}
    # food neto per-insumo = 100000 + 90000 = 190000; ventas netas = 1000000.
    # ratio = 190000/1000000 = 1900 bps. El re-neteo global (BUG F3) daría 1744.
    assert kpis["food_cost"]["value"] == 1900
    # Margen por producto (ProductPerformance): ventas netas − food neto per-plato.
    margins = {m["product_name"]: m["margin_amount"] for m in body["product_margins"]}
    assert margins["PlatoA"] == 400000  # 500000 − 100000
    assert margins["PlatoB"] == 410000  # 500000 − 90000 (monotributo, no netea)


async def test_recipe_unit_converts_food_cost(client):
    """Fase 2C: costo cargado por LITRO, receta en ML → food cost exacto."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    r = await http.post(
        "/api/v1/inventory/ingredients",
        json={
            "name": "Aceite",
            "unit": "L",
            "min_qty": 0,
            "unit_cost_amount": 200000,  # ARS 2000 por litro
            "stock_qty": 1_000_000,
            "recipe_unit": "ML",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    aceite = r.json()["ingredient_id"]
    pid = await _product(http, h, "Fritura", 300000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": aceite, "qty": 250_000}]},  # 250 ml
        headers=h,
    )
    # 2000/L × 0,25 L = 500,00 = 50000 c (sin conversión daría un disparate).
    assert await _food_cost(http, h, pid) == 50000


async def test_incompatible_recipe_unit_rejected(client):
    """Fase 2C: recipe_unit fuera de la familia del insumo → 422."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    r = await http.post(
        "/api/v1/inventory/ingredients",
        json={
            "name": "Aceite",
            "unit": "L",
            "min_qty": 0,
            "unit_cost_amount": 200000,
            "stock_qty": 0,
            "recipe_unit": "G",  # masa para un insumo de volumen
        },
        headers=h,
    )
    assert r.status_code == 422, r.text
    assert "incompatible_units" in r.text


async def test_recipe_version_increments_on_save(client):
    """Fase 2D: cada guardado de receta incrementa la versión (nueva → v1)."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    ing = await _ingredient(http, h, "Carne", unit_cost_amount=1000)
    pid = await _product(http, h, "Plato", 150000)
    r1 = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": ing, "qty": 100}]},
        headers=h,
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["version"] == 1
    r2 = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": ing, "qty": 200}]},
        headers=h,
    )
    assert r2.json()["version"] == 2
    got = await http.get(f"/api/v1/products/{pid}/recipe", headers=h)
    assert got.json()["version"] == 2


async def test_replacement_cost_is_last_purchase_with_history(client):
    """Fase 2D T1.4: el costo de reposición = último precio (ya default); una compra
    más cara sube el food cost, y queda en el histórico del insumo."""
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    ing = await _ingredient(http, h, "Carne", unit_cost_amount=100000)  # 1000/kg
    pid = await _product(http, h, "Plato", 300000)
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": ing, "qty": 1000}]},  # 1,0 unidad base
        headers=h,
    )
    assert await _food_cost(http, h, pid) == 100000
    # Compra a mayor precio → último costo (reposición) → food cost sube.
    r = await http.post(
        f"/api/v1/inventory/ingredients/{ing}/purchase",
        json={"qty": 1000, "unit_cost_amount": 200000},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert await _food_cost(http, h, pid) == 200000
    # El histórico registra la compra (la creación del insumo no es una compra).
    hist = (
        await http.get(f"/api/v1/inventory/ingredients/{ing}/cost-history", headers=h)
    ).json()
    assert [p["unit_cost_amount"] for p in hist] == [200000]

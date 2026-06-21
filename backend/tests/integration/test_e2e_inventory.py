"""End-to-end inventory (stock / suppliers / recipe) flow over HTTP + DB."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _new_ingredient(http, h, **overrides) -> dict:
    body = {
        "name": "Harina",
        "unit": "KG",
        "min_qty": 1000,
        "unit_cost_amount": 50000,
        "stock_qty": 5000,
    }
    body.update(overrides)
    resp = await http.post("/api/v1/inventory/ingredients", json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_and_list_ingredient(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    created = await _new_ingredient(http, h)
    assert "ingredient_id" in created

    listed = await http.get("/api/v1/inventory/ingredients", headers=h)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "Harina"
    assert row["unit"] == "KG"
    assert row["stock_qty"] == 5000
    assert row["unit_cost_amount"] == 50000
    assert row["currency"] == "ARS"
    assert row["is_below_min"] is False


async def test_purchase_raises_stock_and_updates_cost(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    created = await _new_ingredient(http, h)
    iid = created["ingredient_id"]

    purchased = await http.post(
        f"/api/v1/inventory/ingredients/{iid}/purchase",
        json={"qty": 3000, "unit_cost_amount": 60000},
        headers=h,
    )
    assert purchased.status_code == 200, purchased.text
    body = purchased.json()
    assert body["stock_qty"] == 8000  # 5000 + 3000
    assert body["unit_cost_amount"] == 60000  # last-cost policy


async def test_waste_lowers_stock(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    iid = (await _new_ingredient(http, h))["ingredient_id"]

    wasted = await http.post(
        f"/api/v1/inventory/ingredients/{iid}/waste",
        json={"qty": 2000, "note": "se cayó"},
        headers=h,
    )
    assert wasted.status_code == 200, wasted.text
    assert wasted.json()["stock_qty"] == 3000  # 5000 - 2000


async def test_low_stock_alert_when_at_or_below_min(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    iid = (await _new_ingredient(http, h, stock_qty=1200, min_qty=1000))["ingredient_id"]

    # Not yet below min.
    assert (await http.get("/api/v1/inventory/low-stock", headers=h)).json() == []

    # Drop to/below the minimum → appears in alerts.
    await http.post(
        f"/api/v1/inventory/ingredients/{iid}/waste", json={"qty": 300}, headers=h
    )
    low = await http.get("/api/v1/inventory/low-stock", headers=h)
    assert low.status_code == 200
    rows = low.json()
    assert len(rows) == 1
    assert rows[0]["id"] == iid
    assert rows[0]["is_below_min"] is True


async def test_create_and_list_supplier(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    created = await http.post(
        "/api/v1/inventory/suppliers",
        json={"name": "Molino SA", "contact": "ventas@molino.com"},
        headers=h,
    )
    assert created.status_code == 201, created.text

    listed = await http.get("/api/v1/inventory/suppliers", headers=h)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["name"] == "Molino SA"
    assert rows[0]["contact"] == "ventas@molino.com"


async def test_set_and_get_recipe_opt_in(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    product = await http.post(
        "/api/v1/products",
        json={"name": "Pan", "price_amount": 100000, "category": "Panadería"},
        headers=h,
    )
    pid = product.json()["product_id"]
    iid = (await _new_ingredient(http, h))["ingredient_id"]

    # No recipe yet.
    none_yet = await http.get(f"/api/v1/products/{pid}/recipe", headers=h)
    assert none_yet.status_code == 200
    assert none_yet.json()["has_recipe"] is False
    assert none_yet.json()["items"] == []

    # Set the recipe.
    put = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},
        headers=h,
    )
    assert put.status_code == 200, put.text
    assert put.json()["has_recipe"] is True

    got = await http.get(f"/api/v1/products/{pid}/recipe", headers=h)
    assert got.json()["has_recipe"] is True
    assert got.json()["items"] == [{"ingredient_id": iid, "qty": 200}]


async def test_set_recipe_unknown_ingredient_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    product = await http.post(
        "/api/v1/products",
        json={"name": "Pan", "price_amount": 100000, "category": None},
        headers=h,
    )
    pid = product.json()["product_id"]
    bad = await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": "00000000-0000-0000-0000-000000000000", "qty": 1}]},
        headers=h,
    )
    assert bad.status_code == 404
    assert bad.json()["code"] == "ingredient_not_found"


async def test_update_ingredient_fields(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    iid = (await _new_ingredient(http, h))["ingredient_id"]

    patched = await http.patch(
        f"/api/v1/inventory/ingredients/{iid}",
        json={"name": "Harina 0000", "min_qty": 2000, "active": False},
        headers=h,
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["name"] == "Harina 0000"
    assert body["min_qty"] == 2000
    assert body["active"] is False


async def test_update_unknown_ingredient_404(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.patch(
        f"/api/v1/inventory/ingredients/{missing}", json={"name": "X"}, headers=h
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "ingredient_not_found"


async def test_purchase_unknown_ingredient_404(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.post(
        f"/api/v1/inventory/ingredients/{missing}/purchase",
        json={"qty": 100, "unit_cost_amount": 100},
        headers=h,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "ingredient_not_found"


async def test_waste_unknown_ingredient_404(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.post(
        f"/api/v1/inventory/ingredients/{missing}/waste", json={"qty": 100}, headers=h
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "ingredient_not_found"


async def test_set_recipe_unknown_product_404(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.put(
        f"/api/v1/products/{missing}/recipe", json={"items": []}, headers=h
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "product_not_found"


async def test_inventory_rls_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await _new_ingredient(http, _auth(t1))
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    assert (await http.get("/api/v1/inventory/ingredients", headers=_auth(t2))).json() == []

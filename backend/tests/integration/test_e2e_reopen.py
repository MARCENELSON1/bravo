"""End-to-end reabrir comanda (Tanda E 2b): pagar → reabrir revierte venta y
stock de forma idempotente → re-cobrar re-proyecta. Sobre HTTP + DB real."""

from __future__ import annotations

from httpx import AsyncClient

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _stock(http: AsyncClient, h: dict, ingredient_id: str) -> int:
    rows = (await http.get("/api/v1/inventory/ingredients", headers=h)).json()
    return next(r for r in rows if r["id"] == ingredient_id)["stock_qty"]


async def _sales(http: AsyncClient, h: dict) -> int:
    return (await http.get("/api/v1/analytics/revenue", headers=h)).json()["sales_amount"]


async def _setup(http: AsyncClient, h: dict) -> tuple[str, str]:
    """A product with a recipe (200 per unit) + an order of qty 2 (total 300000,
    consumes 400 of the ingredient). Returns (order_id, ingredient_id)."""
    pid = (
        await http.post(
            "/api/v1/products",
            json={"name": "Milanesa", "price_amount": 150000, "category": None},
            headers=h,
        )
    ).json()["product_id"]
    iid = (
        await http.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": "Carne",
                "unit": "KG",
                "min_qty": 0,
                "unit_cost_amount": 80000,
                "stock_qty": 5000,
            },
            headers=h,
        )
    ).json()["ingredient_id"]
    await http.put(
        f"/api/v1/products/{pid}/recipe",
        json={"items": [{"ingredient_id": iid, "qty": 200}]},
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
        json={"product_id": pid, "quantity": 2},
        headers=h,
    )
    return order_id, iid


async def _pay(http: AsyncClient, h: dict, order_id: str) -> None:
    resp = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    assert resp.status_code == 201, resp.text


async def test_reopen_reverses_sale_and_stock_then_repay_reprojects(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    order_id, iid = await _setup(http, h)

    # Pay → PAID, stock discounted (5000 - 2*200), revenue projected.
    await _pay(http, h, order_id)
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"
    assert await _stock(http, h, iid) == 4600
    assert await _sales(http, h) == 300000

    # Reopen → not PAID anymore, stock credited back, facts gone.
    reopened = await http.post(f"/api/v1/orders/{order_id}/reopen", headers=h)
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["status"] == "OPEN"  # items never marched → all PENDING
    assert await _stock(http, h, iid) == 5000
    assert await _sales(http, h) == 0

    # Reopen again (already active) → idempotent no-op: no double stock credit.
    again = await http.post(f"/api/v1/orders/{order_id}/reopen", headers=h)
    assert again.status_code == 200
    assert again.json()["status"] == "OPEN"
    assert await _stock(http, h, iid) == 5000

    # Re-pay → re-consumes and re-projects from scratch (guards reset).
    await _pay(http, h, order_id)
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "PAID"
    assert await _stock(http, h, iid) == 4600
    assert await _sales(http, h) == 300000


async def test_reopen_unknown_order_404(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    missing = "00000000-0000-0000-0000-000000000000"
    resp = await http.post(f"/api/v1/orders/{missing}/reopen", headers=h)
    assert resp.status_code == 404
    assert resp.json()["code"] == "order_not_found"


async def test_reopen_unpaid_order_is_noop(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    order_id, _ = await _setup(http, h)  # never paid → still OPEN
    resp = await http.post(f"/api/v1/orders/{order_id}/reopen", headers=h)
    assert resp.status_code == 200
    assert resp.json()["status"] == "OPEN"

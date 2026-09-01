"""End-to-end product enrichment (Carta QR F2 Tanda A): a product carries a photo,
a description and a daily-availability flag ('86'd'), all surfaced on the QR menu."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_create_with_enrichment_and_toggle_availability(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    created = await http.post(
        "/api/v1/products",
        json={
            "name": "Milanesa",
            "price_amount": 850000,
            "category": "Platos",
            "image_url": "https://cdn.example.com/mila.jpg",
            "description": "Con puré y huevo.",
        },
        headers=h,
    )
    assert created.status_code == 201, created.text
    product_id = created.json()["product_id"]

    # Catalog exposes the enrichment; a new product is available by default.
    listing = (await http.get("/api/v1/products", headers=h)).json()
    row = next(p for p in listing if p["id"] == product_id)
    assert row["image_url"] == "https://cdn.example.com/mila.jpg"
    assert row["description"] == "Con puré y huevo."
    assert row["available_today"] is True

    # '86'd' toggle flips availability without deactivating the product.
    toggled = await http.put(
        f"/api/v1/products/{product_id}/availability",
        json={"available_today": False},
        headers=h,
    )
    assert toggled.status_code == 200, toggled.text
    assert toggled.json()["available_today"] is False
    assert toggled.json()["active"] is True


async def test_public_menu_carries_enrichment(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    await http.post(
        "/api/v1/products",
        json={
            "name": "Flan",
            "price_amount": 300000,
            "category": "Postres",
            "image_url": "https://cdn.example.com/flan.jpg",
            "description": "Con dulce de leche.",
        },
        headers=h,
    )
    table = await http.post("/api/v1/tables", json={"number": 4, "name": None}, headers=h)
    table_id = table.json()["table_id"]
    token = (await http.get(f"/api/v1/tables/{table_id}/qr", headers=h)).json()["token"]

    menu = (await http.get("/api/v1/public/menu", params={"token": token})).json()
    item = menu["categories"][0]["items"][0]
    assert item["image_url"] == "https://cdn.example.com/flan.jpg"
    assert item["description"] == "Con dulce de leche."
    assert item["available_today"] is True

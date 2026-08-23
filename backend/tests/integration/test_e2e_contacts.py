"""End-to-end CRM: bitácora de contacto + loop de resultado (contactó→volvió→$)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _make_order


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_contact_log_and_result_loop(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="loop", email="o@loop.com")
    h = _auth(tokens)

    cid = (
        await http.post("/api/v1/customers", json={"name": "En Riesgo"}, headers=h)
    ).json()["id"]

    # Marcar contactado (tras escribirle por WhatsApp).
    logged = await http.post(
        f"/api/v1/customers/{cid}/contact", json={"reason": "en_riesgo"}, headers=h
    )
    assert logged.status_code == 204, logged.text

    # Aparece en los contactados recientes (para no re-sugerirlo).
    recent = (await http.get("/api/v1/customers/contacts?days=7", headers=h)).json()
    assert cid in recent["customer_ids"]

    # Loop: contactado 1, todavía no volvió.
    r0 = (await http.get("/api/v1/customers/contact-result?days=30", headers=h)).json()
    assert r0["contacted"] == 1
    assert r0["returned"] == 0
    assert r0["revenue"] == 0

    # Volvió: una comanda pagada DESPUÉS del contacto, atribuida al cliente.
    order_id = await _make_order(http, h)  # 300000
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    await http.put(f"/api/v1/orders/{order_id}/customer", json={"customer_id": cid}, headers=h)

    r1 = (await http.get("/api/v1/customers/contact-result?days=30", headers=h)).json()
    assert r1["contacted"] == 1
    assert r1["returned"] == 1
    assert r1["revenue"] == 300000


async def test_contact_requires_existing_customer(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="loop2", email="o@loop2.com")
    h = _auth(tokens)
    missing = await http.post(
        "/api/v1/customers/00000000-0000-0000-0000-000000000000/contact",
        json={"reason": "manual"},
        headers=h,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "customer_not_found"

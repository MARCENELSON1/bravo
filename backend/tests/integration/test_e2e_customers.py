"""End-to-end CRM: alta / búsqueda / edición / borrado de clientes."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _make_order


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_customer_purchase_history(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="hist", email="o@hist.com")
    h = _auth(tokens)

    cid = (
        await http.post("/api/v1/customers", json={"name": "Cliente Fiel"}, headers=h)
    ).json()["id"]

    # Sin comandas atribuidas → historial en cero (nada se infla).
    empty = (await http.get(f"/api/v1/customers/{cid}/history", headers=h)).json()
    assert empty == {
        "customer_id": cid,
        "currency": "ARS",
        "visits": 0,
        "total_spent": 0,
        "last_visit_at": None,
    }

    # Una comanda pagada (total 300000), atribuida al cliente tras cobrar.
    order_id = await _make_order(http, h)
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    assigned = await http.put(
        f"/api/v1/orders/{order_id}/customer", json={"customer_id": cid}, headers=h
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["customer_id"] == cid

    hist = (await http.get(f"/api/v1/customers/{cid}/history", headers=h)).json()
    assert hist["visits"] == 1
    assert hist["total_spent"] == 300000
    assert hist["last_visit_at"] is not None

    # Desatribuir (customer_id=null) → vuelve a cero.
    await http.put(
        f"/api/v1/orders/{order_id}/customer", json={"customer_id": None}, headers=h
    )
    back = (await http.get(f"/api/v1/customers/{cid}/history", headers=h)).json()
    assert back["visits"] == 0
    assert back["total_spent"] == 0


async def test_customer_crud_and_search(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="crm", email="o@crm.com")
    h = _auth(tokens)

    assert (await http.get("/api/v1/customers", headers=h)).json() == []

    # Alta: el teléfono se normaliza a dígitos (para wa.me).
    created = await http.post(
        "/api/v1/customers",
        json={"name": "Juan Pérez", "phone": "+54 9 11 2345-6789", "email": "juan@mail.com"},
        headers=h,
    )
    assert created.status_code == 201, created.text
    cid = created.json()["id"]
    assert created.json()["phone"] == "5491123456789"
    assert created.json()["no_contactar"] is False

    await http.post("/api/v1/customers", json={"name": "Ana Gómez"}, headers=h)

    # Lista ordenada por nombre.
    listed = (await http.get("/api/v1/customers", headers=h)).json()
    assert [c["name"] for c in listed] == ["Ana Gómez", "Juan Pérez"]

    # Búsqueda por nombre y por teléfono.
    by_name = (await http.get("/api/v1/customers?search=juan", headers=h)).json()
    assert [c["name"] for c in by_name] == ["Juan Pérez"]
    by_phone = (await http.get("/api/v1/customers?search=112345", headers=h)).json()
    assert [c["id"] for c in by_phone] == [cid]

    # Edición: opt-out de contacto.
    updated = await http.put(
        f"/api/v1/customers/{cid}",
        json={"name": "Juan Pérez", "phone": "1122223333", "no_contactar": True},
        headers=h,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["no_contactar"] is True
    assert updated.json()["phone"] == "1122223333"

    # Ficha.
    got = await http.get(f"/api/v1/customers/{cid}", headers=h)
    assert got.status_code == 200
    assert got.json()["email"] is None  # se limpió al no mandarlo en el update

    # Borrado.
    assert (await http.delete(f"/api/v1/customers/{cid}", headers=h)).status_code == 204
    remaining = (await http.get("/api/v1/customers", headers=h)).json()
    assert [c["name"] for c in remaining] == ["Ana Gómez"]


async def test_customer_not_found(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="crm2", email="o@crm2.com")
    h = _auth(tokens)
    missing = await http.get(
        "/api/v1/customers/00000000-0000-0000-0000-000000000000", headers=h
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "customer_not_found"

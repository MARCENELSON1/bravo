"""E2e del panel de plataforma: gateo por super-admin (flag en el usuario, leído
de la DB) + CRUD del catálogo global de planes."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth


async def _make_admin(admin_engine: AsyncEngine, email: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET platform_admin = true WHERE email = :e"), {"e": email}
        )


async def test_platform_plans_crud_gated_by_super_admin(client, admin_engine: AsyncEngine):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="plat", email="o@plat.com")
    h = _auth(tokens)

    # Sin el flag → /access dice false y /plans da 403.
    acc = await http.get("/api/v1/platform/access", headers=h)
    assert acc.status_code == 200 and acc.json() == {"platform_admin": False}
    denied = await http.get("/api/v1/platform/plans", headers=h)
    assert denied.status_code == 403, denied.text

    # Se promueve a super-admin (el token no cambia; el flag se lee de la DB).
    await _make_admin(admin_engine, "o@plat.com")
    acc2 = await http.get("/api/v1/platform/access", headers=h)
    assert acc2.json() == {"platform_admin": True}

    # Catálogo de features + planes vacíos.
    feats = await http.get("/api/v1/platform/features", headers=h)
    assert feats.status_code == 200, feats.text
    keys = {f["key"] for f in feats.json()}
    assert "copilot" in keys and "crm" in keys
    assert (await http.get("/api/v1/platform/plans", headers=h)).json() == []

    # Crear un plan.
    created = await http.post(
        "/api/v1/platform/plans",
        json={
            "tier": "PRO",
            "region": "INTL",
            "amount": 4900,
            "currency": "USD",
            "features": ["copilot", "advisor"],
        },
        headers=h,
    )
    assert created.status_code == 200, created.text
    plan_id = created.json()["id"]
    assert created.json()["amount"] == 4900
    assert sorted(created.json()["features"]) == ["advisor", "copilot"]

    listed = await http.get("/api/v1/platform/plans", headers=h)
    assert [p["id"] for p in listed.json()] == [plan_id]

    # Actualizar (mismo id) el precio.
    updated = await http.post(
        "/api/v1/platform/plans",
        json={
            "id": plan_id,
            "tier": "PRO",
            "region": "INTL",
            "amount": 5900,
            "currency": "USD",
            "features": ["copilot"],
        },
        headers=h,
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == 5900
    assert (await http.get("/api/v1/platform/plans", headers=h)).json()[0]["amount"] == 5900

    # Feature inválida → 422.
    bad = await http.post(
        "/api/v1/platform/plans",
        json={
            "tier": "BASIC",
            "region": "AR",
            "amount": 100,
            "currency": "ARS",
            "features": ["nope"],
        },
        headers=h,
    )
    assert bad.status_code == 422, bad.text
    assert bad.json()["code"] == "invalid_plan_feature"

    # Borrar.
    dele = await http.delete(f"/api/v1/platform/plans/{plan_id}", headers=h)
    assert dele.status_code == 204, dele.text
    assert (await http.get("/api/v1/platform/plans", headers=h)).json() == []

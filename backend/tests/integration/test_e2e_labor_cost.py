"""E2E Tanda D Finanzas: valor/hora por empleado → labor real en el Asesor."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _insert_closed_shift(
    admin_engine, *, tenant_id: str, user_id: str, hours: float
) -> None:
    now = datetime.now(timezone.utc)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO shifts (id, tenant_id, user_id, clock_in_at, clock_out_at,"
                " status, source) VALUES (:id, :tid, :uid, :cin, :cout, 'CLOSED', 'MANAGER')"
            ),
            {
                "id": str(uuid.uuid4()),
                "tid": tenant_id,
                "uid": user_id,
                "cin": now - timedelta(hours=hours),
                "cout": now,
            },
        )


async def test_hourly_rate_feeds_real_labor_cost(client, admin_engine):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    me = (await http.get("/api/v1/me", headers=h)).json()

    # Rate: $2.000/h → 200000 minor units. 4h fichadas → labor 800000.
    rate = await http.put(
        f"/api/v1/users/{me['user_id']}/hourly-rate",
        json={"hourly_rate_amount": 200000},
        headers=h,
    )
    assert rate.status_code == 200, rate.text
    assert rate.json()["hourly_rate_amount"] == 200000

    await _insert_closed_shift(
        admin_engine, tenant_id=me["tenant_id"], user_id=me["user_id"], hours=4
    )

    report = (await http.get("/api/v1/advisor/report", headers=h)).json()
    assert report["kpis"]["labor_cost_amount"] == 4 * 200000

    # El staff report expone el rate para editarlo desde la gestión de equipo.
    staff = (await http.get("/api/v1/reports/staff", headers=h)).json()
    row = next(r for r in staff["rows"] if r["user_id"] == me["user_id"])
    assert row["hourly_rate_amount"] == 200000

    # Borrar el rate (null) → vuelve el fallback (sin settings cargados: labor 0).
    cleared = await http.put(
        f"/api/v1/users/{me['user_id']}/hourly-rate",
        json={"hourly_rate_amount": None},
        headers=h,
    )
    assert cleared.status_code == 200
    report2 = (await http.get("/api/v1/advisor/report", headers=h)).json()
    assert report2["kpis"]["labor_cost_amount"] == 0


async def test_hourly_rate_requires_manager(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    other = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    me = (await http.get("/api/v1/me", headers=_auth(tokens))).json()

    # Un tenant no puede setear el rate de un usuario de OTRO tenant (404 por scope).
    resp = await http.put(
        f"/api/v1/users/{me['user_id']}/hourly-rate",
        json={"hourly_rate_amount": 100000},
        headers=_auth(other),
    )
    assert resp.status_code == 404

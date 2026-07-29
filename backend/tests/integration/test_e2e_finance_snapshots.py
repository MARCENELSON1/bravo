"""E2E Tanda F: la capa de snapshots da el MISMO overview que el cálculo live
(paridad), se mantiene incremental en cada cobro, y el rebuild reconstruye igual."""

from __future__ import annotations

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_finance import _auth, _sell_with_recipe


@pytest_asyncio.fixture
async def snapshot_app(clean_tables):
    """App donde se puede alternar el modo de lectura de Finanzas (live/snapshot)."""
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    transport = ASGITransport(app=app)

    def set_mode(mode: str) -> None:
        container.config.override(
            providers.Object(Settings(finance_snapshots_read=mode))
        )

    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, set_mode
    finally:
        container.email_sender.reset_override()
        container.config.reset_override()
        await container.db().dispose()


async def _overview(http, h) -> dict:
    body = (await http.get("/api/v1/finance/overview", headers=h)).json()
    return {k["key"]: k["value"] for k in body["kpis"]}


async def test_snapshot_mode_matches_live_incrementally(snapshot_app):
    http, fake_email, set_mode = snapshot_app
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=2, cost_per_kg=80000)

    set_mode("live")
    live = await _overview(http, h)
    set_mode("snapshot")  # sin rebuild: el snapshot ya se mantuvo incremental
    snap = await _overview(http, h)

    assert snap == live  # paridad total de los KPIs
    assert live["food_cost"] > 0  # había ventas: no es un empate trivial en 0


async def test_new_sale_updates_snapshot_without_rebuild(snapshot_app):
    http, fake_email, set_mode = snapshot_app
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=2, cost_per_kg=80000)

    set_mode("snapshot")
    before = await _overview(http, h)
    # Un cobro nuevo (el projector actualiza el snapshot del día) se refleja al toque.
    await _sell_with_recipe(http, h, price=100000, qty=1, cost_per_kg=50000)
    after = await _overview(http, h)
    assert after["gross_margin"] > before["gross_margin"]


async def test_rebuild_reconstructs_matching_snapshots(snapshot_app):
    http, fake_email, set_mode = snapshot_app
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _sell_with_recipe(http, h, price=150000, qty=2, cost_per_kg=80000)

    set_mode("live")
    live = await _overview(http, h)

    rebuild = await http.post("/api/v1/finance/snapshots/rebuild", headers=h)
    assert rebuild.status_code == 200, rebuild.text
    assert rebuild.json()["days"] == 1  # una jornada con ventas

    set_mode("snapshot")
    assert await _overview(http, h) == live  # rebuild da paridad

    # Rebuild idempotente: correrlo otra vez no duplica ni cambia el resultado.
    assert (await http.post("/api/v1/finance/snapshots/rebuild", headers=h)).json()["days"] == 1
    assert await _overview(http, h) == live

"""E2E del caché de diagnósticos del asesor (Fase 9.1 / Pantalla Finanzas Tanda C).

El LLM se "prende" con un synthesizer contador (fake); narrator, read models y el
caché SQL son REALES (Postgres + RLS). Verifica: 2º request sirve del caché sin
re-sintetizar, el rebuild manual purga solo lo del tenant y el próximo request
regenera.
"""

from __future__ import annotations

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.application.advisor.report import GetAdvisorReport
from app.domain.advisor.kpis import AdvisorKpis
from app.domain.advisor.ports import AdvisorSynthesizer, NarratedInsight
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class _CountingSynthesizer(AdvisorSynthesizer):
    def __init__(self) -> None:
        self.calls = 0

    async def synthesize(
        self, kpis: AdvisorKpis, narrated: list[NarratedInsight]
    ) -> str | None:
        self.calls += 1
        return "resumen de prueba"


@pytest_asyncio.fixture
async def advisor_client(clean_tables):
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    synth = _CountingSynthesizer()
    container.email_sender.override(providers.Object(fake_email))
    container.get_advisor_report.override(
        providers.Factory(
            GetAdvisorReport,
            read_model=container.advisor_read_model,
            settings=container.advisor_settings_repository,
            narrator=container.template_narrator,
            synthesizer=synth,
            tenant_context=container.tenant_context,
            llm_enabled=True,
            cache=container.advisor_diagnostics_cache,
        )
    )
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, synth
    finally:
        container.email_sender.reset_override()
        container.get_advisor_report.reset_override()
        await container.db().dispose()


async def test_second_request_serves_from_cache_and_rebuild_regenerates(advisor_client):
    http, fake_email, synth = advisor_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))

    # 1º request: genera y cachea.
    first = await http.get("/api/v1/advisor/report", headers=h)
    assert first.status_code == 200
    assert first.json()["summary"] == "resumen de prueba"
    assert synth.calls == 1

    # 2º request, misma data → cache hit en Postgres: NO se vuelve a sintetizar.
    second = await http.get("/api/v1/advisor/report", headers=h)
    assert second.status_code == 200
    assert second.json()["summary"] == "resumen de prueba"
    assert synth.calls == 1

    # Rebuild manual → purga lo cacheado del tenant.
    rebuild = await http.post("/api/v1/advisor/diagnostics/rebuild", headers=h)
    assert rebuild.status_code == 200
    assert rebuild.json()["purged"] == 1

    # Próximo request regenera.
    third = await http.get("/api/v1/advisor/report", headers=h)
    assert third.status_code == 200
    assert synth.calls == 2


async def test_rebuild_is_tenant_isolated(advisor_client):
    http, fake_email, synth = advisor_client
    h1 = _auth(await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com"))
    h2 = _auth(await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com"))

    # Tenant 1 genera y cachea su diagnóstico.
    assert (await http.get("/api/v1/advisor/report", headers=h1)).status_code == 200

    # El rebuild del tenant 2 no toca el caché del tenant 1 (RLS + filtro explícito).
    rebuild = await http.post("/api/v1/advisor/diagnostics/rebuild", headers=h2)
    assert rebuild.status_code == 200
    assert rebuild.json()["purged"] == 0

    # Tenant 1 sigue sirviendo del caché (no re-sintetiza).
    calls_before = synth.calls
    assert (await http.get("/api/v1/advisor/report", headers=h1)).status_code == 200
    assert synth.calls == calls_before

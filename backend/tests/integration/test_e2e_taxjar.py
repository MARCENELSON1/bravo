"""E2e de la credencial de TaxJar por tenant (conectar/estado/desconectar) y del
drain per-tenant: si el local no conectó su cuenta, el reporte NO se presenta
bajo una cuenta de plataforma — queda fallado y reintentable, sin tocar la red."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from cryptography.fernet import Fernet
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth, _make_order


@pytest_asyncio.fixture
async def taxjar_client(clean_tables: None) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender]]:
    """Como el fixture ``client`` pero con el token_cipher real overrideado por uno
    con clave válida (conectar TaxJar cifra el token)."""
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    container.token_cipher.override(
        providers.Object(FernetTokenCipher(Fernet.generate_key().decode()))
    )
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email
    finally:
        container.email_sender.reset_override()
        container.token_cipher.reset_override()
        await container.db().dispose()


async def test_taxjar_connect_status_disconnect(taxjar_client):
    http, fake_email = taxjar_client
    tokens = await _onboard_verify_login(http, fake_email, slug="tj1", email="o@tj1.com")
    h = _auth(tokens)

    # Arranca desconectado.
    r = await http.get("/api/v1/integrations/taxjar", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["connected"] is False

    # Conecta su cuenta (token propio).
    put = await http.put(
        "/api/v1/integrations/taxjar",
        json={"api_token": "tenant-secret-token", "sandbox": True},
        headers=h,
    )
    assert put.status_code == 204, put.text

    got = await http.get("/api/v1/integrations/taxjar", headers=h)
    assert got.json() == {"connected": True, "sandbox": True}

    # Desconecta.
    dele = await http.delete("/api/v1/integrations/taxjar", headers=h)
    assert dele.status_code == 204, dele.text
    assert (await http.get("/api/v1/integrations/taxjar", headers=h)).json()["connected"] is False


async def test_report_pending_without_connection_fails_safely(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="tj2", email="o@tj2.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)  # subtotal 300000
    # Cobro con sales tax → se encola en el outbox (PENDING).
    pay = await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 332250, "tax": 32250},
        headers=h,
    )
    assert pay.status_code == 201, pay.text

    # Sin cuenta conectada, el drain NO reporta (no hay red): la fila queda fallada.
    run = await http.post("/api/v1/finance/tax/report-pending", headers=h)
    assert run.status_code == 200, run.text
    assert run.json() == {"pending": 1, "sent": 0, "failed": 1}


async def test_report_pending_is_noop_in_ar(client):
    # Paridad: sin sales tax no hay nada encolado → drain all-zeros.
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="tj3", email="o@tj3.com")
    h = _auth(tokens)
    order_id = await _make_order(http, h)
    await http.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"method": "CASH", "amount": 300000},
        headers=h,
    )
    run = await http.post("/api/v1/finance/tax/report-pending", headers=h)
    assert run.status_code == 200, run.text
    assert run.json() == {"pending": 0, "sent": 0, "failed": 0}

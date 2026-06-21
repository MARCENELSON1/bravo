"""End-to-end facturación (con FakeInvoicing): conectar AFIP → cobro → facturar
→ CAE, sobre HTTP + DB. Los tokens se cifran con un Fernet de test."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date

import pytest_asyncio
from cryptography.fernet import Fernet
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.domain.invoice.entities import Invoice
from app.domain.invoice.ports import CaeResult, ElectronicInvoicing
from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth, _make_order

_AFIP = {
    "cuit": "20111111112",
    "certificate": "FAKE-CERT-PEM",
    "private_key": "FAKE-KEY-PEM",
    "point_of_sale": 1,
    "fiscal_condition": "RESPONSABLE_INSCRIPTO",
}


@pytest_asyncio.fixture
async def afip_client(clean_tables: None) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender]]:
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


async def _paid_order(http: AsyncClient, h: dict) -> str:
    order_id = await _make_order(http, h)  # total 300000
    await http.post(
        f"/api/v1/orders/{order_id}/payments", json={"method": "CASH", "amount": 300000}, headers=h
    )
    return order_id


async def test_issue_invoice_for_paid_order(afip_client) -> None:
    http, fake_email = afip_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    assert (await http.put("/api/v1/integrations/afip", json=_AFIP, headers=h)).status_code == 204
    order_id = await _paid_order(http, h)

    inv = await http.post(
        f"/api/v1/orders/{order_id}/invoice",
        json={"doc_type": "CONSUMIDOR_FINAL", "doc_number": "0"},
        headers=h,
    )
    assert inv.status_code == 201, inv.text
    body = inv.json()
    assert body["status"] == "AUTHORIZED"
    assert body["type"] == "FACTURA_B"  # emisor RI → consumidor final
    assert body["cae"] and body["number"] == 1
    assert body["total"] == 300000
    assert body["net"] + body["vat"] == 300000  # IVA incluido
    assert body["net"] == 247934  # round(300000 / 1.21)

    # Idempotente: refacturar la misma comanda devuelve el mismo comprobante.
    again = await http.post(
        f"/api/v1/orders/{order_id}/invoice", json={"doc_type": "CONSUMIDOR_FINAL"}, headers=h
    )
    assert again.json()["id"] == body["id"]

    listed = await http.get("/api/v1/invoices", headers=h)
    assert len(listed.json()) == 1


async def test_invoice_requires_paid_order(afip_client) -> None:
    http, fake_email = afip_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    await http.put("/api/v1/integrations/afip", json=_AFIP, headers=h)
    order_id = await _make_order(http, h)  # not paid

    bad = await http.post(
        f"/api/v1/orders/{order_id}/invoice", json={"doc_type": "CONSUMIDOR_FINAL"}, headers=h
    )
    assert bad.status_code == 409
    assert bad.json()["code"] == "order_not_invoiceable"


async def test_invoice_requires_afip_connected(afip_client) -> None:
    http, fake_email = afip_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    order_id = await _paid_order(http, h)  # AFIP NOT connected

    bad = await http.post(
        f"/api/v1/orders/{order_id}/invoice", json={"doc_type": "CONSUMIDOR_FINAL"}, headers=h
    )
    assert bad.status_code == 409
    assert bad.json()["code"] == "tax_gateway_not_connected"


class _RejectThenAuthorize(ElectronicInvoicing):
    """Rejects the first authorize() (e.g. AFIP observation) then approves —
    exercises the reissue-after-reject path."""

    def __init__(self) -> None:
        self.calls = 0

    async def authorize(self, *, invoice: Invoice) -> CaeResult:
        self.calls += 1
        if self.calls == 1:
            return CaeResult(False, None, None, None, "10016: dato faltante")
        return CaeResult(True, 1, "68000000000001", date(2030, 1, 1), None)


@pytest_asyncio.fixture
async def rejecting_afip_client(
    clean_tables: None,
) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender]]:
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    container.token_cipher.override(
        providers.Object(FernetTokenCipher(Fernet.generate_key().decode()))
    )
    container.invoicing_provider.override(providers.Object(_RejectThenAuthorize()))
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email
    finally:
        container.email_sender.reset_override()
        container.token_cipher.reset_override()
        container.invoicing_provider.reset_override()
        await container.db().dispose()


async def test_reissue_after_reject_keeps_single_invoice(rejecting_afip_client) -> None:
    http, fake_email = rejecting_afip_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    await http.put("/api/v1/integrations/afip", json=_AFIP, headers=h)
    order_id = await _paid_order(http, h)

    first = await http.post(
        f"/api/v1/orders/{order_id}/invoice", json={"doc_type": "CONSUMIDOR_FINAL"}, headers=h
    )
    assert first.status_code == 201
    assert first.json()["status"] == "REJECTED"

    retry = await http.post(
        f"/api/v1/orders/{order_id}/invoice", json={"doc_type": "CONSUMIDOR_FINAL"}, headers=h
    )
    assert retry.status_code == 201
    assert retry.json()["status"] == "AUTHORIZED"

    # Single row per order: get_by_order must not raise MultipleResultsFound.
    got = await http.get(f"/api/v1/orders/{order_id}/invoice", headers=h)
    assert got.status_code == 200
    assert got.json()["status"] == "AUTHORIZED"
    assert len((await http.get("/api/v1/invoices", headers=h)).json()) == 1

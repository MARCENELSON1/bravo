"""e2e del endpoint público de captación de la landing."""

from __future__ import annotations

from dependency_injector import providers

from app.domain.marketing.entities import Lead
from app.domain.marketing.exceptions import LeadNotDelivered
from app.domain.marketing.ports import LeadGateway


class FakeLeadGateway(LeadGateway):
    def __init__(self, fail: bool = False) -> None:
        self.received: list[Lead] = []
        self._fail = fail

    async def submit(self, lead: Lead) -> None:
        if self._fail:
            raise LeadNotDelivered()
        self.received.append(lead)


def _override(http, gateway: FakeLeadGateway):
    container = http._transport.app.state.container
    container.lead_gateway.override(providers.Object(gateway))
    return container


async def test_lead_reaches_the_gateway_without_auth(client) -> None:
    http, _ = client
    gateway = FakeLeadGateway()
    container = _override(http, gateway)
    try:
        res = await http.post(
            "/api/v1/leads",
            json={"email": "due@bar.com", "name": "Ana Gómez", "message": "3 locales"},
        )
        assert res.status_code == 201
        assert res.json()["message"].startswith("¡Listo!")
        assert len(gateway.received) == 1
        assert gateway.received[0].email == "due@bar.com"
        assert gateway.received[0].message == "3 locales"
    finally:
        container.lead_gateway.reset_override()


async def test_invalid_email_is_rejected(client) -> None:
    http, _ = client
    gateway = FakeLeadGateway()
    container = _override(http, gateway)
    try:
        res = await http.post("/api/v1/leads", json={"email": "no-es-mail"})
        assert res.status_code == 400
        # code estable en inglés + message en español, como el resto de la API.
        assert res.json()["code"] == "invalid_lead"
        assert gateway.received == []
    finally:
        container.lead_gateway.reset_override()


async def test_when_the_crm_fails_the_visitor_gets_an_error_not_a_fake_success(client) -> None:
    """La regla del cambio: nunca prometer un contacto que no va a pasar."""
    http, _ = client
    gateway = FakeLeadGateway(fail=True)
    container = _override(http, gateway)
    try:
        res = await http.post("/api/v1/leads", json={"email": "due@bar.com"})
        assert res.status_code >= 400
        assert "¡Listo!" not in res.text
    finally:
        container.lead_gateway.reset_override()

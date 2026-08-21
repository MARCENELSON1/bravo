"""Unit tests del adapter de Twenty (transporte httpx en proceso)."""

from __future__ import annotations

import json

import httpx
import pytest

from app.application.marketing.submit_lead import SubmitLead
from app.domain.marketing.entities import Lead
from app.domain.marketing.exceptions import InvalidLead, LeadNotDelivered
from app.infrastructure.marketing.twenty_lead_gateway import TwentyLeadGateway


def _gateway(handler) -> TwentyLeadGateway:
    return TwentyLeadGateway(
        base_url="https://crm.test/",
        api_key="tw_secret",
        transport=httpx.MockTransport(handler),
    )


async def test_creates_person_with_split_name() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"data": {"createPerson": {"id": "p-1"}}})

    await _gateway(handler).submit(Lead(email="due@bar.com", name="Ana Gómez"))

    assert seen["path"] == "/rest/people"
    assert seen["auth"] == "Bearer tw_secret"
    assert seen["body"]["name"] == {"firstName": "Ana", "lastName": "Gómez"}
    assert seen["body"]["emails"]["primaryEmail"] == "due@bar.com"


async def test_message_becomes_a_note_linked_to_the_person() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/rest/people":
            return httpx.Response(201, json={"data": {"createPerson": {"id": "p-9"}}})
        if request.url.path == "/rest/notes":
            body = json.loads(request.content)
            assert body["bodyV2"]["markdown"] == "Tengo 3 locales"
            return httpx.Response(201, json={"data": {"createNote": {"id": "n-9"}}})
        body = json.loads(request.content)
        # targetPersonId (no personId): con el nombre viejo Twenty devuelve 400.
        assert body["noteId"] == "n-9"
        assert body["targetPersonId"] == "p-9"
        return httpx.Response(201, json={"data": {}})

    await _gateway(handler).submit(Lead(email="a@b.com", message="Tengo 3 locales"))

    assert calls == ["/rest/people", "/rest/notes", "/rest/noteTargets"]


async def test_without_message_it_does_not_touch_notes() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(201, json={"data": {"createPerson": {"id": "p-2"}}})

    await _gateway(handler).submit(Lead(email="a@b.com"))

    assert calls == ["/rest/people"]


async def test_person_failure_raises_so_the_visitor_is_told() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"messages": ["Token invalid."]})

    with pytest.raises(LeadNotDelivered):
        await _gateway(handler).submit(Lead(email="a@b.com"))


async def test_network_error_raises_too() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    with pytest.raises(LeadNotDelivered):
        await _gateway(handler).submit(Lead(email="a@b.com"))


async def test_note_failure_does_not_lose_the_lead() -> None:
    """El contacto ya quedó creado: el mensaje es un extra, no aborta el lead."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/people":
            return httpx.Response(201, json={"data": {"createPerson": {"id": "p-3"}}})
        return httpx.Response(500, text="boom")

    await _gateway(handler).submit(Lead(email="a@b.com", message="hola"))


async def test_use_case_rejects_a_bad_email_before_calling_the_crm() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(201, json={})

    with pytest.raises(InvalidLead):
        await SubmitLead(_gateway(handler)).execute(email="no-es-mail", name=None, message=None)

    assert called is False


async def test_use_case_trims_and_caps_free_text() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/people":
            seen["body"] = json.loads(request.content)
            return httpx.Response(201, json={"data": {"createPerson": {"id": "p-4"}}})
        if request.url.path == "/rest/notes":
            seen["note"] = json.loads(request.content)
            return httpx.Response(201, json={"data": {"createNote": {"id": "n-4"}}})
        return httpx.Response(201, json={"data": {}})

    await SubmitLead(_gateway(handler)).execute(
        email="  a@b.com  ", name="  Ana  ", message="x" * 5000
    )

    assert seen["body"]["emails"]["primaryEmail"] == "a@b.com"
    assert seen["body"]["name"]["firstName"] == "Ana"
    # El texto libre se recorta antes de salir hacia el CRM.
    assert len(seen["note"]["bodyV2"]["markdown"]) == 2000

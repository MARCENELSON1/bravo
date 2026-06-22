"""End-to-end copilot (Fase 11): the LLM is FAKED (no network) and returns a SQL
string; the REAL guardrail + read-only/RLS runner execute it. Verifies the safety
guarantees: tenant isolation by RLS, unsafe queries rejected, disabled by default."""

from __future__ import annotations

import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.application.copilot.ask import AskCopilot
from app.domain.copilot.ports import CopilotLLM, QueryResult
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login


class _FakeCopilotLLM(CopilotLLM):
    def __init__(self) -> None:
        self.sql = "SELECT name FROM products"

    async def to_sql(self, question: str, schema_doc: str) -> str:
        return self.sql

    async def answer(self, question: str, result: QueryResult) -> str:
        return f"Encontré {len(result.rows)} resultados."


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def copilot_client(clean_tables):
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    fake_llm = _FakeCopilotLLM()
    container.email_sender.override(providers.Object(fake_email))
    # Enable the copilot with the fake LLM; the runner stays REAL (RLS applies).
    container.ask_copilot.override(
        providers.Factory(
            AskCopilot,
            llm=fake_llm,
            runner=container.copilot_query_runner,
            tenant_context=container.tenant_context,
            max_rows=200,
            enabled=True,
        )
    )
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email, fake_llm
    finally:
        container.email_sender.reset_override()
        container.ask_copilot.reset_override()
        await container.db().dispose()


async def _product(http, h, name: str) -> None:
    resp = await http.post(
        "/api/v1/products",
        json={"name": name, "price_amount": 100000, "category": None},
        headers=h,
    )
    assert resp.status_code == 201, resp.text


async def test_ask_returns_tenant_rows(copilot_client):
    http, fake_email, fake_llm = copilot_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _product(http, h, "Milanesa")
    fake_llm.sql = "SELECT name FROM products"

    resp = await http.post(
        "/api/v1/copilot/ask", json={"question": "qué productos tengo"}, headers=h
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["columns"] == ["name"]
    assert ["Milanesa"] in body["rows"]
    assert "select" in body["sql"].lower()
    assert body["answer"]
    assert body["llm_enabled"] is True


async def test_rls_isolation_even_without_tenant_filter(copilot_client):
    http, fake_email, fake_llm = copilot_client
    h1 = _auth(await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com"))
    await _product(http, h1, "Milanesa")
    # The SQL has NO tenant filter on purpose — RLS must still scope to tenant2.
    fake_llm.sql = "SELECT name FROM products"
    h2 = _auth(await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com"))

    resp = await http.post("/api/v1/copilot/ask", json={"question": "productos"}, headers=h2)
    assert resp.status_code == 200
    assert resp.json()["rows"] == []  # tenant2 sees none of tenant1's products


async def test_unsafe_query_rejected(copilot_client):
    http, fake_email, fake_llm = copilot_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    fake_llm.sql = "DROP TABLE products"

    resp = await http.post(
        "/api/v1/copilot/ask", json={"question": "borrá todo"}, headers=h
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "unsafe_query"


async def test_select_outside_allowlist_rejected(copilot_client):
    http, fake_email, fake_llm = copilot_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    fake_llm.sql = "SELECT email, password_hash FROM users"

    resp = await http.post(
        "/api/v1/copilot/ask", json={"question": "dame las claves"}, headers=h
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "unsafe_query"


async def test_disabled_by_default(client):
    # Standard fixture → copilot_provider=off → disabled.
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    resp = await http.post("/api/v1/copilot/ask", json={"question": "hola"}, headers=h)
    assert resp.status_code == 409
    assert resp.json()["code"] == "copilot_disabled"

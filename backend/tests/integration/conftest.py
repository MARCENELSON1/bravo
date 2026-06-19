"""DB-backed fixtures for integration/e2e tests.

These talk to a real Postgres (``bravo_dev``). Each test starts from a clean
schema (truncated via an admin connection that bypasses RLS). The app under test
connects with the non-superuser ``bravo_app`` role, so RLS is enforced. Email is
overridden with an in-memory fake to capture the links that flows generate.

Every async engine is created and disposed within the test's own event loop to
avoid asyncpg cross-loop issues.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest_asyncio
from dependency_injector import providers
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tests.fakes import FakeEmailSender

load_dotenv()

_TABLES = [
    "auth_audit",
    "invitations",
    "email_verification_tokens",
    "password_reset_tokens",
    "refresh_tokens",
    "users",
    "tenants",
]


@pytest_asyncio.fixture
async def admin_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(os.environ["ALEMBIC_DATABASE_URL"])
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(admin_engine: AsyncEngine) -> AsyncIterator[None]:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE " + ", ".join(_TABLES) + " RESTART IDENTITY CASCADE")
        )
    yield


@pytest_asyncio.fixture
async def client(clean_tables: None) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender]]:
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http, fake_email
    finally:
        container.email_sender.reset_override()
        await container.db().dispose()

"""Verifies Postgres RLS isolates tenants for the app role (defence net)."""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.context import reset_current_tenant, set_current_tenant
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.user_repo import SqlAlchemyUserRepository


async def _seed_two_tenants(admin_engine: AsyncEngine) -> tuple[str, str]:
    tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:a, 'a', 'A'), (:b, 'b', 'B')"),
            {"a": tenant_a, "b": tenant_b},
        )
        await conn.execute(
            text(
                "INSERT INTO users (id, tenant_id, email, role, email_verified, active, "
                "failed_attempts) VALUES "
                "(:ua, :a, 'a@a.com', 'OWNER', true, true, 0), "
                "(:ub, :b, 'b@b.com', 'OWNER', true, true, 0)"
            ),
            {"ua": str(uuid.uuid4()), "a": tenant_a, "ub": str(uuid.uuid4()), "b": tenant_b},
        )
    return tenant_a, tenant_b


async def test_rls_isolates_users_between_tenants(admin_engine: AsyncEngine):
    tenant_a, tenant_b = await _seed_two_tenants(admin_engine)
    db = Database(Settings(_env_file=".env").database_url)
    repo = SqlAlchemyUserRepository(db.session)
    try:
        token = set_current_tenant(tenant_a)
        try:
            assert await repo.get_by_email(tenant_a, "a@a.com") is not None
            # Asking for B's row while scoped to A → RLS hides it.
            assert await repo.get_by_email(tenant_b, "b@b.com") is None
        finally:
            reset_current_tenant(token)

        token = set_current_tenant(tenant_b)
        try:
            assert await repo.get_by_email(tenant_b, "b@b.com") is not None
            assert await repo.get_by_email(tenant_a, "a@a.com") is None
        finally:
            reset_current_tenant(token)
    finally:
        await db.dispose()


async def test_no_tenant_context_sees_nothing(admin_engine: AsyncEngine):
    tenant_a, _ = await _seed_two_tenants(admin_engine)
    db = Database(Settings(_env_file=".env").database_url)
    repo = SqlAlchemyUserRepository(db.session)
    try:
        # No tenant in context → SET LOCAL is skipped → RLS returns no rows.
        assert await repo.get_by_email(tenant_a, "a@a.com") is None
    finally:
        await db.dispose()

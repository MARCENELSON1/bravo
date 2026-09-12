"""The outbox against a real Postgres: claiming, retrying, and RLS.

These need real Postgres, not a fake: ``FOR UPDATE SKIP LOCKED``, the partial
behaviour of unique constraints over NULLs, and row-level security are all
database semantics — a fake would only assert that the fake works.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.application.outbox.ports import OutboxKind
from app.config import Settings
from app.context import reset_current_tenant, set_current_tenant
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.outbox_repo import SqlAlchemyOutbox

PUSH = OutboxKind.PUSH_NOTIFICATION


async def _seed_tenant(admin_engine: AsyncEngine, slug: str) -> str:
    tenant_id = str(uuid.uuid4())
    async with admin_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, :slug)"),
            {"id": tenant_id, "slug": slug},
        )
    return tenant_id


def _outbox() -> tuple[Database, SqlAlchemyOutbox]:
    db = Database(Settings(_env_file=".env").database_url)
    return db, SqlAlchemyOutbox(db.session)


async def test_enqueued_task_is_claimed_once_and_marked_done(admin_engine: AsyncEngine):
    tenant_id = await _seed_tenant(admin_engine, "outbox-a")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_id)
    try:
        await outbox.enqueue(tenant_id, PUSH, {"user_id": "u1", "title": "Mesa 4"})

        claimed = await outbox.claim_batch(tenant_id)
        assert [t.payload["title"] for t in claimed] == ["Mesa 4"]
        assert claimed[0].attempts == 1  # bumped on claim, so a crash burns a try

        # The lease pushed run_after into the future: the next pass sees nothing.
        assert await outbox.claim_batch(tenant_id) == []

        await outbox.mark_done(claimed[0].id)
        assert await _status(db, claimed[0].id) == "DONE"
    finally:
        reset_current_tenant(token)
        await db.dispose()


async def test_dedup_key_collapses_repeats_but_untagged_tasks_all_insert(
    admin_engine: AsyncEngine,
):
    tenant_id = await _seed_tenant(admin_engine, "outbox-b")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_id)
    try:
        await outbox.enqueue(tenant_id, PUSH, {"n": 1}, dedup_key="order-1")
        await outbox.enqueue(tenant_id, PUSH, {"n": 2}, dedup_key="order-1")
        # No key → Postgres treats the NULLs as distinct, so both land.
        await outbox.enqueue(tenant_id, PUSH, {"n": 3})
        await outbox.enqueue(tenant_id, PUSH, {"n": 4})

        claimed = await outbox.claim_batch(tenant_id)
        assert sorted(t.payload["n"] for t in claimed) == [1, 3, 4]
    finally:
        reset_current_tenant(token)
        await db.dispose()


async def test_concurrent_drainers_never_claim_the_same_task(admin_engine: AsyncEngine):
    """Two replicas draining at once must not send the same push twice."""
    tenant_id = await _seed_tenant(admin_engine, "outbox-c")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_id)
    try:
        for n in range(6):
            await outbox.enqueue(tenant_id, PUSH, {"n": n})

        # Same tenant, same instant, both asking for everything.
        left, right = await asyncio.gather(
            outbox.claim_batch(tenant_id, limit=6),
            outbox.claim_batch(tenant_id, limit=6),
        )
        ids = [t.id for t in left] + [t.id for t in right]
        assert len(ids) == 6, "every task claimed exactly once"
        assert len(set(ids)) == 6, "no task claimed by both drainers"
    finally:
        reset_current_tenant(token)
        await db.dispose()


async def test_failure_retries_with_backoff_then_gives_up(admin_engine: AsyncEngine):
    tenant_id = await _seed_tenant(admin_engine, "outbox-d")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_id)
    try:
        await outbox.enqueue(tenant_id, PUSH, {"user_id": "u1"})
        task = (await outbox.claim_batch(tenant_id))[0]

        await outbox.mark_failed(task.id, "fcm timeout", max_attempts=2)
        # Still PENDING, but dated forward — retryable, not lost.
        assert await _status(db, task.id) == "PENDING"
        assert await outbox.claim_batch(tenant_id) == []

        await _make_due(db, task.id)
        again = await outbox.claim_batch(tenant_id)
        assert again[0].attempts == 2

        await outbox.mark_failed(task.id, "fcm timeout", max_attempts=2)
        assert await _status(db, task.id) == "DEAD"
        await _make_due(db, task.id)
        assert await outbox.claim_batch(tenant_id) == [], "a dead task stays dead"
    finally:
        reset_current_tenant(token)
        await db.dispose()


async def test_rls_hides_another_tenants_tasks(admin_engine: AsyncEngine):
    tenant_a = await _seed_tenant(admin_engine, "outbox-e")
    tenant_b = await _seed_tenant(admin_engine, "outbox-f")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_a)
    try:
        await outbox.enqueue(tenant_a, PUSH, {"n": "a"})
    finally:
        reset_current_tenant(token)

    token = set_current_tenant(tenant_b)
    try:
        # Asking for A's rows while scoped to B: the filter is bypassed on
        # purpose here, so what stops it is the policy.
        assert await outbox.claim_batch(tenant_a) == []
    finally:
        reset_current_tenant(token)
        await db.dispose()


async def test_the_drainer_cannot_read_the_queue_without_a_tenant(
    admin_engine: AsyncEngine,
):
    """Why the worker walks the tenant list instead of selecting the whole table."""
    tenant_id = await _seed_tenant(admin_engine, "outbox-g")
    db, outbox = _outbox()
    token = set_current_tenant(tenant_id)
    try:
        await outbox.enqueue(tenant_id, PUSH, {"n": 1})
    finally:
        reset_current_tenant(token)

    try:
        # No tenant in context, so the policy compares against an unset setting.
        # Postgres may refuse the query outright (the empty string does not cast
        # to uuid) or match nothing, depending on what the pooled connection was
        # last used for. Either is fine; what matters is that the rows never come
        # back — which is why the worker walks the tenant list instead.
        try:
            assert await outbox.claim_batch(tenant_id) == []
        except SQLAlchemyError:
            pass
    finally:
        await db.dispose()


async def _status(db: Database, task_id: str) -> str:
    async with db.session() as session:
        row = await session.execute(
            text("SELECT status FROM outbox_tasks WHERE id = :id"), {"id": task_id}
        )
        return row.scalar_one()


async def _make_due(db: Database, task_id: str) -> None:
    """Fast-forward past the lease/backoff instead of sleeping through it."""
    async with db.session() as session:
        await session.execute(
            text("UPDATE outbox_tasks SET run_after = now() - interval '1 hour' WHERE id = :id"),
            {"id": task_id},
        )

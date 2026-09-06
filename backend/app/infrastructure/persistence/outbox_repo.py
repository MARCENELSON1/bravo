"""Postgres-backed outbox. Tenant-scoped (RLS + explicit filter).

The claim is the interesting part: several API replicas drain the same table, so
rows are taken with ``FOR UPDATE SKIP LOCKED`` — a replica locks the rows it is
about to take and the others walk past them instead of blocking, which is what
lets the drainer scale out without ever sending the same push twice.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.application.outbox.ports import OutboxKind, OutboxPort, OutboxTask
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import OutboxTaskORM

# How long a claimed task stays invisible to other drainers. Long enough for the
# slowest handler (a push fan-out over several devices), short enough that work
# orphaned by a crashed process comes back reasonably soon.
_LEASE = timedelta(minutes=5)

# Retry backoff, indexed by attempts already made. Past the end, the task is dead.
_BACKOFF = (
    timedelta(seconds=30),
    timedelta(minutes=2),
    timedelta(minutes=10),
    timedelta(hours=1),
)


class SqlAlchemyOutbox(OutboxPort):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def enqueue(
        self,
        tenant_id: str,
        kind: OutboxKind,
        payload: dict,
        *,
        dedup_key: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            stmt = pg_insert(OutboxTaskORM).values(
                id=str(uuid4()),
                tenant_id=tenant_id,
                kind=str(kind),
                payload=payload,
                dedup_key=dedup_key,
            )
            if dedup_key is not None:
                # Postgres treats NULLs as distinct, so the constraint only bites
                # when a key was actually given — un-keyed tasks always insert.
                stmt = stmt.on_conflict_do_nothing(
                    constraint="uq_outbox_tasks_tenant_kind_dedup"
                )
            await session.execute(stmt)

    async def claim_batch(self, tenant_id: str, *, limit: int = 20) -> list[OutboxTask]:
        async with self._session_factory() as session:
            due = (
                select(OutboxTaskORM.id)
                .where(
                    OutboxTaskORM.tenant_id == tenant_id,
                    OutboxTaskORM.status == "PENDING",
                    OutboxTaskORM.run_after <= func.now(),
                )
                .order_by(OutboxTaskORM.run_after)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            ids = list((await session.execute(due)).scalars().all())
            if not ids:
                return []

            # Taking the lease inside the same transaction as the lock is what
            # makes the claim exclusive: by the time the row is unlocked it is
            # already dated into the future, so no other drainer sees it as due.
            claimed = (
                update(OutboxTaskORM)
                .where(OutboxTaskORM.id.in_(ids))
                .values(
                    attempts=OutboxTaskORM.attempts + 1,
                    run_after=func.now() + _LEASE,
                )
                .returning(
                    OutboxTaskORM.id,
                    OutboxTaskORM.tenant_id,
                    OutboxTaskORM.kind,
                    OutboxTaskORM.payload,
                    OutboxTaskORM.attempts,
                )
            )
            rows = (await session.execute(claimed)).all()
            return [
                OutboxTask(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    kind=OutboxKind(row.kind),
                    payload=row.payload or {},
                    attempts=row.attempts,
                )
                for row in rows
            ]

    async def mark_done(self, task_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(OutboxTaskORM)
                .where(OutboxTaskORM.id == task_id)
                .values(status="DONE", last_error=None)
            )

    async def mark_failed(self, task_id: str, error: str, *, max_attempts: int) -> None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(OutboxTaskORM.attempts).where(OutboxTaskORM.id == task_id)
                )
            ).scalar_one_or_none()
            if row is None:
                return
            values: dict = {"last_error": error[:500]}
            if row >= max_attempts:
                # Kept as DEAD rather than deleted: a push that never went out is
                # something an operator should be able to find and explain.
                values["status"] = "DEAD"
            else:
                delay = _BACKOFF[min(max(row - 1, 0), len(_BACKOFF) - 1)]
                values["run_after"] = func.now() + delay
            await session.execute(
                update(OutboxTaskORM).where(OutboxTaskORM.id == task_id).values(**values)
            )

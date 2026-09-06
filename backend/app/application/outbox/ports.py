"""Generic outbox: work that must happen, but not while the user waits.

Marking a course ready used to wait for the whole push round-trip — load the
waiter's device tokens, mint a Google OAuth token, POST to FCM once per device,
sequentially — before it could answer the kitchen. The mozo's phone does not
learn about the plate any sooner for the KDS having waited, so the notification
is enqueued here and a drainer sends it out of band, with retries.

Deliberately a table and not a broker: the row is written with the same database
as the business change, it survives a restart, and it is inspectable with SQL.
Mirrors the shape the project already uses for tax reports
(:class:`~app.application.tax.reporting.TaxReportLedger`), generalised by
``kind`` so one drainer serves every deferred job.

**Row-level security shapes the drainer.** The queue is tenant-scoped like every
other table, and the policy hides every row when ``app.tenant_id`` is unset — so
a process running outside a request cannot read the queue globally. Rather than
weaken that policy with a bypass, the drainer asks the (RLS-free) ``tenants``
table who exists and drains each tenant inside its own scoped transaction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class OutboxKind(StrEnum):
    """What a task does. The drainer dispatches on this.

    Only push so far, and deliberately so. What earns a place here is work that
    *leaves the process* — an external call whose latency nobody controls. Local
    database writes are cheaper to just do, and the ones after a sale
    (stock, sale facts) have an inverse that a reopen runs, so deferring them
    would race the undo against the do. Tax reporting is absent for the opposite
    reason: it already has its own durable outbox and drain use case, and only
    ever lacked someone to call it — the worker schedules that directly rather
    than wrapping a queue in a queue.
    """

    PUSH_NOTIFICATION = "PUSH_NOTIFICATION"


@dataclass(frozen=True)
class OutboxTask:
    """A claimed unit of work.

    ``payload`` is a **snapshot**, never a reference: a push carries the title and
    body already rendered, so a comanda that changes between enqueue and drain can
    never turn into a notification describing something else.
    """

    id: str
    tenant_id: str
    kind: OutboxKind
    payload: dict = field(default_factory=dict)
    attempts: int = 0


class OutboxPort(ABC):
    """Durable queue of deferred work, tenant-scoped."""

    @abstractmethod
    async def enqueue(
        self,
        tenant_id: str,
        kind: OutboxKind,
        payload: dict,
        *,
        dedup_key: str | None = None,
    ) -> None:
        """Add a task. With ``dedup_key``, idempotent per (tenant, kind, key) —
        re-enqueuing the same work is a no-op instead of a duplicate push."""

    @abstractmethod
    async def claim_batch(self, tenant_id: str, *, limit: int = 20) -> list[OutboxTask]:
        """Take up to ``limit`` due tasks for this tenant and mark them in flight.

        Uses ``FOR UPDATE SKIP LOCKED`` so several replicas can drain at once
        without two of them claiming the same row (which would send the same push
        twice)."""

    @abstractmethod
    async def mark_done(self, task_id: str) -> None: ...

    @abstractmethod
    async def mark_failed(self, task_id: str, error: str, *, max_attempts: int) -> None:
        """Record the failure and schedule a retry with exponential backoff, or
        give up permanently once ``max_attempts`` is reached."""

"""Running the deferred work: one tenant at a time, one task at a time.

Two use cases. :class:`DrainOutbox` empties one tenant's queue and is what an
endpoint or a test calls when it wants the work to happen *now*.
:class:`DrainAllTenants` is what the background worker calls on a timer: it walks
the tenant list and scopes itself to each one, because row-level security means
there is no such thing as reading the queue globally.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.outbox.ports import OutboxKind, OutboxPort, OutboxTask
from app.application.tax.reporting import ReportPendingTaxSales
from app.domain.identity.ports import TenantContext
from app.domain.notification.ports import NotificationService, PushMessage
from app.domain.tenant.repository import TenantRepository

logger = logging.getLogger(__name__)

# A task that has failed this many times is parked as DEAD instead of retried
# forever. Five attempts spread over the backoff covers an outage of about an
# hour, which is far longer than any push is still worth sending.
MAX_ATTEMPTS = 5


@dataclass(frozen=True)
class OutboxRun:
    """What one drain pass did. Returned so an operator (or a test) can see it."""

    claimed: int = 0
    done: int = 0
    failed: int = 0


class DrainOutbox:
    """Run one tenant's due tasks.

    Per-task isolation is the whole point: one stale device token, or one FCM
    hiccup, marks that row failed and the pass keeps going. Nothing here is
    allowed to raise — the caller is a timer with nobody to report to.
    """

    def __init__(
        self,
        outbox: OutboxPort,
        tenant_context: TenantContext,
        notifications: NotificationService,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> None:
        self._outbox = outbox
        self._tenant_context = tenant_context
        self._notifications = notifications
        self._max_attempts = max_attempts

    async def execute(self, *, tenant_id: str, limit: int = 20) -> OutboxRun:
        self._tenant_context.set(tenant_id)
        tasks = await self._outbox.claim_batch(tenant_id, limit=limit)
        done = 0
        failed = 0
        for task in tasks:
            try:
                await self._run(task)
                await self._outbox.mark_done(task.id)
                done += 1
            except Exception as exc:  # noqa: BLE001 — isolate one bad task
                logger.warning(
                    "outbox task %s (%s) failed on attempt %d",
                    task.id,
                    task.kind,
                    task.attempts,
                    exc_info=True,
                )
                await self._outbox.mark_failed(
                    task.id, str(exc)[:500], max_attempts=self._max_attempts
                )
                failed += 1
        return OutboxRun(claimed=len(tasks), done=done, failed=failed)

    async def _run(self, task: OutboxTask) -> None:
        if task.kind is OutboxKind.PUSH_NOTIFICATION:
            await self._send_push(task)

    async def _send_push(self, task: OutboxTask) -> None:
        payload = task.payload
        await self._notifications.notify_user(
            tenant_id=task.tenant_id,
            user_id=payload["user_id"],
            message=PushMessage(
                # Rendered at enqueue time, so a comanda that changed since can
                # never turn into a notification describing something else.
                title=payload.get("title", ""),
                body=payload.get("body", ""),
                data=payload.get("data") or {},
            ),
        )


class DrainAllTenants:
    """One background pass over every tenant.

    Also runs the tax-report drain, which was already built and simply never
    scheduled: until now those rows only moved when somebody hit the endpoint by
    hand. AR tenants have an empty tax outbox, so for them it is a no-op.
    """

    def __init__(
        self,
        tenants: TenantRepository,
        drain: DrainOutbox,
        tax_drain: ReportPendingTaxSales | None = None,
    ) -> None:
        self._tenants = tenants
        self._drain = drain
        self._tax_drain = tax_drain

    async def execute(self, *, limit: int = 20) -> OutboxRun:
        total = OutboxRun()
        for tenant_id in await self._tenants.list_ids():
            try:
                run = await self._drain.execute(tenant_id=tenant_id, limit=limit)
            except Exception:  # noqa: BLE001 — one tenant must not stop the rest
                logger.warning("outbox drain failed for tenant %s", tenant_id, exc_info=True)
                continue
            total = OutboxRun(
                claimed=total.claimed + run.claimed,
                done=total.done + run.done,
                failed=total.failed + run.failed,
            )
            if self._tax_drain is not None:
                try:
                    await self._tax_drain.execute(tenant_id=tenant_id)
                except Exception:  # noqa: BLE001 — reporting must not stop draining
                    logger.warning(
                        "tax report drain failed for tenant %s", tenant_id, exc_info=True
                    )
        return total

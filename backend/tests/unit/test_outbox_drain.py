"""The drainer's behaviour: isolation, retries, and what it hands to the sender."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.outbox.drain import DrainAllTenants, DrainOutbox, OutboxRun
from app.application.outbox.ports import OutboxKind, OutboxPort, OutboxTask
from app.domain.notification.ports import NotificationService, PushMessage
from app.domain.tenant.entities import Tenant
from tests.fakes import FakeTenantContext, FakeTenantRepository

PUSH = OutboxKind.PUSH_NOTIFICATION


class FakeOutbox(OutboxPort):
    def __init__(self) -> None:
        self.pending: list[OutboxTask] = []
        self.done: list[str] = []
        self.failed: list[tuple[str, str]] = []

    async def enqueue(self, tenant_id, kind, payload, *, dedup_key=None) -> None:
        self.pending.append(
            OutboxTask(
                id=f"t{len(self.pending)}",
                tenant_id=tenant_id,
                kind=kind,
                payload=payload,
                attempts=1,
            )
        )

    async def claim_batch(self, tenant_id, *, limit=20) -> list[OutboxTask]:
        taken = [t for t in self.pending if t.tenant_id == tenant_id][:limit]
        self.pending = [t for t in self.pending if t not in taken]
        return taken

    async def mark_done(self, task_id: str) -> None:
        self.done.append(task_id)

    async def mark_failed(self, task_id: str, error: str, *, max_attempts: int) -> None:
        self.failed.append((task_id, error))


@dataclass
class FakePush(NotificationService):
    sent: list[tuple[str, str, PushMessage]] = field(default_factory=list)
    fail_for: set[str] = field(default_factory=set)

    async def notify_user(self, *, tenant_id, user_id, message) -> None:
        if user_id in self.fail_for:
            raise RuntimeError("device token rejected")
        self.sent.append((tenant_id, user_id, message))


def _task(tid: str, user_id: str, **payload) -> OutboxTask:
    return OutboxTask(
        id=tid,
        tenant_id="tenant-1",
        kind=PUSH,
        payload={"user_id": user_id, **payload},
        attempts=1,
    )


def _drain(outbox: FakeOutbox, push: FakePush) -> DrainOutbox:
    return DrainOutbox(outbox, FakeTenantContext(), push)


async def test_a_claimed_push_is_sent_with_the_text_it_was_queued_with():
    outbox, push = FakeOutbox(), FakePush()
    outbox.pending = [_task("t1", "waiter-1", title="Mesa 4 · entrada lista", body="2× Empanadas")]

    run = await _drain(outbox, push).execute(tenant_id="tenant-1")

    assert run == OutboxRun(claimed=1, done=1, failed=0)
    tenant_id, user_id, message = push.sent[0]
    assert (tenant_id, user_id) == ("tenant-1", "waiter-1")
    assert message.title == "Mesa 4 · entrada lista"
    assert message.body == "2× Empanadas"
    assert outbox.done == ["t1"]


async def test_one_failing_push_does_not_stop_the_others():
    outbox, push = FakeOutbox(), FakePush(fail_for={"waiter-2"})
    outbox.pending = [
        _task("t1", "waiter-1", title="Mesa 1"),
        _task("t2", "waiter-2", title="Mesa 2"),
        _task("t3", "waiter-3", title="Mesa 3"),
    ]

    run = await _drain(outbox, push).execute(tenant_id="tenant-1")

    assert (run.done, run.failed) == (2, 1)
    assert [m.title for _, _, m in push.sent] == ["Mesa 1", "Mesa 3"]
    assert outbox.done == ["t1", "t3"]
    assert [tid for tid, _ in outbox.failed] == ["t2"]


async def test_the_drainer_scopes_itself_to_each_tenant():
    """Without this the queue is invisible: RLS hides every row until a tenant is
    in context, so a drainer that forgets to scope silently does nothing."""
    outbox, push = FakeOutbox(), FakePush()
    context = FakeTenantContext()
    outbox.pending = [_task("t1", "waiter-1", title="Mesa 1")]

    await DrainOutbox(outbox, context, push).execute(tenant_id="tenant-1")

    assert context.current == "tenant-1"


async def test_every_tenant_gets_drained_even_if_one_blows_up():
    push = FakePush()
    tenants = FakeTenantRepository()
    for slug in ("a", "b"):
        await tenants.add(Tenant(id=f"tenant-{slug}", slug=slug, name=slug))
    ids = await tenants.list_ids()

    class Exploding(FakeOutbox):
        async def claim_batch(self, tenant_id, *, limit=20):
            if tenant_id == ids[0]:
                raise RuntimeError("connection reset")
            return await super().claim_batch(tenant_id, limit=limit)

    outbox = Exploding()
    outbox.pending = [
        OutboxTask(id="t1", tenant_id=ids[1], kind=PUSH, payload={"user_id": "w"}, attempts=1)
    ]

    run = await DrainAllTenants(tenants, _drain(outbox, push)).execute()

    assert run.done == 1, "the healthy tenant still got drained"
    assert len(push.sent) == 1


async def test_the_tax_drain_runs_for_every_tenant():
    """It was built with the outbox and never scheduled — this is the wiring that
    finally calls it without anyone hitting the endpoint by hand."""
    tenants = FakeTenantRepository()
    for slug in ("a", "b"):
        await tenants.add(Tenant(id=f"tenant-{slug}", slug=slug, name=slug))

    class SpyTaxDrain:
        def __init__(self) -> None:
            self.calls: list[str] = []

        async def execute(self, *, tenant_id: str, limit: int = 100) -> None:
            self.calls.append(tenant_id)

    tax = SpyTaxDrain()
    await DrainAllTenants(tenants, _drain(FakeOutbox(), FakePush()), tax_drain=tax).execute()

    assert sorted(tax.calls) == await tenants.list_ids()

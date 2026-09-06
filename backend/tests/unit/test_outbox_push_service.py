"""The enqueue side: what the use cases get when PUSH_DELIVERY=outbox."""

from __future__ import annotations

from app.application.outbox.ports import OutboxKind
from app.domain.notification.ports import PushMessage
from app.infrastructure.notification.outbox_service import OutboxPushService
from tests.unit.test_outbox_drain import FakeOutbox


async def test_notifying_a_user_queues_the_rendered_message_instead_of_sending():
    outbox = FakeOutbox()

    await OutboxPushService(outbox).notify_user(
        tenant_id="tenant-1",
        user_id="waiter-1",
        message=PushMessage(
            title="Mesa 4 · entrada lista",
            body="2× Empanadas",
            data={"kind": "order.ready", "order_id": "o1"},
        ),
    )

    (task,) = outbox.pending
    assert task.kind is OutboxKind.PUSH_NOTIFICATION
    assert task.tenant_id == "tenant-1"
    assert task.payload == {
        "user_id": "waiter-1",
        "title": "Mesa 4 · entrada lista",
        "body": "2× Empanadas",
        "data": {"kind": "order.ready", "order_id": "o1"},
    }


async def test_a_broken_queue_does_not_break_marking_a_plate_ready():
    """The aviso is secondary to the operation that triggers it. If the write
    fails, the kitchen still gets its answer — the mozo just misses the push."""

    class BrokenOutbox(FakeOutbox):
        async def enqueue(self, tenant_id, kind, payload, *, dedup_key=None) -> None:
            raise RuntimeError("connection reset")

    await OutboxPushService(BrokenOutbox()).notify_user(
        tenant_id="tenant-1", user_id="waiter-1", message=PushMessage(title="x", body="y")
    )

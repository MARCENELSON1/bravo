from __future__ import annotations

import asyncio

import pytest

from app.domain.realtime.ports import DomainEvent
from app.infrastructure.realtime.memory_bus import InMemoryEventBus


async def test_publish_reaches_subscriber_of_same_tenant() -> None:
    bus = InMemoryEventBus()
    sub = bus.subscribe("t1")
    await bus.publish(
        DomainEvent(type="kds.changed", tenant_id="t1", payload={"order_id": "o1"})
    )
    event = await asyncio.wait_for(sub.get(), timeout=1)
    assert event.type == "kds.changed"
    assert event.payload["order_id"] == "o1"
    sub.close()


async def test_subscriber_never_sees_other_tenants_events() -> None:
    bus = InMemoryEventBus()
    sub_a = bus.subscribe("a")
    sub_b = bus.subscribe("b")
    await bus.publish(DomainEvent(type="kds.changed", tenant_id="a"))

    a_event = await asyncio.wait_for(sub_a.get(), timeout=1)
    assert a_event.tenant_id == "a"
    # B's stream stays empty — isolation does not depend on anything but the bus.
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(sub_b.get(), timeout=0.05)
    sub_a.close()
    sub_b.close()


async def test_close_unsubscribes_and_publish_stays_a_noop() -> None:
    bus = InMemoryEventBus()
    sub = bus.subscribe("t1")
    sub.close()
    # No subscribers left → publish must not raise.
    await bus.publish(DomainEvent(type="kds.changed", tenant_id="t1"))


async def test_a_stalled_subscriber_cannot_grow_memory_without_end() -> None:
    # A phone that lost signal mid-service keeps its SSE queue open and stops
    # draining it. Publishing must stay non-blocking and the queue bounded, or
    # one dead client would both stall waiters' requests and leak memory.
    bus = InMemoryEventBus(max_queued_events=3)
    sub = bus.subscribe("t1")

    for index in range(10):
        await asyncio.wait_for(
            bus.publish(
                DomainEvent(type="kds.changed", tenant_id="t1", payload={"n": str(index)})
            ),
            timeout=0.5,  # publish must never wait on the subscriber
        )

    seen = [(await asyncio.wait_for(sub.get(), timeout=1)).payload["n"] for _ in range(3)]
    assert seen == ["7", "8", "9"]  # oldest dropped, freshest state kept
    sub.close()

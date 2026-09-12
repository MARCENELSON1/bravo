from __future__ import annotations

import asyncio
from collections.abc import Callable

from app.domain.realtime.ports import DomainEvent, EventBus, Subscription
from app.infrastructure.realtime.queueing import MAX_QUEUED_EVENTS, offer


class _MemorySubscription(Subscription):
    def __init__(
        self, queue: asyncio.Queue[DomainEvent], on_close: Callable[[], None]
    ) -> None:
        self._queue = queue
        self._on_close = on_close

    async def get(self) -> DomainEvent:
        return await self._queue.get()

    def close(self) -> None:
        self._on_close()


class InMemoryEventBus(EventBus):
    """In-process pub/sub keyed by tenant (single-worker default).

    Subscribers register a queue; ``publish`` fans out to every queue of the
    event's tenant only — a subscriber for tenant A never receives tenant B's
    events. It does **not** cross processes: with several replicas, swap in
    :class:`RedisEventBus` behind this same port.

    Queues are bounded and drop their oldest entry when full, so a client that
    stopped draining (a phone that lost signal mid-service) cannot grow the
    process's memory without end.
    """

    def __init__(self, max_queued_events: int = MAX_QUEUED_EVENTS) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[DomainEvent]]] = {}
        self._max_queued = max_queued_events

    async def publish(self, event: DomainEvent) -> None:
        for queue in list(self._subscribers.get(event.tenant_id, ())):
            # Never ``await put``: that would block the waiter's own request on
            # behalf of a subscriber that stopped reading.
            offer(queue, event)

    def subscribe(self, tenant_id: str) -> Subscription:
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue(maxsize=self._max_queued)
        self._subscribers.setdefault(tenant_id, set()).add(queue)

        def on_close() -> None:
            subs = self._subscribers.get(tenant_id)
            if subs is not None:
                subs.discard(queue)
                if not subs:
                    self._subscribers.pop(tenant_id, None)

        return _MemorySubscription(queue, on_close)

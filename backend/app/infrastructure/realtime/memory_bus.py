from __future__ import annotations

import asyncio
from collections.abc import Callable

from app.domain.realtime.ports import DomainEvent, EventBus, Subscription


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
    """In-process pub/sub keyed by tenant (single-worker MVP).

    Subscribers register a queue; ``publish`` fans out to every queue of the
    event's tenant only — a subscriber for tenant A never receives tenant B's
    events. For multiple Railway replicas, swap a Postgres LISTEN/NOTIFY adapter
    behind the ``EventBus`` port (this in-memory bus does not cross processes).
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[DomainEvent]]] = {}

    async def publish(self, event: DomainEvent) -> None:
        for queue in list(self._subscribers.get(event.tenant_id, ())):
            queue.put_nowait(event)

    def subscribe(self, tenant_id: str) -> Subscription:
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._subscribers.setdefault(tenant_id, set()).add(queue)

        def on_close() -> None:
            subs = self._subscribers.get(tenant_id)
            if subs is not None:
                subs.discard(queue)
                if not subs:
                    self._subscribers.pop(tenant_id, None)

        return _MemorySubscription(queue, on_close)

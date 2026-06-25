from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainEvent:
    """A lightweight realtime notification, scoped to a tenant.

    The payload is intentionally small (ids/status) — it is a "something changed,
    refetch now" signal, NOT the data itself. Clients still read the data through
    the normal RLS-scoped endpoints, so tenant isolation never depends on the
    stream.
    """

    type: str
    tenant_id: str
    payload: dict[str, str] = field(default_factory=dict)


class Subscription(ABC):
    """A single subscriber's stream of events. ``close()`` releases it."""

    @abstractmethod
    async def get(self) -> DomainEvent: ...

    @abstractmethod
    def close(self) -> None: ...


class EventBus(ABC):
    """Publish/subscribe for realtime events, keyed by tenant.

    The in-process adapter is enough for a single worker; for multiple replicas
    swap a Postgres ``LISTEN/NOTIFY`` (or Redis) adapter behind this same port.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def subscribe(self, tenant_id: str) -> Subscription: ...

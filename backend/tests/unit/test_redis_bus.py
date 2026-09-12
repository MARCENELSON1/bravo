"""The Redis event bus: what makes running more than one replica safe.

The fake below is a stand-in Redis Pub/Sub *server*: every bus built on the same
fake talks through one shared broker, exactly as two API processes would. That is
what lets these tests assert cross-instance delivery without a real server; the
genuine cross-process proof lives in the manual two-process check.
"""

from __future__ import annotations

import asyncio

import pytest

from app.domain.realtime.ports import DomainEvent
from app.infrastructure.realtime.redis_bus import RedisEventBus


class _FakeBroker:
    """Channel → subscriber queues, shared by every client built from it."""

    def __init__(self) -> None:
        self.channels: dict[str, list[asyncio.Queue[bytes]]] = {}

    async def publish(self, channel: str, message: str) -> int:
        listeners = self.channels.get(channel, [])
        for queue in listeners:
            queue.put_nowait(message.encode())
        return len(listeners)

    def attach(self, channel: str) -> asyncio.Queue[bytes]:
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.channels.setdefault(channel, []).append(queue)
        return queue

    def detach(self, channel: str, queue: asyncio.Queue[bytes]) -> None:
        listeners = self.channels.get(channel, [])
        if queue in listeners:
            listeners.remove(queue)


class _FakePubSub:
    def __init__(self, broker: _FakeBroker) -> None:
        self._broker = broker
        self._channel: str | None = None
        self._queue: asyncio.Queue[bytes] | None = None
        self.closed = False

    async def subscribe(self, channel: str) -> None:
        self._channel = channel
        self._queue = self._broker.attach(channel)

    async def get_message(
        self,
        ignore_subscribe_messages: bool = False,
        timeout: float = 1.0,  # noqa: ASYNC109 - firma impuesta por redis-py
    ) -> dict[str, object] | None:
        assert self._queue is not None
        try:
            data = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except TimeoutError:
            return None
        return {"type": "message", "channel": self._channel, "data": data}

    async def aclose(self) -> None:
        self.closed = True
        if self._channel is not None and self._queue is not None:
            self._broker.detach(self._channel, self._queue)


class _FakeRedis:
    def __init__(self, broker: _FakeBroker) -> None:
        self._broker = broker
        self.pubsubs: list[_FakePubSub] = []

    async def publish(self, channel: str, message: str) -> int:
        return await self._broker.publish(channel, message)

    def pubsub(self) -> _FakePubSub:
        created = _FakePubSub(self._broker)
        self.pubsubs.append(created)
        return created


class _FakeProvider:
    """Stands in for :class:`RedisProvider`, handing out the same fake server."""

    def __init__(self, broker: _FakeBroker) -> None:
        self._redis = _FakeRedis(broker)

    def client(self):  # noqa: ANN201 - mirrors the provider's loose typing
        return self._redis

    def pubsub_client(self):  # noqa: ANN201
        return self._redis


class _BrokenProvider:
    def client(self):  # noqa: ANN201
        raise RuntimeError("redis is down")

    def pubsub_client(self):  # noqa: ANN201
        raise RuntimeError("redis is down")


class _NoRedisProvider:
    """What the real provider returns when the driver or URL is unusable."""

    def client(self):  # noqa: ANN201
        return None

    def pubsub_client(self):  # noqa: ANN201
        return None


async def _next(sub, seconds: float = 1.0) -> DomainEvent:  # noqa: ANN001
    return await asyncio.wait_for(sub.get(), timeout=seconds)


async def _settle() -> None:
    """Let the pump task run its subscribe before we publish."""
    for _ in range(5):
        await asyncio.sleep(0)


async def test_event_published_on_one_instance_reaches_another() -> None:
    # The whole point of the phase: replica A publishes, replica B's waiter sees
    # it. With the in-process bus this is impossible by construction.
    broker = _FakeBroker()
    replica_a = RedisEventBus(_FakeProvider(broker))
    replica_b = RedisEventBus(_FakeProvider(broker))

    sub = replica_b.subscribe("t1")
    await _settle()
    await replica_a.publish(
        DomainEvent(type="kds.changed", tenant_id="t1", payload={"order_id": "o1"})
    )

    event = await _next(sub)
    assert event.type == "kds.changed"
    assert event.tenant_id == "t1"
    assert event.payload["order_id"] == "o1"
    sub.close()


async def test_subscriber_never_sees_another_tenants_events() -> None:
    # Isolation is structural (one channel per tenant), not a filter that could
    # be forgotten. A leak here would show one venue another's activity.
    broker = _FakeBroker()
    bus = RedisEventBus(_FakeProvider(broker))
    sub_a = bus.subscribe("a")
    sub_b = bus.subscribe("b")
    await _settle()

    await bus.publish(DomainEvent(type="floor.changed", tenant_id="a"))

    assert (await _next(sub_a)).tenant_id == "a"
    with pytest.raises(TimeoutError):
        await _next(sub_b, seconds=0.05)
    sub_a.close()
    sub_b.close()


async def test_every_subscriber_of_a_tenant_receives_the_event() -> None:
    broker = _FakeBroker()
    bus = RedisEventBus(_FakeProvider(broker))
    first = bus.subscribe("t1")
    second = bus.subscribe("t1")
    await _settle()

    await bus.publish(DomainEvent(type="order.ready", tenant_id="t1"))

    assert (await _next(first)).type == "order.ready"
    assert (await _next(second)).type == "order.ready"
    first.close()
    second.close()


async def test_real_payloads_survive_the_json_round_trip() -> None:
    broker = _FakeBroker()
    bus = RedisEventBus(_FakeProvider(broker))
    sub = bus.subscribe("t1")
    await _settle()

    payload = {
        "order_id": "0a1bcd7a-bac7-4c33-95c4-adbaeed22bfd",
        "table_id": "a606a53a-1381-40f5-9518-fbb7479a4a4f",
        "table_number": "7",
        "waiter_id": "w1",
        "course": "STARTER",
        "course_label": "entrada",
    }
    await bus.publish(DomainEvent(type="order.ready", tenant_id="t1", payload=payload))

    assert (await _next(sub)).payload == payload
    sub.close()


async def test_publish_with_redis_down_does_not_break_the_caller() -> None:
    # Fail-open: losing the nudge is an annoyance, failing the payment that
    # triggered it is not.
    bus = RedisEventBus(_BrokenProvider())
    await bus.publish(DomainEvent(type="kds.changed", tenant_id="t1"))


async def test_subscribe_without_a_backend_stays_quiet() -> None:
    bus = RedisEventBus(_NoRedisProvider())
    sub = bus.subscribe("t1")
    await _settle()
    with pytest.raises(TimeoutError):
        await _next(sub, seconds=0.05)
    sub.close()


async def test_slow_subscriber_is_capped_and_keeps_the_newest_events() -> None:
    # A phone that lost signal must not grow the process's memory without end.
    broker = _FakeBroker()
    bus = RedisEventBus(_FakeProvider(broker), max_queued_events=3)
    sub = bus.subscribe("t1")
    await _settle()

    for index in range(6):
        await bus.publish(
            DomainEvent(type="kds.changed", tenant_id="t1", payload={"n": str(index)})
        )
    await _settle()

    seen = [(await _next(sub)).payload["n"] for _ in range(3)]
    assert seen == ["3", "4", "5"]  # oldest dropped, newest kept
    sub.close()


async def test_close_releases_the_pubsub_connection() -> None:
    # Without this, every disconnected SSE client would leak a connection.
    broker = _FakeBroker()
    provider = _FakeProvider(broker)
    bus = RedisEventBus(provider)
    sub = bus.subscribe("t1")
    await _settle()

    sub.close()
    await _settle()
    await asyncio.sleep(0.01)

    assert provider.client().pubsubs[0].closed is True
    assert broker.channels.get("events:t1") == []

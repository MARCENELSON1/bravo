from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.domain.realtime.ports import DomainEvent, EventBus, Subscription
from app.infrastructure.realtime.queueing import MAX_QUEUED_EVENTS, offer
from app.infrastructure.redis.connection import RedisProvider

logger = logging.getLogger(__name__)

# How long the pump waits on Redis before looping. It only decides how quickly a
# cancelled subscription notices; events arrive as soon as they are published.
_POLL_INTERVAL_S = 1.0


def _channel(tenant_id: str) -> str:
    """One channel per tenant.

    Isolation is structural: a subscriber only ever listens to its own tenant's
    channel, so another tenant's event is never delivered to be filtered out.
    """
    return f"events:{tenant_id}"


class _RedisSubscription(Subscription):
    """A tenant's stream, fed by a background task listening on its channel."""

    def __init__(self, queue: asyncio.Queue[DomainEvent], task: asyncio.Task[None]) -> None:
        self._queue = queue
        self._task = task

    async def get(self) -> DomainEvent:
        return await self._queue.get()

    def close(self) -> None:
        # Cancelling is what unsubscribes: the pump releases the Pub/Sub
        # connection in its ``finally``. Without this the task would outlive the
        # SSE response and leak a connection per disconnected client.
        self._task.cancel()


class RedisEventBus(EventBus):
    """Pub/Sub event bus shared across replicas.

    Same contract as :class:`InMemoryEventBus`, but ``publish`` reaches every
    process: this is what lets the API run on more than one instance without a
    waiter connected to replica A missing what replica B published.

    **Fire-and-forget on purpose.** Redis Pub/Sub does not persist, and that is
    the right fit: the stream is a "something changed, refetch" nudge, never the
    source of truth. The KDS reads from Postgres and the client polls as a safety
    net, so a dropped event costs a few seconds of staleness — not data.

    **Fail-open**: a Redis outage silences the realtime nudge but never breaks
    the request that published it. Losing an event is an annoyance; failing a
    payment because the notification could not go out is not.
    """

    def __init__(
        self,
        redis: RedisProvider,
        *,
        max_queued_events: int = MAX_QUEUED_EVENTS,
    ) -> None:
        self._redis = redis
        self._max_queued = max_queued_events

    async def publish(self, event: DomainEvent) -> None:
        # Everything, including getting the client, sits inside the guard: the
        # fail-open promise cannot depend on the provider never raising.
        try:
            client = self._redis.client()
            if client is None:
                return
            await client.publish(_channel(event.tenant_id), _encode(event))
        except Exception:
            logger.debug("event publish failed for %s", event.type, exc_info=True)

    def subscribe(self, tenant_id: str) -> Subscription:
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue(maxsize=self._max_queued)
        task = asyncio.create_task(self._pump(tenant_id, queue))
        return _RedisSubscription(queue, task)

    async def _pump(self, tenant_id: str, queue: asyncio.Queue[DomainEvent]) -> None:
        """Forward this tenant's channel into the subscriber's queue.

        Runs until cancelled by ``close()``. Any Redis failure ends the pump
        quietly: the SSE response keeps heart-beating and the client's poll keeps
        it correct, which is the degraded mode we want.
        """
        pubsub = None
        try:
            client = self._redis.pubsub_client()
            if client is None:
                return
            pubsub = client.pubsub()
            await pubsub.subscribe(_channel(tenant_id))
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=_POLL_INTERVAL_S
                )
                if message is None:
                    continue
                event = _decode(message.get("data"), tenant_id)
                if event is not None:
                    offer(queue, event)
        except asyncio.CancelledError:
            raise
        except Exception:  # pragma: no cover - transient backend failure
            logger.debug("event subscription for %s ended", tenant_id, exc_info=True)
        finally:
            if pubsub is not None:
                try:
                    await pubsub.aclose()
                except Exception:  # pragma: no cover - best effort on teardown
                    logger.debug("pubsub close failed", exc_info=True)


def _encode(event: DomainEvent) -> str:
    return json.dumps({"type": event.type, "payload": event.payload})


def _decode(raw: Any, tenant_id: str) -> DomainEvent | None:
    """Rebuild the event. ``tenant_id`` comes from the channel, never the payload,
    so a malformed message cannot claim to belong to another tenant."""
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return DomainEvent(
            type=str(data["type"]),
            tenant_id=tenant_id,
            payload=dict(data.get("payload") or {}),
        )
    except Exception:
        logger.debug("dropping malformed event on %s", tenant_id, exc_info=True)
        return None

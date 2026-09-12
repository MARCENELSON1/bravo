"""Back-pressure policy shared by both event bus adapters.

A subscriber that stops draining — a phone that lost signal with its SSE stream
still open — must never cost the publisher anything. Both buses therefore hand
events over the same way: bounded queue, never block, drop the oldest.
"""

from __future__ import annotations

import asyncio
import logging

from app.domain.realtime.ports import DomainEvent

logger = logging.getLogger(__name__)

# Roughly a minute of a very busy service. Past this the subscriber is not
# keeping up, and the freshest events are the ones worth keeping.
MAX_QUEUED_EVENTS = 100


def offer(queue: asyncio.Queue[DomainEvent], event: DomainEvent) -> None:
    """Enqueue without ever blocking the publisher.

    ``await queue.put()`` would stall whoever is publishing — in the in-process
    bus, that is the waiter's own request — because some other client stopped
    reading. When the queue is full the oldest event is dropped instead: the
    newest state is what matters, and the client refetches anyway.
    """
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:  # pragma: no cover - drained in between
            pass
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:  # pragma: no cover - another producer refilled it
            logger.debug("dropping event, subscriber queue is full")

"""The timer that runs the outbox.

An asyncio task inside the API process rather than a separate service: the work
is a few notifications a minute, and a second deployable would cost more to run
and operate than it saves. Because claims are exclusive (``FOR UPDATE SKIP
LOCKED``), running one of these in every replica is safe and gives the drain the
same redundancy as the API itself — no leader election, no scheduler.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class OutboxWorker:
    """Calls ``run_once`` every ``interval_s`` until stopped.

    Deliberately unkillable by its own work: a pass that raises is logged and the
    loop sleeps on to the next one, because a worker that dies quietly is worse
    than one that keeps failing loudly — the first stops every future push too.
    """

    def __init__(
        self,
        run_once: Callable[[], Awaitable[object]],
        *,
        interval_s: int = 5,
    ) -> None:
        self._run_once = run_once
        self._interval_s = interval_s
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop(), name="outbox-worker")

    async def stop(self) -> None:
        """Stop on shutdown. Anything already claimed but not finished keeps its
        row: the lease expires and another pass (or another replica) picks it up,
        which is the point of leasing rather than flagging."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._interval_s)
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — the loop outlives any single pass
                logger.warning("outbox worker pass failed", exc_info=True)

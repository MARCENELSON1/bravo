"""The timer. What matters is that it keeps going and that it stops cleanly."""

from __future__ import annotations

import asyncio

from app.infrastructure.outbox.worker import OutboxWorker


async def _settle() -> None:
    """Let the loop's zero-second sleep and body run."""
    for _ in range(6):
        await asyncio.sleep(0)


async def test_a_failing_pass_does_not_kill_the_loop():
    """A worker that dies quietly is worse than one that fails loudly: it takes
    every future push with it, and nothing says so."""
    calls = 0

    async def flaky() -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("database went away")

    worker = OutboxWorker(flaky, interval_s=0)
    worker.start()
    await _settle()
    await worker.stop()

    assert calls > 1, "kept running after the failed pass"


async def test_stop_ends_the_task_and_can_be_called_twice():
    async def noop() -> None:
        return None

    worker = OutboxWorker(noop, interval_s=0)
    worker.start()
    worker.start()  # idempotent: no second loop
    await _settle()
    await worker.stop()
    await worker.stop()  # shutdown paths run more than once; must not raise

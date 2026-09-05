"""Argon2 hashing: correctness, and that it stays off the event loop.

The blocking-vs-threaded behaviour is the point of these tests: Argon2 is
memory-hard by design, so hashing inline would stall every other request in the
process (SSE streams, the KDS board, a charge in flight).
"""

from __future__ import annotations

import asyncio

from app.infrastructure.security.hasher import Argon2Hasher

# Generated with the adapter's own parameters before the move to a worker
# thread. Guards against silently re-tuning Argon2, which would lock every
# existing user out of their account.
_LEGACY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$mZjV7P93s8ChgHjHIWomKw"
    "$S1MgY/TYIXYd7CnkwsLw/YbLPc4mBef4IfT0XVE5wOk"
)
_LEGACY_PASSWORD = "Sup3rSecret!"


async def test_hash_then_verify_roundtrip():
    hasher = Argon2Hasher()
    digest = await hasher.hash("Sup3rSecret!")
    assert digest != "Sup3rSecret!"
    assert await hasher.verify("Sup3rSecret!", digest) is True


async def test_verify_rejects_wrong_password():
    hasher = Argon2Hasher()
    digest = await hasher.hash("Sup3rSecret!")
    assert await hasher.verify("otra-password", digest) is False


async def test_verify_rejects_corrupt_hash_without_raising():
    hasher = Argon2Hasher()
    assert await hasher.verify("Sup3rSecret!", "no-es-un-hash") is False


async def test_verify_accepts_hashes_stored_before_the_change():
    hasher = Argon2Hasher()
    assert await hasher.verify(_LEGACY_PASSWORD, _LEGACY_HASH) is True


async def test_hashing_does_not_block_the_event_loop():
    """The regression this whole change exists for.

    A ticker task is started and the hash is awaited with no yield point in
    between: if hashing ran inline the coroutine would never hand control back,
    so the ticker would not advance a single step.
    """
    hasher = Argon2Hasher()
    ticks = 0

    async def ticker() -> None:
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0)

    task = asyncio.create_task(ticker())
    try:
        await hasher.hash("Sup3rSecret!")
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    assert ticks > 0, "el event loop quedó bloqueado durante el hasheo"


async def test_concurrent_hashes_do_not_interfere():
    hasher = Argon2Hasher()
    passwords = ["uno", "dos", "tres", "cuatro"]

    digests = await asyncio.gather(*(hasher.hash(p) for p in passwords))

    assert len(set(digests)) == len(passwords)  # salted: no two are equal
    results = await asyncio.gather(
        *(hasher.verify(p, d) for p, d in zip(passwords, digests, strict=True))
    )
    assert all(results)

from __future__ import annotations

import asyncio

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.domain.identity.ports import PasswordHasher


class Argon2Hasher(PasswordHasher):
    """Argon2id password hashing (no 72-byte limit, sane defaults).

    Hashing is deliberately CPU-heavy (~50-100 ms), so it runs in a worker
    thread: on a single-process API, doing it inline would freeze the event
    loop — SSE streams, the KDS board and payments included — for the whole
    duration of every login. The parameters are untouched, so hashes stored
    before this change keep verifying.
    """

    def __init__(self) -> None:
        self._ph = Argon2PasswordHasher()

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._ph.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        try:
            return await asyncio.to_thread(self._ph.verify, password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

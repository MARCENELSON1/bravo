from __future__ import annotations

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.domain.identity.ports import PasswordHasher


class Argon2Hasher(PasswordHasher):
    """Argon2id password hashing (no 72-byte limit, sane defaults)."""

    def __init__(self) -> None:
        self._ph = Argon2PasswordHasher()

    def hash(self, password: str) -> str:
        return self._ph.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._ph.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

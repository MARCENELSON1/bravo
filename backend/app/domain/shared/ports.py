from __future__ import annotations

from abc import ABC, abstractmethod


class TokenCipher(ABC):
    """Symmetric encryption for secrets at rest (e.g. tenants' gateway tokens).

    Implementations keep the key out of the domain; ciphertext is what gets
    persisted, plaintext only ever lives in memory at the moment of use.
    """

    @abstractmethod
    def encrypt(self, plaintext: str) -> str: ...

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str: ...

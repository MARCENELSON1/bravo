from __future__ import annotations

from cryptography.fernet import Fernet

from app.domain.shared.ports import TokenCipher


class FernetTokenCipher(TokenCipher):
    """``TokenCipher`` backed by Fernet (AES-128-CBC + HMAC). The key is a
    url-safe base64 32-byte value from ``CREDENTIALS_ENCRYPTION_KEY`` (generate
    with ``Fernet.generate_key()``); it lives only in the environment.

    The Fernet instance is built lazily so the container can wire the cipher even
    when no key is configured (it only fails if something actually encrypts)."""

    def __init__(self, key: str) -> None:
        self._key = key
        self._fernet: Fernet | None = None

    def _cipher(self) -> Fernet:
        if self._fernet is None:
            self._fernet = Fernet(self._key.encode())
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        return self._cipher().encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._cipher().decrypt(ciphertext.encode()).decode()

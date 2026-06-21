from __future__ import annotations

from cryptography.fernet import Fernet

from app.domain.shared.ports import TokenCipher


class FernetTokenCipher(TokenCipher):
    """``TokenCipher`` backed by Fernet (AES-128-CBC + HMAC). The key is a
    url-safe base64 32-byte value from ``CREDENTIALS_ENCRYPTION_KEY`` (generate
    with ``Fernet.generate_key()``); it lives only in the environment."""

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()

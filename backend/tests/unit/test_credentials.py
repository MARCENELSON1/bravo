from __future__ import annotations

from cryptography.fernet import Fernet

from app.infrastructure.security.fernet_cipher import FernetTokenCipher


def test_cipher_roundtrip() -> None:
    cipher = FernetTokenCipher(Fernet.generate_key().decode())
    token = "APP_USR-1234567890-secret-access-token"

    encrypted = cipher.encrypt(token)

    assert encrypted != token
    assert cipher.decrypt(encrypted) == token


def test_cipher_two_encryptions_differ_but_decrypt_same() -> None:
    cipher = FernetTokenCipher(Fernet.generate_key().decode())
    token = "refresh-token"

    a = cipher.encrypt(token)
    b = cipher.encrypt(token)

    # Fernet embeds a timestamp/IV, so ciphertexts differ even for the same input.
    assert a != b
    assert cipher.decrypt(a) == token
    assert cipher.decrypt(b) == token

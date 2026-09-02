from __future__ import annotations

from cryptography.fernet import Fernet

from app.application.payment.connect_mercadopago import sign_oauth_state, verify_oauth_state
from app.infrastructure.payments.credentials_resolver import DbPaymentCredentialsResolver
from app.infrastructure.security.fernet_cipher import FernetTokenCipher


class _NoCredsRepo:
    async def get_by_tenant(self, tenant_id: str, provider: str) -> None:
        return None

    async def get_by_account_id(self, account_id: str) -> None:
        return None


async def test_resolver_fallback_force_sandbox_marks_sandbox() -> None:
    # Token de test user (APP_USR-, "parece prod") + force_sandbox → checkout sandbox.
    resolver = DbPaymentCredentialsResolver(
        credentials=_NoCredsRepo(),  # type: ignore[arg-type]
        oauth=None,  # type: ignore[arg-type]
        cipher=None,  # type: ignore[arg-type]
        fallback_token="APP_USR-test-seller-token",
        force_sandbox=True,
    )
    creds = await resolver.for_tenant("t1")
    assert creds.live_mode is False


async def test_resolver_fallback_app_usr_is_live_without_force() -> None:
    resolver = DbPaymentCredentialsResolver(
        credentials=_NoCredsRepo(),  # type: ignore[arg-type]
        oauth=None,  # type: ignore[arg-type]
        cipher=None,  # type: ignore[arg-type]
        fallback_token="APP_USR-real-prod-token",
    )
    creds = await resolver.for_tenant("t1")
    assert creds.live_mode is True  # sin force_sandbox: la heurística lo toma como prod


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


def test_oauth_state_roundtrip() -> None:
    state = sign_oauth_state("secret", "tenant-1", 1000)
    assert verify_oauth_state("secret", state, now=1000, max_age_s=600) == "tenant-1"


def test_oauth_state_tampered_or_wrong_secret_rejected() -> None:
    state = sign_oauth_state("secret", "tenant-1", 1000)
    assert verify_oauth_state("secret", state + "x", now=1000, max_age_s=600) is None
    assert verify_oauth_state("other-secret", state, now=1000, max_age_s=600) is None
    assert verify_oauth_state("secret", "garbage", now=1000, max_age_s=600) is None


def test_oauth_state_expired_rejected() -> None:
    state = sign_oauth_state("secret", "tenant-1", 1000)
    assert verify_oauth_state("secret", state, now=1000 + 601, max_age_s=600) is None

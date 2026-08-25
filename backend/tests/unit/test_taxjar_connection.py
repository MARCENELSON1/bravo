from __future__ import annotations

import httpx
import pytest

from app.application.tax.taxjar_connection import ConnectTaxJar
from app.domain.tax.credentials import TaxJarCredential
from app.domain.tax.credentials_repository import TaxJarCredentialRepository
from app.domain.tax.exceptions import (
    InvalidTaxProviderCredential,
    TaxProviderUnavailable,
)
from app.domain.tax.ports import TaxCredentialValidator
from app.infrastructure.tax.taxjar_validator import TaxJarCredentialValidator

# --- El validador (infra, contra la API de TaxJar vía MockTransport) ----------


async def test_valid_token_passes():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"rate": {"zip": "90210"}})

    v = TaxJarCredentialValidator(transport=httpx.MockTransport(handler))
    await v.verify(api_token="good-token", sandbox=True)  # no raise

    assert captured["url"].endswith("/v2/rates/90210")
    assert captured["auth"] == "Bearer good-token"


async def test_invalid_token_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Unauthorized"})

    v = TaxJarCredentialValidator(transport=httpx.MockTransport(handler))
    with pytest.raises(InvalidTaxProviderCredential):
        await v.verify(api_token="bad", sandbox=True)


async def test_unreachable_provider_is_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    v = TaxJarCredentialValidator(transport=httpx.MockTransport(handler))
    with pytest.raises(TaxProviderUnavailable):
        await v.verify(api_token="x", sandbox=True)


async def test_server_error_is_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    v = TaxJarCredentialValidator(transport=httpx.MockTransport(handler))
    with pytest.raises(TaxProviderUnavailable):
        await v.verify(api_token="x", sandbox=True)


# --- ConnectTaxJar valida ANTES de guardar (que "conectado" no mienta) --------


class _FakeCreds(TaxJarCredentialRepository):
    def __init__(self) -> None:
        self.stored: TaxJarCredential | None = None

    async def get_by_tenant(self, tenant_id: str) -> TaxJarCredential | None:
        return self.stored

    async def upsert(self, credential: TaxJarCredential) -> None:
        self.stored = credential

    async def delete(self, tenant_id: str) -> None:
        self.stored = None


class _FakeCipher:
    def encrypt(self, plaintext: str) -> str:
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext.removeprefix("enc:")


class _OkValidator(TaxCredentialValidator):
    async def verify(self, *, api_token: str, sandbox: bool) -> None:
        pass


class _BadValidator(TaxCredentialValidator):
    async def verify(self, *, api_token: str, sandbox: bool) -> None:
        raise InvalidTaxProviderCredential()


class _NoopCtx:
    def set(self, tenant_id: str) -> None:
        pass


async def test_connect_validates_then_stores_encrypted():
    creds = _FakeCreds()
    uc = ConnectTaxJar(creds, _FakeCipher(), _OkValidator(), _NoopCtx())
    await uc.execute(tenant_id="t1", api_token="tok", sandbox=True)
    assert creds.stored is not None
    assert creds.stored.api_token == "enc:tok"  # cifrado en reposo
    assert creds.stored.sandbox is True


async def test_connect_rejects_bad_token_without_storing():
    creds = _FakeCreds()
    uc = ConnectTaxJar(creds, _FakeCipher(), _BadValidator(), _NoopCtx())
    with pytest.raises(InvalidTaxProviderCredential):
        await uc.execute(tenant_id="t1", api_token="bad", sandbox=True)
    assert creds.stored is None  # no guardó nada

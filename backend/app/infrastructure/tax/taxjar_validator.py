"""TaxJar adapter: verify an API token before we store it.

A cheap authenticated call (``GET /v2/rates/{zip}``) is enough to tell a working
token from a bad one: 2xx means it authenticates, 401/403 means the token is
invalid, anything else (network / 5xx) means we couldn't verify right now. The
token is passed in only to test it and is never logged. ``transport`` is
injectable so tests replay TaxJar's response without a network call."""

from __future__ import annotations

import httpx

from app.domain.tax.exceptions import (
    InvalidTaxProviderCredential,
    TaxProviderUnavailable,
)
from app.domain.tax.ports import TaxCredentialValidator

_SANDBOX_BASE = "https://api.sandbox.taxjar.com"
_LIVE_BASE = "https://api.taxjar.com"
_PROBE_ZIP = "90210"  # any valid ZIP; the call just needs to authenticate


class TaxJarCredentialValidator(TaxCredentialValidator):
    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    async def verify(self, *, api_token: str, sandbox: bool) -> None:
        base = _SANDBOX_BASE if sandbox else _LIVE_BASE
        try:
            async with httpx.AsyncClient(
                base_url=base,
                transport=self._transport,
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=10.0,
            ) as client:
                resp = await client.get(f"/v2/rates/{_PROBE_ZIP}")
        except httpx.HTTPError as exc:  # network / timeout
            raise TaxProviderUnavailable() from exc
        if resp.status_code in (401, 403):
            raise InvalidTaxProviderCredential()
        if resp.status_code >= 400:
            raise TaxProviderUnavailable()

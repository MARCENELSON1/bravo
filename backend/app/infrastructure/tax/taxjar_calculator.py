"""TaxJar adapter: real US sales-tax rate by jurisdiction (the ADDED model).

Calls TaxJar's ``POST /v2/taxes`` with the point-of-sale address and the taxable
subtotal; returns how much tax to add. Money crosses the API boundary as a float
in major units (dollars); inside the domain it is always an integer in minor
units. The token is passed in from settings (env only) and never logged.
``transport`` is injectable so tests replay the real sandbox response without a
network call.
"""

from __future__ import annotations

import httpx

from app.domain.shared.money import Money
from app.domain.tax.ports import TaxCalculator
from app.domain.tax.value_objects import FiscalAddress, TaxCalculation

_SANDBOX_BASE = "https://api.sandbox.taxjar.com"
_LIVE_BASE = "https://api.taxjar.com"
_MINOR_UNIT = 100  # USD (and the launch currencies) use 2 decimals


def _jurisdiction(j: dict) -> str | None:
    parts = [j.get("city"), j.get("county"), j.get("state")]
    named = [str(p) for p in parts if p]
    return ", ".join(named) if named else None


class TaxJarCalculator(TaxCalculator):
    def __init__(
        self,
        api_token: str,
        *,
        sandbox: bool = True,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token = api_token
        self._base = _SANDBOX_BASE if sandbox else _LIVE_BASE
        self._transport = transport  # injectable for tests (httpx.MockTransport)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base,
            transport=self._transport,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=10.0,
        )

    async def calculate(self, *, taxable: Money, address: FiscalAddress) -> TaxCalculation:
        # Dine-in: the sale is sourced at the venue → from == to.
        body = {
            "from_country": address.country,
            "from_zip": address.zip,
            "from_state": address.state,
            "from_city": address.city,
            "from_street": address.street,
            "to_country": address.country,
            "to_zip": address.zip,
            "to_state": address.state,
            "to_city": address.city,
            "to_street": address.street,
            "amount": taxable.amount / _MINOR_UNIT,
            "shipping": 0,
        }
        async with self._client() as client:
            resp = await client.post("/v2/taxes", json=body)
            resp.raise_for_status()
            data = resp.json().get("tax") or {}

        # ``amount_to_collect`` is authoritative (TaxJar applies the jurisdiction's
        # rounding rules); we only round the float major-units back to minor units.
        tax_amount = round(float(data.get("amount_to_collect") or 0) * _MINOR_UNIT)
        rate_bps = round(float(data.get("rate") or 0) * 10000)
        tax = Money(tax_amount, taxable.currency)
        return TaxCalculation(
            subtotal=taxable,
            tax=tax,
            total=taxable.plus(tax),
            rate_bps=rate_bps,
            jurisdiction=_jurisdiction(data.get("jurisdictions") or {}),
        )

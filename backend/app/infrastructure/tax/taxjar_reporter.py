"""TaxJar adapter: report a settled sale so TaxJar can file/remit it (AutoFile).

Calls ``POST /v2/transactions/orders`` with the sale's totals and point-of-sale
address. ``transaction_id`` is the order id, so re-sending the same order is
idempotent: TaxJar answers 422 "already been taken", which we treat as success
(the sale is already recorded). Money crosses the boundary as a float in major
units; inside the domain it is always integer minor units. The token comes from
settings (env only) and is never logged. ``transport`` is injectable so tests
replay TaxJar's response without a network call.
"""

from __future__ import annotations

import httpx

from app.domain.tax.ports import TaxReporter
from app.domain.tax.value_objects import TaxSale

_SANDBOX_BASE = "https://api.sandbox.taxjar.com"
_LIVE_BASE = "https://api.taxjar.com"
_MINOR_UNIT = 100  # USD (and the launch currencies) use 2 decimals


class TaxJarReporter(TaxReporter):
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

    async def report_sale(self, sale: TaxSale) -> str:
        a = sale.address
        body = {
            "transaction_id": sale.transaction_id,
            "transaction_date": sale.occurred_at,
            "to_country": a.country,
            "to_zip": a.zip,
            "to_state": a.state,
            "to_city": a.city,
            "to_street": a.street,
            # ``amount`` is the sale total EXCLUDING sales tax (TaxJar re-adds it).
            "amount": sale.amount.amount / _MINOR_UNIT,
            "shipping": 0,
            "sales_tax": sale.sales_tax.amount / _MINOR_UNIT,
        }
        async with self._client() as client:
            resp = await client.post("/v2/transactions/orders", json=body)
        # Idempotent: a re-report of an existing transaction is already filed.
        if resp.status_code == 422 and "already" in resp.text.lower():
            return sale.transaction_id
        resp.raise_for_status()
        order = resp.json().get("order") or {}
        return str(order.get("transaction_id") or sale.transaction_id)

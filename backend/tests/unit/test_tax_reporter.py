from __future__ import annotations

import json

import httpx

from app.domain.shared.money import Money
from app.domain.tax.value_objects import FiscalAddress, TaxSale
from app.infrastructure.tax.taxjar_reporter import TaxJarReporter

_ADDRESS = FiscalAddress(
    street="1218 3rd St", city="Santa Monica", state="CA", zip="90404", country="US"
)
_SALE = TaxSale(
    transaction_id="order-123",
    amount=Money(10000, "USD"),  # $100 pre-tax subtotal
    sales_tax=Money(1075, "USD"),  # $10.75 collected
    address=_ADDRESS,
    occurred_at="2026-08-25T18:00:00+00:00",
)


async def test_reporter_posts_transaction_and_returns_id():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            201, json={"order": {"transaction_id": "order-123", "amount": 100.0}}
        )

    reporter = TaxJarReporter("tok", sandbox=True, transport=httpx.MockTransport(handler))
    external_id = await reporter.report_sale(_SALE)

    assert captured["url"].endswith("/v2/transactions/orders")
    body = captured["body"]
    assert body["transaction_id"] == "order-123"
    assert body["transaction_date"] == "2026-08-25T18:00:00+00:00"
    # amount is the pre-tax subtotal in major units; sales_tax reported separately.
    assert body["amount"] == 100.0
    assert body["sales_tax"] == 10.75
    assert body["to_zip"] == "90404"
    assert external_id == "order-123"


async def test_reporter_is_idempotent_on_duplicate():
    # Re-reporting an already-recorded order: TaxJar answers 422 "already been
    # taken" — we treat it as success (the sale is already filed), not an error.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422, json={"error": "Unprocessable Entity", "detail": "has already been taken"}
        )

    reporter = TaxJarReporter("tok", sandbox=True, transport=httpx.MockTransport(handler))
    external_id = await reporter.report_sale(_SALE)
    assert external_id == "order-123"


async def test_reporter_raises_on_other_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Unauthorized"})

    reporter = TaxJarReporter("tok", sandbox=True, transport=httpx.MockTransport(handler))
    try:
        await reporter.report_sale(_SALE)
    except httpx.HTTPStatusError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected an HTTPStatusError on a non-duplicate failure")

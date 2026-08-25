from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.shared.money import Money
from app.domain.tax.value_objects import FiscalAddress, TaxCalculation, TaxSale
from app.domain.tenant.regional import TaxEngine


class TaxCalculator(ABC):
    """Computes the sales tax to add on top of a taxable subtotal for a given
    point-of-sale address.

    Adapters: ``TaxJarCalculator`` (real rate by jurisdiction), ``FlatRateTaxCalculator``
    (deterministic, for tests / a v1 flat rate) and ``IncludedTaxCalculator``
    (tax-inclusive regime → nothing to add). Which one runs is chosen per tenant
    by the engine resolver from ``tenant.tax_engine``.
    """

    @abstractmethod
    async def calculate(self, *, taxable: Money, address: FiscalAddress) -> TaxCalculation: ...


class TaxEngineResolver(ABC):
    """Picks the ``TaxCalculator`` for a tenant's configured engine — the one
    place the AR-vs-US decision is made. Consumers stay engine-agnostic."""

    @abstractmethod
    def for_engine(self, engine: TaxEngine) -> TaxCalculator: ...


class TaxReporter(ABC):
    """Reports a settled taxable sale to the tax provider so it can be filed and
    remitted (TaxJar AutoFile). Must be idempotent on ``sale.transaction_id`` —
    re-reporting the same order is a safe no-op. Returns the provider's
    transaction id.

    Only ever invoked for tenants on a reporting engine (US/TaxJar); AR never
    reaches it (no tax is collected, so nothing is ever enqueued to report).
    """

    @abstractmethod
    async def report_sale(self, sale: TaxSale) -> str: ...


class TaxReporterResolver(ABC):
    """Builds the reporter for a tenant from its **own** TaxJar credential.

    AutoFile files under the taxpayer's account, so reporting is strictly
    per-tenant: returns ``None`` when the tenant hasn't connected TaxJar (there
    is nothing to file under, and never a fallback to a shared platform account).
    """

    @abstractmethod
    async def reporter_for(self, tenant_id: str) -> TaxReporter | None: ...


class TaxCredentialValidator(ABC):
    """Verifies a tax-provider API token actually works before we store it, so
    "connected" is never a lie. Raises ``InvalidTaxProviderCredential`` for a bad
    token and ``TaxProviderUnavailable`` when the provider can't be reached."""

    @abstractmethod
    async def verify(self, *, api_token: str, sandbox: bool) -> None: ...

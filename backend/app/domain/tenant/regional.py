from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TaxRegime(StrEnum):
    """Which fiscal engine a tenant operates under.

    Drives which invoicing gateway (AFIP vs a plain US receipt) and which tax
    model (VAT-inclusive vs sales-tax-added) applies. Read per tenant at runtime.
    """

    AR_AFIP = "AR_AFIP"
    US_SALES_TAX = "US_SALES_TAX"


class TaxEngine(StrEnum):
    """External rate/calculation engine for the tenant's sales tax.

    ``NONE`` = the tax comes from the regime itself (AR: IVA is a single national
    rate, no external lookup). US tenants use an engine to resolve the combined
    state/county/city rate.
    """

    NONE = "NONE"
    TAXJAR = "TAXJAR"
    AVALARA = "AVALARA"


@dataclass(frozen=True)
class RegionalDefaults:
    """The fiscal/locale profile a tenant inherits from its country at onboarding."""

    tax_regime: TaxRegime
    currency: str
    locale: str
    timezone: str
    tax_engine: TaxEngine


# Country (ISO-3166 alpha-2) → its default profile. Unknown countries fall back
# to AR so existing/legacy tenants keep today's behavior (parity).
_DEFAULTS_BY_COUNTRY: dict[str, RegionalDefaults] = {
    "AR": RegionalDefaults(
        tax_regime=TaxRegime.AR_AFIP,
        currency="ARS",
        locale="es-AR",
        timezone="America/Argentina/Buenos_Aires",
        tax_engine=TaxEngine.NONE,
    ),
    "US": RegionalDefaults(
        tax_regime=TaxRegime.US_SALES_TAX,
        currency="USD",
        locale="en-US",
        # The US spans many zones; this is the onboarding default, adjustable later.
        timezone="America/New_York",
        tax_engine=TaxEngine.TAXJAR,
    ),
}

_FALLBACK = _DEFAULTS_BY_COUNTRY["AR"]


def regional_defaults(country: str | None) -> RegionalDefaults:
    """Map a 2-letter country code to its fiscal/locale defaults.

    Case-insensitive; unknown or empty falls back to AR (today everyone is AR).
    """
    return _DEFAULTS_BY_COUNTRY.get((country or "AR").strip().upper(), _FALLBACK)

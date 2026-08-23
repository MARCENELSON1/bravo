from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.tenant.regional import TaxEngine, TaxRegime


@dataclass
class Tenant:
    """A tenant (a single business/workspace). Not itself tenant-scoped."""

    id: str
    slug: str
    name: str
    country: str = "AR"
    currency: str = "ARS"
    standard_workday_minutes: int = 480
    # Regional/fiscal identity — defaults are AR so any Tenant built without these
    # behaves exactly as today (parity). Derived from `country` at onboarding.
    tax_regime: TaxRegime = TaxRegime.AR_AFIP
    locale: str = "es-AR"
    timezone: str = "America/Argentina/Buenos_Aires"
    tax_engine: TaxEngine = TaxEngine.NONE
    created_at: datetime | None = None

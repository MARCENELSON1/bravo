from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from app.domain.invoice.entities import Invoice
from app.domain.invoice.value_objects import FiscalCondition


@dataclass(frozen=True)
class CaeResult:
    """Resultado de pedir el CAE a AFIP (o al fake). ``authorized`` False trae
    las observaciones/errores en ``observations``."""

    authorized: bool
    number: int | None
    cae: str | None
    cae_expiration: date | None
    observations: str | None


class ElectronicInvoicing(ABC):
    """Port de facturación electrónica. ``FakeInvoicing`` (dev/MVP) autoriza al
    instante; ``AfipInvoicing`` (WSAA + WSFEv1) se enchufa detrás del mismo port.
    El adapter resuelve las credenciales del tenant por ``invoice.tenant_id``."""

    @abstractmethod
    async def authorize(self, *, invoice: Invoice) -> CaeResult: ...


@dataclass(frozen=True)
class ResolvedTaxCredentials:
    cuit: str
    certificate: str  # PEM en claro (solo en memoria)
    private_key: str
    point_of_sale: int
    fiscal_condition: FiscalCondition
    live_mode: bool


class TaxCredentialsResolver(ABC):
    @abstractmethod
    async def for_tenant(self, tenant_id: str) -> ResolvedTaxCredentials: ...

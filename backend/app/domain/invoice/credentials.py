from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.invoice.value_objects import FiscalCondition


@dataclass
class TaxCredential:
    """Credenciales fiscales del tenant (su CUIT + certificado AFIP). El
    certificado y la clave privada se guardan **cifrados** en reposo; en memoria
    son PEM en claro. ``live_mode`` False = homologación (testing)."""

    id: str
    tenant_id: str
    cuit: str
    certificate: str
    private_key: str
    point_of_sale: int
    fiscal_condition: FiscalCondition
    live_mode: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

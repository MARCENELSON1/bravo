from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaxJarCredential:
    """La credencial de TaxJar de un tenant (su propia cuenta). El ``api_token``
    se guarda **cifrado** en reposo; en memoria es texto en claro solo tras
    desencriptar. ``sandbox`` False = entorno productivo (AutoFile real).

    Es per-tenant a propósito: cada declaración se presenta bajo la cuenta del
    contribuyente (su nexus, sus estados, su calendario), nunca bajo una cuenta
    de plataforma compartida."""

    id: str
    tenant_id: str
    api_token: str
    sandbox: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

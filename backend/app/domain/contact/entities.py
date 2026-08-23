from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContactLog:
    """Un contacto registrado a un cliente (CRM Fase 12, loop de resultado). El
    dueño marca "contactado" tras escribirle por WhatsApp; después medimos si
    volvió. ``reason`` = por qué se sugirió (ej. "en_riesgo")."""

    id: str
    tenant_id: str
    customer_id: str
    reason: str
    contacted_by: str
    contacted_at: datetime | None = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Customer:
    """A customer (cliente) of the local, scoped to a tenant. Foundation of the
    CRM (Fase 12): manual for now; auto-identity matching from payments/reservas
    is a later slice. ``phone`` is stored as digits (E.164-ish) so a ``wa.me``
    deep link works. ``no_contactar`` is a hard opt-out honored everywhere."""

    id: str
    tenant_id: str
    name: str
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    no_contactar: bool = False
    created_at: datetime | None = None

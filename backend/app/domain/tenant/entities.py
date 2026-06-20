from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Tenant:
    """A tenant (a single business/workspace). Not itself tenant-scoped."""

    id: str
    slug: str
    name: str
    country: str = "AR"
    currency: str = "ARS"
    created_at: datetime | None = None

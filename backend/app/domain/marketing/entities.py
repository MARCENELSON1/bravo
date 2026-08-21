"""Marketing (captación). A diferencia del resto del dominio, esto NO es
multi-tenant: un lead es un prospecto de Wellnod, todavía no un comercio."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lead:
    """Un interesado que dejó sus datos en la landing."""

    email: str
    name: str | None = None
    message: str | None = None

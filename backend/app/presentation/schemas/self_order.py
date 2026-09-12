from __future__ import annotations

from pydantic import BaseModel


class SelfOrderSettingsResponse(BaseModel):
    enabled: bool
    requires_confirmation: bool
    # Fase 3: modo (READ_ONLY | SALON | SELF_SERVICE), derivado de los flags, +
    # el flag de pagar-primero. La UI muestra el modo; los flags son el storage.
    prepay_required: bool = False
    mode: str = "READ_ONLY"


class UpdateSelfOrderSettingsRequest(BaseModel):
    # Preferido: ``mode`` (deriva los flags). Compat Fase 1/2: los flags crudos
    # ``enabled``/``requires_confirmation`` (que nunca prenden prepay).
    mode: str | None = None
    enabled: bool | None = None
    requires_confirmation: bool | None = None

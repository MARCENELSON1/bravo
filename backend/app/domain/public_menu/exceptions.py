from __future__ import annotations

from app.domain.errors import DomainError


class InvalidTableQrToken(DomainError):
    code = "invalid_table_qr_token"
    message = "El código QR de la mesa no es válido o expiró."

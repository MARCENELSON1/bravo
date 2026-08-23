from __future__ import annotations

from app.domain.errors import DomainError


class CustomerNotFound(DomainError):
    code = "customer_not_found"
    message = "No encontramos el cliente indicado."

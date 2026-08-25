from __future__ import annotations

from app.domain.errors import DomainError


class InvalidTaxProviderCredential(DomainError):
    code = "invalid_tax_provider_credential"
    message = "El token de TaxJar no es válido. Revisá que lo hayas copiado bien."


class TaxProviderUnavailable(DomainError):
    code = "tax_provider_unavailable"
    message = "No pudimos verificar el token con TaxJar ahora. Probá de nuevo en un momento."

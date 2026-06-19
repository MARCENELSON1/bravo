from app.domain.errors import DomainError


class TenantNotFound(DomainError):
    code = "tenant_not_found"
    message = "No encontramos el comercio indicado."


class TenantAlreadyExists(DomainError):
    code = "tenant_already_exists"
    message = "Ya existe un comercio con esos datos."

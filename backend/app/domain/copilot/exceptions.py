from __future__ import annotations

from app.domain.errors import DomainError


class UnsafeQuery(DomainError):
    code = "unsafe_query"
    message = "No pudimos correr esa consulta de forma segura."


class CopilotDisabled(DomainError):
    code = "copilot_disabled"
    message = "El copiloto no está habilitado."


class CopilotQueryError(DomainError):
    code = "copilot_query_error"
    message = "No pudimos responder esa pregunta."

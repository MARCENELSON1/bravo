from __future__ import annotations

from app.domain.errors import DomainError


class InvalidAdvisorSettings(DomainError):
    code = "invalid_advisor_settings"
    message = "Los datos de costos no son válidos."

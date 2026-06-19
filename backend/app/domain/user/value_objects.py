from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.domain.user.exceptions import InvalidEmail

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Role(StrEnum):
    """Roles within a tenant."""

    OWNER = "OWNER"
    MANAGER = "MANAGER"
    WAITER = "WAITER"
    KITCHEN = "KITCHEN"
    CASHIER = "CASHIER"


@dataclass(frozen=True)
class Email:
    """Validated, normalized email address (lowercased, trimmed)."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise InvalidEmail()
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

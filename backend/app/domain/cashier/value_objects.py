from __future__ import annotations

from enum import StrEnum


class CashSessionStatus(StrEnum):
    """Lifecycle of a register session (turno de caja)."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashMovementKind(StrEnum):
    """A manual cash-drawer movement that is NOT a sale: it moves physical cash
    in or out of the drawer and so shifts what the arqueo Z should find at close.

    - ``DEPOSIT`` (ingreso/reposición de cambio): cash in  → +
    - ``DROP`` (sangría / retiro a caja fuerte):  cash out → −
    - ``PAYOUT`` (pago en efectivo desde el cajón): cash out → −
    """

    DEPOSIT = "DEPOSIT"
    DROP = "DROP"
    PAYOUT = "PAYOUT"

    @property
    def is_inflow(self) -> bool:
        """True if the movement adds cash to the drawer (DEPOSIT)."""
        return self is CashMovementKind.DEPOSIT

    def signed(self, amount: int) -> int:
        """The movement's signed effect on the drawer's cash (+in / −out)."""
        return amount if self.is_inflow else -amount

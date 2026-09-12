from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.public_menu.value_objects import TableQrClaims


class TableQrToken(ABC):
    """Port for the signed table-QR token. Modelled on the presence device token
    (``hmac_presence``): a stateless, signed credential — no DB, stable across
    restarts (so a printed QR keeps working). The token proves which tenant's
    (and table's) public menu to serve; it grants nothing but reading that menu."""

    @abstractmethod
    def issue(self, tenant_id: str, table_id: str) -> str:
        """Mint a signed token for a table (printed into the QR)."""

    @abstractmethod
    def verify(self, token: str) -> TableQrClaims:
        """Validate the signature and return the claims (pure; no I/O). Raises
        ``InvalidTableQrToken`` if the token is malformed or tampered."""

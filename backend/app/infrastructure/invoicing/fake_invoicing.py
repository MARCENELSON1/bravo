from __future__ import annotations

from datetime import date

from app.domain.invoice.entities import Invoice
from app.domain.invoice.ports import CaeResult, ElectronicInvoicing


class FakeInvoicing(ElectronicInvoicing):
    """Dev/MVP transport: authorises immediately with a fixed CAE and incremental
    numbering — lets the whole flow (cobro → facturar → CAE) be tested without
    AFIP. The real WSAA/WSFEv1 adapter slots in behind the same port."""

    def __init__(self) -> None:
        self._counter = 0

    async def authorize(self, *, invoice: Invoice) -> CaeResult:
        self._counter += 1
        return CaeResult(
            authorized=True,
            number=self._counter,
            cae="68000000000001",
            cae_expiration=date(2030, 1, 1),
            observations=None,
        )

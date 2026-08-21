"""Propinas por mozo (read model CQRS-lite) + liquidación.

La propina se atribuye al mozo por ``Order.waiter_id`` del cobro; el pago al mozo
se registra como un egreso (OUTFLOW) categoría "Propinas" con ``counterparty`` =
``waiter_id``, así el saldo pendiente = Σ propinas ganadas − Σ liquidadas y la
caja queda honesta (la plata que sale baja el efectivo). No hay agregado nuevo:
reusa el modelo de pagos/egresos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.domain.cashier.tip_payout import TipPayout, TipPayoutRepository
from app.domain.identity.ports import TenantContext
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository
from app.domain.user.exceptions import UserNotFound
from app.domain.user.repository import UserRepository

# Categoría canónica del egreso de liquidación de propinas (en inglés en código,
# pero es la etiqueta que comparte con el reporte para casar ganado vs pagado).
TIP_PAYOUT_CATEGORY = "Propinas"


@dataclass(frozen=True)
class TipsReportRow:
    waiter_id: str
    waiter_name: str  # nombre del mozo (fallback email); nunca el UUID
    earned: int  # Σ propinas de cobros CONFIRMED de las órdenes de este mozo
    paid: int  # Σ liquidaciones (egreso Propinas) a este mozo
    pending: int  # earned - paid


@dataclass(frozen=True)
class TipsReport:
    currency: str
    rows: list[TipsReportRow]
    earned_total: int
    paid_total: int
    pending_total: int


class TipsReadModel(ABC):
    @abstractmethod
    async def report(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TipsReport: ...


class GetTipsReport:
    def __init__(self, read_model: TipsReadModel, tenant_context: TenantContext) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TipsReport:
        self._tenant_context.set(tenant_id)
        return await self._read_model.report(tenant_id, since=since, until=until)


class PayTips:
    """Liquidar (pagar) propinas a un mozo: registra un **pasivo** en el ledger
    ``tip_payouts``. NO es un egreso → no pega en el resultado del mes; solo salda lo
    que ya se le debía. El saldo pendiente sale del reporte (ganado − liquidado)."""

    def __init__(
        self,
        payouts: TipPayoutRepository,
        users: UserRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._payouts = payouts
        self._users = users
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, waiter_id: str, amount: int, method: str = "CASH"
    ) -> TipPayout:
        self._tenant_context.set(tenant_id)
        waiter = await self._users.get_by_id(tenant_id, waiter_id)
        if waiter is None:
            raise UserNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        payout = TipPayout(
            id=str(uuid4()),
            tenant_id=tenant_id,
            waiter_id=waiter_id,
            amount=amount,
            currency=tenant.currency,
            method=method,
        )
        await self._payouts.add(payout)
        return payout

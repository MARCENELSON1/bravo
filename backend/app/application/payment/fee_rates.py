"""Config de tasas de comisión por método (comisiones slice B). Upsert por método
→ NO reconstruye una entidad global (sin lost-update; por eso vive en tabla propia,
no en advisor_settings)."""

from __future__ import annotations

from app.domain.identity.ports import TenantContext
from app.domain.payment.repository import PaymentFeeRateRepository


class GetPaymentFeeRates:
    def __init__(
        self, rates: PaymentFeeRateRepository, tenant_context: TenantContext
    ) -> None:
        self._rates = rates
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> dict[str, int]:
        self._tenant_context.set(tenant_id)
        return await self._rates.rates_for(tenant_id)


class UpdatePaymentFeeRates:
    def __init__(
        self, rates: PaymentFeeRateRepository, tenant_context: TenantContext
    ) -> None:
        self._rates = rates
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, rates: dict[str, int]) -> dict[str, int]:
        # Solo toca los métodos enviados → no pisa los demás. La validación de método
        # y rango (0–10000 bps) es del schema.
        self._tenant_context.set(tenant_id)
        for method, fee_bps in rates.items():
            await self._rates.save(tenant_id, method, fee_bps)
        return await self._rates.rates_for(tenant_id)

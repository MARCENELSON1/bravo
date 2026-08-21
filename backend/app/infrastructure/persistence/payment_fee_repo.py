from __future__ import annotations

from sqlalchemy import select

from app.domain.payment.repository import PaymentFeeRateRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import PaymentFeeRateORM


class SqlAlchemyPaymentFeeRateRepository(PaymentFeeRateRepository):
    """Lee las tasas de comisión por método del tenant. Sin filas → dict vacío →
    todo 0 → paridad (net == bruto)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def rates_for(self, tenant_id: str) -> dict[str, int]:
        async with self._session_factory() as db:
            rows = (
                await db.execute(
                    select(PaymentFeeRateORM.method, PaymentFeeRateORM.fee_bps).where(
                        PaymentFeeRateORM.tenant_id == tenant_id
                    )
                )
            ).all()
            return {method: int(bps) for method, bps in rows}

    async def save(self, tenant_id: str, method: str, fee_bps: int) -> None:
        async with self._session_factory() as db:
            await db.merge(
                PaymentFeeRateORM(
                    tenant_id=tenant_id, method=method, fee_bps=fee_bps
                )
            )

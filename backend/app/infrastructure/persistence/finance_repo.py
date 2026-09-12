from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.finance.dtos import (
    ExpenseBreakdown,
    ExpenseCategoryRow,
    MovementRow,
    ProductCostPoint,
    ProductDetail,
    ProductSaleLine,
)
from app.application.finance.tax_collected import TaxCollected, TaxCollectedReadModel
from app.application.finance.use_cases import (
    ExpenseBreakdownReadModel,
    FinanceCommissionsReadModel,
    FinanceProductDetailReadModel,
    InventoryValueReadModel,
    RecentMovementsReadModel,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    IngredientORM,
    PaymentORM,
    SaleFactORM,
    TenantORM,
)
from app.infrastructure.persistence.payment_columns import net_collected_col


def _net_line(row: SaleFactORM) -> int:
    """Ventas netas de IVA congeladas de una fila; cae al bruto si aún no está seteado."""
    return row.line_net_amount if row.line_net_amount is not None else row.line_amount


def _net_food(row: SaleFactORM) -> int:
    """Food cost neto congelado de una fila; cae al bruto si aún no está seteado."""
    if row.food_cost_net_amount is not None:
        return row.food_cost_net_amount
    return row.food_cost_amount or 0

_OTROS = "Otros"


async def _tenant_currency(session, tenant_id: str) -> str:
    return (
        await session.execute(select(TenantORM.currency).where(TenantORM.id == tenant_id))
    ).scalar_one_or_none() or "ARS"

# Las cantidades de insumo se guardan en milésimas de la unidad base.
_QUANTITY_SCALE = 1000


class SqlAlchemyFinanceCommissionsReadModel(FinanceCommissionsReadModel):
    """Σ fee_amount y Σ neto cobrado (net_collected_col) sobre cobros
    CONFIRMED/INFLOW en la ventana — mismo predicado que el hero del Home, para
    que cuadren. Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def fees_and_net(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> tuple[int, int]:
        async with self._session_factory() as session:
            stmt = select(
                func.coalesce(func.sum(PaymentORM.fee_amount), 0),
                func.coalesce(func.sum(net_collected_col()), 0),
            ).where(
                PaymentORM.tenant_id == tenant_id,
                PaymentORM.direction == PaymentDirection.INFLOW.value,
                PaymentORM.status == PaymentStatus.CONFIRMED.value,
            )
            if since is not None:
                stmt = stmt.where(PaymentORM.created_at >= since)
            if until is not None:
                stmt = stmt.where(PaymentORM.created_at <= until)
            fees, net = (await session.execute(stmt)).one()
            return int(fees), int(net)


class SqlAlchemyTaxCollectedReadModel(TaxCollectedReadModel):
    """Σ tax_amount sobre cobros CONFIRMED/INFLOW en la ventana (el sales tax
    cobrado, a remitir al fisco). 0 en AR. Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def total(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> TaxCollected:
        async with self._session_factory() as session:
            stmt = select(func.coalesce(func.sum(PaymentORM.tax_amount), 0)).where(
                PaymentORM.tenant_id == tenant_id,
                PaymentORM.direction == PaymentDirection.INFLOW.value,
                PaymentORM.status == PaymentStatus.CONFIRMED.value,
            )
            if since is not None:
                stmt = stmt.where(PaymentORM.created_at >= since)
            if until is not None:
                stmt = stmt.where(PaymentORM.created_at <= until)
            amount = int((await session.execute(stmt)).scalar_one())
            currency = await _tenant_currency(session, tenant_id)
            return TaxCollected(amount=amount, currency=currency)


class SqlAlchemyInventoryValueReadModel(InventoryValueReadModel):
    """Valor del inventario a mano: Σ (stock_qty × unit_cost) / 1000 sobre insumos
    activos (misma técnica que la valuación de mermas). Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def total_value(self, tenant_id: str) -> int:
        async with self._session_factory() as session:
            raw = (
                await session.execute(
                    select(
                        func.coalesce(
                            func.sum(
                                IngredientORM.stock_qty * IngredientORM.unit_cost_amount
                            ),
                            0,
                        )
                    ).where(
                        IngredientORM.tenant_id == tenant_id,
                        IngredientORM.active.is_(True),
                        IngredientORM.stock_qty > 0,
                    )
                )
            ).scalar_one()
            return int(raw) // _QUANTITY_SCALE


class SqlAlchemyFinanceProductDetailReadModel(FinanceProductDetailReadModel):
    """Líneas de `sale_facts` de un producto en la ventana, con sus agregados.
    Tenant-scoped (RLS + filtro explícito); solo lectura.

    **Los totales se suman en SQL, no en Python.** Antes esto traía a memoria una
    fila por venta para calcular cuatro sumas y devolvía todas al navegador: un
    plato con 50.000 ventas costaba 50.000 filas. Ahora son tres consultas
    acotadas —totales, evolución por día, y las últimas ``_LINE_LIMIT`` líneas—
    y el costo deja de crecer con el historial.
    """

    # Tope del listado de movimientos. Los totales y la serie NO dependen de él,
    # así que subirlo o bajarlo solo cambia cuántas líneas se listan.
    _LINE_LIMIT = 500

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _scope(stmt, tenant_id: str, product_id: str, since, until):
        stmt = stmt.where(
            SaleFactORM.tenant_id == tenant_id,
            SaleFactORM.product_id == product_id,
        )
        if since is not None:
            stmt = stmt.where(SaleFactORM.occurred_at >= since)
        if until is not None:
            stmt = stmt.where(SaleFactORM.occurred_at <= until)
        return stmt

    async def detail(
        self,
        tenant_id: str,
        product_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductDetail:
        # Margen neto congelado (Solución 1): ventas netas − food neto per-insumo.
        # Los COALESCE son los mismos ``_net_line``/``_net_food``, en SQL.
        net_line = func.coalesce(SaleFactORM.line_net_amount, SaleFactORM.line_amount)
        net_food = func.coalesce(
            SaleFactORM.food_cost_net_amount, SaleFactORM.food_cost_amount, 0
        )
        gross_food = func.coalesce(SaleFactORM.food_cost_amount, 0)

        async with self._session_factory() as session:
            totals = (
                await session.execute(
                    self._scope(
                        select(
                            func.coalesce(func.sum(SaleFactORM.quantity), 0),
                            func.coalesce(func.sum(SaleFactORM.line_amount), 0),
                            func.coalesce(func.sum(gross_food), 0),
                            func.coalesce(func.sum(net_line - net_food), 0),
                            func.count(),
                        ),
                        tenant_id, product_id, since, until,
                    )
                )
            ).one()
            units_sold, sales_amount, food_cost_amount, margin_amount, total_lines = totals

            # Evolución del costo unitario por día. Se agrupa por la fecha **UTC**
            # para no mover ningún punto respecto de cuando esto se derivaba del
            # ISO de cada fila en el navegador; y se descartan las filas sin food
            # cost o sin cantidad, que allá tampoco entraban al promedio.
            day = func.date(func.timezone("UTC", SaleFactORM.occurred_at))
            series_rows = (
                await session.execute(
                    self._scope(
                        select(day, func.sum(SaleFactORM.food_cost_amount),
                               func.sum(SaleFactORM.quantity)),
                        tenant_id, product_id, since, until,
                    )
                    .where(
                        SaleFactORM.food_cost_amount.is_not(None),
                        SaleFactORM.quantity > 0,
                    )
                    .group_by(day)
                    .order_by(day)
                )
            ).all()

            rows = (
                await session.execute(
                    self._scope(
                        select(SaleFactORM), tenant_id, product_id, since, until
                    )
                    .order_by(SaleFactORM.occurred_at.desc())
                    .limit(self._LINE_LIMIT)
                )
            ).scalars().all()

        # Igual que antes: la moneda sale de la venta más reciente (``rows`` sigue
        # ordenada desc), con ARS de respaldo cuando no hubo ninguna.
        currency = rows[0].currency if rows else "ARS"
        return ProductDetail(
            product_id=product_id,
            currency=currency,
            units_sold=int(units_sold),
            sales_amount=int(sales_amount),
            food_cost_amount=int(food_cost_amount),
            margin_amount=int(margin_amount),
            lines=[
                ProductSaleLine(
                    order_id=r.order_id,
                    occurred_at=r.occurred_at.isoformat(),
                    quantity=r.quantity,
                    line_amount=r.line_amount,
                    food_cost_amount=r.food_cost_amount,
                    margin_amount=_net_line(r) - _net_food(r),
                )
                for r in rows
            ],
            cost_series=[
                ProductCostPoint(day=d.isoformat(), unit_cost=round(int(cost) / int(qty)))
                for d, cost, qty in series_rows
            ],
            lines_truncated=int(total_lines) > len(rows),
        )


class SqlAlchemyExpenseBreakdownReadModel(ExpenseBreakdownReadModel):
    """Egresos (payments OUTFLOW+CONFIRMED) por categoría en la ventana + el mismo
    largo de ventana previa para el comparativo. Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def breakdown(
        self, tenant_id: str, *, since: datetime | None = None, until: datetime | None = None
    ) -> ExpenseBreakdown:
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)
            current = await self._by_category(session, tenant_id, since, until)
            previous: dict[str, int] = {}
            if since is not None and until is not None:
                span = until - since
                previous = await self._by_category(session, tenant_id, since - span, since)
            categories = set(current) | set(previous)
            rows = [
                ExpenseCategoryRow(
                    category=cat,
                    amount=current.get(cat, 0),
                    previous=previous.get(cat, 0),
                    delta=current.get(cat, 0) - previous.get(cat, 0),
                )
                for cat in categories
            ]
            rows.sort(key=lambda r: r.amount, reverse=True)
            return ExpenseBreakdown(
                currency=currency, total=sum(r.amount for r in rows), rows=rows
            )

    async def _by_category(
        self, session, tenant_id: str, since: datetime | None, until: datetime | None
    ) -> dict[str, int]:
        stmt = (
            select(PaymentORM.category, func.coalesce(func.sum(PaymentORM.amount), 0))
            .where(
                PaymentORM.tenant_id == tenant_id,
                PaymentORM.direction == PaymentDirection.OUTFLOW.value,
                PaymentORM.status == PaymentStatus.CONFIRMED.value,
            )
            .group_by(PaymentORM.category)
        )
        if since is not None:
            stmt = stmt.where(PaymentORM.created_at >= since)
        if until is not None:
            stmt = stmt.where(PaymentORM.created_at <= until)
        # None → "Otros" y se acumulan (dos filas None+"Otros" podrían coexistir).
        result: dict[str, int] = {}
        for cat, amount in (await session.execute(stmt)).all():
            result[cat or _OTROS] = result.get(cat or _OTROS, 0) + int(amount)
        return result


class SqlAlchemyRecentMovementsReadModel(RecentMovementsReadModel):
    """Últimos movimientos (cobros + egresos CONFIRMED) por created_at desc.
    Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def recent(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 20,
    ) -> list[MovementRow]:
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)
            stmt = (
                select(PaymentORM)
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.status == PaymentStatus.CONFIRMED.value,
                )
                .order_by(PaymentORM.created_at.desc())
                .limit(limit)
            )
            if since is not None:
                stmt = stmt.where(PaymentORM.created_at >= since)
            if until is not None:
                stmt = stmt.where(PaymentORM.created_at <= until)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                MovementRow(
                    occurred_at=p.created_at.isoformat(),
                    kind="IN" if p.direction == PaymentDirection.INFLOW.value else "OUT",
                    amount=p.amount,
                    method=p.method,
                    category=p.category,
                    description=p.description,
                    currency=currency,
                )
                for p in rows
            ]

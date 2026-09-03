from __future__ import annotations

from dataclasses import dataclass, field

from app.application.order.dtos import BatchOrderItemInput
from app.application.order.use_cases import AddOrderItemsBatch, CreateOrder
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order
from app.domain.order.exceptions import SelfOrderDisabled
from app.domain.order.settings import SelfOrderSettings, SelfOrderSettingsRepository
from app.domain.order.value_objects import (
    CUSTOMER_WAITER_ID,
    OrderSource,
    SelectedOption,
)
from app.domain.product.exceptions import InactiveProduct, ProductNotFound, ProductUnavailable
from app.domain.product.modifier_repository import ModifierRepository
from app.domain.product.modifiers import select_options
from app.domain.product.repository import ProductRepository
from app.domain.public_menu.ports import TableQrToken
from app.domain.shared.rate_limiter import RateLimiter
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.table_session.repository import TableSessionRepository

# Rate limit (por mesa) del autopedido — baranda de abuso (endpoint público).
_ORDER_LIMIT = 12  # varias rondas ok, pero no spam a la cocina
_ORDER_WINDOW_S = 60


@dataclass(frozen=True)
class CustomerOrderLineInput:
    """One cart line from the diner: product + quantity + the modifier option ids
    they chose (resolved + validated server-side). Only ids — never prices."""

    product_id: str
    quantity: int
    note: str | None = None
    option_ids: list[str] = field(default_factory=list)

# Sentinel del mozo del autopedido (definido en el dominio, compartido con la
# asignación por confirmación). Alias local para no tocar el resto del archivo.
_CUSTOMER_WAITER_ID = CUSTOMER_WAITER_ID


class GetSelfOrderSettings:
    def __init__(
        self, settings: SelfOrderSettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> SelfOrderSettings:
        self._tenant_context.set(tenant_id)
        return await self._settings.get(tenant_id)


class UpdateSelfOrderSettings:
    """Owner sets the self-order policy: enable the QR autopedido + the kitchen gate."""

    def __init__(
        self, settings: SelfOrderSettingsRepository, tenant_context: TenantContext
    ) -> None:
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, enabled: bool, requires_confirmation: bool
    ) -> SelfOrderSettings:
        self._tenant_context.set(tenant_id)
        settings = SelfOrderSettings(
            enabled=enabled, requires_confirmation=requires_confirmation
        )
        await self._settings.update(tenant_id, settings)
        return settings


class SubmitCustomerOrder:
    """Public (Carta QR F2): the diner sends their cart from the QR menu.

    Verifies the table token, enforces the self-order gate config, then reuses the
    real order engine: ``CreateOrder`` (opens/reuses the table's session) +
    ``AddOrderItemsBatch``. Prices come from the catalog server-side (the client
    only sends product ids + quantities — a tampered cart never changes the total),
    and unavailable/inactive dishes are rejected. The kitchen gate is just the
    existing PENDING flow: ``requires_confirmation`` ON → leave the items PENDING
    (the waiter marches them); OFF → auto-march (``send=True``)."""

    def __init__(
        self,
        token: TableQrToken,
        settings: SelfOrderSettingsRepository,
        products: ProductRepository,
        modifiers: ModifierRepository,
        sessions: TableSessionRepository,
        create_order: CreateOrder,
        add_items_batch: AddOrderItemsBatch,
        tables: TableRepository,
        tenant_context: TenantContext,
        rate_limiter: RateLimiter,
    ) -> None:
        self._token = token
        self._settings = settings
        self._products = products
        self._modifiers = modifiers
        self._sessions = sessions
        self._create_order = create_order
        self._add_items_batch = add_items_batch
        self._tables = tables
        self._tenant_context = tenant_context
        self._rate_limiter = rate_limiter

    async def execute(
        self, *, token: str, lines: list[CustomerOrderLineInput]
    ) -> Order:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        tenant_id = claims.tenant_id
        await self._rate_limiter.check(
            f"order:{tenant_id}:{claims.table_id}",
            limit=_ORDER_LIMIT,
            window_seconds=_ORDER_WINDOW_S,
        )
        self._tenant_context.set(tenant_id)

        settings = await self._settings.get(tenant_id)
        if not settings.enabled:
            raise SelfOrderDisabled()

        table = await self._tables.get_by_id(tenant_id, claims.table_id)
        if table is None:
            raise TableNotFound()

        # Resolve + validate every line against the catalog BEFORE creating
        # anything, so a bad cart never leaves a half-open order behind. This
        # checks availability ("86'd") and the modifier min/max, and snapshots the
        # chosen options' name + price_delta server-side (the cart only sent ids).
        batch = await self._resolve_lines(tenant_id, lines)

        waiter_id = await self._resolve_waiter(tenant_id, claims.table_id)
        created = await self._create_order.execute(
            tenant_id=tenant_id,
            waiter_id=waiter_id,
            table_id=claims.table_id,
            source=OrderSource.CUSTOMER_QR,
        )
        return await self._add_items_batch.execute(
            tenant_id=tenant_id,
            order_id=created.order_id,
            items=batch,
            send=not settings.requires_confirmation,
        )

    async def _resolve_lines(
        self, tenant_id: str, lines: list[CustomerOrderLineInput]
    ) -> list[BatchOrderItemInput]:
        resolved: list[BatchOrderItemInput] = []
        for line in lines:
            product = await self._products.get_by_id(tenant_id, line.product_id)
            if product is None:
                raise ProductNotFound()
            if not product.active:
                raise InactiveProduct()
            if not product.available_today:
                raise ProductUnavailable()
            groups = await self._modifiers.list_for_product(tenant_id, line.product_id)
            chosen = select_options(groups, line.option_ids)  # InvalidModifierSelection
            resolved.append(
                BatchOrderItemInput(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    note=line.note,
                    selected_options=[
                        SelectedOption(o.id, o.name, o.price_delta) for o in chosen
                    ],
                )
            )
        return resolved

    async def _resolve_waiter(self, tenant_id: str, table_id: str) -> str:
        session = await self._sessions.get_open_by_table(tenant_id, table_id)
        if session is not None and session.waiter_id:
            return session.waiter_id
        return _CUSTOMER_WAITER_ID

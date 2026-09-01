from __future__ import annotations

from app.application.public_menu.dtos import (
    IssueTableQrResult,
    PublicMenu,
    PublicMenuCategory,
    PublicMenuItem,
)
from app.domain.identity.ports import TenantContext
from app.domain.product.entities import Product
from app.domain.product.repository import ProductRepository
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.public_menu.ports import TableQrToken
from app.domain.public_menu.value_objects import TableCallKind
from app.domain.realtime.ports import DomainEvent, EventBus
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.tenant.repository import TenantRepository


def group_menu(products: list[Product]) -> list[PublicMenuCategory]:
    """Group active products into categories, preserving first-seen order for both
    categories and items (deterministic, matches the catalog order). Uncategorised
    products fall into a single ``None`` group. Pure — no I/O, easy to test."""
    order: list[str | None] = []
    buckets: dict[str | None, list[PublicMenuItem]] = {}
    for product in products:
        category = product.category or None
        if category not in buckets:
            buckets[category] = []
            order.append(category)
        buckets[category].append(
            PublicMenuItem(
                id=product.id,
                name=product.name,
                price_amount=product.price.amount,
                image_url=product.image_url,
                description=product.description,
                available_today=product.available_today,
            )
        )
    return [PublicMenuCategory(name=category, items=buckets[category]) for category in order]


class IssueTableQr:
    """Owner/manager action: mint the signed token for a table and build the deep
    link the QR encodes. Stateless and idempotent — the same table always yields
    the same token (given the signing secret), so a printed QR never goes stale."""

    def __init__(
        self,
        token: TableQrToken,
        tables: TableRepository,
        tenant_context: TenantContext,
        app_base_url: str,
    ) -> None:
        self._token = token
        self._tables = tables
        self._tenant_context = tenant_context
        self._app_base_url = app_base_url

    async def execute(self, *, tenant_id: str, table_id: str) -> IssueTableQrResult:
        self._tenant_context.set(tenant_id)
        table = await self._tables.get_by_id(tenant_id, table_id)
        if table is None:
            raise TableNotFound()
        signed = self._token.issue(tenant_id, table_id)
        url = f"{self._app_base_url.rstrip('/')}/carta/{signed}"
        return IssueTableQrResult(token=signed, url=url)


class GetPublicMenu:
    """Public (no auth): resolve the tenant from the scanned token, then return its
    branded, active-only, cost-free menu. The token is the tenant scope — set it on
    the context before any query so RLS filters to that tenant."""

    def __init__(
        self,
        token: TableQrToken,
        products: ProductRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._token = token
        self._products = products
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(self, *, token: str) -> PublicMenu:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        self._tenant_context.set(claims.tenant_id)
        tenant = await self._tenants.get_by_id(claims.tenant_id)
        if tenant is None:
            # A signed token for a tenant that no longer exists — treat as invalid
            # rather than leaking that distinction.
            raise InvalidTableQrToken()
        products = await self._products.list(claims.tenant_id, only_active=True)
        return PublicMenu(
            tenant_name=tenant.name,
            currency=tenant.currency,
            locale=tenant.locale,
            categories=group_menu(products),
        )


class RequestTableAttention:
    """Public: a diner taps 'call waiter' / 'request bill' from the QR menu. Verify
    the token, then emit a realtime ``floor.call`` signal to the tenant's floor/
    cashier (reuses the KDS/floor event bus). Carries the table number so the
    salon can render "Table N is calling" without another round-trip."""

    def __init__(
        self,
        token: TableQrToken,
        tables: TableRepository,
        event_bus: EventBus,
        tenant_context: TenantContext,
    ) -> None:
        self._token = token
        self._tables = tables
        self._event_bus = event_bus
        self._tenant_context = tenant_context

    async def execute(self, *, token: str, kind: TableCallKind) -> None:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        self._tenant_context.set(claims.tenant_id)
        table = await self._tables.get_by_id(claims.tenant_id, claims.table_id)
        if table is None:
            raise TableNotFound()
        await self._event_bus.publish(
            DomainEvent(
                type="floor.call",
                tenant_id=claims.tenant_id,
                payload={
                    "table_id": table.id,
                    "table_number": str(table.number),
                    "kind": kind.value,
                },
            )
        )

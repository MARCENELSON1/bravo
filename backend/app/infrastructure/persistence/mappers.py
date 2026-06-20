"""Mappers between ORM models and domain entities.

``*_to_orm`` omits ``created_at`` so that ``session.merge`` (updates) never
clobbers the DB-managed timestamp and inserts use the column ``server_default``.
"""

from __future__ import annotations

from app.domain.identity.tokens import (
    AuthAuditEntry,
    AuthEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import OrderStatus
from app.domain.product.entities import Product
from app.domain.shared.money import Money
from app.domain.table.entities import Table
from app.domain.tenant.entities import Tenant
from app.domain.user.entities import User
from app.domain.user.value_objects import Email, Role
from app.infrastructure.persistence.models import (
    AuthAuditORM,
    EmailVerificationTokenORM,
    InvitationORM,
    OrderItemORM,
    OrderORM,
    PasswordResetTokenORM,
    ProductORM,
    RefreshTokenORM,
    TableORM,
    TenantORM,
    UserORM,
)

# --- Tenant ---------------------------------------------------------------


def tenant_to_domain(row: TenantORM) -> Tenant:
    return Tenant(
        id=row.id,
        slug=row.slug,
        name=row.name,
        country=row.country,
        currency=row.currency,
        created_at=row.created_at,
    )


def tenant_to_orm(tenant: Tenant) -> TenantORM:
    return TenantORM(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        country=tenant.country,
        currency=tenant.currency,
    )


# --- User -----------------------------------------------------------------


def user_to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        tenant_id=row.tenant_id,
        email=Email(row.email),
        role=Role(row.role),
        password_hash=row.password_hash,
        email_verified=row.email_verified,
        active=row.active,
        failed_attempts=row.failed_attempts,
        locked_until=row.locked_until,
        created_at=row.created_at,
    )


def user_to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.id,
        tenant_id=user.tenant_id,
        email=str(user.email),
        role=user.role.value,
        password_hash=user.password_hash,
        email_verified=user.email_verified,
        active=user.active,
        failed_attempts=user.failed_attempts,
        locked_until=user.locked_until,
    )


# --- Refresh token --------------------------------------------------------


def refresh_token_to_domain(row: RefreshTokenORM) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        revoked=row.revoked,
        created_at=row.created_at,
    )


def refresh_token_to_orm(token: RefreshToken) -> RefreshTokenORM:
    return RefreshTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        revoked=token.revoked,
    )


# --- Password reset token -------------------------------------------------


def reset_token_to_domain(row: PasswordResetTokenORM) -> PasswordResetToken:
    return PasswordResetToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used=row.used,
        created_at=row.created_at,
    )


def reset_token_to_orm(token: PasswordResetToken) -> PasswordResetTokenORM:
    return PasswordResetTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        used=token.used,
    )


# --- Email verification token ---------------------------------------------


def verification_token_to_domain(row: EmailVerificationTokenORM) -> EmailVerificationToken:
    return EmailVerificationToken(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used=row.used,
        created_at=row.created_at,
    )


def verification_token_to_orm(token: EmailVerificationToken) -> EmailVerificationTokenORM:
    return EmailVerificationTokenORM(
        id=token.id,
        tenant_id=token.tenant_id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        used=token.used,
    )


# --- Invitation -----------------------------------------------------------


def invitation_to_domain(row: InvitationORM) -> Invitation:
    return Invitation(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        email=row.email,
        role=Role(row.role),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        invited_by=row.invited_by,
        used=row.used,
        created_at=row.created_at,
    )


def invitation_to_orm(invitation: Invitation) -> InvitationORM:
    return InvitationORM(
        id=invitation.id,
        tenant_id=invitation.tenant_id,
        user_id=invitation.user_id,
        email=invitation.email,
        role=invitation.role.value,
        token_hash=invitation.token_hash,
        expires_at=invitation.expires_at,
        used=invitation.used,
        invited_by=invitation.invited_by,
    )


# --- Audit ----------------------------------------------------------------


def audit_to_orm(entry: AuthAuditEntry) -> AuthAuditORM:
    return AuthAuditORM(
        id=entry.id,
        tenant_id=entry.tenant_id,
        user_id=entry.user_id,
        event=str(entry.event),
        detail=entry.detail,
    )


def audit_to_domain(row: AuthAuditORM) -> AuthAuditEntry:
    return AuthAuditEntry(
        id=row.id,
        tenant_id=row.tenant_id,
        event=AuthEvent(row.event),
        user_id=row.user_id,
        detail=row.detail,
        created_at=row.created_at,
    )


# --- Table ----------------------------------------------------------------


def table_to_domain(row: TableORM) -> Table:
    return Table(
        id=row.id,
        tenant_id=row.tenant_id,
        number=row.number,
        name=row.name,
        active=row.active,
        created_at=row.created_at,
    )


def table_to_orm(table: Table) -> TableORM:
    return TableORM(
        id=table.id,
        tenant_id=table.tenant_id,
        number=table.number,
        name=table.name,
        active=table.active,
    )


# --- Product --------------------------------------------------------------


def product_to_domain(row: ProductORM) -> Product:
    return Product(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        price=Money(row.price_amount, row.price_currency),
        category=row.category,
        active=row.active,
        created_at=row.created_at,
    )


def product_to_orm(product: Product) -> ProductORM:
    return ProductORM(
        id=product.id,
        tenant_id=product.tenant_id,
        name=product.name,
        price_amount=product.price.amount,
        price_currency=product.price.currency,
        category=product.category,
        active=product.active,
    )


# --- Order (aggregate: order + items) -------------------------------------


def order_to_domain(row: OrderORM, item_rows: list[OrderItemORM]) -> Order:
    return Order(
        id=row.id,
        tenant_id=row.tenant_id,
        table_id=row.table_id,
        waiter_id=row.waiter_id,
        currency=row.currency,
        status=OrderStatus(row.status),
        items=[
            OrderItem(
                id=item.id,
                product_id=item.product_id,
                name=item.name,
                unit_price=Money(item.unit_price_amount, row.currency),
                quantity=item.quantity,
                note=item.note,
            )
            for item in item_rows
        ],
        created_at=row.created_at,
    )


def order_to_orm(order: Order) -> OrderORM:
    return OrderORM(
        id=order.id,
        tenant_id=order.tenant_id,
        table_id=order.table_id,
        waiter_id=order.waiter_id,
        status=order.status.value,
        currency=order.currency,
    )


def order_item_to_orm(item: OrderItem, order: Order, position: int) -> OrderItemORM:
    return OrderItemORM(
        id=item.id,
        tenant_id=order.tenant_id,
        order_id=order.id,
        product_id=item.product_id,
        name=item.name,
        unit_price_amount=item.unit_price.amount,
        quantity=item.quantity,
        note=item.note,
        position=position,
    )

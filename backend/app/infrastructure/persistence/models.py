"""SQLAlchemy ORM models (separate from domain entities; mapped via mappers.py).

UUID columns are stored as native Postgres ``uuid`` but surfaced as ``str`` to
keep the boundaries string-based. Tenant-scoped tables carry ``tenant_id``; RLS
policies for the sensitive ones are created in the Alembic migration.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base; ``Base.metadata`` is the Alembic target."""


class TenantORM(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2), server_default="AR")
    currency: Mapped[str] = mapped_column(String(3), server_default="ARS")
    standard_workday_minutes: Mapped[int] = mapped_column(Integer, server_default="480")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
    )
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PasswordResetTokenORM(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EmailVerificationTokenORM(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InvitationORM(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(254))
    role: Mapped[str] = mapped_column(String(20))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    invited_by: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuthAuditORM(Base):
    __tablename__ = "auth_audit"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    user_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    event: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 2: comandas (tenant-scoped) -------------------------------------


class TableORM(Base):
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    price_amount: Mapped[int] = mapped_column(BigInteger)
    price_currency: Mapped[str] = mapped_column(String(3))
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    table_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    waiter_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True)
    currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OrderItemORM(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    name: Mapped[str] = mapped_column(String(120))
    unit_price_amount: Mapped[int] = mapped_column(BigInteger)
    quantity: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 3: pagos (ingresos/egresos, tenant-scoped) -----------------------


class PaymentORM(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(10), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    order_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentCredentialORM(Base):
    __tablename__ = "payment_credentials"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "provider", name="uq_payment_credentials_tenant_provider"
        ),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(20), index=True)
    external_account_id: Mapped[str] = mapped_column(String(64), index=True)
    # Tokens are stored encrypted (TEXT — no length cap).
    access_token: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    public_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    live_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InvoiceORM(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(30))
    point_of_sale: Mapped[int] = mapped_column(Integer)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(20))
    doc_number: Mapped[str] = mapped_column(String(20))
    concept: Mapped[str] = mapped_column(String(20))
    net_amount: Mapped[int] = mapped_column(BigInteger)
    vat_amount: Mapped[int] = mapped_column(BigInteger)
    total_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    vat_items: Mapped[list[dict[str, int]]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), index=True)
    cae: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cae_expiration: Mapped[date | None] = mapped_column(Date, nullable=True)
    rejection: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TaxCredentialORM(Base):
    __tablename__ = "tax_credentials"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tax_credentials_tenant"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    cuit: Mapped[str] = mapped_column(String(13))
    # Certificate + key stored encrypted (TEXT).
    certificate: Mapped[str] = mapped_column(String)
    private_key: Mapped[str] = mapped_column(String)
    point_of_sale: Mapped[int] = mapped_column(Integer)
    fiscal_condition: Mapped[str] = mapped_column(String(30))
    live_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --- Fase 5: fichaje (shifts, tenant-scoped) -------------------------------


class ShiftORM(Base):
    __tablename__ = "shifts"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    clock_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    clock_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    source: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adjusted_by: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UsedPresenceTokenORM(Base):
    """Single-use ledger for presence tokens: one row per consumed
    ``(tenant, time_step, user)``. Also feeds the per-user rate limit."""

    __tablename__ = "used_presence_tokens"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "time_step", "user_id", name="uq_used_presence_token"
        ),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    time_step: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 6: inventario (stock / food cost, tenant-scoped) ------------------


class IngredientORM(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(10))
    # Quantities are integers in milésimas of the base unit; stock may go negative.
    stock_qty: Mapped[int] = mapped_column(BigInteger, default=0)
    min_qty: Mapped[int] = mapped_column(BigInteger, default=0)
    unit_cost_amount: Mapped[int] = mapped_column(BigInteger)
    unit_cost_currency: Mapped[str] = mapped_column(String(3))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SupplierORM(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecipeORM(Base):
    """A product's recipe (opt-in, 1:1 with a product). Keyed by ``product_id``."""

    __tablename__ = "recipes"

    product_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecipeItemORM(Base):
    __tablename__ = "recipe_items"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("recipes.product_id", ondelete="CASCADE"),
        index=True,
    )
    ingredient_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    qty: Mapped[int] = mapped_column(BigInteger)


class StockMovementORM(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ingredient_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("ingredients.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str] = mapped_column(String(20), index=True)
    qty: Mapped[int] = mapped_column(BigInteger)
    order_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    unit_cost_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    unit_cost_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

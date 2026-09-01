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
    Text,
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
    # Guarda B3: ¿este local exige una caja abierta para poder cobrar? OFF por
    # default (paridad); se prende por tenant para el rollout del bloqueo de cobro.
    require_open_cash_session: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # Arqueo ciego: al cerrar caja, el cajero cuenta SIN ver el esperado (la
    # diferencia sale honesta). OFF por default (paridad).
    blind_cash_count: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # Autopedido (Carta QR F2). Deshabilitado por default → la carta es solo lectura
    # (paridad). requires_confirmation ON = el mozo confirma el pedido del cliente.
    self_order_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    self_order_requires_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    # Pago desde la mesa (Carta QR F3). Deshabilitado por default → la carta mantiene
    # "llamar mozo"/"pedir cuenta" (paridad F1/F2). tips_enabled ON = ofrece propina
    # (el dueño la puede apagar desde la UI).
    self_pay_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    self_pay_tips_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    # Regional/fiscal spine (Fase 0 internacionalización). Defaults AR → paridad
    # total para los tenants existentes; los resolvers leen estos campos por tenant.
    tax_regime: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="AR_AFIP"
    )
    locale: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="es-AR"
    )
    timezone: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default="America/Argentina/Buenos_Aires"
    )
    tax_engine: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="NONE"
    )
    # Fiscal address (point of sale) for a rate-by-address engine (US/TaxJar).
    # Nullable → AR tenants leave it empty (parity).
    fiscal_street: Mapped[str | None] = mapped_column(String(160), nullable=True)
    fiscal_city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fiscal_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fiscal_zip: Mapped[str | None] = mapped_column(String(16), nullable=True)
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
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Valor/hora en unidad mínima (Tanda D Finanzas): opcional; sin rate el
    # labor cae al costo mensual configurado en el Asesor.
    hourly_rate_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    platform_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
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
    # table_sessions (cimiento): zona + capacidad. Nullable → paridad.
    sector_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SectorORM(Base):
    """Zona del salón para agrupar/facturar mesas. Datos operativos → RLS."""

    __tablename__ = "sectors"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TableSessionORM(Base):
    """La visita de una mesa (turno). Timestamps + PAX + mozo + status cache.
    Datos operativos/de plata → RLS."""

    __tablename__ = "table_sessions"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    table_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    status: Mapped[str] = mapped_column(String(20), server_default="OPEN", index=True)
    origin: Mapped[str] = mapped_column(String(20), server_default="SALON")
    pax: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiter_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_item_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bill_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merged_into_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    station: Mapped[str] = mapped_column(String(10), server_default="KITCHEN")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # QR menu enrichment (Carta QR F2). Nullable/defaulted → parity for existing rows.
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_today: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProductPriceChangeORM(Base):
    """Append-only log of a product's price over time (Productos v2 Tanda B).
    One row per change (the first, at creation, has ``old_price_amount`` NULL).
    Drives "días desde el último aumento" y "debería estar en $X". Tenant-scoped → RLS."""

    __tablename__ = "product_price_changes"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    old_price_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    new_price_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
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
    # table_sessions (cimiento): la comanda cuelga de la sesión (1:N). Nullable → paridad.
    session_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    # CRM: cliente atribuido a la comanda (para el historial de compras). Nullable.
    customer_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3))
    # Origen de la comanda (Carta QR F2). Default WAITER → paridad.
    source: Mapped[str] = mapped_column(String(16), server_default="WAITER")
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
    # Per-item kitchen lifecycle + routing (Fase 14): see ItemStatus / Station.
    status: Mapped[str] = mapped_column(String(20), server_default="PENDING", index=True)
    station: Mapped[str] = mapped_column(String(10), server_default="KITCHEN", index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Modificadores elegidos (Carta QR F2 D). Snapshot JSON [{option_id,name,price_delta}]
    # — display-only (el delta ya está en unit_price_amount). Nullable → paridad.
    selected_options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProductModifierGroupORM(Base):
    """A product's modifier group (ej. "Punto de cocción"). Carta QR F2 D. RLS."""

    __tablename__ = "product_modifier_groups"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    min_select: Mapped[int] = mapped_column(Integer, server_default="0")
    max_select: Mapped[int] = mapped_column(Integer, server_default="1")
    position: Mapped[int] = mapped_column(Integer, default=0)


class ProductModifierOptionORM(Base):
    """One option inside a modifier group (ej. "+Panceta", price_delta 1200)."""

    __tablename__ = "product_modifier_options"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    group_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("product_modifier_groups.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120))
    price_delta: Mapped[int] = mapped_column(BigInteger, server_default="0")
    position: Mapped[int] = mapped_column(Integer, default=0)


# --- Fase 3: pagos (ingresos/egresos, tenant-scoped) -----------------------


class PaymentORM(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(10), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    # Propina cobrada encima del ``amount`` de la venta (0 si no hubo). No es
    # ingreso del local: solo cuenta para el arqueo de caja.
    tip_amount: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    tax_amount: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    # Comisiones: retención de la pasarela y neto que queda. net_amount NULL → se
    # lee como amount (COALESCE) → paridad para pagos previos / sin comisión.
    fee_amount: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    net_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    order_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    # Caja (guarda B): sesión de caja abierta al cobrar (None si no había caja).
    cash_session_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), nullable=True, index=True
    )
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentFeeRateORM(Base):
    """Tasa de comisión por método por tenant (bps). Sin fila → 0 (sin comisión).
    Datos de plata → RLS."""

    __tablename__ = "payment_fee_rates"

    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    method: Mapped[str] = mapped_column(String(20), primary_key=True)
    fee_bps: Mapped[int] = mapped_column(Integer, server_default="0")


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


class TaxReportORM(Base):
    """Outbox de ventas con sales tax cobrado, a reportar al proveedor (TaxJar
    AutoFile). Una fila por comanda que cobró impuesto; idempotente por
    (tenant, order). Vacía en AR (nunca se cobra tax). Datos de plata → RLS."""

    __tablename__ = "tax_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_id", name="uq_tax_reports_tenant_order"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    # PENDING (por enviar) | SENT (reportado) | FAILED (último intento falló, se reintenta)
    status: Mapped[str] = mapped_column(String(20), index=True, server_default="PENDING")
    provider: Mapped[str] = mapped_column(String(20), server_default="TAXJAR")
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaxJarCredentialORM(Base):
    """Credencial de TaxJar por tenant (su propia cuenta, para reportar/AutoFile).
    El token se guarda cifrado (TEXT). Una por tenant. Datos sensibles → RLS."""

    __tablename__ = "taxjar_credentials"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_taxjar_credentials_tenant"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # API token stored encrypted (TEXT — no length cap).
    api_token: Mapped[str] = mapped_column(String)
    sandbox: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlanORM(Base):
    """Catálogo de planes del SaaS (Flujo A). GLOBAL, no tenant-scoped (no lleva
    RLS): el mismo tier existe una vez por región (BASIC/AR en ARS, BASIC/INTL en
    USD). Lo lee cualquiera (pricing); lo escribe el admin (seed)."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tier: Mapped[str] = mapped_column(String(20), index=True)
    region: Mapped[str] = mapped_column(String(10), index=True)
    price_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    interval: Mapped[str] = mapped_column(String(10), server_default="MONTH")
    features: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SubscriptionORM(Base):
    """Suscripción de un tenant a un plan (Flujo A). Una por tenant. Datos de
    plata → RLS. ``external_ref`` = id en la pasarela (Stripe sub_… / MP preapproval)."""

    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_subscriptions_tenant"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    region: Mapped[str] = mapped_column(String(10))
    rail: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
    # Yield (rendimiento/merma) in basis points; 10000 = 100% = no loss.
    yield_pct: Mapped[int] = mapped_column(Integer, server_default="10000")
    # Whether the loaded cost includes VAT (net it) or is already net (monotributo).
    cost_includes_tax: Mapped[bool] = mapped_column(Boolean, default=True)
    # Recipe unit (Fase 2C): finer same-family sub-unit the recipe qty is in
    # (KG→G, L→ML). NULL = recipe uses the base unit (parity).
    recipe_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
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
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    # Incremental recipe version (Fase 2D); bumped on every SetRecipe.
    version: Mapped[int] = mapped_column(Integer, server_default="1")
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
    # Un ítem apunta a un insumo O a una preparación (receta madre), no ambos.
    ingredient_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), index=True, nullable=True
    )
    preparation_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), index=True, nullable=True
    )
    qty: Mapped[int] = mapped_column(BigInteger)


class PreparationORM(Base):
    """Preparación base reutilizable (receta madre, Productos v2 Tanda C). NO es
    un producto vendible. Datos del tenant → RLS."""

    __tablename__ = "preparations"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    yield_qty: Mapped[int] = mapped_column(BigInteger)  # rendimiento en milésimas
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PreparationItemORM(Base):
    """Componente de una preparación: un insumo O una sub-preparación (multinivel)."""

    __tablename__ = "preparation_items"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    preparation_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("preparations.id", ondelete="CASCADE"),
        index=True,
    )
    ingredient_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), index=True, nullable=True
    )
    sub_preparation_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), index=True, nullable=True
    )
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
    supplier_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 7: reservas (tenant-scoped) --------------------------------------


class ReservationORM(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    party_size: Mapped[int] = mapped_column(Integer)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    turn: Mapped[str] = mapped_column(String(10), index=True)
    # Soft reference (no FK): a reservation survives a table being deactivated.
    table_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 8: modelo canónico (silver) — sale_facts (tenant-scoped) ---------


class SaleFactORM(Base):
    """Canonical revenue fact: one line of a PAID order. Maintained by the sales
    projection on the PAID transition. Tenant-scoped + RLS (datos de plata)."""

    __tablename__ = "sale_facts"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    order_item_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    product_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    product_name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_amount: Mapped[int] = mapped_column(BigInteger)
    line_amount: Mapped[int] = mapped_column(BigInteger)
    # Ventas netas de IVA congeladas en la proyección (Solución 1); nullable →
    # filas previas se leen como bruto vía COALESCE. Igual al bruto con VAT 0.
    line_net_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    food_cost_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Neto de IVA per-insumo congelado (Solución 1); nullable → bruto vía COALESCE.
    food_cost_net_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Versión de la receta al momento de la venta (Fase 2D); NULL en filas previas.
    recipe_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    waiter_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    table_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Fase 9: asesor financiero — advisor_settings (tenant-scoped, 1:1) ------


class CashSessionORM(Base):
    """A register turn (caja). Tenant-scoped + RLS (datos de plata)."""

    __tablename__ = "cash_sessions"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    opened_by: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    opening_float_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CashCountORM(Base):
    """One arqueo line for a closed session: expected vs counted, per method."""

    __tablename__ = "cash_counts"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    cash_session_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("cash_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    method: Mapped[str] = mapped_column(String(20))
    expected_amount: Mapped[int] = mapped_column(BigInteger)
    counted_amount: Mapped[int] = mapped_column(BigInteger)


class CashMovementORM(Base):
    """Manual cash-drawer movements (sangría / ingreso / pago en efectivo) on an
    open session. Reconcile the arqueo Z; NOT a sale. Datos de plata → RLS."""

    __tablename__ = "cash_movements"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    cash_session_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("cash_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TipPayoutORM(Base):
    """Liquidaciones de propina (guarda D): pasivo neutro al resultado, NO egreso.
    Datos de plata → RLS."""

    __tablename__ = "tip_payouts"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    waiter_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    method: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AdvisorSettingsORM(Base):
    """Per-tenant cost profile (1:1, keyed by tenant_id). Datos de plata → RLS."""

    __tablename__ = "advisor_settings"

    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    labor_cost_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    other_fixed_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    currency: Mapped[str] = mapped_column(String(3))
    target_food_cost_bps: Mapped[int] = mapped_column(Integer, server_default="3000")
    # Tanda E Finanzas: inputs de RevPASH (capacidad total + minutos abiertos/día).
    seats: Mapped[int] = mapped_column(Integer, server_default="0")
    daily_open_minutes: Mapped[int] = mapped_column(Integer, server_default="0")
    # Productos v2 Tanda B: inflación mensual estimada (bps) para "debería estar en $X".
    monthly_inflation_bps: Mapped[int] = mapped_column(Integer, server_default="0")
    # Productos v3 Tanda 2B: IVA global (bps) para netear costos y precios.
    # 0 = sin cargar (netting off, paridad); el dueño carga 2100 (21%) para activar.
    default_vat_bps: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AdvisorDiagnosticsORM(Base):
    """Caché de diagnósticos narrados (Fase 9.1): un payload JSON por
    (tenant, fingerprint de insights+proveedor). Datos de plata → RLS."""

    __tablename__ = "advisor_diagnostics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "fingerprint", name="uq_advisor_diagnostics_tenant_fingerprint"
        ),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str] = mapped_column(String)  # JSON: {insights:[...], summary}
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FinanceDailySnapshotORM(Base):
    """Capa 2 (Tanda F): totales diarios pre-agregados de ventas para servir la
    Pantalla Finanzas sin escanear todo el historial de sale_facts. Se mantiene
    incremental en el projector y se puede reconstruir. Datos de plata → RLS."""

    __tablename__ = "finance_daily_snapshots"

    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    sales_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    # Ventas netas de IVA congeladas (Solución 1). Igual al bruto con VAT 0.
    sales_net_amount: Mapped[int] = mapped_column(
        BigInteger, server_default="0", default=0
    )
    food_cost_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    # Neto de IVA per-insumo (Solución 1): base del margen. Igual al bruto con VAT 0.
    food_cost_net_amount: Mapped[int] = mapped_column(
        BigInteger, server_default="0", default=0
    )
    orders_count: Mapped[int] = mapped_column(Integer, default=0)
    units_sold: Mapped[int] = mapped_column(BigInteger, default=0)


class CustomerORM(Base):
    """Cliente del local (CRM, Fase 12). Manual por ahora; el matcheo automático
    y los segmentos son slices posteriores. Datos del cliente → RLS."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    no_contactar: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ContactLogORM(Base):
    """Bitácora de contactos a clientes (CRM, loop de resultado). Datos del
    cliente → RLS."""

    __tablename__ = "contact_log"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(40))
    contacted_by: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    contacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

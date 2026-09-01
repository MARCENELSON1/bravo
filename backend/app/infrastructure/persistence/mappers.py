"""Mappers between ORM models and domain entities.

``*_to_orm`` omits ``created_at`` so that ``session.merge`` (updates) never
clobbers the DB-managed timestamp and inserts use the column ``server_default``.
"""

from __future__ import annotations

from app.domain.advisor.entities import AdvisorSettings
from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.value_objects import (
    BillingInterval,
    BillingRail,
    BillingRegion,
    PlanTier,
    SubscriptionStatus,
)
from app.domain.cashier.entities import CashCount, CashMovement, CashSession
from app.domain.cashier.value_objects import CashMovementKind, CashSessionStatus
from app.domain.customer.entities import Customer
from app.domain.identity.tokens import (
    AuthAuditEntry,
    AuthEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.inventory.entities import Ingredient, StockMovement, Supplier
from app.domain.inventory.recipe import Preparation, Recipe, RecipeItem
from app.domain.inventory.value_objects import (
    MovementDirection,
    MovementReason,
    UnitOfMeasure,
)
from app.domain.invoice.credentials import TaxCredential
from app.domain.invoice.entities import Invoice, VatItem
from app.domain.invoice.value_objects import (
    Concept,
    DocType,
    FiscalCondition,
    InvoiceStatus,
    InvoiceType,
)
from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import (
    ItemStatus,
    OrderSource,
    OrderStatus,
    SelectedOption,
    Station,
)
from app.domain.payment.credentials import (
    ConnectionStatus,
    PaymentCredential,
    PaymentProvider,
)
from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.product.entities import Product
from app.domain.product.modifiers import ModifierGroup, ModifierOption
from app.domain.reservation.entities import Reservation
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn
from app.domain.shared.money import Money
from app.domain.table.entities import Table
from app.domain.table_session.entities import Sector, TableSession
from app.domain.table_session.value_objects import SessionOrigin, SessionStatus
from app.domain.tax.credentials import TaxJarCredential
from app.domain.tenant.entities import Tenant
from app.domain.tenant.regional import TaxEngine, TaxRegime
from app.domain.timeclock.entities import Shift
from app.domain.timeclock.value_objects import ShiftSource, ShiftStatus
from app.domain.user.entities import User
from app.domain.user.value_objects import Email, Role
from app.infrastructure.persistence.models import (
    AdvisorSettingsORM,
    AuthAuditORM,
    CashCountORM,
    CashMovementORM,
    CashSessionORM,
    CustomerORM,
    EmailVerificationTokenORM,
    IngredientORM,
    InvitationORM,
    InvoiceORM,
    OrderItemORM,
    OrderORM,
    PasswordResetTokenORM,
    PaymentCredentialORM,
    PaymentORM,
    PlanORM,
    PreparationItemORM,
    PreparationORM,
    ProductModifierGroupORM,
    ProductModifierOptionORM,
    ProductORM,
    RecipeItemORM,
    RecipeORM,
    RefreshTokenORM,
    ReservationORM,
    SectorORM,
    ShiftORM,
    StockMovementORM,
    SubscriptionORM,
    SupplierORM,
    TableORM,
    TableSessionORM,
    TaxCredentialORM,
    TaxJarCredentialORM,
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
        standard_workday_minutes=row.standard_workday_minutes,
        tax_regime=TaxRegime(row.tax_regime),
        locale=row.locale,
        timezone=row.timezone,
        tax_engine=TaxEngine(row.tax_engine),
        fiscal_street=row.fiscal_street,
        fiscal_city=row.fiscal_city,
        fiscal_state=row.fiscal_state,
        fiscal_zip=row.fiscal_zip,
        created_at=row.created_at,
    )


def tenant_to_orm(tenant: Tenant) -> TenantORM:
    return TenantORM(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        country=tenant.country,
        currency=tenant.currency,
        standard_workday_minutes=tenant.standard_workday_minutes,
        tax_regime=tenant.tax_regime.value,
        locale=tenant.locale,
        timezone=tenant.timezone,
        tax_engine=tenant.tax_engine.value,
        fiscal_street=tenant.fiscal_street,
        fiscal_city=tenant.fiscal_city,
        fiscal_state=tenant.fiscal_state,
        fiscal_zip=tenant.fiscal_zip,
    )


# --- User -----------------------------------------------------------------


def user_to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        tenant_id=row.tenant_id,
        email=Email(row.email),
        role=Role(row.role),
        name=row.name,
        hourly_rate_amount=row.hourly_rate_amount,
        password_hash=row.password_hash,
        email_verified=row.email_verified,
        active=row.active,
        platform_admin=row.platform_admin,
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
        name=user.name,
        hourly_rate_amount=user.hourly_rate_amount,
        password_hash=user.password_hash,
        email_verified=user.email_verified,
        active=user.active,
        platform_admin=user.platform_admin,
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
        sector_id=row.sector_id,
        capacity=row.capacity,
        created_at=row.created_at,
    )


def table_to_orm(table: Table) -> TableORM:
    return TableORM(
        id=table.id,
        tenant_id=table.tenant_id,
        number=table.number,
        name=table.name,
        active=table.active,
        sector_id=table.sector_id,
        capacity=table.capacity,
    )


def sector_to_domain(row: SectorORM) -> Sector:
    return Sector(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        color=row.color,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def sector_to_orm(sector: Sector) -> SectorORM:
    return SectorORM(
        id=sector.id,
        tenant_id=sector.tenant_id,
        name=sector.name,
        color=sector.color,
        sort_order=sector.sort_order,
    )


def table_session_to_domain(row: TableSessionORM) -> TableSession:
    return TableSession(
        id=row.id,
        tenant_id=row.tenant_id,
        table_id=row.table_id,
        status=SessionStatus(row.status),
        origin=SessionOrigin(row.origin),
        pax=row.pax,
        waiter_id=row.waiter_id,
        opened_at=row.opened_at,
        first_item_at=row.first_item_at,
        fired_at=row.fired_at,
        ready_at=row.ready_at,
        bill_requested_at=row.bill_requested_at,
        closed_at=row.closed_at,
        merged_into_id=row.merged_into_id,
        customer_id=row.customer_id,
        notes=row.notes,
    )


def table_session_to_orm(session: TableSession) -> TableSessionORM:
    return TableSessionORM(
        id=session.id,
        tenant_id=session.tenant_id,
        table_id=session.table_id,
        status=session.status.value,
        origin=session.origin.value,
        pax=session.pax,
        waiter_id=session.waiter_id,
        opened_at=session.opened_at,
        first_item_at=session.first_item_at,
        fired_at=session.fired_at,
        ready_at=session.ready_at,
        bill_requested_at=session.bill_requested_at,
        closed_at=session.closed_at,
        merged_into_id=session.merged_into_id,
        customer_id=session.customer_id,
        notes=session.notes,
    )


# --- Product --------------------------------------------------------------


def product_to_domain(row: ProductORM) -> Product:
    return Product(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        price=Money(row.price_amount, row.price_currency),
        category=row.category,
        station=Station(row.station),
        active=row.active,
        image_url=row.image_url,
        description=row.description,
        available_today=row.available_today,
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
        station=product.station.value,
        active=product.active,
        image_url=product.image_url,
        description=product.description,
        available_today=product.available_today,
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
        session_id=row.session_id,
        customer_id=row.customer_id,
        source=OrderSource(row.source),
        items=[
            OrderItem(
                id=item.id,
                product_id=item.product_id,
                name=item.name,
                unit_price=Money(item.unit_price_amount, row.currency),
                quantity=item.quantity,
                note=item.note,
                station=Station(item.station),
                status=ItemStatus(item.status),
                sent_at=item.sent_at,
                ready_at=item.ready_at,
                selected_options=[
                    SelectedOption(
                        option_id=o["option_id"],
                        name=o["name"],
                        price_delta=o["price_delta"],
                    )
                    for o in (item.selected_options or [])
                ],
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
        session_id=order.session_id,
        customer_id=order.customer_id,
        currency=order.currency,
        source=order.source.value,
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
        status=item.status.value,
        station=item.station.value,
        sent_at=item.sent_at,
        ready_at=item.ready_at,
        position=position,
        selected_options=(
            [
                {"option_id": o.option_id, "name": o.name, "price_delta": o.price_delta}
                for o in item.selected_options
            ]
            or None
        ),
    )


# --- Product modifiers (Carta QR F2 D) -------------------------------------


def modifier_group_to_domain(
    group_row: ProductModifierGroupORM, option_rows: list[ProductModifierOptionORM]
) -> ModifierGroup:
    return ModifierGroup(
        id=group_row.id,
        tenant_id=group_row.tenant_id,
        product_id=group_row.product_id,
        name=group_row.name,
        min_select=group_row.min_select,
        max_select=group_row.max_select,
        options=[
            ModifierOption(id=o.id, name=o.name, price_delta=o.price_delta)
            for o in sorted(option_rows, key=lambda o: o.position)
        ],
    )


def modifier_group_to_orm(
    group: ModifierGroup, position: int
) -> ProductModifierGroupORM:
    return ProductModifierGroupORM(
        id=group.id,
        tenant_id=group.tenant_id,
        product_id=group.product_id,
        name=group.name,
        min_select=group.min_select,
        max_select=group.max_select,
        position=position,
    )


def modifier_option_to_orm(
    option: ModifierOption, group: ModifierGroup, position: int
) -> ProductModifierOptionORM:
    return ProductModifierOptionORM(
        id=option.id,
        tenant_id=group.tenant_id,
        group_id=group.id,
        name=option.name,
        price_delta=option.price_delta,
        position=position,
    )


# --- Payment --------------------------------------------------------------


def payment_to_domain(row: PaymentORM) -> Payment:
    return Payment(
        id=row.id,
        tenant_id=row.tenant_id,
        direction=PaymentDirection(row.direction),
        amount=Money(row.amount, row.currency),
        method=PaymentMethod(row.method),
        status=PaymentStatus(row.status),
        order_id=row.order_id,
        cash_session_id=row.cash_session_id,
        tip_amount=row.tip_amount,
        tax_amount=row.tax_amount,
        fee_amount=row.fee_amount,
        net_amount=row.net_amount,
        category=row.category,
        counterparty=row.counterparty,
        description=row.description,
        external_ref=row.external_ref,
        created_at=row.created_at,
    )


def payment_to_orm(payment: Payment) -> PaymentORM:
    return PaymentORM(
        id=payment.id,
        tenant_id=payment.tenant_id,
        direction=payment.direction.value,
        amount=payment.amount.amount,
        tip_amount=payment.tip_amount,
        tax_amount=payment.tax_amount,
        fee_amount=payment.fee_amount,
        net_amount=payment.net_amount,
        currency=payment.amount.currency,
        method=payment.method.value,
        status=payment.status.value,
        order_id=payment.order_id,
        cash_session_id=payment.cash_session_id,
        category=payment.category,
        counterparty=payment.counterparty,
        description=payment.description,
        external_ref=payment.external_ref,
    )


# --- Payment credential (gateway connection per tenant) -------------------


def payment_credential_to_domain(row: PaymentCredentialORM) -> PaymentCredential:
    return PaymentCredential(
        id=row.id,
        tenant_id=row.tenant_id,
        provider=PaymentProvider(row.provider),
        external_account_id=row.external_account_id,
        access_token=row.access_token,
        refresh_token=row.refresh_token,
        public_key=row.public_key,
        nickname=row.nickname,
        expires_at=row.expires_at,
        live_mode=row.live_mode,
        status=ConnectionStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def invoice_to_domain(row: InvoiceORM) -> Invoice:
    currency = row.currency
    return Invoice(
        id=row.id,
        tenant_id=row.tenant_id,
        type=InvoiceType(row.type),
        point_of_sale=row.point_of_sale,
        doc_type=DocType(row.doc_type),
        doc_number=row.doc_number,
        concept=Concept(row.concept),
        net=Money(row.net_amount, currency),
        vat=Money(row.vat_amount, currency),
        total=Money(row.total_amount, currency),
        vat_items=[
            VatItem(
                rate=item["rate"],
                base=Money(item["base"], currency),
                amount=Money(item["amount"], currency),
            )
            for item in row.vat_items
        ],
        status=InvoiceStatus(row.status),
        order_id=row.order_id,
        number=row.number,
        cae=row.cae,
        cae_expiration=row.cae_expiration,
        rejection=row.rejection,
        issued_at=row.issued_at,
        created_at=row.created_at,
    )


def invoice_to_orm(invoice: Invoice) -> InvoiceORM:
    return InvoiceORM(
        id=invoice.id,
        tenant_id=invoice.tenant_id,
        type=invoice.type.value,
        point_of_sale=invoice.point_of_sale,
        number=invoice.number,
        doc_type=invoice.doc_type.value,
        doc_number=invoice.doc_number,
        concept=invoice.concept.value,
        net_amount=invoice.net.amount,
        vat_amount=invoice.vat.amount,
        total_amount=invoice.total.amount,
        currency=invoice.total.currency,
        vat_items=[
            {"rate": v.rate, "base": v.base.amount, "amount": v.amount.amount}
            for v in invoice.vat_items
        ],
        status=invoice.status.value,
        cae=invoice.cae,
        cae_expiration=invoice.cae_expiration,
        rejection=invoice.rejection,
        order_id=invoice.order_id,
    )


# --- Shift (fichaje) ------------------------------------------------------


def shift_to_domain(row: ShiftORM) -> Shift:
    return Shift(
        id=row.id,
        tenant_id=row.tenant_id,
        user_id=row.user_id,
        clock_in_at=row.clock_in_at,
        clock_out_at=row.clock_out_at,
        status=ShiftStatus(row.status),
        source=ShiftSource(row.source),
        note=row.note,
        adjusted_by=row.adjusted_by,
        created_at=row.created_at,
    )


def shift_to_orm(shift: Shift) -> ShiftORM:
    return ShiftORM(
        id=shift.id,
        tenant_id=shift.tenant_id,
        user_id=shift.user_id,
        clock_in_at=shift.clock_in_at,
        clock_out_at=shift.clock_out_at,
        status=shift.status.value,
        source=shift.source.value,
        note=shift.note,
        adjusted_by=shift.adjusted_by,
    )


def tax_credential_to_domain(row: TaxCredentialORM) -> TaxCredential:
    return TaxCredential(
        id=row.id,
        tenant_id=row.tenant_id,
        cuit=row.cuit,
        certificate=row.certificate,
        private_key=row.private_key,
        point_of_sale=row.point_of_sale,
        fiscal_condition=FiscalCondition(row.fiscal_condition),
        live_mode=row.live_mode,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def tax_credential_to_orm(credential: TaxCredential) -> TaxCredentialORM:
    return TaxCredentialORM(
        id=credential.id,
        tenant_id=credential.tenant_id,
        cuit=credential.cuit,
        certificate=credential.certificate,
        private_key=credential.private_key,
        point_of_sale=credential.point_of_sale,
        fiscal_condition=credential.fiscal_condition.value,
        live_mode=credential.live_mode,
    )


def taxjar_credential_to_domain(row: TaxJarCredentialORM) -> TaxJarCredential:
    return TaxJarCredential(
        id=row.id,
        tenant_id=row.tenant_id,
        api_token=row.api_token,
        sandbox=row.sandbox,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def taxjar_credential_to_orm(credential: TaxJarCredential) -> TaxJarCredentialORM:
    return TaxJarCredentialORM(
        id=credential.id,
        tenant_id=credential.tenant_id,
        api_token=credential.api_token,
        sandbox=credential.sandbox,
    )


def plan_to_domain(row: PlanORM) -> Plan:
    return Plan(
        id=row.id,
        tier=PlanTier(row.tier),
        region=BillingRegion(row.region),
        price=Money(row.price_amount, row.currency),
        interval=BillingInterval(row.interval),
        features=frozenset(row.features or []),
        active=row.active,
    )


def plan_to_orm(plan: Plan) -> PlanORM:
    return PlanORM(
        id=plan.id,
        tier=plan.tier.value,
        region=plan.region.value,
        price_amount=plan.price.amount,
        currency=plan.price.currency,
        interval=plan.interval.value,
        features=list(plan.features),
        active=plan.active,
    )


def subscription_to_domain(row: SubscriptionORM) -> Subscription:
    return Subscription(
        id=row.id,
        tenant_id=row.tenant_id,
        plan_id=row.plan_id,
        region=BillingRegion(row.region),
        rail=BillingRail(row.rail),
        status=SubscriptionStatus(row.status),
        external_ref=row.external_ref,
        trial_end=row.trial_end,
        current_period_end=row.current_period_end,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def subscription_to_orm(subscription: Subscription) -> SubscriptionORM:
    return SubscriptionORM(
        id=subscription.id,
        tenant_id=subscription.tenant_id,
        plan_id=subscription.plan_id,
        region=subscription.region.value,
        rail=subscription.rail.value,
        status=subscription.status.value,
        external_ref=subscription.external_ref,
        trial_end=subscription.trial_end,
        current_period_end=subscription.current_period_end,
    )


def payment_credential_to_orm(credential: PaymentCredential) -> PaymentCredentialORM:
    return PaymentCredentialORM(
        id=credential.id,
        tenant_id=credential.tenant_id,
        provider=credential.provider.value,
        external_account_id=credential.external_account_id,
        access_token=credential.access_token,
        refresh_token=credential.refresh_token,
        public_key=credential.public_key,
        nickname=credential.nickname,
        expires_at=credential.expires_at,
        live_mode=credential.live_mode,
        status=credential.status.value,
    )


# --- Inventory: ingredient / supplier / recipe / stock movement -----------


def ingredient_to_domain(row: IngredientORM) -> Ingredient:
    return Ingredient(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        # Lectura tolerante: una unidad legacy inválida degrada a UNIT en vez de
        # romper todo el listado/food-cost (los writes siguen estrictos).
        unit=UnitOfMeasure.parse(row.unit),
        stock_qty=row.stock_qty,
        min_qty=row.min_qty,
        unit_cost=Money(row.unit_cost_amount, row.unit_cost_currency),
        yield_pct=row.yield_pct,
        cost_includes_tax=row.cost_includes_tax,
        recipe_unit=UnitOfMeasure.parse(row.recipe_unit) if row.recipe_unit else None,
        active=row.active,
        created_at=row.created_at,
    )


def ingredient_to_orm(ingredient: Ingredient) -> IngredientORM:
    return IngredientORM(
        id=ingredient.id,
        tenant_id=ingredient.tenant_id,
        name=ingredient.name,
        unit=ingredient.unit.value,
        stock_qty=ingredient.stock_qty,
        min_qty=ingredient.min_qty,
        unit_cost_amount=ingredient.unit_cost.amount,
        unit_cost_currency=ingredient.unit_cost.currency,
        yield_pct=ingredient.yield_pct,
        cost_includes_tax=ingredient.cost_includes_tax,
        recipe_unit=ingredient.recipe_unit.value if ingredient.recipe_unit else None,
        active=ingredient.active,
    )


def supplier_to_domain(row: SupplierORM) -> Supplier:
    return Supplier(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        contact=row.contact,
        phone=row.phone,
        notes=row.notes,
        active=row.active,
        created_at=row.created_at,
    )


def supplier_to_orm(supplier: Supplier) -> SupplierORM:
    return SupplierORM(
        id=supplier.id,
        tenant_id=supplier.tenant_id,
        name=supplier.name,
        contact=supplier.contact,
        phone=supplier.phone,
        notes=supplier.notes,
        active=supplier.active,
    )


def stock_movement_to_domain(row: StockMovementORM) -> StockMovement:
    unit_cost = (
        Money(row.unit_cost_amount, row.unit_cost_currency)
        if row.unit_cost_amount is not None and row.unit_cost_currency is not None
        else None
    )
    return StockMovement(
        id=row.id,
        tenant_id=row.tenant_id,
        ingredient_id=row.ingredient_id,
        direction=MovementDirection(row.direction),
        reason=MovementReason(row.reason),
        qty=row.qty,
        order_id=row.order_id,
        unit_cost=unit_cost,
        note=row.note,
        supplier_id=row.supplier_id,
        created_at=row.created_at,
    )


def stock_movement_to_orm(movement: StockMovement) -> StockMovementORM:
    return StockMovementORM(
        id=movement.id,
        tenant_id=movement.tenant_id,
        ingredient_id=movement.ingredient_id,
        direction=movement.direction.value,
        reason=movement.reason.value,
        qty=movement.qty,
        order_id=movement.order_id,
        unit_cost_amount=movement.unit_cost.amount if movement.unit_cost else None,
        unit_cost_currency=movement.unit_cost.currency if movement.unit_cost else None,
        note=movement.note,
        supplier_id=movement.supplier_id,
    )


def _recipe_item_to_domain(item: RecipeItemORM) -> RecipeItem:
    if item.preparation_id is not None:
        return RecipeItem(preparation_id=item.preparation_id, qty=item.qty)
    return RecipeItem(ingredient_id=item.ingredient_id, qty=item.qty)


def recipe_to_domain(row: RecipeORM, item_rows: list[RecipeItemORM]) -> Recipe:
    return Recipe(
        product_id=row.product_id,
        tenant_id=row.tenant_id,
        items=[_recipe_item_to_domain(item) for item in item_rows],
        version=row.version,
    )


def recipe_to_orm(recipe: Recipe) -> RecipeORM:
    return RecipeORM(
        product_id=recipe.product_id,
        tenant_id=recipe.tenant_id,
        version=recipe.version,
    )


def recipe_item_to_orm(item: RecipeItem, recipe: Recipe, item_id: str) -> RecipeItemORM:
    return RecipeItemORM(
        id=item_id,
        tenant_id=recipe.tenant_id,
        product_id=recipe.product_id,
        ingredient_id=item.ingredient_id,
        preparation_id=item.preparation_id,
        qty=item.qty,
    )


# --- Preparation (receta madre; sus ítems reusan RecipeItem) ----------------


def _preparation_item_to_domain(item: PreparationItemORM) -> RecipeItem:
    if item.sub_preparation_id is not None:
        return RecipeItem(preparation_id=item.sub_preparation_id, qty=item.qty)
    return RecipeItem(ingredient_id=item.ingredient_id, qty=item.qty)


def preparation_to_domain(
    row: PreparationORM, item_rows: list[PreparationItemORM]
) -> Preparation:
    return Preparation(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        yield_qty=row.yield_qty,
        items=[_preparation_item_to_domain(item) for item in item_rows],
    )


def preparation_to_orm(prep: Preparation) -> PreparationORM:
    return PreparationORM(
        id=prep.id,
        tenant_id=prep.tenant_id,
        name=prep.name,
        yield_qty=prep.yield_qty,
    )


def preparation_item_to_orm(
    item: RecipeItem, prep: Preparation, item_id: str
) -> PreparationItemORM:
    # En el dominio, un ítem de preparación que apunta a otra prep usa
    # ``preparation_id``; en el ORM eso es ``sub_preparation_id``.
    return PreparationItemORM(
        id=item_id,
        tenant_id=prep.tenant_id,
        preparation_id=prep.id,
        ingredient_id=item.ingredient_id,
        sub_preparation_id=item.preparation_id,
        qty=item.qty,
    )


# --- Reservation ----------------------------------------------------------


def reservation_to_domain(row: ReservationORM) -> Reservation:
    return Reservation(
        id=row.id,
        tenant_id=row.tenant_id,
        customer_name=row.customer_name,
        party_size=row.party_size,
        reserved_at=row.reserved_at,
        turn=ServiceTurn(row.turn),
        customer_phone=row.customer_phone,
        table_id=row.table_id,
        status=ReservationStatus(row.status),
        note=row.note,
        created_at=row.created_at,
    )


def advisor_settings_to_domain(row: AdvisorSettingsORM) -> AdvisorSettings:
    return AdvisorSettings(
        tenant_id=row.tenant_id,
        monthly_labor_cost=Money(row.labor_cost_amount, row.currency),
        monthly_other_fixed_costs=Money(row.other_fixed_amount, row.currency),
        target_food_cost_bps=row.target_food_cost_bps,
        seats=row.seats,
        daily_open_minutes=row.daily_open_minutes,
        monthly_inflation_bps=row.monthly_inflation_bps,
        default_vat_bps=row.default_vat_bps,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def advisor_settings_to_orm(settings: AdvisorSettings) -> AdvisorSettingsORM:
    return AdvisorSettingsORM(
        tenant_id=settings.tenant_id,
        labor_cost_amount=settings.monthly_labor_cost.amount,
        other_fixed_amount=settings.monthly_other_fixed_costs.amount,
        currency=settings.currency,
        target_food_cost_bps=settings.target_food_cost_bps,
        seats=settings.seats,
        daily_open_minutes=settings.daily_open_minutes,
        monthly_inflation_bps=settings.monthly_inflation_bps,
        default_vat_bps=settings.default_vat_bps,
    )


def cash_session_to_domain(
    row: CashSessionORM, count_rows: list[CashCountORM]
) -> CashSession:
    currency = row.currency
    return CashSession(
        id=row.id,
        tenant_id=row.tenant_id,
        opened_by=row.opened_by,
        opening_float=Money(row.opening_float_amount, currency),
        currency=currency,
        status=CashSessionStatus(row.status),
        opened_at=row.opened_at,
        closed_at=row.closed_at,
        closed_by=row.closed_by,
        note=row.note,
        counts=[
            CashCount(
                method=PaymentMethod(c.method),
                expected=Money(c.expected_amount, currency),
                counted=Money(c.counted_amount, currency),
            )
            for c in count_rows
        ],
    )


def cash_session_to_orm(session: CashSession) -> CashSessionORM:
    return CashSessionORM(
        id=session.id,
        tenant_id=session.tenant_id,
        opened_by=session.opened_by,
        opening_float_amount=session.opening_float.amount,
        currency=session.currency,
        status=session.status.value,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        closed_by=session.closed_by,
        note=session.note,
    )


def cash_count_to_orm(
    count: CashCount, session: CashSession, count_id: str
) -> CashCountORM:
    return CashCountORM(
        id=count_id,
        tenant_id=session.tenant_id,
        cash_session_id=session.id,
        method=count.method.value,
        expected_amount=count.expected.amount,
        counted_amount=count.counted.amount,
    )


def cash_movement_to_domain(row: CashMovementORM) -> CashMovement:
    return CashMovement(
        id=row.id,
        tenant_id=row.tenant_id,
        cash_session_id=row.cash_session_id,
        kind=CashMovementKind(row.kind),
        amount=Money(row.amount, row.currency),
        created_by=row.created_by,
        reason=row.reason,
        created_at=row.created_at,
    )


def cash_movement_to_orm(movement: CashMovement) -> CashMovementORM:
    return CashMovementORM(
        id=movement.id,
        tenant_id=movement.tenant_id,
        cash_session_id=movement.cash_session_id,
        kind=movement.kind.value,
        amount=movement.amount.amount,
        currency=movement.amount.currency,
        reason=movement.reason,
        created_by=movement.created_by,
    )


def customer_to_domain(row: CustomerORM) -> Customer:
    return Customer(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        phone=row.phone,
        email=row.email,
        notes=row.notes,
        no_contactar=row.no_contactar,
        created_at=row.created_at,
    )


def customer_to_orm(customer: Customer) -> CustomerORM:
    return CustomerORM(
        id=customer.id,
        tenant_id=customer.tenant_id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        notes=customer.notes,
        no_contactar=customer.no_contactar,
    )


def reservation_to_orm(reservation: Reservation) -> ReservationORM:
    return ReservationORM(
        id=reservation.id,
        tenant_id=reservation.tenant_id,
        customer_name=reservation.customer_name,
        customer_phone=reservation.customer_phone,
        party_size=reservation.party_size,
        reserved_at=reservation.reserved_at,
        turn=reservation.turn.value,
        table_id=reservation.table_id,
        status=reservation.status.value,
        note=reservation.note,
    )

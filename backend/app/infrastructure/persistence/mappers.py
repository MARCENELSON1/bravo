"""Mappers between ORM models and domain entities.

``*_to_orm`` omits ``created_at`` so that ``session.merge`` (updates) never
clobbers the DB-managed timestamp and inserts use the column ``server_default``.
"""

from __future__ import annotations

from app.domain.advisor.entities import AdvisorSettings
from app.domain.cashier.entities import CashCount, CashSession
from app.domain.cashier.value_objects import CashSessionStatus
from app.domain.identity.tokens import (
    AuthAuditEntry,
    AuthEvent,
    EmailVerificationToken,
    Invitation,
    PasswordResetToken,
    RefreshToken,
)
from app.domain.inventory.entities import Ingredient, StockMovement, Supplier
from app.domain.inventory.recipe import Recipe, RecipeItem
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
from app.domain.order.value_objects import ItemStatus, OrderStatus, Station
from app.domain.payment.credentials import (
    ConnectionStatus,
    PaymentCredential,
    PaymentProvider,
)
from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.product.entities import Product
from app.domain.reservation.entities import Reservation
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn
from app.domain.shared.money import Money
from app.domain.table.entities import Table
from app.domain.tenant.entities import Tenant
from app.domain.timeclock.entities import Shift
from app.domain.timeclock.value_objects import ShiftSource, ShiftStatus
from app.domain.user.entities import User
from app.domain.user.value_objects import Email, Role
from app.infrastructure.persistence.models import (
    AdvisorSettingsORM,
    AuthAuditORM,
    CashCountORM,
    CashSessionORM,
    EmailVerificationTokenORM,
    IngredientORM,
    InvitationORM,
    InvoiceORM,
    OrderItemORM,
    OrderORM,
    PasswordResetTokenORM,
    PaymentCredentialORM,
    PaymentORM,
    ProductORM,
    RecipeItemORM,
    RecipeORM,
    RefreshTokenORM,
    ReservationORM,
    ShiftORM,
    StockMovementORM,
    SupplierORM,
    TableORM,
    TaxCredentialORM,
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
        station=Station(row.station),
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
        station=product.station.value,
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
                station=Station(item.station),
                status=ItemStatus(item.status),
                sent_at=item.sent_at,
                ready_at=item.ready_at,
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
        status=item.status.value,
        station=item.station.value,
        sent_at=item.sent_at,
        ready_at=item.ready_at,
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
        currency=payment.amount.currency,
        method=payment.method.value,
        status=payment.status.value,
        order_id=payment.order_id,
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
        unit=UnitOfMeasure(row.unit),
        stock_qty=row.stock_qty,
        min_qty=row.min_qty,
        unit_cost=Money(row.unit_cost_amount, row.unit_cost_currency),
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
        active=ingredient.active,
    )


def supplier_to_domain(row: SupplierORM) -> Supplier:
    return Supplier(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        contact=row.contact,
        active=row.active,
        created_at=row.created_at,
    )


def supplier_to_orm(supplier: Supplier) -> SupplierORM:
    return SupplierORM(
        id=supplier.id,
        tenant_id=supplier.tenant_id,
        name=supplier.name,
        contact=supplier.contact,
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
    )


def recipe_to_domain(row: RecipeORM, item_rows: list[RecipeItemORM]) -> Recipe:
    return Recipe(
        product_id=row.product_id,
        tenant_id=row.tenant_id,
        items=[
            RecipeItem(ingredient_id=item.ingredient_id, qty=item.qty) for item in item_rows
        ],
    )


def recipe_to_orm(recipe: Recipe) -> RecipeORM:
    return RecipeORM(product_id=recipe.product_id, tenant_id=recipe.tenant_id)


def recipe_item_to_orm(item: RecipeItem, recipe: Recipe, item_id: str) -> RecipeItemORM:
    return RecipeItemORM(
        id=item_id,
        tenant_id=recipe.tenant_id,
        product_id=recipe.product_id,
        ingredient_id=item.ingredient_id,
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

"""Dependency-injection container: wires domain ports to concrete adapters.

Services are singletons; repositories and use cases are factories (per use).
Tests override providers with fakes via ``container.<provider>.override(...)``.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from app.application.identity.accept_invitation import AcceptInvitation
from app.application.identity.authenticate import Authenticate
from app.application.identity.change_password import ChangePassword
from app.application.identity.invite_user import InviteUser
from app.application.identity.logout import Logout
from app.application.identity.onboard_tenant import OnboardTenant
from app.application.identity.refresh_token import RefreshAccessToken
from app.application.identity.request_password_reset import RequestPasswordReset
from app.application.identity.reset_password import ResetPassword
from app.application.identity.verify_email import VerifyEmail
from app.application.inventory.consume import ConsumeRecipesForOrder
from app.application.inventory.food_cost import GetFoodCost
from app.application.inventory.use_cases import (
    CreateIngredient,
    CreateSupplier,
    GetRecipe,
    ListIngredients,
    ListLowStock,
    ListSuppliers,
    RegisterPurchase,
    RegisterWaste,
    SetRecipe,
    UpdateIngredient,
)
from app.application.invoice.connect_afip import (
    ConnectAfip,
    DisconnectAfip,
    GetAfipConnection,
)
from app.application.invoice.use_cases import GetOrderInvoice, IssueInvoice, ListInvoices
from app.application.order.use_cases import (
    AddOrderItem,
    AdvanceOrder,
    CreateOrder,
    GetKdsOrders,
    GetOrder,
    ListOrders,
    SendOrder,
)
from app.application.payment.connect_mercadopago import (
    CompleteMercadoPagoConnection,
    DisconnectMercadoPago,
    GetMercadoPagoConnection,
    StartMercadoPagoConnection,
)
from app.application.payment.use_cases import (
    ConfirmGatewayPayment,
    ListExpenses,
    ListOrderPayments,
    RegisterExpense,
    RegisterPayment,
)
from app.application.product.use_cases import CreateProduct, ListProducts
from app.application.reporting.dashboard import GetDashboardSummary
from app.application.reporting.staff import GetStaffReport
from app.application.reservation.use_cases import (
    CancelReservation,
    CompleteReservation,
    ConfirmReservation,
    CreateReservation,
    GetReservation,
    ListReservations,
    MarkNoShow,
    SeatReservation,
    UpdateReservation,
)
from app.application.table.use_cases import CreateTable, ListTables
from app.application.timeclock.presence import (
    GetPresenceChallenge,
    PunchWithPresence,
    RegisterPresenceDevice,
)
from app.application.timeclock.use_cases import (
    AdjustShift,
    ClockIn,
    ClockOut,
    GetMyTimeclock,
    ListShifts,
    Punch,
)
from app.config import Settings
from app.infrastructure.email.console_sender import ConsoleEmailSender
from app.infrastructure.email.smtp_sender import SmtpEmailSender
from app.infrastructure.invoicing.afip_invoicing import AfipInvoicing
from app.infrastructure.invoicing.credentials_resolver import DbTaxCredentialsResolver
from app.infrastructure.invoicing.fake_invoicing import FakeInvoicing
from app.infrastructure.payments.credentials_resolver import DbPaymentCredentialsResolver
from app.infrastructure.payments.manual_gateway import ManualPaymentGateway
from app.infrastructure.payments.mercadopago_gateway import MercadoPagoGateway
from app.infrastructure.payments.mercadopago_oauth import MercadoPagoOAuthClient
from app.infrastructure.persistence.audit_repo import SqlAlchemyAuditRepository
from app.infrastructure.persistence.credentials_repo import (
    SqlAlchemyPaymentCredentialRepository,
)
from app.infrastructure.persistence.dashboard_repo import SqlAlchemyDashboardReadModel
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.food_cost_repo import SqlAlchemyFoodCostReadModel
from app.infrastructure.persistence.ingredient_repo import SqlAlchemyIngredientRepository
from app.infrastructure.persistence.invitation_repo import SqlAlchemyInvitationRepository
from app.infrastructure.persistence.invoice_repo import SqlAlchemyInvoiceRepository
from app.infrastructure.persistence.order_repo import SqlAlchemyOrderRepository
from app.infrastructure.persistence.payment_repo import SqlAlchemyPaymentRepository
from app.infrastructure.persistence.presence_store_repo import (
    SqlAlchemyPresenceUsageStore,
)
from app.infrastructure.persistence.product_repo import SqlAlchemyProductRepository
from app.infrastructure.persistence.recipe_repo import SqlAlchemyRecipeRepository
from app.infrastructure.persistence.refresh_token_repo import SqlAlchemyRefreshTokenRepository
from app.infrastructure.persistence.reservation_repo import (
    SqlAlchemyReservationRepository,
)
from app.infrastructure.persistence.reset_token_repo import SqlAlchemyResetTokenRepository
from app.infrastructure.persistence.shift_repo import SqlAlchemyShiftRepository
from app.infrastructure.persistence.staff_report_repo import SqlAlchemyStaffReportReadModel
from app.infrastructure.persistence.stock_movement_repo import (
    SqlAlchemyStockMovementRepository,
)
from app.infrastructure.persistence.supplier_repo import SqlAlchemySupplierRepository
from app.infrastructure.persistence.table_repo import SqlAlchemyTableRepository
from app.infrastructure.persistence.tax_credentials_repo import (
    SqlAlchemyTaxCredentialRepository,
)
from app.infrastructure.persistence.tenant_repo import SqlAlchemyTenantRepository
from app.infrastructure.persistence.user_repo import SqlAlchemyUserRepository
from app.infrastructure.persistence.verification_token_repo import (
    SqlAlchemyVerificationTokenRepository,
)
from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tenant_context import ContextVarTenantContext
from app.infrastructure.security.token_service import JwtTokenService
from app.infrastructure.timeclock.hmac_presence import HmacPresenceToken
from app.infrastructure.timeclock.no_presence import NoPresence


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.presentation"])

    config = providers.Singleton(Settings)
    db = providers.Singleton(Database, url=config.provided.database_url)

    # --- external services (singletons) ---
    password_hasher = providers.Singleton(Argon2Hasher)
    token_service = providers.Singleton(
        JwtTokenService,
        secret=config.provided.jwt_secret,
        algorithm=config.provided.jwt_alg,
        access_token_ttl_min=config.provided.access_token_ttl_min,
    )
    tenant_context = providers.Singleton(ContextVarTenantContext)
    email_sender = providers.Selector(
        config.provided.email_transport,
        console=providers.Singleton(ConsoleEmailSender),
        smtp=providers.Singleton(
            SmtpEmailSender,
            host=config.provided.smtp_host,
            port=config.provided.smtp_port,
            username=config.provided.smtp_user,
            password=config.provided.smtp_password,
            from_email=config.provided.from_email,
            use_tls=config.provided.smtp_use_tls,
        ),
    )

    # --- repositories (per-use factories) ---
    tenant_repository = providers.Factory(
        SqlAlchemyTenantRepository, session_factory=db.provided.session
    )
    user_repository = providers.Factory(
        SqlAlchemyUserRepository, session_factory=db.provided.session
    )
    table_repository = providers.Factory(
        SqlAlchemyTableRepository, session_factory=db.provided.session
    )
    product_repository = providers.Factory(
        SqlAlchemyProductRepository, session_factory=db.provided.session
    )
    order_repository = providers.Factory(
        SqlAlchemyOrderRepository, session_factory=db.provided.session
    )
    refresh_token_repository = providers.Factory(
        SqlAlchemyRefreshTokenRepository, session_factory=db.provided.session
    )
    reset_token_repository = providers.Factory(
        SqlAlchemyResetTokenRepository, session_factory=db.provided.session
    )
    verification_token_repository = providers.Factory(
        SqlAlchemyVerificationTokenRepository, session_factory=db.provided.session
    )
    invitation_repository = providers.Factory(
        SqlAlchemyInvitationRepository, session_factory=db.provided.session
    )
    audit_repository = providers.Factory(
        SqlAlchemyAuditRepository, session_factory=db.provided.session
    )

    # --- use cases (per-use factories) ---
    authenticate = providers.Factory(
        Authenticate,
        users=user_repository,
        tenants=tenant_repository,
        hasher=password_hasher,
        tokens=token_service,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
        max_login_attempts=config.provided.max_login_attempts,
        lockout_minutes=config.provided.lockout_minutes,
        refresh_token_ttl_days=config.provided.refresh_token_ttl_days,
    )
    refresh_access_token = providers.Factory(
        RefreshAccessToken,
        refresh_tokens=refresh_token_repository,
        users=user_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
        refresh_token_ttl_days=config.provided.refresh_token_ttl_days,
    )
    logout = providers.Factory(
        Logout,
        refresh_tokens=refresh_token_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    change_password = providers.Factory(
        ChangePassword,
        users=user_repository,
        hasher=password_hasher,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    request_password_reset = providers.Factory(
        RequestPasswordReset,
        tenants=tenant_repository,
        users=user_repository,
        reset_tokens=reset_token_repository,
        tokens=token_service,
        email_sender=email_sender,
        tenant_context=tenant_context,
        reset_token_ttl_min=config.provided.reset_token_ttl_min,
        app_base_url=config.provided.app_base_url,
    )
    reset_password = providers.Factory(
        ResetPassword,
        reset_tokens=reset_token_repository,
        users=user_repository,
        hasher=password_hasher,
        tokens=token_service,
        refresh_tokens=refresh_token_repository,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    verify_email = providers.Factory(
        VerifyEmail,
        verification_tokens=verification_token_repository,
        users=user_repository,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )
    onboard_tenant = providers.Factory(
        OnboardTenant,
        tenants=tenant_repository,
        users=user_repository,
        verification_tokens=verification_token_repository,
        hasher=password_hasher,
        tokens=token_service,
        email_sender=email_sender,
        audit=audit_repository,
        tenant_context=tenant_context,
        verification_token_ttl_hours=config.provided.verification_token_ttl_hours,
        app_base_url=config.provided.app_base_url,
    )
    invite_user = providers.Factory(
        InviteUser,
        users=user_repository,
        invitations=invitation_repository,
        tenants=tenant_repository,
        tokens=token_service,
        email_sender=email_sender,
        audit=audit_repository,
        tenant_context=tenant_context,
        invitation_token_ttl_hours=config.provided.invitation_token_ttl_hours,
        app_base_url=config.provided.app_base_url,
    )
    accept_invitation = providers.Factory(
        AcceptInvitation,
        invitations=invitation_repository,
        users=user_repository,
        hasher=password_hasher,
        tokens=token_service,
        audit=audit_repository,
        tenant_context=tenant_context,
    )

    # --- Fase 2: comandas / KDS ---
    create_product = providers.Factory(
        CreateProduct,
        products=product_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    list_products = providers.Factory(
        ListProducts, products=product_repository, tenant_context=tenant_context
    )
    create_table = providers.Factory(
        CreateTable, tables=table_repository, tenant_context=tenant_context
    )
    list_tables = providers.Factory(
        ListTables, tables=table_repository, tenant_context=tenant_context
    )
    create_order = providers.Factory(
        CreateOrder,
        orders=order_repository,
        tables=table_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    get_order = providers.Factory(
        GetOrder, orders=order_repository, tenant_context=tenant_context
    )
    add_order_item = providers.Factory(
        AddOrderItem,
        orders=order_repository,
        products=product_repository,
        tenant_context=tenant_context,
    )
    send_order = providers.Factory(
        SendOrder, orders=order_repository, tenant_context=tenant_context
    )
    advance_order = providers.Factory(
        AdvanceOrder, orders=order_repository, tenant_context=tenant_context
    )
    list_orders = providers.Factory(
        ListOrders, orders=order_repository, tenant_context=tenant_context
    )
    get_kds_orders = providers.Factory(
        GetKdsOrders, orders=order_repository, tenant_context=tenant_context
    )

    # --- Fase 6 (repos de inventario + consumo por venta) ---
    # Definidos antes de pagos porque el settle inyecta el InventoryConsumer.
    # El resto de los casos de uso de inventario está más abajo.
    ingredient_repository = providers.Factory(
        SqlAlchemyIngredientRepository, session_factory=db.provided.session
    )
    supplier_repository = providers.Factory(
        SqlAlchemySupplierRepository, session_factory=db.provided.session
    )
    recipe_repository = providers.Factory(
        SqlAlchemyRecipeRepository, session_factory=db.provided.session
    )
    stock_movement_repository = providers.Factory(
        SqlAlchemyStockMovementRepository, session_factory=db.provided.session
    )
    consume_recipes_for_order = providers.Factory(
        ConsumeRecipesForOrder,
        orders=order_repository,
        recipes=recipe_repository,
        ingredients=ingredient_repository,
        movements=stock_movement_repository,
        tenant_context=tenant_context,
    )

    # --- Fase 3: pagos (ingresos/egresos) ---
    payment_repository = providers.Factory(
        SqlAlchemyPaymentRepository, session_factory=db.provided.session
    )
    # --- Fase 3.5: conexión MP por tenant (OAuth) ---
    token_cipher = providers.Singleton(
        FernetTokenCipher, key=config.provided.credentials_encryption_key
    )
    payment_credential_repository = providers.Factory(
        SqlAlchemyPaymentCredentialRepository, session_factory=db.provided.session
    )
    mercadopago_oauth = providers.Singleton(
        MercadoPagoOAuthClient,
        client_id=config.provided.mp_client_id,
        client_secret=config.provided.mp_client_secret,
    )
    payment_credentials_resolver = providers.Singleton(
        DbPaymentCredentialsResolver,
        credentials=payment_credential_repository,
        oauth=mercadopago_oauth,
        cipher=token_cipher,
        fallback_token=config.provided.mp_access_token,
    )

    # Online gateway (MercadoPago): resolves the tenant's OWN token per charge;
    # also serves the inbound webhook regardless of the selected gateway.
    mercadopago_gateway = providers.Singleton(
        MercadoPagoGateway,
        credentials_resolver=payment_credentials_resolver,
        webhook_secret=config.provided.mp_webhook_secret,
        notification_url=config.provided.mp_notification_url,
        access_token=config.provided.mp_access_token,
        marketplace_fee=config.provided.mp_marketplace_fee,
    )
    start_mp_connection = providers.Factory(
        StartMercadoPagoConnection,
        oauth=mercadopago_oauth,
        tenant_context=tenant_context,
        state_secret=config.provided.jwt_secret,
        redirect_uri=config.provided.mp_oauth_redirect_uri,
    )
    complete_mp_connection = providers.Factory(
        CompleteMercadoPagoConnection,
        oauth=mercadopago_oauth,
        credentials=payment_credential_repository,
        cipher=token_cipher,
        tenant_context=tenant_context,
        state_secret=config.provided.jwt_secret,
        redirect_uri=config.provided.mp_oauth_redirect_uri,
        state_ttl_min=config.provided.oauth_state_ttl_min,
    )
    disconnect_mp = providers.Factory(
        DisconnectMercadoPago,
        credentials=payment_credential_repository,
        tenant_context=tenant_context,
    )
    get_mp_connection = providers.Factory(
        GetMercadoPagoConnection,
        credentials=payment_credential_repository,
        tenant_context=tenant_context,
    )
    payment_gateway = providers.Selector(
        config.provided.payment_gateway,
        manual=providers.Singleton(ManualPaymentGateway),
        mercadopago=mercadopago_gateway,
    )
    register_payment = providers.Factory(
        RegisterPayment,
        payments=payment_repository,
        orders=order_repository,
        gateway=payment_gateway,
        tenant_context=tenant_context,
        inventory=consume_recipes_for_order,
    )
    confirm_gateway_payment = providers.Factory(
        ConfirmGatewayPayment,
        payments=payment_repository,
        orders=order_repository,
        notifications=mercadopago_gateway,
        resolver=payment_credentials_resolver,
        tenant_context=tenant_context,
        inventory=consume_recipes_for_order,
    )
    register_expense = providers.Factory(
        RegisterExpense,
        payments=payment_repository,
        tenants=tenant_repository,
        gateway=payment_gateway,
        tenant_context=tenant_context,
    )
    list_order_payments = providers.Factory(
        ListOrderPayments, payments=payment_repository, tenant_context=tenant_context
    )
    list_expenses = providers.Factory(
        ListExpenses, payments=payment_repository, tenant_context=tenant_context
    )

    # --- Reporting (read models) ---
    dashboard_read_model = providers.Factory(
        SqlAlchemyDashboardReadModel, session_factory=db.provided.session
    )
    get_dashboard_summary = providers.Factory(
        GetDashboardSummary, read_model=dashboard_read_model, tenant_context=tenant_context
    )
    staff_report_read_model = providers.Factory(
        SqlAlchemyStaffReportReadModel, session_factory=db.provided.session
    )
    get_staff_report = providers.Factory(
        GetStaffReport, read_model=staff_report_read_model, tenant_context=tenant_context
    )

    # --- Fase 4: facturación electrónica AFIP ---
    invoice_repository = providers.Factory(
        SqlAlchemyInvoiceRepository, session_factory=db.provided.session
    )
    tax_credential_repository = providers.Factory(
        SqlAlchemyTaxCredentialRepository, session_factory=db.provided.session
    )
    tax_credentials_resolver = providers.Singleton(
        DbTaxCredentialsResolver, credentials=tax_credential_repository, cipher=token_cipher
    )
    invoicing_provider = providers.Selector(
        config.provided.invoicing_provider,
        fake=providers.Singleton(FakeInvoicing),
        afip=providers.Singleton(
            AfipInvoicing,
            resolver=tax_credentials_resolver,
            afip_env=config.provided.afip_env,
        ),
    )
    issue_invoice = providers.Factory(
        IssueInvoice,
        invoices=invoice_repository,
        orders=order_repository,
        tax_credentials=tax_credential_repository,
        invoicing=invoicing_provider,
        tenant_context=tenant_context,
    )
    list_invoices = providers.Factory(
        ListInvoices, invoices=invoice_repository, tenant_context=tenant_context
    )
    get_order_invoice = providers.Factory(
        GetOrderInvoice, invoices=invoice_repository, tenant_context=tenant_context
    )
    connect_afip = providers.Factory(
        ConnectAfip,
        credentials=tax_credential_repository,
        cipher=token_cipher,
        tenant_context=tenant_context,
    )
    get_afip_connection = providers.Factory(
        GetAfipConnection, credentials=tax_credential_repository, tenant_context=tenant_context
    )
    disconnect_afip = providers.Factory(
        DisconnectAfip, credentials=tax_credential_repository, tenant_context=tenant_context
    )

    # --- Fase 5: fichaje (shifts) ---
    shift_repository = providers.Factory(
        SqlAlchemyShiftRepository, session_factory=db.provided.session
    )
    clock_in = providers.Factory(
        ClockIn, shifts=shift_repository, tenant_context=tenant_context
    )
    clock_out = providers.Factory(
        ClockOut, shifts=shift_repository, tenant_context=tenant_context
    )
    punch = providers.Factory(
        Punch, shifts=shift_repository, tenant_context=tenant_context
    )
    get_my_timeclock = providers.Factory(
        GetMyTimeclock, shifts=shift_repository, tenant_context=tenant_context
    )
    list_shifts = providers.Factory(
        ListShifts, shifts=shift_repository, tenant_context=tenant_context
    )
    adjust_shift = providers.Factory(
        AdjustShift, shifts=shift_repository, tenant_context=tenant_context
    )

    # --- Fase 5.5: capa de presencia (QR + código rotativo) ---
    presence_usage_store = providers.Factory(
        SqlAlchemyPresenceUsageStore, session_factory=db.provided.session
    )
    presence_token = providers.Selector(
        config.provided.presence_provider,
        hmac=providers.Singleton(
            HmacPresenceToken,
            store=presence_usage_store,
            secret=config.provided.effective_presence_secret,
            period_seconds=config.provided.presence_period_seconds,
            rate_max=config.provided.presence_rate_max,
            rate_window_seconds=config.provided.presence_rate_window_seconds,
        ),
        off=providers.Singleton(NoPresence),
    )
    register_presence_device = providers.Factory(
        RegisterPresenceDevice, presence=presence_token, tenant_context=tenant_context
    )
    get_presence_challenge = providers.Factory(
        GetPresenceChallenge, presence=presence_token
    )
    punch_with_presence = providers.Factory(
        PunchWithPresence,
        presence=presence_token,
        punch=punch,
        tenant_context=tenant_context,
    )

    # --- Fase 6: inventario (casos de uso; repos arriba, antes de pagos) ---
    create_ingredient = providers.Factory(
        CreateIngredient,
        ingredients=ingredient_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    list_ingredients = providers.Factory(
        ListIngredients, ingredients=ingredient_repository, tenant_context=tenant_context
    )
    update_ingredient = providers.Factory(
        UpdateIngredient, ingredients=ingredient_repository, tenant_context=tenant_context
    )
    register_purchase = providers.Factory(
        RegisterPurchase,
        ingredients=ingredient_repository,
        movements=stock_movement_repository,
        tenant_context=tenant_context,
    )
    register_waste = providers.Factory(
        RegisterWaste,
        ingredients=ingredient_repository,
        movements=stock_movement_repository,
        tenant_context=tenant_context,
    )
    list_low_stock = providers.Factory(
        ListLowStock, ingredients=ingredient_repository, tenant_context=tenant_context
    )
    create_supplier = providers.Factory(
        CreateSupplier, suppliers=supplier_repository, tenant_context=tenant_context
    )
    list_suppliers = providers.Factory(
        ListSuppliers, suppliers=supplier_repository, tenant_context=tenant_context
    )
    set_recipe = providers.Factory(
        SetRecipe,
        recipes=recipe_repository,
        products=product_repository,
        ingredients=ingredient_repository,
        tenant_context=tenant_context,
    )
    get_recipe = providers.Factory(
        GetRecipe, recipes=recipe_repository, tenant_context=tenant_context
    )
    food_cost_read_model = providers.Factory(
        SqlAlchemyFoodCostReadModel, session_factory=db.provided.session
    )
    get_food_cost = providers.Factory(
        GetFoodCost, read_model=food_cost_read_model, tenant_context=tenant_context
    )

    # --- Fase 7: reservas ---
    reservation_repository = providers.Factory(
        SqlAlchemyReservationRepository, session_factory=db.provided.session
    )
    create_reservation = providers.Factory(
        CreateReservation,
        reservations=reservation_repository,
        tables=table_repository,
        tenant_context=tenant_context,
    )
    list_reservations = providers.Factory(
        ListReservations, reservations=reservation_repository, tenant_context=tenant_context
    )
    get_reservation = providers.Factory(
        GetReservation, reservations=reservation_repository, tenant_context=tenant_context
    )
    confirm_reservation = providers.Factory(
        ConfirmReservation, reservations=reservation_repository, tenant_context=tenant_context
    )
    seat_reservation = providers.Factory(
        SeatReservation, reservations=reservation_repository, tenant_context=tenant_context
    )
    complete_reservation = providers.Factory(
        CompleteReservation,
        reservations=reservation_repository,
        tenant_context=tenant_context,
    )
    cancel_reservation = providers.Factory(
        CancelReservation, reservations=reservation_repository, tenant_context=tenant_context
    )
    mark_no_show = providers.Factory(
        MarkNoShow, reservations=reservation_repository, tenant_context=tenant_context
    )
    update_reservation = providers.Factory(
        UpdateReservation,
        reservations=reservation_repository,
        tables=table_repository,
        tenant_context=tenant_context,
    )

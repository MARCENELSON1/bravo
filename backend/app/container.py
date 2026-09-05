"""Dependency-injection container: wires domain ports to concrete adapters.

Services are singletons; repositories and use cases are factories (per use).
Tests override providers with fakes via ``container.<provider>.override(...)``.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from app.application.advisor.report import GetAdvisorReport
from app.application.advisor.use_cases import (
    GetAdvisorSettings,
    RebuildAdvisorDiagnostics,
    UpdateAdvisorSettings,
)
from app.application.analytics.projection import ProjectOrderSales
from app.application.analytics.rebuild import RebuildSalesFacts
from app.application.analytics.use_cases import (
    GetPaymentMix,
    GetProductPerformance,
    GetRevenueDaily,
    GetRevenueSummary,
)
from app.application.billing.platform_use_cases import (
    DeletePlan,
    ListAllPlans,
    SavePlan,
)
from app.application.billing.use_cases import (
    CancelSubscription,
    GetSubscription,
    HandleBillingWebhook,
    ListPlans,
    StartSubscriptionCheckout,
)
from app.application.cashier.settings import GetCashSettings, UpdateCashSettings
from app.application.cashier.tips import GetTipsReport, PayTips
from app.application.cashier.use_cases import (
    CloseCashSession,
    GetCurrentCashReport,
    OpenCashSession,
    RegisterCashMovement,
)
from app.application.contact.use_cases import (
    GetContactResult,
    GetRecentContacts,
    LogContact,
)
from app.application.copilot.ask import AskCopilot
from app.application.customer.use_cases import (
    AssignOrderCustomer,
    CreateCustomer,
    DeleteCustomer,
    GetCustomer,
    GetCustomerHistory,
    GetCustomerStats,
    ListCustomers,
    UpdateCustomer,
)
from app.application.finance.snapshots import RebuildFinanceSnapshots
from app.application.finance.tax_collected import GetTaxCollected
from app.application.finance.use_cases import (
    GetExpenseBreakdown,
    GetFinanceOverview,
    GetProductDetail,
    GetRecentMovements,
)
from app.application.floor.use_cases import GetFloor
from app.application.identity.accept_invitation import AcceptInvitation
from app.application.identity.authenticate import Authenticate
from app.application.identity.change_password import ChangePassword
from app.application.identity.get_my_profile import GetMyProfile
from app.application.identity.invite_user import InviteUser
from app.application.identity.logout import Logout
from app.application.identity.onboard_tenant import OnboardTenant
from app.application.identity.refresh_token import RefreshAccessToken
from app.application.identity.request_password_reset import RequestPasswordReset
from app.application.identity.reset_password import ResetPassword
from app.application.identity.set_hourly_rate import SetUserHourlyRate
from app.application.identity.verify_email import VerifyEmail
from app.application.inventory.consume import ConsumeRecipesForOrder
from app.application.inventory.cost_history import GetIngredientCostHistory
from app.application.inventory.food_cost import GetFoodCost
from app.application.inventory.preparations import (
    DeletePreparation,
    ListPreparations,
    SavePreparation,
)
from app.application.inventory.use_cases import (
    CreateIngredient,
    CreateSupplier,
    GetRecipe,
    GetSupplierPurchases,
    ListIngredients,
    ListLowStock,
    ListSuppliers,
    RegisterPurchase,
    RegisterWaste,
    SetRecipe,
    UpdateIngredient,
    UpdateSupplier,
)
from app.application.invoice.connect_afip import (
    ConnectAfip,
    DisconnectAfip,
    GetAfipConnection,
)
from app.application.invoice.use_cases import GetOrderInvoice, IssueInvoice, ListInvoices
from app.application.marketing.submit_lead import SubmitLead
from app.application.notification.use_cases import RegisterDeviceToken
from app.application.order.auto_assign import AutoAssignWaiter
from app.application.order.self_order import (
    GetSelfOrderSettings,
    SubmitCustomerOrder,
    UpdateSelfOrderSettings,
)
from app.application.order.table_bill import GetTableBill
from app.application.order.use_cases import (
    AddOrderItem,
    AddOrderItemsBatch,
    AdvanceItem,
    AdvanceOrder,
    CloseSettledOrder,
    CreateOrder,
    GetKdsOrders,
    GetOrder,
    ListOrders,
    ListPendingQrOrders,
    MergeOrders,
    RemoveOrderItem,
    ReopenOrder,
    SendOrder,
    SetItemNote,
    SetItemQuantity,
    TransferOrder,
)
from app.application.payment.connect_mercadopago import (
    CompleteMercadoPagoConnection,
    DisconnectMercadoPago,
    GetMercadoPagoConnection,
    StartMercadoPagoConnection,
)
from app.application.payment.fee_rates import GetPaymentFeeRates, UpdatePaymentFeeRates
from app.application.payment.pay_table_bill import (
    GetPublicPaymentReceipt,
    GetPublicPaymentStatus,
    PayTableBill,
)
from app.application.payment.self_pay import GetSelfPaySettings, UpdateSelfPaySettings
from app.application.payment.use_cases import (
    ConfirmGatewayPayment,
    ListExpenses,
    ListOrderPayments,
    RefundPayment,
    RegisterExpense,
    RegisterPayment,
)
from app.application.product.modifiers import (
    GetProductModifiers,
    ListMenuModifiers,
    SetProductModifiers,
)
from app.application.product.use_cases import (
    CreateProduct,
    GetPricingInsights,
    GetProductPriceHistory,
    GetProductRotation,
    ListProducts,
    SetProductAvailability,
    UpdateProductPrice,
)
from app.application.public_menu.use_cases import (
    GetPublicMenu,
    IssueTableQr,
    RequestTableAttention,
)
from app.application.reporting.dashboard import GetDashboardSummary
from app.application.reporting.exports import ExportReport
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
from app.application.table.use_cases import CreateTable, ListTables, UpdateTable
from app.application.table_session.sectors import (
    CreateSector,
    DeleteSector,
    ListSectors,
    UpdateSector,
)
from app.application.table_session.use_cases import (
    AssignTableWaiter,
    OpenSession,
    RequestBill,
    SetSessionPax,
)
from app.application.tax.quote_order_tax import QuoteOrderTax
from app.application.tax.reporting import GetTaxReportStatus, ReportPendingTaxSales
from app.application.tax.taxjar_connection import (
    ConnectTaxJar,
    DisconnectTaxJar,
    GetTaxJarConnection,
)
from app.application.tenant.fiscal import (
    GetTenantFiscalSettings,
    UpdateTenantFiscalAddress,
)
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
from app.infrastructure.advisor.claude_narrator import ClaudeNarrator
from app.infrastructure.advisor.claude_synthesizer import ClaudeSynthesizer
from app.infrastructure.advisor.llm import AnthropicAdvisorLLM
from app.infrastructure.advisor.no_synthesis import NoSynthesis
from app.infrastructure.advisor.template_narrator import TemplateNarrator
from app.infrastructure.billing.mercadopago_gateway import MercadoPagoPreapprovalGateway
from app.infrastructure.billing.resolver import RailBillingGatewayResolver
from app.infrastructure.billing.stripe_gateway import StripeBillingGateway
from app.infrastructure.copilot.anthropic_copilot import AnthropicCopilotLLM
from app.infrastructure.copilot.no_copilot import NoCopilot
from app.infrastructure.copilot.sql_runner import SqlAlchemyCopilotQueryRunner
from app.infrastructure.email.console_sender import ConsoleEmailSender
from app.infrastructure.email.resend_sender import ResendEmailSender
from app.infrastructure.email.smtp_sender import SmtpEmailSender
from app.infrastructure.invoicing.afip_invoicing import AfipInvoicing
from app.infrastructure.invoicing.credentials_resolver import DbTaxCredentialsResolver
from app.infrastructure.invoicing.fake_invoicing import FakeInvoicing
from app.infrastructure.llm.client import AnthropicClient
from app.infrastructure.marketing.log_lead_gateway import LogLeadGateway
from app.infrastructure.marketing.twenty_lead_gateway import TwentyLeadGateway
from app.infrastructure.notification.fcm_service import FcmPushService
from app.infrastructure.notification.null_service import NullPushService
from app.infrastructure.payments.credentials_resolver import DbPaymentCredentialsResolver
from app.infrastructure.payments.manual_gateway import ManualPaymentGateway
from app.infrastructure.payments.mercadopago_gateway import MercadoPagoGateway
from app.infrastructure.payments.mercadopago_oauth import MercadoPagoOAuthClient
from app.infrastructure.persistence.advisor_diagnostics_repo import (
    SqlAlchemyAdvisorDiagnosticsCache,
)
from app.infrastructure.persistence.advisor_repo import (
    SqlAlchemyAdvisorReadModel,
    SqlAlchemyAdvisorSnapshotReadModel,
)
from app.infrastructure.persistence.advisor_settings_repo import (
    SqlAlchemyAdvisorSettingsRepository,
)
from app.infrastructure.persistence.analytics_repo import (
    SqlAlchemyPaymentMixReadModel,
    SqlAlchemyProductPerformanceReadModel,
    SqlAlchemyRevenueDailyReadModel,
    SqlAlchemyRevenueReadModel,
)
from app.infrastructure.persistence.audit_repo import SqlAlchemyAuditRepository
from app.infrastructure.persistence.billing_repo import (
    SqlAlchemyPlanRepository,
    SqlAlchemySubscriptionRepository,
)
from app.infrastructure.persistence.cash_movement_repo import (
    SqlAlchemyCashMovementRepository,
)
from app.infrastructure.persistence.cash_policy_repo import SqlAlchemyCashSessionPolicy
from app.infrastructure.persistence.cash_repo import SqlAlchemyCashSessionRepository
from app.infrastructure.persistence.cash_settings_repo import (
    SqlAlchemyCashSettingsRepository,
)
from app.infrastructure.persistence.contact_repo import (
    SqlAlchemyContactLogRepository,
)
from app.infrastructure.persistence.contact_result_repo import (
    SqlAlchemyContactResultReadModel,
)
from app.infrastructure.persistence.cost_history_repo import (
    SqlAlchemyIngredientCostHistoryReadModel,
)
from app.infrastructure.persistence.credentials_repo import (
    SqlAlchemyPaymentCredentialRepository,
)
from app.infrastructure.persistence.customer_history_repo import (
    SqlAlchemyCustomerHistoryReadModel,
)
from app.infrastructure.persistence.customer_repo import SqlAlchemyCustomerRepository
from app.infrastructure.persistence.customer_stats_repo import (
    SqlAlchemyCustomerStatsReadModel,
)
from app.infrastructure.persistence.dashboard_repo import SqlAlchemyDashboardReadModel
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.device_token_repo import (
    SqlAlchemyDeviceTokenRepository,
)
from app.infrastructure.persistence.finance_repo import (
    SqlAlchemyExpenseBreakdownReadModel,
    SqlAlchemyFinanceCommissionsReadModel,
    SqlAlchemyFinanceProductDetailReadModel,
    SqlAlchemyInventoryValueReadModel,
    SqlAlchemyRecentMovementsReadModel,
    SqlAlchemyTaxCollectedReadModel,
)
from app.infrastructure.persistence.finance_snapshot_repo import (
    SqlAlchemyFinanceSnapshotRepository,
)
from app.infrastructure.persistence.food_cost_repo import SqlAlchemyFoodCostReadModel
from app.infrastructure.persistence.ingredient_repo import SqlAlchemyIngredientRepository
from app.infrastructure.persistence.invitation_repo import SqlAlchemyInvitationRepository
from app.infrastructure.persistence.invoice_repo import SqlAlchemyInvoiceRepository
from app.infrastructure.persistence.labor_cost_repo import SqlAlchemyLaborCostReadModel
from app.infrastructure.persistence.modifier_repo import SqlAlchemyModifierRepository
from app.infrastructure.persistence.order_repo import SqlAlchemyOrderRepository
from app.infrastructure.persistence.payment_fee_repo import (
    SqlAlchemyPaymentFeeRateRepository,
)
from app.infrastructure.persistence.payment_repo import SqlAlchemyPaymentRepository
from app.infrastructure.persistence.preparation_repo import (
    SqlAlchemyPreparationRepository,
)
from app.infrastructure.persistence.presence_store_repo import (
    SqlAlchemyPresenceUsageStore,
)
from app.infrastructure.persistence.product_pricing_repo import (
    SqlAlchemyPriceChangeRepository,
    SqlAlchemyPricingReadModel,
    SqlAlchemyRotationReadModel,
)
from app.infrastructure.persistence.product_repo import SqlAlchemyProductRepository
from app.infrastructure.persistence.recipe_repo import SqlAlchemyRecipeRepository
from app.infrastructure.persistence.refresh_token_repo import SqlAlchemyRefreshTokenRepository
from app.infrastructure.persistence.report_export_repo import (
    SqlAlchemyReportExportReadModel,
)
from app.infrastructure.persistence.reservation_repo import (
    SqlAlchemyReservationRepository,
)
from app.infrastructure.persistence.reset_token_repo import SqlAlchemyResetTokenRepository
from app.infrastructure.persistence.sale_facts_repo import SqlAlchemySaleFactsRepository
from app.infrastructure.persistence.sector_repo import SqlAlchemySectorRepository
from app.infrastructure.persistence.self_order_settings_repo import (
    SqlAlchemySelfOrderSettingsRepository,
)
from app.infrastructure.persistence.self_pay_settings_repo import (
    SqlAlchemySelfPaySettingsRepository,
)
from app.infrastructure.persistence.shift_repo import SqlAlchemyShiftRepository
from app.infrastructure.persistence.staff_report_repo import SqlAlchemyStaffReportReadModel
from app.infrastructure.persistence.stock_movement_repo import (
    SqlAlchemyStockMovementRepository,
)
from app.infrastructure.persistence.supplier_purchases_repo import (
    SqlAlchemySupplierPurchasesReadModel,
)
from app.infrastructure.persistence.supplier_repo import SqlAlchemySupplierRepository
from app.infrastructure.persistence.table_repo import SqlAlchemyTableRepository
from app.infrastructure.persistence.table_session_repo import (
    SqlAlchemyTableSessionRepository,
)
from app.infrastructure.persistence.tax_credentials_repo import (
    SqlAlchemyTaxCredentialRepository,
)
from app.infrastructure.persistence.tax_report_repo import (
    SqlAlchemyTaxReportLedger,
    SqlAlchemyTaxReportStatusReadModel,
)
from app.infrastructure.persistence.taxjar_credentials_repo import (
    SqlAlchemyTaxJarCredentialRepository,
)
from app.infrastructure.persistence.tenant_repo import SqlAlchemyTenantRepository
from app.infrastructure.persistence.tips_repo import (
    SqlAlchemyTipPayoutRepository,
    SqlAlchemyTipsReadModel,
)
from app.infrastructure.persistence.user_repo import SqlAlchemyUserRepository
from app.infrastructure.persistence.verification_token_repo import (
    SqlAlchemyVerificationTokenRepository,
)
from app.infrastructure.public_menu.signed_table_qr import HmacTableQrToken
from app.infrastructure.realtime.memory_bus import InMemoryEventBus
from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.rate_limiter import InMemoryRateLimiter
from app.infrastructure.security.tenant_context import ContextVarTenantContext
from app.infrastructure.security.token_service import JwtTokenService
from app.infrastructure.tax.reporter_resolver import DbTaxJarReporterResolver
from app.infrastructure.tax.resolver import EngineTaxCalculatorResolver
from app.infrastructure.tax.simple_calculators import IncludedTaxCalculator
from app.infrastructure.tax.taxjar_calculator import TaxJarCalculator
from app.infrastructure.tax.taxjar_validator import TaxJarCredentialValidator
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
    # Realtime bus (Fase 13 T4): SINGLETON so publishers (order use cases) and
    # SSE subscribers share the same in-process instance.
    event_bus = providers.Singleton(InMemoryEventBus)
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
        resend=providers.Singleton(
            ResendEmailSender,
            api_key=config.provided.resend_api_key,
            from_email=config.provided.from_email,
        ),
    )
    # Push (Fase 4): none = no-op (default, seguro); fcm = envío real por FCM.
    device_token_repository = providers.Factory(
        SqlAlchemyDeviceTokenRepository, session_factory=db.provided.session
    )
    push_service = providers.Selector(
        config.provided.push_provider,
        none=providers.Singleton(NullPushService),
        fcm=providers.Singleton(
            FcmPushService,
            device_tokens=device_token_repository,
            credentials_path=config.provided.fcm_credentials_path,
            credentials_json=config.provided.fcm_credentials_json,
        ),
    )
    lead_gateway = providers.Selector(
        config.provided.lead_gateway,
        log=providers.Singleton(LogLeadGateway),
        twenty=providers.Singleton(
            TwentyLeadGateway,
            base_url=config.provided.twenty_base_url,
            api_key=config.provided.twenty_api_key,
        ),
    )
    submit_lead = providers.Factory(SubmitLead, gateway=lead_gateway)

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
    table_session_repository = providers.Factory(
        SqlAlchemyTableSessionRepository, session_factory=db.provided.session
    )
    shift_repository = providers.Factory(
        SqlAlchemyShiftRepository, session_factory=db.provided.session
    )
    sector_repository = providers.Factory(
        SqlAlchemySectorRepository, session_factory=db.provided.session
    )
    customer_repository = providers.Factory(
        SqlAlchemyCustomerRepository, session_factory=db.provided.session
    )
    product_repository = providers.Factory(
        SqlAlchemyProductRepository, session_factory=db.provided.session
    )
    modifier_repository = providers.Factory(
        SqlAlchemyModifierRepository, session_factory=db.provided.session
    )
    price_change_repository = providers.Factory(
        SqlAlchemyPriceChangeRepository, session_factory=db.provided.session
    )
    pricing_read_model = providers.Factory(
        SqlAlchemyPricingReadModel, session_factory=db.provided.session
    )
    rotation_read_model = providers.Factory(
        SqlAlchemyRotationReadModel, session_factory=db.provided.session
    )
    order_repository = providers.Factory(
        SqlAlchemyOrderRepository, session_factory=db.provided.session
    )
    refresh_token_repository = providers.Factory(
        SqlAlchemyRefreshTokenRepository, session_factory=db.provided.session
    )
    register_device_token = providers.Factory(
        RegisterDeviceToken,
        devices=device_token_repository,
        tenant_context=tenant_context,
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
    get_my_profile = providers.Factory(
        GetMyProfile,
        users=user_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
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
        price_changes=price_change_repository,
        tenant_context=tenant_context,
    )
    list_products = providers.Factory(
        ListProducts, products=product_repository, tenant_context=tenant_context
    )
    set_product_availability = providers.Factory(
        SetProductAvailability, products=product_repository, tenant_context=tenant_context
    )
    get_product_modifiers = providers.Factory(
        GetProductModifiers, modifiers=modifier_repository, tenant_context=tenant_context
    )
    list_menu_modifiers = providers.Factory(
        ListMenuModifiers,
        products=product_repository,
        modifiers=modifier_repository,
        tenant_context=tenant_context,
    )
    set_product_modifiers = providers.Factory(
        SetProductModifiers,
        modifiers=modifier_repository,
        products=product_repository,
        tenant_context=tenant_context,
    )
    update_product_price = providers.Factory(
        UpdateProductPrice,
        products=product_repository,
        price_changes=price_change_repository,
        tenant_context=tenant_context,
    )
    get_product_price_history = providers.Factory(
        GetProductPriceHistory,
        products=product_repository,
        price_changes=price_change_repository,
        tenant_context=tenant_context,
    )
    get_product_rotation = providers.Factory(
        GetProductRotation,
        rotation=rotation_read_model,
        tenant_context=tenant_context,
    )
    create_table = providers.Factory(
        CreateTable, tables=table_repository, tenant_context=tenant_context
    )
    list_tables = providers.Factory(
        ListTables, tables=table_repository, tenant_context=tenant_context
    )
    update_table = providers.Factory(
        UpdateTable, tables=table_repository, tenant_context=tenant_context
    )
    create_order = providers.Factory(
        CreateOrder,
        orders=order_repository,
        tables=table_repository,
        tenants=tenant_repository,
        sessions=table_session_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    get_floor = providers.Factory(
        GetFloor,
        tables=table_repository,
        orders=order_repository,
        sessions=table_session_repository,
        users=user_repository,
        tenant_context=tenant_context,
    )
    open_session = providers.Factory(
        OpenSession,
        sessions=table_session_repository,
        tables=table_repository,
        tenant_context=tenant_context,
    )
    set_session_pax = providers.Factory(
        SetSessionPax,
        sessions=table_session_repository,
        tenant_context=tenant_context,
    )
    request_bill = providers.Factory(
        RequestBill,
        sessions=table_session_repository,
        tenant_context=tenant_context,
    )
    assign_table_waiter = providers.Factory(
        AssignTableWaiter,
        sessions=table_session_repository,
        orders=order_repository,
        tenant_context=tenant_context,
    )
    list_sectors = providers.Factory(
        ListSectors, sectors=sector_repository, tenant_context=tenant_context
    )
    create_sector = providers.Factory(
        CreateSector, sectors=sector_repository, tenant_context=tenant_context
    )
    update_sector = providers.Factory(
        UpdateSector, sectors=sector_repository, tenant_context=tenant_context
    )
    delete_sector = providers.Factory(
        DeleteSector, sectors=sector_repository, tenant_context=tenant_context
    )
    list_customers = providers.Factory(
        ListCustomers, customers=customer_repository, tenant_context=tenant_context
    )
    get_customer = providers.Factory(
        GetCustomer, customers=customer_repository, tenant_context=tenant_context
    )
    create_customer = providers.Factory(
        CreateCustomer, customers=customer_repository, tenant_context=tenant_context
    )
    update_customer = providers.Factory(
        UpdateCustomer, customers=customer_repository, tenant_context=tenant_context
    )
    delete_customer = providers.Factory(
        DeleteCustomer, customers=customer_repository, tenant_context=tenant_context
    )
    assign_order_customer = providers.Factory(
        AssignOrderCustomer,
        orders=order_repository,
        customers=customer_repository,
        tenant_context=tenant_context,
    )
    customer_history_read_model = providers.Factory(
        SqlAlchemyCustomerHistoryReadModel, session_factory=db.provided.session
    )
    get_customer_history = providers.Factory(
        GetCustomerHistory,
        customers=customer_repository,
        read_model=customer_history_read_model,
        tenant_context=tenant_context,
    )
    customer_stats_read_model = providers.Factory(
        SqlAlchemyCustomerStatsReadModel, session_factory=db.provided.session
    )
    get_customer_stats = providers.Factory(
        GetCustomerStats,
        read_model=customer_stats_read_model,
        tenant_context=tenant_context,
    )
    contact_log_repository = providers.Factory(
        SqlAlchemyContactLogRepository, session_factory=db.provided.session
    )
    contact_result_read_model = providers.Factory(
        SqlAlchemyContactResultReadModel, session_factory=db.provided.session
    )
    log_contact = providers.Factory(
        LogContact,
        contacts=contact_log_repository,
        customers=customer_repository,
        tenant_context=tenant_context,
    )
    get_recent_contacts = providers.Factory(
        GetRecentContacts,
        contacts=contact_log_repository,
        tenant_context=tenant_context,
    )
    get_contact_result = providers.Factory(
        GetContactResult,
        read_model=contact_result_read_model,
        tenant_context=tenant_context,
    )
    get_order = providers.Factory(
        GetOrder, orders=order_repository, tenant_context=tenant_context
    )
    add_order_item = providers.Factory(
        AddOrderItem,
        orders=order_repository,
        products=product_repository,
        modifiers=modifier_repository,
        tenant_context=tenant_context,
    )
    add_order_items_batch = providers.Factory(
        AddOrderItemsBatch,
        orders=order_repository,
        products=product_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    remove_order_item = providers.Factory(
        RemoveOrderItem, orders=order_repository, tenant_context=tenant_context
    )
    set_item_quantity = providers.Factory(
        SetItemQuantity, orders=order_repository, tenant_context=tenant_context
    )
    set_item_note = providers.Factory(
        SetItemNote, orders=order_repository, tenant_context=tenant_context
    )
    send_order = providers.Factory(
        SendOrder,
        orders=order_repository,
        assign_waiter=assign_table_waiter,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    advance_order = providers.Factory(
        AdvanceOrder,
        orders=order_repository,
        tables=table_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
        notifications=push_service,
    )
    advance_item = providers.Factory(
        AdvanceItem,
        orders=order_repository,
        tables=table_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
        notifications=push_service,
    )
    transfer_order = providers.Factory(
        TransferOrder,
        orders=order_repository,
        tables=table_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    merge_orders = providers.Factory(
        MergeOrders,
        orders=order_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    list_orders = providers.Factory(
        ListOrders, orders=order_repository, tenant_context=tenant_context
    )
    get_kds_orders = providers.Factory(
        GetKdsOrders, orders=order_repository, tenant_context=tenant_context
    )
    list_pending_qr = providers.Factory(
        ListPendingQrOrders, orders=order_repository, tenant_context=tenant_context
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
    preparation_repository = providers.Factory(
        SqlAlchemyPreparationRepository, session_factory=db.provided.session
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

    # --- Fase 8 (proyección): sale_facts + projector, antes de pagos ---
    # El settle de pagos inyecta el SalesProjector como segundo hook post-PAID.
    sale_facts_repository = providers.Factory(
        SqlAlchemySaleFactsRepository, session_factory=db.provided.session
    )
    finance_snapshot_repository = providers.Factory(
        SqlAlchemyFinanceSnapshotRepository, session_factory=db.provided.session
    )
    # Definido acá (antes de project_order_sales, que lo usa para netear el IVA).
    advisor_settings_repository = providers.Factory(
        SqlAlchemyAdvisorSettingsRepository, session_factory=db.provided.session
    )
    project_order_sales = providers.Factory(
        ProjectOrderSales,
        orders=order_repository,
        products=product_repository,
        recipes=recipe_repository,
        ingredients=ingredient_repository,
        preparations=preparation_repository,
        sale_facts=sale_facts_repository,
        snapshots=finance_snapshot_repository,
        advisor_settings=advisor_settings_repository,
        tenant_context=tenant_context,
    )

    # --- Fase 3: pagos (ingresos/egresos) ---
    payment_repository = providers.Factory(
        SqlAlchemyPaymentRepository, session_factory=db.provided.session
    )
    # "Liberar mesa" (Autoservicio): cierra una comanda ya paga → libera el plano.
    close_settled_order = providers.Factory(
        CloseSettledOrder,
        orders=order_repository,
        payments=payment_repository,
        tenant_context=tenant_context,
        event_bus=event_bus,
    )
    # Outbox de reportes de sales tax (TaxJar AutoFile). Se enqueue en la
    # transición a PAID solo si se cobró tax (>0) → vacío en AR (paridad).
    tax_report_ledger = providers.Factory(
        SqlAlchemyTaxReportLedger, session_factory=db.provided.session
    )
    # Billing del SaaS (Flujo A): catálogo de planes + suscripciones por tenant.
    plan_repository = providers.Factory(
        SqlAlchemyPlanRepository, session_factory=db.provided.session
    )
    subscription_repository = providers.Factory(
        SqlAlchemySubscriptionRepository, session_factory=db.provided.session
    )
    # Pasarelas de billing (Flujo A): Stripe (USD) + MercadoPago (ARS), elegidas
    # por riel. Keys del entorno (Railway). El resolver materializa el anti-arbitraje.
    stripe_billing_gateway = providers.Singleton(
        StripeBillingGateway,
        api_key=config.provided.stripe_api_key,
        webhook_secret=config.provided.stripe_webhook_secret,
    )
    mercadopago_billing_gateway = providers.Singleton(
        MercadoPagoPreapprovalGateway,
        access_token=config.provided.mp_billing_access_token,
        webhook_secret=config.provided.mp_billing_webhook_secret,
    )
    billing_gateway_resolver = providers.Singleton(
        RailBillingGatewayResolver,
        stripe=stripe_billing_gateway,
        mercadopago=mercadopago_billing_gateway,
    )
    list_plans = providers.Factory(ListPlans, plans=plan_repository)
    # Panel de plataforma: gestión del catálogo global de planes (super-admin).
    list_all_plans = providers.Factory(ListAllPlans, plans=plan_repository)
    save_plan = providers.Factory(SavePlan, plans=plan_repository)
    delete_plan = providers.Factory(DeletePlan, plans=plan_repository)
    get_subscription = providers.Factory(
        GetSubscription,
        subscriptions=subscription_repository,
        tenant_context=tenant_context,
    )
    start_subscription_checkout = providers.Factory(
        StartSubscriptionCheckout,
        plans=plan_repository,
        subscriptions=subscription_repository,
        gateways=billing_gateway_resolver,
        tenant_context=tenant_context,
    )
    cancel_subscription = providers.Factory(
        CancelSubscription,
        subscriptions=subscription_repository,
        gateways=billing_gateway_resolver,
        tenant_context=tenant_context,
    )
    handle_billing_webhook = providers.Factory(
        HandleBillingWebhook,
        subscriptions=subscription_repository,
        gateways=billing_gateway_resolver,
        tenant_context=tenant_context,
    )
    # --- Fase 14: caja / arqueo Z ---
    cash_session_repository = providers.Factory(
        SqlAlchemyCashSessionRepository, session_factory=db.provided.session
    )
    cash_movement_repository = providers.Factory(
        SqlAlchemyCashMovementRepository, session_factory=db.provided.session
    )
    cash_settings_repository = providers.Factory(
        SqlAlchemyCashSettingsRepository, session_factory=db.provided.session
    )
    cash_session_policy = providers.Factory(
        SqlAlchemyCashSessionPolicy, session_factory=db.provided.session
    )
    payment_fee_rate_repository = providers.Factory(
        SqlAlchemyPaymentFeeRateRepository, session_factory=db.provided.session
    )
    get_payment_fee_rates = providers.Factory(
        GetPaymentFeeRates,
        rates=payment_fee_rate_repository,
        tenant_context=tenant_context,
    )
    update_payment_fee_rates = providers.Factory(
        UpdatePaymentFeeRates,
        rates=payment_fee_rate_repository,
        tenant_context=tenant_context,
    )
    open_cash_session = providers.Factory(
        OpenCashSession,
        cash=cash_session_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    get_current_cash_report = providers.Factory(
        GetCurrentCashReport,
        cash=cash_session_repository,
        payments=payment_repository,
        movements=cash_movement_repository,
        settings=cash_settings_repository,
        tenant_context=tenant_context,
    )
    get_cash_settings = providers.Factory(
        GetCashSettings,
        settings=cash_settings_repository,
        tenant_context=tenant_context,
    )
    update_cash_settings = providers.Factory(
        UpdateCashSettings,
        settings=cash_settings_repository,
        tenant_context=tenant_context,
    )
    close_cash_session = providers.Factory(
        CloseCashSession,
        cash=cash_session_repository,
        payments=payment_repository,
        movements=cash_movement_repository,
        tenant_context=tenant_context,
    )
    register_cash_movement = providers.Factory(
        RegisterCashMovement,
        cash=cash_session_repository,
        movements=cash_movement_repository,
        tenant_context=tenant_context,
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
        sales=project_order_sales,
        cash=cash_session_repository,
        policy=cash_session_policy,
        fee_rates=payment_fee_rate_repository,
        tax_outbox=tax_report_ledger,
    )
    # Cobro del comensal (Carta QR F3): mismo motor que el cajero pero con la
    # política de caja RELAJADA (cash=None, policy=None) → no exige caja abierta ni
    # cajero. Proyecta venta/stock/impuesto igual (idempotente en el webhook).
    register_public_payment = providers.Factory(
        RegisterPayment,
        payments=payment_repository,
        orders=order_repository,
        gateway=payment_gateway,
        tenant_context=tenant_context,
        inventory=consume_recipes_for_order,
        sales=project_order_sales,
        fee_rates=payment_fee_rate_repository,
        tax_outbox=tax_report_ledger,
    )
    auto_assign_waiter = providers.Factory(
        AutoAssignWaiter,
        shifts=shift_repository,
        users=user_repository,
        sessions=table_session_repository,
        tenant_context=tenant_context,
    )
    confirm_gateway_payment = providers.Factory(
        ConfirmGatewayPayment,
        payments=payment_repository,
        orders=order_repository,
        notifications=mercadopago_gateway,
        resolver=payment_credentials_resolver,
        tenant_context=tenant_context,
        inventory=consume_recipes_for_order,
        sales=project_order_sales,
        tax_outbox=tax_report_ledger,
        send_order=send_order,
        auto_assign=auto_assign_waiter,
        event_bus=event_bus,
        push=push_service,
        tables=table_repository,
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
    refund_payment = providers.Factory(
        RefundPayment, payments=payment_repository, tenant_context=tenant_context
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
    report_export_read_model = providers.Factory(
        SqlAlchemyReportExportReadModel, session_factory=db.provided.session
    )
    export_report = providers.Factory(
        ExportReport, read_model=report_export_read_model, tenant_context=tenant_context
    )
    # --- Fase 14: propinas por mozo (reporte + liquidación como egreso) ---
    tips_read_model = providers.Factory(
        SqlAlchemyTipsReadModel, session_factory=db.provided.session
    )
    get_tips_report = providers.Factory(
        GetTipsReport, read_model=tips_read_model, tenant_context=tenant_context
    )
    tip_payout_repository = providers.Factory(
        SqlAlchemyTipPayoutRepository, session_factory=db.provided.session
    )
    pay_tips = providers.Factory(
        PayTips,
        payouts=tip_payout_repository,
        users=user_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
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

    # Sales tax (Fase 2). The resolver holds both calculators; QuoteOrderTax picks
    # by tenant.tax_engine. TaxJar is constructed with the env token but only
    # invoked for TAXJAR-engine tenants → AR tenants never touch it (parity).
    included_tax_calculator = providers.Singleton(IncludedTaxCalculator)
    taxjar_calculator = providers.Singleton(
        TaxJarCalculator,
        api_token=config.provided.taxjar_api_token,
        sandbox=config.provided.taxjar_sandbox,
    )
    tax_calculator_resolver = providers.Singleton(
        EngineTaxCalculatorResolver,
        taxjar=taxjar_calculator,
        included=included_tax_calculator,
    )
    quote_order_tax = providers.Factory(
        QuoteOrderTax,
        orders=order_repository,
        tenants=tenant_repository,
        resolver=tax_calculator_resolver,
        tenant_context=tenant_context,
    )
    # Reporte de sales tax al proveedor (TaxJar AutoFile). Per-tenant: el reporter
    # se construye con el token PROPIO del tenant (credencial cifrada), nunca con
    # una cuenta de plataforma. El drain recorre el outbox y reporta con
    # transaction_id = order_id (idempotente). En AR el outbox está vacío → no-op.
    taxjar_credential_repository = providers.Factory(
        SqlAlchemyTaxJarCredentialRepository, session_factory=db.provided.session
    )
    taxjar_reporter_resolver = providers.Factory(
        DbTaxJarReporterResolver,
        credentials=taxjar_credential_repository,
        cipher=token_cipher,
    )
    # Verifica el token contra TaxJar antes de guardarlo (que "conectado" no mienta).
    taxjar_credential_validator = providers.Singleton(TaxJarCredentialValidator)
    report_pending_tax_sales = providers.Factory(
        ReportPendingTaxSales,
        ledger=tax_report_ledger,
        resolver=taxjar_reporter_resolver,
        orders=order_repository,
        payments=payment_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    tax_report_status_read_model = providers.Factory(
        SqlAlchemyTaxReportStatusReadModel, session_factory=db.provided.session
    )
    get_tax_report_status = providers.Factory(
        GetTaxReportStatus,
        read_model=tax_report_status_read_model,
        tenant_context=tenant_context,
    )
    connect_taxjar = providers.Factory(
        ConnectTaxJar,
        credentials=taxjar_credential_repository,
        cipher=token_cipher,
        validator=taxjar_credential_validator,
        tenant_context=tenant_context,
    )
    get_taxjar_connection = providers.Factory(
        GetTaxJarConnection,
        credentials=taxjar_credential_repository,
        tenant_context=tenant_context,
    )
    disconnect_taxjar = providers.Factory(
        DisconnectTaxJar,
        credentials=taxjar_credential_repository,
        tenant_context=tenant_context,
    )
    get_tenant_fiscal_settings = providers.Factory(
        GetTenantFiscalSettings, tenants=tenant_repository
    )
    update_tenant_fiscal_address = providers.Factory(
        UpdateTenantFiscalAddress, tenants=tenant_repository
    )
    get_order_invoice = providers.Factory(
        GetOrderInvoice, invoices=invoice_repository, tenant_context=tenant_context
    )
    # Reopen lives here (after the invoice repo): it reverses the sale's
    # side-effects and guards on an authorized comprobante.
    reopen_order = providers.Factory(
        ReopenOrder,
        orders=order_repository,
        invoices=invoice_repository,
        inventory=consume_recipes_for_order,
        sales=project_order_sales,
        tenant_context=tenant_context,
        event_bus=event_bus,
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

    # --- Carta QR (autopedido F1): token firmado de mesa + carta pública ---
    # Rate limiter en memoria (baranda de abuso de los endpoints públicos). Singleton
    # → el estado (hits por mesa) vive mientras corre el proceso.
    public_rate_limiter = providers.Singleton(InMemoryRateLimiter)
    table_qr_token = providers.Singleton(
        HmacTableQrToken, secret=config.provided.effective_table_qr_secret
    )
    issue_table_qr = providers.Factory(
        IssueTableQr,
        token=table_qr_token,
        tables=table_repository,
        tenant_context=tenant_context,
        app_base_url=config.provided.app_base_url,
    )
    self_order_settings_repository = providers.Factory(
        SqlAlchemySelfOrderSettingsRepository, session_factory=db.provided.session
    )
    self_pay_settings_repository = providers.Factory(
        SqlAlchemySelfPaySettingsRepository, session_factory=db.provided.session
    )
    get_table_bill = providers.Factory(
        GetTableBill,
        token=table_qr_token,
        tenants=tenant_repository,
        sessions=table_session_repository,
        orders=order_repository,
        payments=payment_repository,
        settings=self_pay_settings_repository,
        credentials=payment_credential_repository,
        tenant_context=tenant_context,
    )
    pay_table_bill = providers.Factory(
        PayTableBill,
        token=table_qr_token,
        settings=self_pay_settings_repository,
        sessions=table_session_repository,
        orders=order_repository,
        payments=payment_repository,
        register_payment=register_public_payment,
        tenant_context=tenant_context,
        app_base_url=config.provided.app_base_url,
        rate_limiter=public_rate_limiter,
    )
    get_public_payment_status = providers.Factory(
        GetPublicPaymentStatus,
        token=table_qr_token,
        payments=payment_repository,
        tenant_context=tenant_context,
    )
    get_public_payment_receipt = providers.Factory(
        GetPublicPaymentReceipt,
        token=table_qr_token,
        payments=payment_repository,
        orders=order_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    get_self_pay_settings = providers.Factory(
        GetSelfPaySettings,
        settings=self_pay_settings_repository,
        tenant_context=tenant_context,
    )
    update_self_pay_settings = providers.Factory(
        UpdateSelfPaySettings,
        settings=self_pay_settings_repository,
        tenant_context=tenant_context,
    )
    get_public_menu = providers.Factory(
        GetPublicMenu,
        token=table_qr_token,
        products=product_repository,
        modifiers=modifier_repository,
        tenants=tenant_repository,
        settings=self_order_settings_repository,
        tenant_context=tenant_context,
    )
    request_table_attention = providers.Factory(
        RequestTableAttention,
        token=table_qr_token,
        tables=table_repository,
        event_bus=event_bus,
        tenant_context=tenant_context,
        rate_limiter=public_rate_limiter,
    )
    get_self_order_settings = providers.Factory(
        GetSelfOrderSettings,
        settings=self_order_settings_repository,
        tenant_context=tenant_context,
    )
    update_self_order_settings = providers.Factory(
        UpdateSelfOrderSettings,
        settings=self_order_settings_repository,
        tenant_context=tenant_context,
    )
    submit_customer_order = providers.Factory(
        SubmitCustomerOrder,
        token=table_qr_token,
        settings=self_order_settings_repository,
        products=product_repository,
        modifiers=modifier_repository,
        sessions=table_session_repository,
        create_order=create_order,
        add_items_batch=add_order_items_batch,
        tables=table_repository,
        tenant_context=tenant_context,
        rate_limiter=public_rate_limiter,
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
        suppliers=supplier_repository,
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
    update_supplier = providers.Factory(
        UpdateSupplier, suppliers=supplier_repository, tenant_context=tenant_context
    )
    list_suppliers = providers.Factory(
        ListSuppliers, suppliers=supplier_repository, tenant_context=tenant_context
    )
    supplier_purchases_read_model = providers.Factory(
        SqlAlchemySupplierPurchasesReadModel, session_factory=db.provided.session
    )
    get_supplier_purchases = providers.Factory(
        GetSupplierPurchases,
        suppliers=supplier_repository,
        read_model=supplier_purchases_read_model,
        tenant_context=tenant_context,
    )
    set_recipe = providers.Factory(
        SetRecipe,
        recipes=recipe_repository,
        products=product_repository,
        ingredients=ingredient_repository,
        preparations=preparation_repository,
        tenant_context=tenant_context,
    )
    get_recipe = providers.Factory(
        GetRecipe, recipes=recipe_repository, tenant_context=tenant_context
    )
    list_preparations = providers.Factory(
        ListPreparations,
        preparations=preparation_repository,
        tenant_context=tenant_context,
    )
    save_preparation = providers.Factory(
        SavePreparation,
        preparations=preparation_repository,
        ingredients=ingredient_repository,
        tenant_context=tenant_context,
    )
    delete_preparation = providers.Factory(
        DeletePreparation,
        preparations=preparation_repository,
        tenant_context=tenant_context,
    )
    food_cost_read_model = providers.Factory(
        SqlAlchemyFoodCostReadModel, session_factory=db.provided.session
    )
    get_food_cost = providers.Factory(
        GetFoodCost, read_model=food_cost_read_model, tenant_context=tenant_context
    )
    ingredient_cost_history_read_model = providers.Factory(
        SqlAlchemyIngredientCostHistoryReadModel, session_factory=db.provided.session
    )
    get_ingredient_cost_history = providers.Factory(
        GetIngredientCostHistory,
        read_model=ingredient_cost_history_read_model,
        tenant_context=tenant_context,
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

    # --- Fase 8: modelo canónico (analytics; repos/projector arriba, antes de pagos) ---
    rebuild_sales_facts = providers.Factory(
        RebuildSalesFacts,
        orders=order_repository,
        projector=project_order_sales,
        tenant_context=tenant_context,
    )
    revenue_read_model = providers.Factory(
        SqlAlchemyRevenueReadModel, session_factory=db.provided.session
    )
    payment_mix_read_model = providers.Factory(
        SqlAlchemyPaymentMixReadModel, session_factory=db.provided.session
    )
    product_performance_read_model = providers.Factory(
        SqlAlchemyProductPerformanceReadModel, session_factory=db.provided.session
    )
    get_revenue_summary = providers.Factory(
        GetRevenueSummary, read_model=revenue_read_model, tenant_context=tenant_context
    )
    revenue_daily_read_model = providers.Factory(
        SqlAlchemyRevenueDailyReadModel, session_factory=db.provided.session
    )
    get_revenue_daily = providers.Factory(
        GetRevenueDaily, read_model=revenue_daily_read_model, tenant_context=tenant_context
    )
    get_payment_mix = providers.Factory(
        GetPaymentMix, read_model=payment_mix_read_model, tenant_context=tenant_context
    )
    get_product_performance = providers.Factory(
        GetProductPerformance,
        read_model=product_performance_read_model,
        tenant_context=tenant_context,
    )

    # --- Fase 9: asesor financiero (narrator/synthesizer deterministas; LLM en T4) ---
    # advisor_settings_repository se define arriba (lo usa project_order_sales).
    # Tanda F: selector live/snapshot del read model del Asesor (default live).
    advisor_read_model = providers.Selector(
        config.provided.finance_snapshots_read,
        live=providers.Factory(
            SqlAlchemyAdvisorReadModel, session_factory=db.provided.session
        ),
        snapshot=providers.Factory(
            SqlAlchemyAdvisorSnapshotReadModel, session_factory=db.provided.session
        ),
    )
    rebuild_finance_snapshots = providers.Factory(
        RebuildFinanceSnapshots,
        rebuilder=finance_snapshot_repository,
        tenant_context=tenant_context,
    )
    advisor_diagnostics_cache = providers.Factory(
        SqlAlchemyAdvisorDiagnosticsCache, session_factory=db.provided.session
    )
    labor_cost_read_model = providers.Factory(
        SqlAlchemyLaborCostReadModel, session_factory=db.provided.session
    )
    # Capa LLM grounded, detrás de Selector y APAGADA por default (off=template).
    template_narrator = providers.Singleton(TemplateNarrator)
    advisor_llm = providers.Singleton(
        AnthropicAdvisorLLM,
        api_key=config.provided.anthropic_api_key,
        model=config.provided.advisor_llm_model,
    )
    insight_narrator = providers.Selector(
        config.provided.advisor_llm_provider,
        off=template_narrator,
        claude=providers.Singleton(
            ClaudeNarrator, llm=advisor_llm, fallback=template_narrator
        ),
    )
    advisor_synthesizer = providers.Selector(
        config.provided.advisor_llm_provider,
        off=providers.Singleton(NoSynthesis),
        claude=providers.Singleton(ClaudeSynthesizer, llm=advisor_llm),
    )
    get_advisor_report = providers.Factory(
        GetAdvisorReport,
        read_model=advisor_read_model,
        settings=advisor_settings_repository,
        narrator=insight_narrator,
        synthesizer=advisor_synthesizer,
        tenant_context=tenant_context,
        llm_enabled=config.provided.advisor_llm_enabled,
        cache=advisor_diagnostics_cache,
        labor=labor_cost_read_model,
    )
    # --- Pantalla Finanzas (compone advisor + product performance) ---
    inventory_value_read_model = providers.Factory(
        SqlAlchemyInventoryValueReadModel, session_factory=db.provided.session
    )
    finance_commissions_read_model = providers.Factory(
        SqlAlchemyFinanceCommissionsReadModel, session_factory=db.provided.session
    )
    get_finance_overview = providers.Factory(
        GetFinanceOverview,
        advisor=get_advisor_report,
        products=get_product_performance,
        settings=advisor_settings_repository,
        inventory=inventory_value_read_model,
        commissions=finance_commissions_read_model,
        tenant_context=tenant_context,
    )
    tax_collected_read_model = providers.Factory(
        SqlAlchemyTaxCollectedReadModel, session_factory=db.provided.session
    )
    get_tax_collected = providers.Factory(
        GetTaxCollected,
        read_model=tax_collected_read_model,
        tenant_context=tenant_context,
    )
    finance_product_detail_read_model = providers.Factory(
        SqlAlchemyFinanceProductDetailReadModel, session_factory=db.provided.session
    )
    get_product_detail = providers.Factory(
        GetProductDetail,
        read_model=finance_product_detail_read_model,
        tenant_context=tenant_context,
    )
    expense_breakdown_read_model = providers.Factory(
        SqlAlchemyExpenseBreakdownReadModel, session_factory=db.provided.session
    )
    get_expense_breakdown = providers.Factory(
        GetExpenseBreakdown,
        read_model=expense_breakdown_read_model,
        tenant_context=tenant_context,
    )
    recent_movements_read_model = providers.Factory(
        SqlAlchemyRecentMovementsReadModel, session_factory=db.provided.session
    )
    get_recent_movements = providers.Factory(
        GetRecentMovements,
        read_model=recent_movements_read_model,
        tenant_context=tenant_context,
    )
    get_advisor_settings = providers.Factory(
        GetAdvisorSettings,
        settings=advisor_settings_repository,
        tenant_context=tenant_context,
    )
    update_advisor_settings = providers.Factory(
        UpdateAdvisorSettings,
        settings=advisor_settings_repository,
        tenants=tenant_repository,
        tenant_context=tenant_context,
    )
    # Productos v2 Tanda B: precios vs inflación (reusa advisor_settings + productos).
    get_pricing_insights = providers.Factory(
        GetPricingInsights,
        pricing=pricing_read_model,
        settings=advisor_settings_repository,
        tenant_context=tenant_context,
    )
    rebuild_advisor_diagnostics = providers.Factory(
        RebuildAdvisorDiagnostics,
        cache=advisor_diagnostics_cache,
        tenant_context=tenant_context,
    )
    set_user_hourly_rate = providers.Factory(
        SetUserHourlyRate,
        users=user_repository,
        tenant_context=tenant_context,
    )

    # --- Fase 11: copiloto IA (text-to-SQL con guardrails; LLM off por default) ---
    copilot_query_runner = providers.Factory(
        SqlAlchemyCopilotQueryRunner,
        session_factory=db.provided.session,
        statement_timeout_ms=config.provided.copilot_statement_timeout_ms,
    )
    copilot_llm_client = providers.Singleton(
        AnthropicClient,
        api_key=config.provided.anthropic_api_key,
        model=config.provided.copilot_model,
    )
    copilot_llm = providers.Selector(
        config.provided.copilot_provider,
        off=providers.Singleton(NoCopilot),
        claude=providers.Singleton(AnthropicCopilotLLM, llm=copilot_llm_client),
    )
    ask_copilot = providers.Factory(
        AskCopilot,
        llm=copilot_llm,
        runner=copilot_query_runner,
        tenant_context=tenant_context,
        max_rows=config.provided.copilot_row_limit,
        enabled=config.provided.copilot_enabled,
    )

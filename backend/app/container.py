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
from app.application.table.use_cases import CreateTable, ListTables
from app.config import Settings
from app.infrastructure.email.console_sender import ConsoleEmailSender
from app.infrastructure.email.smtp_sender import SmtpEmailSender
from app.infrastructure.payments.credentials_resolver import DbPaymentCredentialsResolver
from app.infrastructure.payments.manual_gateway import ManualPaymentGateway
from app.infrastructure.payments.mercadopago_gateway import MercadoPagoGateway
from app.infrastructure.payments.mercadopago_oauth import MercadoPagoOAuthClient
from app.infrastructure.persistence.audit_repo import SqlAlchemyAuditRepository
from app.infrastructure.persistence.credentials_repo import (
    SqlAlchemyPaymentCredentialRepository,
)
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.invitation_repo import SqlAlchemyInvitationRepository
from app.infrastructure.persistence.order_repo import SqlAlchemyOrderRepository
from app.infrastructure.persistence.payment_repo import SqlAlchemyPaymentRepository
from app.infrastructure.persistence.product_repo import SqlAlchemyProductRepository
from app.infrastructure.persistence.refresh_token_repo import SqlAlchemyRefreshTokenRepository
from app.infrastructure.persistence.reset_token_repo import SqlAlchemyResetTokenRepository
from app.infrastructure.persistence.table_repo import SqlAlchemyTableRepository
from app.infrastructure.persistence.tenant_repo import SqlAlchemyTenantRepository
from app.infrastructure.persistence.user_repo import SqlAlchemyUserRepository
from app.infrastructure.persistence.verification_token_repo import (
    SqlAlchemyVerificationTokenRepository,
)
from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from app.infrastructure.security.hasher import Argon2Hasher
from app.infrastructure.security.tenant_context import ContextVarTenantContext
from app.infrastructure.security.token_service import JwtTokenService


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
    )
    confirm_gateway_payment = providers.Factory(
        ConfirmGatewayPayment,
        payments=payment_repository,
        orders=order_repository,
        notifications=mercadopago_gateway,
        tenant_context=tenant_context,
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

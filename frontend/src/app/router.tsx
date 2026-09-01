import { createBrowserRouter, Navigate } from "react-router-dom"

import { AppShell } from "@/components/shell/app-shell"
import { RequireAuth } from "@/auth/require-auth"
import { RequirePlatformAdmin } from "@/auth/require-platform-admin"
import { RequireRole } from "@/auth/require-role"
import { RoleLanding } from "@/auth/role-landing"
import { AdvisorPage } from "@/features/advisor/advisor-page"
import { AnalyticsPage } from "@/features/analytics/analytics-page"
import { SubscriptionPage } from "@/features/billing/subscription-page"
import { CashSessionPage } from "@/features/cashier/cash-session-page"
import { TipsPage } from "@/features/cashier/tips-page"
import { CopilotPage } from "@/features/copilot/copilot-page"
import { ConfigPage } from "@/features/settings/config-page"
import { FinancePage } from "@/features/finance/finance-page"
import { CustomersPage } from "@/features/crm/customers-page"
import { ReportsPage } from "@/features/reports/reports-page"
import { FloorPage } from "@/features/floor/floor-page"
import { AcceptInvitationPage } from "@/features/identity/accept-invitation-page"
import { InviteUserPage } from "@/features/identity/invite-user-page"
import { LoginPage } from "@/features/identity/login-page"
import { ForgotPasswordPage } from "@/features/identity/forgot-password-page"
import { OnboardingPage } from "@/features/identity/onboarding-page"
import { ResetPasswordPage } from "@/features/identity/reset-password-page"
import { PlatformPage } from "@/features/platform/platform-page"
import { VerifyEmailPage } from "@/features/identity/verify-email-page"
import { ExpensesPage } from "@/features/expenses/expenses-page"
import { IntegrationsPage } from "@/features/integrations/integrations-page"
import { StockPage } from "@/features/inventory/stock-page"
import { SuppliersPage } from "@/features/inventory/suppliers-page"
import { InvoicesPage } from "@/features/invoices/invoices-page"
import { BarPage } from "@/features/kds/bar-page"
import { KdsPage } from "@/features/kds/kds-page"
import { OrderPage } from "@/features/orders/order-page"
import { ProductsPage } from "@/features/products/products-page"
import { ReservationsPage } from "@/features/reservations/reservations-page"
import { PublicMenuPage } from "@/features/public-menu/public-menu-page"
import { PresenceDisplayPage } from "@/features/timeclock/presence-display-page"
import { PunchPage } from "@/features/timeclock/punch-page"
import { StaffPage } from "@/features/timeclock/staff-page"

export const router = createBrowserRouter([
  // Public
  { path: "/login", element: <LoginPage /> },
  { path: "/onboarding", element: <OnboardingPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/accept-invitation", element: <AcceptInvitationPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  // Carta QR de cara al comensal (sin auth; el token porta el tenant).
  { path: "/carta/:token", element: <PublicMenuPage /> },
  // Local fichaje display (device-authenticated, no employee session).
  { path: "/fichaje", element: <PresenceDisplayPage /> },

  // Protected
  {
    element: <RequireAuth />,
    children: [
      // Full-screen (sin el shell/sidebar)
      { path: "/app/config", element: <ConfigPage /> },
      // Panel de plataforma (super-admin, gateado por el flag platform_admin).
      {
        element: <RequirePlatformAdmin />,
        children: [{ path: "/app/platform", element: <PlatformPage /> }],
      },
      {
        element: <AppShell />,
        children: [
          { path: "/app", element: <RoleLanding /> },
          { path: "/app/fichar", element: <PunchPage /> },
          {
            element: <RequireRole allow={["WAITER", "CASHIER", "MANAGER", "OWNER"]} />,
            children: [
              { path: "/app/floor", element: <FloorPage /> },
              { path: "/app/orders/:orderId", element: <OrderPage /> },
              { path: "/app/reservations", element: <ReservationsPage /> },
              { path: "/app/clientes", element: <CustomersPage /> },
            ],
          },
          {
            element: <RequireRole allow={["KITCHEN", "MANAGER", "OWNER"]} />,
            children: [{ path: "/app/kds", element: <KdsPage /> }],
          },
          {
            element: <RequireRole allow={["BAR", "MANAGER", "OWNER"]} />,
            children: [{ path: "/app/bar", element: <BarPage /> }],
          },
          {
            element: <RequireRole allow={["CASHIER", "MANAGER", "OWNER"]} />,
            children: [
              { path: "/app/caja", element: <CashSessionPage /> },
              { path: "/app/propinas", element: <TipsPage /> },
            ],
          },
          {
            element: <RequireRole allow={["OWNER", "MANAGER"]} />,
            children: [
              { path: "/app/invite", element: <InviteUserPage /> },
              { path: "/app/subscription", element: <SubscriptionPage /> },
              { path: "/app/finanzas", element: <FinancePage /> },
              { path: "/app/advisor", element: <AdvisorPage /> },
              { path: "/app/copilot", element: <CopilotPage /> },
              { path: "/app/analytics", element: <AnalyticsPage /> },
              { path: "/app/reportes", element: <ReportsPage /> },
              { path: "/app/products", element: <ProductsPage /> },
              { path: "/app/stock", element: <StockPage /> },
              { path: "/app/suppliers", element: <SuppliersPage /> },
              { path: "/app/expenses", element: <ExpensesPage /> },
              { path: "/app/invoices", element: <InvoicesPage /> },
              { path: "/app/staff", element: <StaffPage /> },
              { path: "/app/integrations", element: <IntegrationsPage /> },
            ],
          },
        ],
      },
    ],
  },

  // Anything else → /app (RequireAuth bounces to /login if there is no session).
  { path: "*", element: <Navigate to="/app" replace /> },
])

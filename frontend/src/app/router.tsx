import { createBrowserRouter, Navigate } from "react-router-dom"

import { AppShell } from "@/components/shell/app-shell"
import { RequireAuth } from "@/auth/require-auth"
import { RequireRole } from "@/auth/require-role"
import { DashboardPage } from "@/features/dashboard/dashboard-page"
import { FloorPage } from "@/features/floor/floor-page"
import { AcceptInvitationPage } from "@/features/identity/accept-invitation-page"
import { InviteUserPage } from "@/features/identity/invite-user-page"
import { LoginPage } from "@/features/identity/login-page"
import { OnboardingPage } from "@/features/identity/onboarding-page"
import { VerifyEmailPage } from "@/features/identity/verify-email-page"
import { ExpensesPage } from "@/features/expenses/expenses-page"
import { IntegrationsPage } from "@/features/integrations/integrations-page"
import { InvoicesPage } from "@/features/invoices/invoices-page"
import { KdsPage } from "@/features/kds/kds-page"
import { OrderPage } from "@/features/orders/order-page"
import { ProductsPage } from "@/features/products/products-page"
import { PresenceDisplayPage } from "@/features/timeclock/presence-display-page"
import { PunchPage } from "@/features/timeclock/punch-page"
import { StaffPage } from "@/features/timeclock/staff-page"

export const router = createBrowserRouter([
  // Public
  { path: "/login", element: <LoginPage /> },
  { path: "/onboarding", element: <OnboardingPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/accept-invitation", element: <AcceptInvitationPage /> },
  // Local fichaje display (device-authenticated, no employee session).
  { path: "/fichaje", element: <PresenceDisplayPage /> },

  // Protected
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/app", element: <DashboardPage /> },
          { path: "/app/fichar", element: <PunchPage /> },
          {
            element: <RequireRole allow={["WAITER", "CASHIER", "MANAGER", "OWNER"]} />,
            children: [
              { path: "/app/floor", element: <FloorPage /> },
              { path: "/app/orders/:orderId", element: <OrderPage /> },
            ],
          },
          {
            element: <RequireRole allow={["KITCHEN", "MANAGER", "OWNER"]} />,
            children: [{ path: "/app/kds", element: <KdsPage /> }],
          },
          {
            element: <RequireRole allow={["OWNER", "MANAGER"]} />,
            children: [
              { path: "/app/invite", element: <InviteUserPage /> },
              { path: "/app/products", element: <ProductsPage /> },
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

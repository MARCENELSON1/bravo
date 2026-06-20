import { createBrowserRouter, Navigate } from "react-router-dom"

import { RequireAuth } from "@/auth/require-auth"
import { RequireRole } from "@/auth/require-role"
import { FloorPage } from "@/features/floor/floor-page"
import { AcceptInvitationPage } from "@/features/identity/accept-invitation-page"
import { HomePage } from "@/features/identity/home-page"
import { InviteUserPage } from "@/features/identity/invite-user-page"
import { LoginPage } from "@/features/identity/login-page"
import { OnboardingPage } from "@/features/identity/onboarding-page"
import { VerifyEmailPage } from "@/features/identity/verify-email-page"
import { ExpensesPage } from "@/features/expenses/expenses-page"
import { KdsPage } from "@/features/kds/kds-page"
import { OrderPage } from "@/features/orders/order-page"
import { ProductsPage } from "@/features/products/products-page"

export const router = createBrowserRouter([
  // Public
  { path: "/login", element: <LoginPage /> },
  { path: "/onboarding", element: <OnboardingPage /> },
  { path: "/verify-email", element: <VerifyEmailPage /> },
  { path: "/accept-invitation", element: <AcceptInvitationPage /> },

  // Protected
  {
    element: <RequireAuth />,
    children: [
      { path: "/app", element: <HomePage /> },
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
        ],
      },
    ],
  },

  // Anything else → /app (RequireAuth bounces to /login if there is no session).
  { path: "*", element: <Navigate to="/app" replace /> },
])

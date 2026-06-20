import { createBrowserRouter, Navigate } from "react-router-dom"

import { RequireAuth } from "@/auth/require-auth"
import { RequireRole } from "@/auth/require-role"
import { AcceptInvitationPage } from "@/features/identity/accept-invitation-page"
import { HomePage } from "@/features/identity/home-page"
import { InviteUserPage } from "@/features/identity/invite-user-page"
import { LoginPage } from "@/features/identity/login-page"
import { OnboardingPage } from "@/features/identity/onboarding-page"
import { VerifyEmailPage } from "@/features/identity/verify-email-page"

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
        element: <RequireRole allow={["OWNER", "MANAGER"]} />,
        children: [{ path: "/app/invite", element: <InviteUserPage /> }],
      },
    ],
  },

  // Anything else → /app (RequireAuth bounces to /login if there is no session).
  { path: "*", element: <Navigate to="/app" replace /> },
])

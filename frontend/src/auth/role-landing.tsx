import { Navigate } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { DashboardPage } from "@/features/dashboard/dashboard-page"

// At /app, send each operational role straight to its screen instead of the
// dashboard (one less tap per shift). Owners/managers keep the dashboard.
const ROLE_HOME: Record<string, string> = {
  WAITER: "/app/floor",
  KITCHEN: "/app/kds",
  CASHIER: "/app/floor?cobrar=1", // floor pre-filtered to "a cobrar"
}

export function RoleLanding() {
  const { session } = useAuth()
  const home = session ? ROLE_HOME[session.role] : undefined
  if (home) return <Navigate to={home} replace />
  return <DashboardPage />
}

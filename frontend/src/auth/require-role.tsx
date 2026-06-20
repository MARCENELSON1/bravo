import { Navigate, Outlet } from "react-router-dom"

import type { Role } from "@/api/types"
import { useAuth } from "@/auth/auth-context"

// Gate for role-restricted routes (e.g. only OWNER/MANAGER may invite).
export function RequireRole({ allow }: { allow: Role[] }) {
  const { session } = useAuth()

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (!allow.includes(session.role)) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center gap-2 bg-background px-6 text-center">
        <h1 className="text-lg font-medium text-foreground">No tenés permisos para ver esto</h1>
        <p className="text-sm text-muted-foreground">
          Esta sección está reservada para otros roles del local.
        </p>
      </div>
    )
  }

  return <Outlet />
}

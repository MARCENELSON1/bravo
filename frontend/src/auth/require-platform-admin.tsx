import { Navigate, Outlet } from "react-router-dom"

import { Spinner } from "@/components/ui/spinner"
import { usePlatformAccess } from "@/hooks/use-platform"

// Gate del panel de plataforma: chequea el flag platform_admin (leído del back,
// no del token). Mientras carga, spinner; si no es admin, redirige a /app.
export function RequirePlatformAdmin() {
  const access = usePlatformAccess()
  if (access.isPending) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <Spinner className="size-6 text-muted-foreground" />
      </div>
    )
  }
  if (!access.data?.platform_admin) {
    return <Navigate to="/app" replace />
  }
  return <Outlet />
}

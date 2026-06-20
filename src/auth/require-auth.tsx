import { Navigate, Outlet, useLocation } from "react-router-dom"

import { Spinner } from "@/components/ui/spinner"
import { useAuth } from "@/auth/auth-context"

// Gate for authenticated routes. While the boot silent-refresh runs we show a
// spinner so protected screens never flash before the session is known.
export function RequireAuth() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === "booting") {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <Spinner className="size-6 text-muted-foreground" />
      </div>
    )
  }

  if (status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}

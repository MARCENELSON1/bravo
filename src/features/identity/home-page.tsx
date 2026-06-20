import { Link } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ROLE_LABELS } from "@/lib/role-labels"

// Protected placeholder: proves the session + role guard end to end. Replaced by
// the real dashboard in later phases.
export function HomePage() {
  const { session, logout } = useAuth()
  if (!session) return null

  const canInvite = session.role === "OWNER" || session.role === "MANAGER"

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-4 px-6 py-10">
      <Card>
        <CardHeader>
          <CardTitle>Sesión iniciada</CardTitle>
          <CardDescription>Estás dentro de BRAVO.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">Rol</dt>
              <dd className="font-medium text-foreground">{ROLE_LABELS[session.role]}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-muted-foreground">Comercio</dt>
              <dd className="truncate font-mono text-xs text-foreground">{session.tenantId}</dd>
            </div>
          </dl>

          {session.role !== "KITCHEN" && session.role !== "CASHIER" ? (
            <Button asChild variant="outline" className="w-full">
              <Link to="/app/floor">Comandas (mesas)</Link>
            </Button>
          ) : null}

          {session.role !== "WAITER" && session.role !== "CASHIER" ? (
            <Button asChild variant="outline" className="w-full">
              <Link to="/app/kds">Cocina (KDS)</Link>
            </Button>
          ) : null}

          {canInvite ? (
            <Button asChild variant="outline" className="w-full">
              <Link to="/app/products">Productos</Link>
            </Button>
          ) : null}

          {canInvite ? (
            <Button asChild variant="outline" className="w-full">
              <Link to="/app/invite">Invitar a tu equipo</Link>
            </Button>
          ) : null}

          <Button variant="ghost" className="w-full" onClick={() => void logout()}>
            Cerrar sesión
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

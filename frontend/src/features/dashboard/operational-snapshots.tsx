import { Link } from "react-router-dom"

import { GlassCard } from "@/components/ui/glass-card"
import { floorSummary } from "@/features/dashboard/floor-summary"
import { useCurrentCashSession } from "@/hooks/use-cash"
import { useFloor } from "@/hooks/use-floor"
import { formatMoney } from "@/lib/money"

// Snapshot del salón en vivo: un vistazo al floor sin entrar a Mesas.
export function SalonSnapshot() {
  const floor = useFloor()
  const s = floorSummary(floor.data ?? [])

  return (
    <GlassCard className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">Salón</h2>
        <Link to="/app/floor" className="text-xs font-medium text-primary hover:underline">
          Ver mesas →
        </Link>
      </div>
      {floor.isPending ? (
        <p className="text-sm text-muted-foreground">Cargando…</p>
      ) : s.total === 0 ? (
        <p className="text-sm text-muted-foreground">No hay mesas cargadas.</p>
      ) : (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span className="text-muted-foreground">
            <span className="font-semibold text-foreground">{s.occupied}</span> ocupadas ·{" "}
            <span className="font-semibold text-foreground">{s.free}</span> libres
          </span>
          {s.toServe > 0 ? (
            <span className="font-medium text-amber-600 dark:text-amber-400">
              {s.toServe} para servir ⚡
            </span>
          ) : null}
          {s.toCharge > 0 ? (
            <span className="font-medium text-primary">{s.toCharge} para cobrar</span>
          ) : null}
        </div>
      )}
    </GlassCard>
  )
}

// Snapshot de la caja del día: abierta/cerrada + esperado.
export function CashSnapshot() {
  const cash = useCurrentCashSession()

  return (
    <GlassCard className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">Caja</h2>
        <Link to="/app/caja" className="text-xs font-medium text-primary hover:underline">
          {cash.data ? "Ir a la caja →" : "Abrir caja →"}
        </Link>
      </div>
      {cash.isPending ? (
        <p className="text-sm text-muted-foreground">Cargando…</p>
      ) : cash.data ? (
        <div className="flex flex-col gap-0.5 text-sm">
          <span className="font-medium text-emerald-600 dark:text-emerald-400">Caja abierta</span>
          <span className="text-muted-foreground">
            Esperado:{" "}
            <span className="font-semibold text-foreground">
              {formatMoney(cash.data.expected_total, cash.data.currency)}
            </span>
          </span>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Caja sin abrir. Abrila para cobrar y hacer el arqueo del turno.
        </p>
      )}
    </GlassCard>
  )
}

import { GlassCard } from "@/components/ui/glass-card"
import { Spinner } from "@/components/ui/spinner"
import { useProductRotation } from "@/hooks/use-products"
import { weekdayLabel } from "@/features/products/pricing"
import { formatMoney } from "@/lib/money"

// Rotación por día de semana (Productos v2 Tanda B): qué días vendés más y cuál es
// el plato estrella de cada día, a partir de sale_facts.
export function RotationSchedule() {
  const rotation = useProductRotation()

  if (rotation.isPending) {
    return (
      <GlassCard className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </GlassCard>
    )
  }
  if (!rotation.data) {
    return (
      <GlassCard className="p-6 text-sm text-muted-foreground">
        No pudimos calcular la rotación.
      </GlassCard>
    )
  }

  const { currency, rows } = rotation.data
  const maxUnits = Math.max(1, ...rows.map((r) => r.units))
  const hasSales = rows.some((r) => r.units > 0)

  return (
    <GlassCard className="flex flex-col gap-4 p-6">
      <header className="flex flex-col gap-1">
        <h2 className="text-base font-semibold text-foreground">Rotación por día</h2>
        <p className="text-sm text-muted-foreground">
          Cuánto vendés cada día de la semana y el plato estrella de cada uno.
        </p>
      </header>

      {!hasSales ? (
        <p className="text-sm text-muted-foreground">
          Todavía no hay ventas para mostrar la rotación.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {rows.map((r) => (
            <li key={r.weekday} className="flex items-center gap-3">
              <span className="w-9 shrink-0 text-xs font-medium text-muted-foreground">
                {weekdayLabel(r.weekday)}
              </span>
              <div className="h-6 flex-1 overflow-hidden rounded-md bg-foreground/5">
                <div
                  className="h-full rounded-md bg-foreground/25"
                  style={{ width: `${Math.round((r.units / maxUnits) * 100)}%` }}
                />
              </div>
              <span className="w-28 shrink-0 truncate text-right text-xs text-muted-foreground">
                {r.top_product_name ?? "—"}
              </span>
              <span className="w-24 shrink-0 text-right text-sm tabular-nums text-foreground">
                {formatMoney(r.sales_amount, currency)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </GlassCard>
  )
}

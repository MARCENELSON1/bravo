import type { ExpenseCategoryRowDTO } from "@/api/types-operations"
import { GlassCard } from "@/components/ui/glass-card"
import { formatMoney } from "@/lib/money"

// Los 3 gastos que más cambiaron vs el período previo (por |delta|).
export function ExpenseChanges({
  rows,
  currency,
}: {
  rows: ExpenseCategoryRowDTO[]
  currency: string
}) {
  const top = [...rows]
    .filter((r) => r.delta !== 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 3)

  return (
    <GlassCard className="p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        Los 3 gastos que más cambiaron
      </h2>
      {top.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Sin cambios relevantes vs el período anterior.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {top.map((r) => {
            const up = r.delta > 0
            return (
              <div key={r.category} className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 flex-1 truncate font-medium text-foreground">
                  {r.category}
                </span>
                <span
                  className={`shrink-0 tabular-nums font-semibold ${up ? "text-destructive" : "text-primary"}`}
                >
                  {up ? "▲" : "▼"} {formatMoney(Math.abs(r.delta), currency)}
                </span>
              </div>
            )
          })}
          <p className="mt-1 text-xs text-muted-foreground">
            ▲ subió vs el período anterior · ▼ bajó
          </p>
        </div>
      )}
    </GlassCard>
  )
}

import { useTranslation } from "react-i18next"

import type { MovementDTO } from "@/api/types-operations"
import { GlassCard } from "@/components/ui/glass-card"
import { dateLocale, dateTimeOptions } from "@/lib/format"
import { formatMoney } from "@/lib/money"

function timeLabel(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString(dateLocale(), dateTimeOptions())
}

// Últimos movimientos (cobros + egresos) — solo en modo Hoy/Semana.
export function RecentMovements({
  movements,
  currency,
  pending,
  fractionDigits,
}: {
  movements: MovementDTO[]
  currency: string
  pending: boolean
  fractionDigits?: number
}) {
  const { t } = useTranslation()
  return (
    <GlassCard className="p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        {t("finance.recentMovements.title")}
      </h2>
      {pending ? (
        <p className="text-sm text-muted-foreground">{t("finance.recentMovements.loading")}</p>
      ) : movements.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("finance.recentMovements.empty")}</p>
      ) : (
        <div className="flex flex-col">
          {movements.map((m, i) => (
            <div
              key={`${m.occurred_at}-${i}`}
              className="flex items-center justify-between gap-3 border-b border-border/60 py-2 text-sm last:border-b-0"
            >
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <span
                  className={`grid size-6 shrink-0 place-items-center rounded-full text-xs ${
                    m.kind === "IN"
                      ? "bg-primary/15 text-primary"
                      : "bg-destructive/15 text-destructive"
                  }`}
                >
                  {m.kind === "IN" ? "+" : "−"}
                </span>
                <span className="min-w-0 flex-1 truncate text-foreground">
                  {m.description ||
                    m.category ||
                    (m.kind === "IN"
                      ? t("finance.recentMovements.income")
                      : t("finance.recentMovements.expense"))}
                </span>
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">{timeLabel(m.occurred_at)}</span>
              <span
                className={`shrink-0 tabular-nums font-medium ${
                  m.kind === "IN" ? "text-primary" : "text-destructive"
                }`}
              >
                {m.kind === "IN" ? "+" : "−"}
                {formatMoney(m.amount, currency, fractionDigits)}
              </span>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

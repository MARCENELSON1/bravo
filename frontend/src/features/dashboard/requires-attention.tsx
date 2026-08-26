import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"

import { GlassCard } from "@/components/ui/glass-card"
import { classifyCustomers } from "@/features/crm/customer-segments"
import { homeAlerts, type AlertTone } from "@/features/dashboard/home-alerts"
import { useCurrentCashSession } from "@/hooks/use-cash"
import { useCustomerStats } from "@/hooks/use-customers"
import { useFloor } from "@/hooks/use-floor"
import { useLowStock } from "@/hooks/use-inventory"
import { floorView } from "@/lib/floor-session"

const TONE_CLASS: Record<AlertTone, string> = {
  attention: "border-amber-500/60 bg-amber-50/60 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300",
  warn: "border-primary/50 bg-primary/10 text-foreground",
  info: "border-border bg-muted/50 text-foreground",
}

// "Requiere tu atención": la franja operativa del Home. Compone mesas + caja +
// stock + clientes en una sola lista de "qué hacer ahora". Convierte el Home de
// reporte en cerebro. Todo dato ya existente; sin backend nuevo.
export function RequiresAttention() {
  const { t } = useTranslation()
  const floor = useFloor()
  const cash = useCurrentCashSession()
  const lowStock = useLowStock()
  const stats = useCustomerStats()
  const [nowMs] = useState(() => Date.now())

  const alerts = useMemo(() => {
    const tables = floor.data ?? []
    const toServe = tables.filter((t) => floorView(t).state === "TO_SERVE").length
    const toCharge = tables.filter((t) => {
      const s = floorView(t).state
      return s === "TO_CHARGE" || s === "SERVED"
    }).length
    const occupied = tables.filter((t) => t.active_order != null).length
    const atRisk = classifyCustomers(stats.data?.rows ?? [], nowMs).filter(
      (c) => c.segment === "en_riesgo"
    ).length
    return homeAlerts({
      toServe,
      toCharge,
      occupied,
      cashOpen: cash.isPending ? null : cash.data != null,
      lowStock: lowStock.data?.length ?? 0,
      atRisk,
    })
  }, [floor.data, cash.isPending, cash.data, lowStock.data, stats.data, nowMs])

  // Mientras carga lo esencial, no mostramos nada (evita parpadeo de "todo ok").
  if (floor.isPending) return null

  return (
    <GlassCard className="p-5">
      <h2 className="mb-3 text-base font-semibold text-foreground">
        {t("dashboard.requiresAttention.title")}
      </h2>
      {alerts.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {t("dashboard.requiresAttention.allClear")}
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {alerts.map((a) => (
            <Link
              key={a.key}
              to={a.to}
              className={
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition hover:opacity-90 " +
                TONE_CLASS[a.tone]
              }
            >
              {t(a.labelKey, a.count !== undefined ? { count: a.count } : undefined)}
              <span aria-hidden>→</span>
            </Link>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

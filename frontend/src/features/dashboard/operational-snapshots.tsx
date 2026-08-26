import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"

import { GlassCard } from "@/components/ui/glass-card"
import { floorSummary } from "@/features/dashboard/floor-summary"
import { useCurrentCashSession } from "@/hooks/use-cash"
import { useFloor } from "@/hooks/use-floor"
import { formatMoney } from "@/lib/money"

// Snapshot del salón en vivo: un vistazo al floor sin entrar a Mesas.
export function SalonSnapshot() {
  const { t } = useTranslation()
  const floor = useFloor()
  const s = floorSummary(floor.data ?? [])

  return (
    <GlassCard className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{t("dashboard.salon.title")}</h2>
        <Link to="/app/floor" className="text-xs font-medium text-primary hover:underline">
          {t("dashboard.salon.viewTables")}
        </Link>
      </div>
      {floor.isPending ? (
        <p className="text-sm text-muted-foreground">{t("dashboard.loading")}</p>
      ) : s.total === 0 ? (
        <p className="text-sm text-muted-foreground">{t("dashboard.salon.empty")}</p>
      ) : (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span className="text-muted-foreground">
            <span className="font-semibold text-foreground">{s.occupied}</span>{" "}
            {t("dashboard.salon.occupied")} ·{" "}
            <span className="font-semibold text-foreground">{s.free}</span>{" "}
            {t("dashboard.salon.free")}
          </span>
          {s.toServe > 0 ? (
            <span className="font-medium text-amber-600 dark:text-amber-400">
              {s.toServe} {t("dashboard.salon.toServe")}
            </span>
          ) : null}
          {s.toCharge > 0 ? (
            <span className="font-medium text-primary">
              {s.toCharge} {t("dashboard.salon.toCharge")}
            </span>
          ) : null}
        </div>
      )}
    </GlassCard>
  )
}

// Snapshot de la caja del día: abierta/cerrada + esperado.
export function CashSnapshot() {
  const { t } = useTranslation()
  const cash = useCurrentCashSession()

  return (
    <GlassCard className="flex flex-col gap-2 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{t("dashboard.cash.title")}</h2>
        <Link to="/app/caja" className="text-xs font-medium text-primary hover:underline">
          {cash.data ? t("dashboard.cash.goToRegister") : t("dashboard.cash.openRegister")}
        </Link>
      </div>
      {cash.isPending ? (
        <p className="text-sm text-muted-foreground">{t("dashboard.loading")}</p>
      ) : cash.data ? (
        <div className="flex flex-col gap-0.5 text-sm">
          <span className="font-medium text-emerald-600 dark:text-emerald-400">
            {t("dashboard.cash.open")}
          </span>
          <span className="text-muted-foreground">
            {t("dashboard.cash.expected")}{" "}
            <span className="font-semibold text-foreground">
              {formatMoney(cash.data.expected_total, cash.data.currency)}
            </span>
          </span>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("dashboard.cash.closedHint")}</p>
      )}
    </GlassCard>
  )
}

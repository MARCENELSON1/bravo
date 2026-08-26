import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Spinner } from "@/components/ui/spinner"
import { todaysActions } from "@/features/crm/customer-segments"
import {
  useContactResult,
  useCustomers,
  useCustomerStats,
  useLogContact,
  useRecentContacts,
} from "@/hooks/use-customers"
import { formatMoney } from "@/lib/money"
import { waLink } from "@/lib/wa"

// El corazón del CRM: "acciones para hoy" (máx 3 en riesgo por plata en juego) +
// el loop de resultado arriba (contactaste N, volvieron M, $X).
export function CustomerActionsView() {
  const { t } = useTranslation()
  const stats = useCustomerStats()
  const customers = useCustomers()
  const recent = useRecentContacts(7)
  const result = useContactResult(30)
  const logContact = useLogContact()
  const [nowMs] = useState(() => Date.now())

  const optOutIds = useMemo(
    () => new Set((customers.data ?? []).filter((c) => c.no_contactar).map((c) => c.id)),
    [customers.data]
  )
  const recentIds = useMemo(
    () => new Set(recent.data?.customer_ids ?? []),
    [recent.data]
  )
  const rows = useMemo(() => stats.data?.rows ?? [], [stats.data])
  const currency = stats.data?.currency ?? "ARS"
  const actions = useMemo(
    () => todaysActions(rows, optOutIds, recentIds, nowMs),
    [rows, optOutIds, recentIds, nowMs]
  )

  if (stats.isPending) return <Spinner />
  if (rows.length === 0) return null

  const res = result.data

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <div>
        <h2 className="text-base font-semibold text-foreground">{t("crm.actions.title")}</h2>
        {res && res.contacted > 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("crm.actions.resultA")}
            <span className="font-medium text-foreground">{res.contacted}</span>
            {t("crm.actions.resultB")}
            <span className="font-medium text-foreground">{res.returned}</span>
            {t("crm.actions.resultC")}
            <span className="font-medium text-foreground">
              {formatMoney(res.revenue, res.currency)}
            </span>
            {t("crm.actions.resultD")}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">{t("crm.actions.subtitle")}</p>
        )}
      </div>

      {actions.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("crm.actions.empty")}</p>
      ) : (
        <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {actions.map((c) => {
            const link = waLink(c.phone, t("crm.waWinback", { name: c.name }))
            return (
              <div key={c.customer_id} className="flex flex-wrap items-center gap-2 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium">{c.name}</span>
                  <p className="text-xs text-muted-foreground">
                    {t("crm.actions.atRisk")} · {formatMoney(c.total_spent, currency)}{" "}
                    {t("crm.spent")}
                    {c.daysSinceLast !== null
                      ? t("crm.daysAgo", { days: c.daysSinceLast })
                      : ""}
                  </p>
                </div>
                {link ? (
                  <a href={link} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline">
                      {t("crm.whatsapp")}
                    </Button>
                  </a>
                ) : null}
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={logContact.isPending}
                  onClick={() =>
                    logContact.mutate(
                      { id: c.customer_id, reason: "en_riesgo" },
                      {
                        onSuccess: () => toast.success(t("crm.actions.markedSuccess")),
                        onError: (e) =>
                          toast.error(apiErrorText(e, t, t("crm.actions.markError"))),
                      }
                    )
                  }
                >
                  {t("crm.actions.markContacted")}
                </Button>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}

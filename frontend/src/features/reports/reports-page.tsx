import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { AccountantExport } from "@/features/finance/accountant-export"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useProductPerformance, useRevenueDaily } from "@/hooks/use-analytics"
import { useDashboard } from "@/hooks/use-dashboard"
import {
  useExpenseBreakdown,
  useReportPendingTax,
  useTaxCollected,
  useTaxReportStatus,
} from "@/hooks/use-finance"
import { FINANCE_RANGES, rangeWindow, type FinanceRange } from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

export function ReportsPage() {
  const { t } = useTranslation()
  const [range, setRange] = useState<FinanceRange>("month")
  const window = useMemo(() => rangeWindow(range), [range])

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <GradientHeading>{t("reports.title")}</GradientHeading>
        <div className="flex flex-wrap gap-1">
          {FINANCE_RANGES.map((r) => (
            <Button
              key={r.value}
              size="sm"
              variant={range === r.value ? "default" : "outline"}
              onClick={() => setRange(r.value)}
            >
              {t(`reports.ranges.${r.value}`)}
            </Button>
          ))}
        </div>
      </header>

      <Summary window={window} />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <SalesByDay window={window} />
        <ExpensesByCategory window={window} />
      </div>
      <TopProducts window={window} />
      <TaxToRemit window={window} />
      <TaxReportStatusCard />
      <AccountantExport window={window} />
    </div>
  )
}

type Win = { from: string; to: string }

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={`text-lg font-bold tabular-nums ${accent ? "text-primary" : "text-foreground"}`}
      >
        {value}
      </span>
    </div>
  )
}

function Summary({ window }: { window: Win }) {
  const { t } = useTranslation()
  const q = useDashboard({ from: window.from, to: window.to })
  const d = q.data
  const cur = d?.currency ?? "ARS"
  const money = (n: number) => formatMoney(n, cur)
  return (
    <GlassCard className="p-6">
      <h2 className="mb-3 text-base font-semibold text-foreground">{t("reports.summary.title")}</h2>
      {q.isPending ? (
        <Spinner />
      ) : d ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <Stat label={t("reports.summary.sales")} value={money(d.sales)} />
          <Stat label={t("reports.summary.collectedNet")} value={money(d.collected_net)} />
          <Stat label={t("reports.summary.expenses")} value={money(d.expenses)} />
          <Stat
            label={t("reports.summary.profit")}
            value={money(d.collected_net - d.expenses)}
            accent
          />
          <Stat label={t("reports.summary.avgTicket")} value={money(d.avg_ticket)} />
          <Stat label={t("reports.summary.orders")} value={String(d.paid_orders)} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("reports.summary.error")}</p>
      )}
    </GlassCard>
  )
}

function SalesByDay({ window }: { window: Win }) {
  const { t } = useTranslation()
  const q = useRevenueDaily({ from: window.from, to: window.to })
  const rows = q.data ?? []
  const max = rows.reduce((m, r) => Math.max(m, r.sales_amount), 0)
  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <h2 className="text-base font-semibold text-foreground">{t("reports.salesByDay.title")}</h2>
      {q.isPending ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("reports.salesByDay.empty")}</p>
      ) : (
        <div className="flex flex-col gap-1.5">
          {rows.map((r) => (
            <div key={r.day} className="flex items-center gap-2 text-sm">
              <span className="w-20 shrink-0 tabular-nums text-muted-foreground">{r.day}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary/70"
                  style={{ width: max > 0 ? `${(r.sales_amount / max) * 100}%` : "0%" }}
                />
              </div>
              <span className="w-24 shrink-0 text-right tabular-nums">
                {formatMoney(r.sales_amount, "ARS")}
              </span>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

function ExpensesByCategory({ window }: { window: Win }) {
  const { t } = useTranslation()
  const q = useExpenseBreakdown({ from: window.from, to: window.to })
  const data = q.data
  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <h2 className="text-base font-semibold text-foreground">
        {t("reports.expensesByCategory.title")}
      </h2>
      {q.isPending ? (
        <Spinner />
      ) : !data || data.rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("reports.expensesByCategory.empty")}</p>
      ) : (
        <div className="flex flex-col gap-1.5 text-sm">
          {data.rows.map((r) => (
            <div key={r.category} className="flex items-center justify-between gap-2">
              <span className="truncate">{r.category}</span>
              <span className="flex items-center gap-2 shrink-0 tabular-nums">
                {r.delta !== 0 ? (
                  <span className={r.delta > 0 ? "text-xs text-destructive" : "text-xs text-success"}>
                    {r.delta > 0 ? "▲" : "▼"} {formatMoney(Math.abs(r.delta), data.currency)}
                  </span>
                ) : null}
                <span className="font-medium">{formatMoney(r.amount, data.currency)}</span>
              </span>
            </div>
          ))}
          <div className="mt-1 flex items-center justify-between border-t pt-2 font-medium">
            <span>{t("reports.expensesByCategory.total")}</span>
            <span className="tabular-nums">{formatMoney(data.total, data.currency)}</span>
          </div>
        </div>
      )}
    </GlassCard>
  )
}

// Sales tax cobrado (a remitir). Sólo se muestra si hay algo (US); en AR el
// impuesto va incluido en el precio y no se cobra aparte → no aparece (paridad).
function TaxToRemit({ window }: { window: Win }) {
  const { t } = useTranslation()
  const q = useTaxCollected({ from: window.from, to: window.to })
  const d = q.data
  if (!d || d.amount <= 0) return null
  return (
    <GlassCard className="flex items-center justify-between gap-4 p-6">
      <div>
        <h2 className="text-base font-semibold text-foreground">{t("reports.taxToRemit.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("reports.taxToRemit.description")}</p>
      </div>
      <span className="shrink-0 text-2xl font-bold tabular-nums text-foreground">
        {formatMoney(d.amount, d.currency)}
      </span>
    </GlassCard>
  )
}

// Estado del reporte al fisco (TaxJar AutoFile) + "Reportar ahora". Solo aparece
// si hay algo en el outbox → en AR no se ve (paridad).
function TaxReportStatusCard() {
  const { t } = useTranslation()
  const q = useTaxReportStatus()
  const run = useReportPendingTax()
  const d = q.data
  if (!d || d.pending + d.sent === 0) return null

  const report = () => {
    run.mutate(undefined, {
      onSuccess: (r) => {
        if (r.failed > 0) {
          toast.error(
            t("reports.taxReport.reportPartialError", { sent: r.sent, failed: r.failed })
          )
        } else {
          toast.success(
            r.sent > 0
              ? t("reports.taxReport.reportSuccess", { sent: r.sent })
              : t("reports.taxReport.reportNothing")
          )
        }
      },
      onError: () => toast.error(t("reports.taxReport.reportError")),
    })
  }

  return (
    <GlassCard className="flex items-center justify-between gap-4 p-6">
      <div>
        <h2 className="text-base font-semibold text-foreground">{t("reports.taxReport.title")}</h2>
        <p className="text-sm text-muted-foreground">
          {d.pending > 0
            ? `${t("reports.taxReport.pending", { count: d.pending })}${
                d.failed > 0 ? t("reports.taxReport.errorsSuffix", { count: d.failed }) : ""
              }.`
            : t("reports.taxReport.allReported", { count: d.sent })}
        </p>
        {d.failed > 0 ? (
          <p className="mt-0.5 text-xs text-warning">
            {t("reports.taxReport.failedNote")}
          </p>
        ) : null}
      </div>
      {d.pending > 0 ? (
        <Button onClick={report} disabled={run.isPending} className="shrink-0">
          {run.isPending ? t("reports.taxReport.reporting") : t("reports.taxReport.reportNow")}
        </Button>
      ) : (
        <span className="shrink-0 text-sm font-medium text-success">
          {t("reports.taxReport.upToDate")}
        </span>
      )}
    </GlassCard>
  )
}

function TopProducts({ window }: { window: Win }) {
  const { t } = useTranslation()
  const q = useProductPerformance({ from: window.from, to: window.to, limit: 10 })
  const rows = q.data ?? []
  const cur = rows[0]?.currency ?? "ARS"
  return (
    <GlassCard className="flex flex-col gap-3 p-6">
      <h2 className="text-base font-semibold text-foreground">{t("reports.topProducts.title")}</h2>
      {q.isPending ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("reports.topProducts.empty")}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[420px] text-sm">
            <thead>
              <tr className="border-b text-xs font-medium text-muted-foreground">
                <th className="py-1 text-left">{t("reports.topProducts.product")}</th>
                <th className="py-1 text-right">{t("reports.topProducts.units")}</th>
                <th className="py-1 text-right">{t("reports.topProducts.sales")}</th>
                <th className="py-1 text-right">{t("reports.topProducts.margin")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.product_id} className="border-b border-border/60 last:border-b-0">
                  <td className="py-1.5 pr-2">{r.product_name}</td>
                  <td className="py-1.5 text-right tabular-nums">{r.units_sold}</td>
                  <td className="py-1.5 text-right tabular-nums">
                    {formatMoney(r.sales_amount, cur)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums font-medium">
                    {formatMoney(r.margin_amount, cur)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </GlassCard>
  )
}

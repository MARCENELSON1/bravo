import type { TFunction } from "i18next"
import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"

import type { FinanceKpiDTO, FinanceOverviewDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { ExpenseChanges } from "@/features/finance/expense-changes"
import { ExpenseDonut } from "@/features/finance/expense-donut"
import { RecentMovements } from "@/features/finance/recent-movements"
import {
  useExpenseBreakdown,
  useFinanceOverview,
  useProductDetail,
  useRecentMovements,
} from "@/hooks/use-finance"
import {
  FINANCE_RANGES,
  rangeWindow,
  type FinanceRange,
  type RangeWindow,
} from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

const STATUS_STYLE: Record<string, string> = {
  healthy: "text-emerald-500",
  warn: "text-amber-500",
  alert: "text-red-500",
  neutral: "text-muted-foreground",
}
const STATUS_DOT: Record<string, string> = {
  healthy: "bg-emerald-500",
  warn: "bg-amber-500",
  alert: "bg-red-500",
  neutral: "bg-muted-foreground",
}

function pct(bps: number): string {
  return `${(bps / 100).toFixed(1)}%`
}

function kpiValue(k: FinanceKpiDTO, currency: string): string {
  if (k.kind === "ratio") return pct(k.value)
  if (k.kind === "turnover")
    return `${(k.value / 100).toLocaleString("es-AR", { maximumFractionDigits: 1 })}×`
  return formatMoney(k.value, currency)
}

function kpiDelta(k: FinanceKpiDTO, currency: string): string | null {
  if (k.delta === 0) return null
  const up = k.delta > 0
  const mag =
    k.kind === "ratio"
      ? `${Math.abs(k.delta / 100).toFixed(1)}pts`
      : formatMoney(Math.abs(k.delta), currency)
  return `${up ? "▲" : "▼"} ${mag}`
}

function healthyHint(k: FinanceKpiDTO, t: TFunction): string | null {
  if (k.kind !== "ratio" || k.healthy_high == null) return null
  return k.healthy_low != null
    ? t("finance.healthyRange", { low: pct(k.healthy_low), high: pct(k.healthy_high) })
    : t("finance.healthyMax", { high: pct(k.healthy_high) })
}

export function FinancePage() {
  const { t } = useTranslation()
  const [range, setRange] = useState<FinanceRange>("month")
  const window = useMemo(() => rangeWindow(range), [range])
  const overview = useFinanceOverview(window)

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <GradientHeading>{t("finance.title")}</GradientHeading>
        <div className="flex flex-wrap gap-1">
          {FINANCE_RANGES.map((r) => (
            <Button
              key={r.value}
              size="sm"
              variant={range === r.value ? "default" : "outline"}
              onClick={() => setRange(r.value)}
            >
              {t(`finance.ranges.${r.value}`)}
            </Button>
          ))}
        </div>
      </header>

      {overview.isLoading ? (
        <Spinner />
      ) : overview.data ? (
        <FinanceBody data={overview.data} window={window} range={range} />
      ) : (
        <p className="text-sm text-muted-foreground">{t("finance.loadError")}</p>
      )}
    </div>
  )
}

function FinanceBody({
  data,
  window,
  range,
}: {
  data: FinanceOverviewDTO
  window: RangeWindow
  range: FinanceRange
}) {
  const { t } = useTranslation()
  const [category, setCategory] = useState<string | null>(null)
  const breakdown = useExpenseBreakdown(window)
  const showMovements = range === "today" || range === "week"
  const movements = useRecentMovements(window, showMovements)

  const kpiByKey = new Map(data.kpis.map((k) => [k.key, k]))
  const net = kpiByKey.get("net_margin")

  return (
    <>
      {/* HERO — ganancia neta del período */}
      <GlassCard className="p-6">
        <p className="text-sm text-muted-foreground">{t("finance.hero.netProfit")}</p>
        <p
          className={`mt-1 text-3xl font-bold tabular-nums sm:text-4xl ${net && net.value < 0 ? "text-red-500" : "text-foreground"}`}
        >
          {net ? formatMoney(net.value, data.currency) : "—"}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-4 text-sm">
          {net && kpiDelta(net, data.currency) ? (
            <span className={net.delta > 0 ? "text-primary" : "text-destructive"}>
              {kpiDelta(net, data.currency)} {t("finance.hero.vsPrevious")}
            </span>
          ) : null}
          {data.projection ? (
            <span className="text-muted-foreground">
              {t("finance.hero.projectionPrefix")}{" "}
              <span className="font-semibold text-foreground">
                {formatMoney(data.projection.sales_amount, data.currency)}
              </span>{" "}
              {t("finance.hero.projectionDays", {
                elapsed: data.projection.elapsed_days,
                total: data.projection.month_days,
              })}
            </span>
          ) : null}
        </div>
      </GlassCard>

      {!data.configured ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-300">
          {t("finance.configureCosts")}
        </p>
      ) : null}

      {/* NIVEL 2 — áreas de salud con acción sugerida */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {(["net_margin", "food_cost", "labor_cost", "waste"] as const).map((key) => {
          const k = kpiByKey.get(key)
          if (!k) return null
          return (
            <GlassCard key={key} className="flex flex-col gap-1 p-4">
              <span className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className={`size-2 rounded-full ${STATUS_DOT[k.status] ?? ""}`} />
                {t(`finance.kpiLabels.${key}`)}
              </span>
              <span className={`text-xl font-bold tabular-nums ${STATUS_STYLE[k.status] ?? ""}`}>
                {kpiValue(k, data.currency)}
              </span>
              <span className="text-xs text-muted-foreground">
                {t(`finance.statusActions.${k.status}`, { defaultValue: "—" })}
              </span>
            </GlassCard>
          )
        })}
      </section>

      {/* Comisiones de cobro — línea SEPARADA del margen (eje de cobranza), para
          no doble-contar con el IVA. Solo si hay tasas cargadas. */}
      {data.commissions_amount > 0 ? (
        <GlassCard className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="text-sm text-muted-foreground">{t("finance.commissions.label")}</p>
            <p className="text-xl font-bold tabular-nums text-destructive">
              −{formatMoney(data.commissions_amount, data.currency)}
            </p>
          </div>
          <p className="text-sm text-muted-foreground">
            {t("finance.commissions.netCollected")}{" "}
            <span className="font-semibold text-foreground">
              {formatMoney(data.collected_net_amount, data.currency)}
            </span>
          </p>
        </GlassCard>
      ) : null}

      {/* NIVEL 3 + 4b — gastos que cambiaron + donut de distribución */}
      <section className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <ExpenseChanges rows={breakdown.data?.rows ?? []} currency={data.currency} />
        <ExpenseDonut
          rows={breakdown.data?.rows ?? []}
          total={breakdown.data?.total ?? 0}
          currency={data.currency}
          selected={category}
          onSelect={setCategory}
        />
      </section>

      {data.summary ? (
        <GlassCard className="p-5 text-sm text-muted-foreground">{data.summary}</GlassCard>
      ) : null}

      {/* NIVEL 5 — KPIs del rubro (los 7) */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
        {data.kpis.map((k) => (
          <GlassCard key={k.key} className="flex flex-col gap-1 p-5">
            <span className="text-sm text-muted-foreground">
              {t(`finance.kpiLabels.${k.key}`, { defaultValue: k.key })}
            </span>
            <span className={`text-2xl font-bold tabular-nums ${STATUS_STYLE[k.status] ?? ""}`}>
              {kpiValue(k, data.currency)}
            </span>
            <span className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{kpiDelta(k, data.currency) ?? "—"}</span>
              <span>{healthyHint(k, t) ?? ""}</span>
            </span>
          </GlassCard>
        ))}
      </section>

      {data.diagnostics.length > 0 ? (
        <GlassCard className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            {t("finance.diagnostics.title")}
          </h2>
          <div className="flex flex-col gap-3">
            {data.diagnostics.map((d) => (
              <div key={d.code} className="border-l-2 border-primary/60 pl-3">
                <p className="text-sm font-medium">{d.title}</p>
                <p className="text-sm text-muted-foreground">{d.body}</p>
                {d.action ? <p className="text-xs text-primary">→ {d.action}</p> : null}
              </div>
            ))}
          </div>
        </GlassCard>
      ) : null}

      {data.product_margins.length > 0 ? (
        <GlassCard className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            {t("finance.productMargins.title")}
          </h2>
          <div className="flex flex-col">
            <div className="flex items-center justify-between border-b pb-1 text-xs font-medium text-muted-foreground">
              <span>{t("finance.productMargins.product")}</span>
              <span>{t("finance.productMargins.unitsMargin")}</span>
            </div>
            {data.product_margins.map((p) => (
              <ProductRow
                key={p.product_id}
                productId={p.product_id}
                name={p.product_name}
                units={p.units_sold}
                margin={p.margin_amount}
                currency={data.currency}
                window={window}
              />
            ))}
          </div>
        </GlassCard>
      ) : null}

      {/* NIVEL 6 — últimos movimientos (solo Hoy/Semana) */}
      {showMovements ? (
        <RecentMovements
          movements={movements.data ?? []}
          currency={data.currency}
          pending={movements.isPending}
        />
      ) : null}
    </>
  )
}

function ProductRow({
  productId,
  name,
  units,
  margin,
  currency,
  window,
}: {
  productId: string
  name: string
  units: number
  margin: number
  currency: string
  window: RangeWindow
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const detail = useProductDetail(open ? productId : null, window)

  return (
    <div className="border-b last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between py-2 text-left text-sm hover:bg-muted/40"
      >
        <span className="truncate">
          {open ? "▾ " : "▸ "}
          {name}
        </span>
        <span className="tabular-nums">
          {units} · <span className="font-medium">{formatMoney(margin, currency)}</span>
        </span>
      </button>
      {open ? (
        <div className="pb-2 pl-4 text-xs text-muted-foreground">
          {detail.isLoading ? (
            <span>{t("finance.loading")}</span>
          ) : detail.data && detail.data.lines.length > 0 ? (
            detail.data.lines.map((line) => (
              <div key={line.order_id} className="flex items-center justify-between py-0.5">
                <span>{new Date(line.occurred_at).toLocaleDateString("es-AR")}</span>
                <span className="tabular-nums">
                  {line.quantity}× · {formatMoney(line.margin_amount, currency)}
                </span>
              </div>
            ))
          ) : (
            <span>{t("finance.productMargins.noLines")}</span>
          )}
        </div>
      ) : null}
    </div>
  )
}

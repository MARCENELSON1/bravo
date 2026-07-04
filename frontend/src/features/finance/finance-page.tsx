import { useMemo, useState } from "react"

import type { FinanceKpiDTO, FinanceOverviewDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useFinanceOverview, useProductDetail } from "@/hooks/use-finance"
import {
  FINANCE_RANGES,
  rangeWindow,
  type FinanceRange,
  type RangeWindow,
} from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

const KPI_LABELS: Record<string, string> = {
  prime_cost: "Prime Cost",
  food_cost: "Food Cost",
  labor_cost: "Costo de personal",
  waste: "Mermas",
  net_margin: "Margen neto",
  gross_margin: "Margen bruto",
  break_even: "Punto de equilibrio",
}

const STATUS_STYLE: Record<string, string> = {
  healthy: "text-emerald-500",
  warn: "text-amber-500",
  alert: "text-red-500",
  neutral: "text-muted-foreground",
}

function pct(bps: number): string {
  return `${(bps / 100).toFixed(1)}%`
}

function kpiValue(k: FinanceKpiDTO, currency: string): string {
  return k.kind === "ratio" ? pct(k.value) : formatMoney(k.value, currency)
}

function kpiDelta(k: FinanceKpiDTO, currency: string): string | null {
  if (k.delta === 0) return null
  const up = k.delta > 0
  const mag = k.kind === "ratio" ? `${Math.abs(k.delta / 100).toFixed(1)}pts` : formatMoney(Math.abs(k.delta), currency)
  return `${up ? "▲" : "▼"} ${mag}`
}

function healthyHint(k: FinanceKpiDTO): string | null {
  if (k.kind !== "ratio" || k.healthy_high == null) return null
  return k.healthy_low != null
    ? `sano ${pct(k.healthy_low)}–${pct(k.healthy_high)}`
    : `sano < ${pct(k.healthy_high)}`
}

export function FinancePage() {
  const [range, setRange] = useState<FinanceRange>("month")
  const window = useMemo(() => rangeWindow(range), [range])
  const overview = useFinanceOverview(window)

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-6 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <GradientHeading>Finanzas</GradientHeading>
        <div className="flex flex-wrap gap-1">
          {FINANCE_RANGES.map((r) => (
            <Button
              key={r.value}
              size="sm"
              variant={range === r.value ? "default" : "outline"}
              onClick={() => setRange(r.value)}
            >
              {r.label}
            </Button>
          ))}
        </div>
      </header>

      {overview.isLoading ? (
        <Spinner />
      ) : overview.data ? (
        <FinanceBody data={overview.data} window={window} />
      ) : (
        <p className="text-sm text-muted-foreground">No pudimos cargar las finanzas.</p>
      )}
    </div>
  )
}

function FinanceBody({ data, window }: { data: FinanceOverviewDTO; window: RangeWindow }) {
  return (
    <>
      {data.projection ? (
        <p className="rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-sm">
          Proyección de cierre del mes:{" "}
          <span className="font-semibold">
            si seguís así, cerrás en {formatMoney(data.projection.sales_amount, data.currency)}
          </span>{" "}
          <span className="text-muted-foreground">
            ({data.projection.elapsed_days}/{data.projection.month_days} días)
          </span>
        </p>
      ) : null}

      {!data.configured ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-300">
          Cargá tus costos fijos (personal y otros) en el Asesor para que el margen neto y el
          prime cost sean exactos.
        </p>
      ) : null}

      {data.summary ? (
        <GlassCard className="p-5 text-sm text-muted-foreground">{data.summary}</GlassCard>
      ) : null}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data.kpis.map((k) => (
          <GlassCard key={k.key} className="flex flex-col gap-1 p-5">
            <span className="text-sm text-muted-foreground">{KPI_LABELS[k.key] ?? k.key}</span>
            <span className={`text-2xl font-bold tabular-nums ${STATUS_STYLE[k.status] ?? ""}`}>
              {kpiValue(k, data.currency)}
            </span>
            <span className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{kpiDelta(k, data.currency) ?? "—"}</span>
              <span>{healthyHint(k) ?? ""}</span>
            </span>
          </GlassCard>
        ))}
      </section>

      {data.diagnostics.length > 0 ? (
        <GlassCard className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">Diagnósticos</h2>
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
            Margen de contribución por producto
          </h2>
          <div className="flex flex-col">
            <div className="flex items-center justify-between border-b pb-1 text-xs font-medium text-muted-foreground">
              <span>Producto</span>
              <span>Unidades · Margen</span>
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
            <span>Cargando…</span>
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
            <span>Sin líneas en el período.</span>
          )}
        </div>
      ) : null}
    </div>
  )
}

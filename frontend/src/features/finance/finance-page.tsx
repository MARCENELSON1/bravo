import { Fragment, useMemo, useState } from "react"

import type { FinanceKpiDTO, FinanceOverviewDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import { useFinanceOverview } from "@/hooks/use-finance"
import { FINANCE_RANGES, rangeWindow, type FinanceRange } from "@/lib/finance-range"
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
    <div className="flex flex-col gap-4">
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
        <FinanceBody data={overview.data} />
      ) : (
        <p className="text-sm text-muted-foreground">No pudimos cargar las finanzas.</p>
      )}
    </div>
  )
}

function FinanceBody({ data }: { data: FinanceOverviewDTO }) {
  return (
    <>
      {!data.configured ? (
        <p className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-300">
          Cargá tus costos fijos (personal y otros) en el Asesor para que el margen neto y el
          prime cost sean exactos.
        </p>
      ) : null}

      {data.summary ? (
        <Card>
          <CardContent className="pt-4 text-sm text-muted-foreground">{data.summary}</CardContent>
        </Card>
      ) : null}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {data.kpis.map((k) => (
          <Card key={k.key}>
            <CardContent className="flex flex-col gap-1 pt-4">
              <span className="text-xs text-muted-foreground">{KPI_LABELS[k.key] ?? k.key}</span>
              <span className={`text-2xl font-semibold tabular-nums ${STATUS_STYLE[k.status] ?? ""}`}>
                {kpiValue(k, data.currency)}
              </span>
              <span className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>{kpiDelta(k, data.currency) ?? "—"}</span>
                <span>{healthyHint(k) ?? ""}</span>
              </span>
            </CardContent>
          </Card>
        ))}
      </section>

      {data.diagnostics.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Diagnósticos</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.diagnostics.map((d) => (
              <div key={d.code} className="border-l-2 border-primary/60 pl-3">
                <p className="text-sm font-medium">{d.title}</p>
                <p className="text-sm text-muted-foreground">{d.body}</p>
                {d.action ? <p className="text-xs text-primary">→ {d.action}</p> : null}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {data.product_margins.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Margen de contribución por producto</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-[1fr_auto_auto] items-center gap-x-3 gap-y-1 text-sm">
              <span className="text-xs font-medium text-muted-foreground">Producto</span>
              <span className="text-right text-xs font-medium text-muted-foreground">Unidades</span>
              <span className="text-right text-xs font-medium text-muted-foreground">Margen</span>
              {data.product_margins.map((p) => (
                <Fragment key={p.product_id}>
                  <span className="truncate">{p.product_name}</span>
                  <span className="text-right tabular-nums text-muted-foreground">{p.units_sold}</span>
                  <span className="text-right tabular-nums font-medium">
                    {formatMoney(p.margin_amount, data.currency)}
                  </span>
                </Fragment>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </>
  )
}

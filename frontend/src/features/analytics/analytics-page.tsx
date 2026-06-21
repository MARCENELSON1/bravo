import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  usePaymentMix,
  useProductPerformance,
  useRevenue,
} from "@/hooks/use-analytics"
import { directionLabel, methodLabel } from "@/lib/analytics"
import { formatMoney } from "@/lib/money"

function KpiCard({
  label,
  value,
  hint,
  negative,
}: {
  label: string
  value: string
  hint?: string
  negative?: boolean
}) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-border p-4">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={`text-xl font-semibold tabular-nums ${negative ? "text-destructive" : "text-foreground"}`}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  )
}

export function AnalyticsPage() {
  const [from, setFrom] = useState("")
  const [to, setTo] = useState("")
  const fromIso = from ? new Date(`${from}T00:00:00`).toISOString() : undefined
  const toIso = to ? new Date(`${to}T23:59:59`).toISOString() : undefined
  const query = { from: fromIso, to: toIso }

  const revenue = useRevenue(query)
  const mix = usePaymentMix(query)
  const products = useProductPerformance({ ...query, limit: 10 })

  const currency = revenue.data?.currency ?? "ARS"
  const money = (amount: number) => formatMoney(amount, currency)

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Analítica
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            Tus números en pesos, leídos del modelo canónico. Dejá las fechas vacías para ver todo.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Desde
            <Input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Hasta
            <Input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="w-auto"
            />
          </label>
        </div>
      </header>

      {revenue.isPending ? (
        <div className="flex justify-center p-10">
          <Spinner className="size-5 text-muted-foreground" />
        </div>
      ) : revenue.data ? (
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <KpiCard label="Ventas" value={money(revenue.data.sales_amount)} />
          <KpiCard label="Cobrado" value={money(revenue.data.collected_amount)} />
          <KpiCard label="Egresos" value={money(revenue.data.expense_amount)} />
          <KpiCard
            label="Margen bruto"
            value={money(revenue.data.gross_margin_amount)}
            hint="Ventas − food cost"
            negative={revenue.data.gross_margin_amount < 0}
          />
          <KpiCard
            label="Ticket promedio"
            value={money(revenue.data.average_ticket_amount)}
            hint={`${revenue.data.orders_count} comanda${revenue.data.orders_count === 1 ? "" : "s"}`}
          />
          <KpiCard label="Food cost" value={money(revenue.data.food_cost_amount)} />
        </section>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">Mix de medios de pago</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {mix.data && mix.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Medio</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Operaciones</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mix.data.map((r) => (
                  <TableRow key={`${r.method}-${r.direction}`}>
                    <TableCell className="font-medium">{methodLabel(r.method)}</TableCell>
                    <TableCell>
                      <Badge variant={r.direction === "INFLOW" ? "default" : "secondary"}>
                        {directionLabel(r.direction)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{r.count}</TableCell>
                    <TableCell className="text-right tabular-nums">{money(r.amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-8 text-center text-sm text-muted-foreground">
              Sin pagos en el período.
            </p>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">Productos más vendidos</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {products.data && products.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead className="text-right">Unidades</TableHead>
                  <TableHead className="text-right">Ventas</TableHead>
                  <TableHead className="text-right">Food cost</TableHead>
                  <TableHead className="text-right">Margen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.data.map((r) => (
                  <TableRow key={r.product_id}>
                    <TableCell className="font-medium">{r.product_name}</TableCell>
                    <TableCell className="text-right tabular-nums">{r.units_sold}</TableCell>
                    <TableCell className="text-right tabular-nums">{money(r.sales_amount)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {money(r.food_cost_amount)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      <span className={r.margin_amount < 0 ? "text-destructive" : undefined}>
                        {money(r.margin_amount)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-8 text-center text-sm text-muted-foreground">
              Sin ventas en el período.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

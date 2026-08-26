import { useState } from "react"
import { useTranslation } from "react-i18next"

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
        className={`text-lg font-semibold tabular-nums sm:text-xl ${negative ? "text-destructive" : "text-foreground"}`}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  )
}

export function AnalyticsPage() {
  const { t } = useTranslation()
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
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("analytics.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            {t("analytics.description")}
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("analytics.dateFrom")}
            <Input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("analytics.dateTo")}
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
          <KpiCard label={t("analytics.kpis.sales")} value={money(revenue.data.sales_amount)} />
          <KpiCard label={t("analytics.kpis.collected")} value={money(revenue.data.collected_amount)} />
          <KpiCard label={t("analytics.kpis.expenses")} value={money(revenue.data.expense_amount)} />
          <KpiCard
            label={t("analytics.kpis.grossMargin")}
            value={money(revenue.data.gross_margin_amount)}
            hint={t("analytics.kpis.grossMarginHint")}
            negative={revenue.data.gross_margin_amount < 0}
          />
          <KpiCard
            label={t("analytics.kpis.averageTicket")}
            value={money(revenue.data.average_ticket_amount)}
            hint={t("analytics.ordersCount", { count: revenue.data.orders_count })}
          />
          <KpiCard label={t("analytics.kpis.foodCost")} value={money(revenue.data.food_cost_amount)} />
        </section>
      ) : null}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">{t("analytics.paymentMix.title")}</h2>
        <p className="-mt-1 text-xs text-muted-foreground">
          {t("analytics.paymentMix.hint")}
        </p>
        <div className="overflow-hidden rounded-xl border border-border">
          {mix.data && mix.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("analytics.paymentMix.method")}</TableHead>
                  <TableHead>{t("analytics.paymentMix.type")}</TableHead>
                  <TableHead className="text-right">{t("analytics.paymentMix.operations")}</TableHead>
                  <TableHead className="text-right">{t("analytics.paymentMix.amount")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mix.data.map((r) => (
                  <TableRow key={`${r.method}-${r.direction}`}>
                    <TableCell className="font-medium">{t(`analytics.methodLabels.${r.method}`)}</TableCell>
                    <TableCell>
                      <Badge variant={r.direction === "INFLOW" ? "default" : "secondary"}>
                        {t(`analytics.directionLabels.${r.direction}`)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{r.count}</TableCell>
                    <TableCell className="text-right tabular-nums">{money(r.amount)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="bg-black/[0.06] p-8 text-center text-sm font-medium text-muted-foreground dark:bg-white/[0.05]">
              {t("analytics.paymentMix.empty")}
            </p>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-foreground">{t("analytics.topProducts.title")}</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          {products.data && products.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("analytics.topProducts.product")}</TableHead>
                  <TableHead className="text-right">{t("analytics.topProducts.units")}</TableHead>
                  <TableHead className="text-right">{t("analytics.topProducts.sales")}</TableHead>
                  <TableHead className="text-right">{t("analytics.topProducts.foodCost")}</TableHead>
                  <TableHead className="text-right">{t("analytics.topProducts.margin")}</TableHead>
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
            <p className="bg-black/[0.06] p-8 text-center text-sm font-medium text-muted-foreground dark:bg-white/[0.05]">
              {t("analytics.topProducts.empty")}
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

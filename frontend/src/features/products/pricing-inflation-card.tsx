import { useState } from "react"
import { toast } from "sonner"
import { useTranslation } from "react-i18next"

import { apiErrorText } from "@/api/translate-error"
import type { PricingRowDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  usePricingInsights,
  useProductPriceHistory,
  useUpdateProductPrice,
} from "@/hooks/use-products"
import { bpsToPct, pricingSummary } from "@/features/products/pricing"
import { formatMoney } from "@/lib/money"

// Precios vs inflación (Productos v2 Tanda B): a cuánto "debería estar" cada precio
// según la inflación mensual estimada, y un editor con el histórico real por plato.
export function PricingInflationCard() {
  const { t } = useTranslation()
  const insights = usePricingInsights()

  if (insights.isPending) {
    return (
      <GlassCard className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </GlassCard>
    )
  }
  if (!insights.data) {
    return (
      <GlassCard className="p-6 text-sm text-muted-foreground">
        {t("products.pricing.computeError")}
      </GlassCard>
    )
  }

  const { currency, configured, monthly_inflation_bps, rows } = insights.data

  if (!configured) {
    return (
      <GlassCard className="flex flex-col gap-2 p-6">
        <h2 className="text-base font-semibold text-foreground">{t("products.pricing.title")}</h2>
        <p className="text-sm text-muted-foreground">
          {t("products.pricing.unconfiguredPre")}
          <span className="font-medium">{t("products.pricing.unconfiguredBold")}</span>
          {t("products.pricing.unconfiguredPost")}
        </p>
      </GlassCard>
    )
  }

  const { laggingCount, worst } = pricingSummary(rows)
  const lagging = rows.filter((r) => r.lagging)

  return (
    <GlassCard className="flex flex-col gap-4 p-6">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-semibold text-foreground">{t("products.pricing.title")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("products.pricing.inflationLine", { pct: bpsToPct(monthly_inflation_bps) })}
          </p>
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
          {laggingCount === 0
            ? t("products.pricing.allCurrent")
            : t("products.pricing.laggingBadge", { count: laggingCount })}
        </span>
      </header>

      {laggingCount === 0 ? (
        <p className="text-sm text-muted-foreground">
          {t("products.pricing.noneLagging")}
        </p>
      ) : (
        <>
          {worst ? (
            <p className="text-sm text-foreground">
              {t("products.pricing.worstPre")}
              <span className="font-medium">{worst.product_name}</span>
              {t("products.pricing.worstMid", {
                price: formatMoney(worst.current_price_amount, currency),
              })}
              <span className="font-medium">
                {formatMoney(worst.suggested_price_amount, currency)}
              </span>
              {t("products.pricing.worstSuffix", { gap: bpsToPct(worst.gap_bps) })}
            </p>
          ) : null}
          <ul className="flex flex-col divide-y divide-border/60">
            {lagging.map((row) => (
              <PricingRowItem key={row.product_id} row={row} currency={currency} />
            ))}
          </ul>
        </>
      )}
    </GlassCard>
  )
}

function PricingRowItem({ row, currency }: { row: PricingRowDTO; currency: string }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  return (
    <li className="py-3">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{row.product_name}</p>
          <p className="text-xs text-muted-foreground">
            {t("products.pricing.daysSinceChange", { count: row.days_since_change })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right text-sm tabular-nums">
            <span className="text-muted-foreground line-through">
              {formatMoney(row.current_price_amount, currency)}
            </span>{" "}
            <span className="font-semibold text-foreground">
              {formatMoney(row.suggested_price_amount, currency)}
            </span>
            <span className="ml-1 text-xs font-medium text-amber-600 dark:text-amber-400">
              +{bpsToPct(row.gap_bps)}
            </span>
          </div>
          <Button variant="outline" size="sm" onClick={() => setOpen((v) => !v)}>
            {open ? t("products.actions.close") : t("products.actions.adjust")}
          </Button>
        </div>
      </div>
      {open ? <PriceEditor row={row} currency={currency} onDone={() => setOpen(false)} /> : null}
    </li>
  )
}

function PriceEditor({
  row,
  currency,
  onDone,
}: {
  row: PricingRowDTO
  currency: string
  onDone: () => void
}) {
  const { t } = useTranslation()
  const history = useProductPriceHistory(row.product_id)
  const update = useUpdateProductPrice()
  // Prefill con el precio sugerido (en la moneda visible, no en minor units).
  const [price, setPrice] = useState(() => String(row.suggested_price_amount / 100))

  const apply = () => {
    const amount = Math.round(Number(price) * 100)
    if (!Number.isFinite(amount) || amount < 0) {
      toast.error(t("products.pricing.invalidPrice"))
      return
    }
    update.mutate(
      { productId: row.product_id, priceAmount: amount },
      {
        onSuccess: () => {
          toast.success(t("products.pricing.priceUpdated"))
          onDone()
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("products.pricing.updateError"))),
      }
    )
  }

  return (
    <div className="mt-3 flex flex-col gap-3 rounded-xl border border-border/60 bg-background/40 p-3">
      <div className="flex items-end gap-2">
        <label className="flex flex-1 flex-col gap-1 text-xs text-muted-foreground">
          {t("products.pricing.newPriceLabel", { currency })}
          <Input
            type="number"
            min={0}
            step="0.01"
            inputMode="decimal"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </label>
        <Button onClick={apply} disabled={update.isPending}>
          {update.isPending ? t("products.actions.saving") : t("products.actions.apply")}
        </Button>
      </div>
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          {t("products.pricing.priceHistory")}
        </p>
        {history.isPending ? (
          <Spinner className="size-4 text-muted-foreground" />
        ) : history.data && history.data.changes.length > 0 ? (
          <ul className="flex flex-col gap-1 text-xs tabular-nums text-muted-foreground">
            {[...history.data.changes].reverse().map((c, i) => (
              <li key={i} className="flex justify-between gap-2">
                <span>{new Date(c.changed_at).toLocaleDateString("es-AR")}</span>
                <span>
                  {c.old_price_amount != null
                    ? `${formatMoney(c.old_price_amount, currency)} → `
                    : t("products.pricing.initialPrice")}
                  <span className="font-medium text-foreground">
                    {formatMoney(c.new_price_amount, currency)}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">{t("products.pricing.noChanges")}</p>
        )}
      </div>
    </div>
  )
}

import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
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
        No pudimos calcular los precios vs inflación.
      </GlassCard>
    )
  }

  const { currency, configured, monthly_inflation_bps, rows } = insights.data

  if (!configured) {
    return (
      <GlassCard className="flex flex-col gap-2 p-6">
        <h2 className="text-base font-semibold text-foreground">Precios vs inflación</h2>
        <p className="text-sm text-muted-foreground">
          Cargá tu <span className="font-medium">inflación mensual estimada</span> en el
          Asesor (Finanzas → Configurar costos) para ver a cuánto debería estar cada
          precio y qué platos quedaron atrás.
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
          <h2 className="text-base font-semibold text-foreground">Precios vs inflación</h2>
          <p className="text-sm text-muted-foreground">
            Inflación mensual estimada: {bpsToPct(monthly_inflation_bps)} · las
            sugerencias se ajustan solas con los días desde el último cambio.
          </p>
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
          {laggingCount === 0
            ? "Todo al día"
            : `${laggingCount} ${laggingCount === 1 ? "precio quedó" : "precios quedaron"} atrás`}
        </span>
      </header>

      {laggingCount === 0 ? (
        <p className="text-sm text-muted-foreground">
          Ningún precio quedó rezagado más de un 5% frente a la inflación. 🎉
        </p>
      ) : (
        <>
          {worst ? (
            <p className="text-sm text-foreground">
              El más rezagado es <span className="font-medium">{worst.product_name}</span>
              : está en {formatMoney(worst.current_price_amount, currency)} y debería estar
              cerca de{" "}
              <span className="font-medium">
                {formatMoney(worst.suggested_price_amount, currency)}
              </span>{" "}
              ({bpsToPct(worst.gap_bps)} por debajo).
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
  const [open, setOpen] = useState(false)
  return (
    <li className="py-3">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{row.product_name}</p>
          <p className="text-xs text-muted-foreground">
            Sin cambios hace {row.days_since_change}{" "}
            {row.days_since_change === 1 ? "día" : "días"}
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
            {open ? "Cerrar" : "Ajustar"}
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
  const history = useProductPriceHistory(row.product_id)
  const update = useUpdateProductPrice()
  // Prefill con el precio sugerido (en la moneda visible, no en minor units).
  const [price, setPrice] = useState(() => String(row.suggested_price_amount / 100))

  const apply = () => {
    const amount = Math.round(Number(price) * 100)
    if (!Number.isFinite(amount) || amount < 0) {
      toast.error("Ingresá un precio válido.")
      return
    }
    update.mutate(
      { productId: row.product_id, priceAmount: amount },
      {
        onSuccess: () => {
          toast.success("Precio actualizado.")
          onDone()
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos actualizar el precio."),
      }
    )
  }

  return (
    <div className="mt-3 flex flex-col gap-3 rounded-xl border border-border/60 bg-background/40 p-3">
      <div className="flex items-end gap-2">
        <label className="flex flex-1 flex-col gap-1 text-xs text-muted-foreground">
          Nuevo precio ({currency})
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
          {update.isPending ? "Guardando…" : "Aplicar"}
        </Button>
      </div>
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          Histórico real de precios
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
                    : "Precio inicial: "}
                  <span className="font-medium text-foreground">
                    {formatMoney(c.new_price_amount, currency)}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">Sin cambios registrados todavía.</p>
        )}
      </div>
    </div>
  )
}

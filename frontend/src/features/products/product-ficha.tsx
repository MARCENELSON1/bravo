import { useMemo, useState } from "react"

import type { ProductDTO } from "@/api/types-operations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import { costSeriesByDay, ingredientCostAlert } from "@/features/products/ficha-logic"
import { useProductDetail } from "@/hooks/use-finance"
import {
  useFoodCost,
  useIngredientCostHistory,
  useIngredients,
  usePreparations,
  useRecipe,
} from "@/hooks/use-inventory"
import { type RangeWindow } from "@/lib/finance-range"
import { formatBps, formatQty, UNIT_LABELS } from "@/lib/inventory"
import { formatMoney } from "@/lib/money"

// Ficha del producto (Fase 7): drawer de composición sobre datos ya existentes.
// Responde "por qué cambió el costo del plato y qué insumo lo movió". Precios vive
// aparte en la página; acá el foco es costo / receta / evolución / insumos.

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null
  const w = 180
  const h = 40
  const pad = 3
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const points = values
    .map((v, i) => {
      const x = pad + (i / (values.length - 1)) * (w - 2 * pad)
      const y = h - pad - ((v - min) / range) * (h - 2 * pad)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")
  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      className="text-primary"
      role="img"
      aria-label="Evolución del costo del plato"
    >
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} />
    </svg>
  )
}

function IngredientAlertRow({ ingredientId, name }: { ingredientId: string; name: string }) {
  const history = useIngredientCostHistory(ingredientId)
  const [now] = useState(() => Date.now()) // estable durante el montaje del drawer
  const alert = ingredientCostAlert(history.data ?? [], now)
  return (
    <div className="flex items-center justify-between gap-2 text-sm">
      <span className="text-foreground">{name}</span>
      <div className="flex items-center gap-1">
        {alert.changePct !== null && alert.changePct !== 0 ? (
          <Badge variant={alert.changePct > 0 ? "destructive" : "default"}>
            {alert.changePct > 0 ? "▲" : "▼"} {Math.abs(alert.changePct)}%
          </Badge>
        ) : null}
        {alert.stale ? (
          <Badge variant="secondary">compra hace {alert.daysSinceLast}d</Badge>
        ) : null}
        {history.data && history.data.length === 0 ? (
          <span className="text-xs text-muted-foreground">sin compras</span>
        ) : null}
      </div>
    </div>
  )
}

function FichaBody({ product, period }: { product: ProductDTO; period: RangeWindow }) {
  const foodCost = useFoodCost()
  const recipe = useRecipe(product.id)
  const ingredients = useIngredients()
  const preparations = usePreparations()
  const detail = useProductDetail(product.id, period)

  const row = foodCost.data?.rows.find((r) => r.product_id === product.id)
  const currency = row?.currency ?? product.currency ?? "ARS"
  const series = useMemo(
    () => costSeriesByDay(detail.data?.lines ?? []),
    [detail.data]
  )
  const ingById = useMemo(
    () => new Map((ingredients.data ?? []).map((i) => [i.id, i])),
    [ingredients.data]
  )
  const prepById = useMemo(
    () => new Map((preparations.data ?? []).map((p) => [p.id, p])),
    [preparations.data]
  )

  if (recipe.isPending || foodCost.isPending) {
    return (
      <div className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </div>
    )
  }

  const items = recipe.data?.items ?? []
  const ingredientItems = items.filter((i) => i.ingredient_id)

  return (
    <div className="flex flex-col gap-5 px-4 pb-6">
      {/* Resumen */}
      <section className="grid grid-cols-2 gap-3">
        <Metric label="Precio" value={formatMoney(product.price_amount, currency)} />
        <Metric
          label="Costo (bruto)"
          value={row ? formatMoney(row.food_cost_amount, currency) : "—"}
        />
        <Metric
          label="Te deja (neto de IVA)"
          value={row ? formatMoney(row.margin_amount, currency) : "—"}
          strong
        />
        <Metric
          label="Food cost %"
          value={row ? formatBps(row.food_cost_ratio_bps) : "—"}
        />
      </section>

      {/* Fase 3: estado de confirmación del costo */}
      {row ? (
        <div className="flex items-center gap-2">
          <Badge variant={row.cost_confirmed ? "default" : "secondary"}>
            {row.cost_confirmed ? "Costo confirmado" : "Costo estimado"}
          </Badge>
          {!row.cost_confirmed ? (
            <span className="text-xs text-muted-foreground">
              {Math.round(row.coverage_bps / 100)}% del costo respaldado por compras —
              cargá las compras que faltan para confirmarlo.
            </span>
          ) : null}
        </div>
      ) : null}

      <Separator />

      {/* Receta */}
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Receta</h3>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Este producto no tiene receta.</p>
        ) : (
          <ul className="flex flex-col gap-1 text-sm">
            {items.map((item, i) => {
              const ing = item.ingredient_id ? ingById.get(item.ingredient_id) : undefined
              const prep = item.preparation_id ? prepById.get(item.preparation_id) : undefined
              const name = ing?.name ?? (prep ? `Preparación: ${prep.name}` : "—")
              const qtyLabel = ing
                ? formatQty(item.qty, ing.recipe_unit ?? ing.unit)
                : `${(item.qty / 1000).toLocaleString("es-AR", { maximumFractionDigits: 3 })} ${
                    prep ? UNIT_LABELS.UNIT : ""
                  }`
              return (
                <li key={i} className="flex items-center justify-between gap-2">
                  <span className="text-foreground">{name}</span>
                  <span className="tabular-nums text-muted-foreground">{qtyLabel}</span>
                </li>
              )
            })}
          </ul>
        )}
        {items.length > 0 && recipe.data?.version ? (
          <p className="text-xs text-muted-foreground">Versión de receta: v{recipe.data.version}</p>
        ) : null}
      </section>

      <Separator />

      {/* Costo del plato en el tiempo */}
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Costo del plato en el tiempo</h3>
        {detail.isPending ? (
          <Spinner className="size-4 text-muted-foreground" />
        ) : series.length >= 2 ? (
          <div className="flex items-center gap-3">
            <Sparkline values={series.map((p) => p.unitCost)} />
            <div className="text-xs text-muted-foreground">
              <div>{formatMoney(series[0].unitCost, currency)}</div>
              <div className="font-medium text-foreground">
                {formatMoney(series[series.length - 1].unitCost, currency)}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Sin suficientes ventas en el período para graficar. El costo se congela por
            venta al cobrar.
          </p>
        )}
      </section>

      <Separator />

      {/* Insumos + alertas */}
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Insumos</h3>
        {ingredientItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin insumos directos.</p>
        ) : (
          <div className="flex flex-col gap-1.5">
            {ingredientItems.map((item, i) => {
              const ing = ingById.get(item.ingredient_id as string)
              if (!ing) return null
              return (
                <IngredientAlertRow key={i} ingredientId={ing.id} name={ing.name} />
              )
            })}
            <p className="mt-1 text-xs text-muted-foreground">
              ▲ = subió desde la primera compra cargada. "compra hace Nd" = costo de
              reposición desactualizado (última compra hace más de 60 días).
            </p>
          </div>
        )}
      </section>
    </div>
  )
}

function Metric({
  label,
  value,
  strong,
}: {
  label: string
  value: string
  strong?: boolean
}) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={strong ? "font-semibold tabular-nums" : "tabular-nums"}>{value}</span>
    </div>
  )
}

export function ProductFicha({
  product,
  period,
}: {
  product: ProductDTO
  period: RangeWindow
}) {
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          Ficha
        </Button>
      </SheetTrigger>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Ficha de {product.name}</SheetTitle>
          <SheetDescription>
            Costo, receta, evolución del costo e insumos del plato.
          </SheetDescription>
        </SheetHeader>
        {open ? <FichaBody product={product} period={period} /> : null}
      </SheetContent>
    </Sheet>
  )
}

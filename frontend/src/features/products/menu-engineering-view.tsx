import { useMemo } from "react"
import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import type { TFunction } from "i18next"

import { Badge } from "@/components/ui/badge"
import { GlassCard } from "@/components/ui/glass-card"
import { coverageGate } from "@/features/products/coverage-gate"
import {
  classifyMenu,
  confirmedMargin,
  topEarners,
  type ClassifiedProduct,
  type MenuCategory,
} from "@/features/products/menu-engineering"
import { useProductPerformance } from "@/hooks/use-analytics"
import { useFoodCost } from "@/hooks/use-inventory"
import { useProducts } from "@/hooks/use-products"
import { type RangeWindow } from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

// Piso mínimo de unidades para clasificar, escalado por el largo del período
// (base ~10/mes, mínimo 3). Por debajo → SIN DATOS.
function minUnitsForPeriod(period: RangeWindow): number {
  const days = Math.max(
    1,
    Math.round((Date.parse(period.to) - Date.parse(period.from)) / 86_400_000),
  )
  return Math.max(3, Math.round((10 * days) / 30))
}

// Color del punto por categoría. Las etiquetas (label/sub) viven en el diccionario
// bajo `products.menuCategories.<cat>` — la CLAVE es el enum de dominio.
const CATEGORY_DOT: Record<MenuCategory, string> = {
  funciona: "bg-success",
  oportunidad: "bg-violet-500",
  estable: "bg-sky-500",
  revisar: "bg-warning",
  no_vendido: "bg-neutral-500",
  sin_datos: "bg-neutral-400",
}
const ORDER: MenuCategory[] = [
  "funciona",
  "oportunidad",
  "estable",
  "revisar",
  "no_vendido",
  "sin_datos",
]

export function MenuEngineering({ period }: { period: RangeWindow }) {
  const { t } = useTranslation()
  // limit alto para no truncar la clasificación (el endpoint corta en le=1000).
  const query = useMemo(() => ({ from: period.from, to: period.to, limit: 1000 }), [period])
  const perf = useProductPerformance(query)
  const foodCost = useFoodCost()
  const productsList = useProducts()
  // Fase 4 (T3.1): categoría de carta por producto, para comparar dentro de la
  // categoría. Sin catálogo aún → undefined → comparación global (paridad).
  const categoryById = useMemo(
    () =>
      productsList.data
        ? new Map(productsList.data.map((p) => [p.id, p.category]))
        : undefined,
    [productsList.data],
  )
  const minUnits = useMemo(() => minUnitsForPeriod(period), [period])
  // Fase 3: platos con costo estimado (no entran a las conclusiones de plata). Sin
  // el food cost cargado → undefined → paridad (todo confirmado, no grisa nada).
  const estimatedIds = useMemo(
    () =>
      foodCost.data
        ? new Set(
            foodCost.data.rows.filter((r) => !r.cost_confirmed).map((r) => r.product_id),
          )
        : undefined,
    [foodCost.data],
  )
  // Guarda Insumos: recetas con ratio food-cost implausible (fuera de 5–95%) → no
  // entran a las conclusiones de plata (como los estimados).
  const insaneIds = useMemo(
    () =>
      foodCost.data
        ? new Set(
            foodCost.data.rows.filter((r) => !r.ratio_sane).map((r) => r.product_id),
          )
        : undefined,
    [foodCost.data],
  )
  const products = useMemo(
    () => classifyMenu(perf.data ?? [], estimatedIds, insaneIds, categoryById, minUnits),
    [perf.data, estimatedIds, insaneIds, categoryById, minUnits],
  )
  const currency = perf.data?.[0]?.currency ?? "ARS"

  if (perf.isPending) {
    return <p className="text-sm text-muted-foreground">{t("products.menu.analyzing")}</p>
  }
  if (products.length === 0) {
    return (
      <GlassCard className="p-6 text-sm text-muted-foreground">
        {t("products.menu.noSales")}
      </GlassCard>
    )
  }

  const byCat = (c: MenuCategory) => products.filter((p) => p.category === c)
  const top = topEarners(products)
  const money = (n: number) => formatMoney(n, currency)
  // Fase 6: gate del hero. Bajo el umbral de cobertura ocultamos las conclusiones
  // de plata (top-earners, "Te dejan $X", "te dejaron $X") — nunca un total inflado
  // por costos estimados. Sin food cost cargado → open (paridad).
  const gate = coverageGate(foodCost.data)

  return (
    <div className="flex flex-col gap-4">
      {/* Hero — resumen de la carta */}
      <GlassCard className="p-6">
        <h2 className="text-base font-semibold text-foreground">{t("products.menu.heroTitle")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("products.menu.heroSummary", {
            total: products.length,
            funciona: byCat("funciona").length,
            oportunidad: byCat("oportunidad").length,
            revisar: byCat("revisar").length,
            noVendido: byCat("no_vendido").length,
          })}
        </p>
        {byCat("sin_datos").length > 0 ? (
          <p className="mt-1 text-xs text-muted-foreground">
            {t("products.menu.unclassified", { count: byCat("sin_datos").length })}
          </p>
        ) : null}
        {gate.open ? (
          <>
            <p className="mt-2 text-sm text-foreground">
              {t("products.menu.leftYou")}{" "}
              <span className="font-semibold tabular-nums">
                {money(confirmedMargin(products))}
              </span>
              .
            </p>
            {foodCost.data && foodCost.data.total_count > 0 ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {t("products.menu.confirmedCount", {
                  confirmed: foodCost.data.confirmed_count,
                  total: foodCost.data.total_count,
                })}
              </p>
            ) : null}
          </>
        ) : (
          <div className="mt-2">
            <p className="text-sm text-foreground">
              {t("products.menu.gateClosedPrefix")}{" "}
              <span className="font-semibold tabular-nums">{gate.missing}</span>{" "}
              {t("products.menu.gateClosedSuffix", {
                confirmed: gate.confirmed,
                total: gate.total,
              })}
            </p>
            <Link
              to="/app/stock"
              className="mt-2 inline-flex text-sm font-medium text-primary hover:underline"
            >
              {t("products.menu.loadPurchases")}
            </Link>
          </div>
        )}
      </GlassCard>

      {/* 5 categorías de acción */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ORDER.map((cat) => {
          const items = byCat(cat)
          const totalMargin = confirmedMargin(items) // Fase 3: solo confirmados
          return (
            <GlassCard key={cat} className="flex flex-col gap-2 p-5">
              <div className="flex items-center gap-2">
                <span className={`size-2.5 rounded-full ${CATEGORY_DOT[cat]}`} />
                <span className="text-sm font-semibold text-foreground">
                  {t(`products.menuCategories.${cat}.label`)}
                </span>
                <span className="ml-auto text-sm tabular-nums text-muted-foreground">
                  {items.length}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {t(`products.menuCategories.${cat}.sub`)}
              </p>
              {gate.open && cat !== "no_vendido" && cat !== "sin_datos" ? (
                <p className="text-sm tabular-nums text-foreground">
                  {t("products.menu.cardLeaves", { amount: money(totalMargin) })}
                </p>
              ) : null}
              <ul className="mt-1 flex flex-col gap-0.5 text-xs text-muted-foreground">
                {items.slice(0, 3).map((p) => (
                  <li key={p.id} className="flex justify-between gap-2">
                    <span className="truncate">{p.name}</span>
                    <span className="tabular-nums">{t("products.menu.units", { count: p.units })}</span>
                  </li>
                ))}
              </ul>
            </GlassCard>
          )
        })}
      </section>

      {/* Top 3 que más plata dejan — solo con cobertura suficiente (Fase 6) */}
      {gate.open ? (
        <GlassCard className="p-6">
          <h2 className="mb-3 text-base font-semibold text-foreground">
            {t("products.menu.topTitle")}
          </h2>
          <div className="flex flex-col gap-2">
            {top.map((p, i) => (
              <div key={p.id} className="flex items-baseline justify-between gap-3 text-sm">
                <span className="flex min-w-0 flex-1 items-center gap-2 truncate">
                  <span className="inline-flex size-5 shrink-0 items-center justify-center rounded-md border border-border text-[11px] font-semibold tabular-nums text-muted-foreground">
                    {i + 1}
                  </span>
                  <span className="truncate">{p.name}</span>
                </span>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  {t("products.menu.units", { count: p.units })} ·{" "}
                  <span className="font-semibold text-foreground">{money(p.margin)}</span>
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      ) : null}

      {/* Tabla de detalle */}
      <GlassCard className="p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">{t("products.menu.detail.title")}</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b text-xs font-medium text-muted-foreground">
                <th className="py-1 text-left">{t("products.menu.detail.product")}</th>
                <th className="py-1 text-right">{t("products.menu.detail.price")}</th>
                <th className="py-1 text-right">{t("products.menu.detail.cost")}</th>
                <th className="py-1 text-right">{t("products.menu.detail.leaves")}</th>
                <th className="py-1 text-right">{t("products.menu.detail.sold")}</th>
                <th className="py-1 text-right">{t("products.menu.detail.status")}</th>
              </tr>
            </thead>
            <tbody>
              {[...products]
                .sort((a, b) => b.margin - a.margin)
                .map((p) => (
                  <MenuRow key={p.id} p={p} money={money} t={t} />
                ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}

function MenuRow({
  p,
  money,
  t,
}: {
  p: ClassifiedProduct
  money: (n: number) => string
  t: TFunction
}) {
  return (
    <tr className="border-b border-border/60 last:border-b-0">
      <td className="py-1.5 pr-2">{p.name}</td>
      <td className="py-1.5 text-right tabular-nums">{money(p.unitPrice)}</td>
      <td className="py-1.5 text-right tabular-nums text-muted-foreground">{money(p.unitCost)}</td>
      <td
        className={`py-1.5 text-right tabular-nums ${
          p.costConfirmed && p.ratioSane ? "font-medium" : "text-muted-foreground"
        }`}
      >
        {money(p.margin)}
      </td>
      <td className="py-1.5 text-right tabular-nums">{p.units}</td>
      <td className="py-1.5">
        <span className="flex items-center justify-end gap-1.5 text-xs">
          {!p.ratioSane ? (
            <Badge variant="outline" className="text-xs font-normal text-warning">
              {t("products.badges.incompleteRecipe")}
            </Badge>
          ) : null}
          {!p.costConfirmed ? (
            <Badge variant="secondary" className="text-xs font-normal">
              {t("products.badges.estimated")}
            </Badge>
          ) : null}
          <span className={`size-2 rounded-full ${CATEGORY_DOT[p.category]}`} />
          {t(`products.menuCategories.${p.category}.label`)}
        </span>
      </td>
    </tr>
  )
}

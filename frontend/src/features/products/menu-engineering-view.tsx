import { useMemo } from "react"
import { Link } from "react-router-dom"

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
import { type RangeWindow } from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

const CATEGORY_META: Record<
  MenuCategory,
  { label: string; sub: string; dot: string }
> = {
  funciona: { label: "Funciona", sub: "Tu motor — mantenelos", dot: "bg-emerald-500" },
  oportunidad: { label: "Oportunidades", sub: "Empujá estos", dot: "bg-violet-500" },
  estable: { label: "Estables", sub: "Tu base — no los toques", dot: "bg-sky-500" },
  revisar: { label: "Revisar", sub: "Están mal, decidí", dot: "bg-orange-500" },
  no_vendido: { label: "No vendidos", sub: "Nadie los pidió", dot: "bg-neutral-500" },
}
const ORDER: MenuCategory[] = ["funciona", "oportunidad", "estable", "revisar", "no_vendido"]

export function MenuEngineering({ period }: { period: RangeWindow }) {
  // limit alto para no truncar la clasificación (el endpoint corta en le=1000).
  const query = useMemo(() => ({ from: period.from, to: period.to, limit: 1000 }), [period])
  const perf = useProductPerformance(query)
  const foodCost = useFoodCost()
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
    () => classifyMenu(perf.data ?? [], estimatedIds, insaneIds),
    [perf.data, estimatedIds, insaneIds],
  )
  const currency = perf.data?.[0]?.currency ?? "ARS"

  if (perf.isPending) {
    return <p className="text-sm text-muted-foreground">Analizando tu carta…</p>
  }
  if (products.length === 0) {
    return (
      <GlassCard className="p-6 text-sm text-muted-foreground">
        Todavía no hay ventas de productos en el período elegido para analizar la carta.
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
        <h2 className="text-base font-semibold text-foreground">Tu carta</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          De tus {products.length} platos, {byCat("funciona").length} son estrellas,{" "}
          {byCat("oportunidad").length} son oportunidades, {byCat("revisar").length} te están
          costando margen y {byCat("no_vendido").length} no se vendieron.
        </p>
        {gate.open ? (
          <>
            <p className="mt-2 text-sm text-foreground">
              En este período tu carta te dejó{" "}
              <span className="font-semibold tabular-nums">
                {money(confirmedMargin(products))}
              </span>
              .
            </p>
            {foodCost.data && foodCost.data.total_count > 0 ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {foodCost.data.confirmed_count} de {foodCost.data.total_count} platos con
                costo confirmado. Los de costo estimado no suman a la plata de arriba —
                cargá sus compras para confirmarlos.
              </p>
            ) : null}
          </>
        ) : (
          <div className="mt-2">
            <p className="text-sm text-foreground">
              Todavía no podemos decirte cuánto te dejó tu carta — te faltan{" "}
              <span className="font-semibold tabular-nums">{gate.missing}</span> platos con
              costo confirmado (vas {gate.confirmed} de {gate.total}).
            </p>
            <Link
              to="/app/stock"
              className="mt-2 inline-flex text-sm font-medium text-primary hover:underline"
            >
              Cargar compras →
            </Link>
          </div>
        )}
      </GlassCard>

      {/* 5 categorías de acción */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ORDER.map((cat) => {
          const items = byCat(cat)
          const meta = CATEGORY_META[cat]
          const totalMargin = confirmedMargin(items) // Fase 3: solo confirmados
          return (
            <GlassCard key={cat} className="flex flex-col gap-2 p-5">
              <div className="flex items-center gap-2">
                <span className={`size-2.5 rounded-full ${meta.dot}`} />
                <span className="text-sm font-semibold text-foreground">{meta.label}</span>
                <span className="ml-auto text-sm tabular-nums text-muted-foreground">
                  {items.length}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{meta.sub}</p>
              {gate.open && cat !== "no_vendido" ? (
                <p className="text-sm tabular-nums text-foreground">
                  Te dejan {money(totalMargin)}
                </p>
              ) : null}
              <ul className="mt-1 flex flex-col gap-0.5 text-xs text-muted-foreground">
                {items.slice(0, 3).map((p) => (
                  <li key={p.id} className="flex justify-between gap-2">
                    <span className="truncate">{p.name}</span>
                    <span className="tabular-nums">{p.units} uds</span>
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
            Los 3 platos que más plata te dejan
          </h2>
          <div className="flex flex-col gap-2">
            {top.map((p, i) => (
              <div key={p.id} className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 flex-1 truncate">
                  {["🥇", "🥈", "🥉"][i]} {p.name}
                </span>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  {p.units} uds ·{" "}
                  <span className="font-semibold text-foreground">{money(p.margin)}</span>
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      ) : null}

      {/* Tabla de detalle */}
      <GlassCard className="p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">Detalle de productos</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b text-xs font-medium text-muted-foreground">
                <th className="py-1 text-left">Producto</th>
                <th className="py-1 text-right">Precio</th>
                <th className="py-1 text-right">Costo</th>
                <th className="py-1 text-right">Te deja</th>
                <th className="py-1 text-right">Vendidos</th>
                <th className="py-1 text-right">Estado</th>
              </tr>
            </thead>
            <tbody>
              {[...products]
                .sort((a, b) => b.margin - a.margin)
                .map((p) => (
                  <MenuRow key={p.id} p={p} money={money} />
                ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}

function MenuRow({ p, money }: { p: ClassifiedProduct; money: (n: number) => string }) {
  const meta = CATEGORY_META[p.category]
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
            <Badge variant="outline" className="text-xs font-normal text-orange-600">
              receta incompleta
            </Badge>
          ) : null}
          {!p.costConfirmed ? (
            <Badge variant="secondary" className="text-xs font-normal">
              estimado
            </Badge>
          ) : null}
          <span className={`size-2 rounded-full ${meta.dot}`} />
          {meta.label}
        </span>
      </td>
    </tr>
  )
}

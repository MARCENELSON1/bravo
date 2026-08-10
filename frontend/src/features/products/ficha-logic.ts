import type { IngredientCostPointDTO } from "@/api/types-inventory"
import type { ProductSaleLineDTO } from "@/api/types-operations"

// Lógica pura de la Ficha del producto (Fase 7). Deriva del dato ya congelado
// (sale_facts / cost-history), sin recalcular históricos. Testeable sin backend.

const DAY_MS = 86_400_000
export const STALE_PURCHASE_DAYS = 60

// Serie de costo del plato por día: el food cost congelado por venta dividido por
// las unidades, promediado por día. Solo días con ventas (con food cost). Devuelve
// milésimas de la moneda (centavos), ascendente por día.
export interface PlateCostPoint {
  day: string // YYYY-MM-DD
  unitCost: number
}

export function costSeriesByDay(lines: ProductSaleLineDTO[]): PlateCostPoint[] {
  const byDay = new Map<string, { cost: number; qty: number }>()
  for (const line of lines) {
    if (line.food_cost_amount == null || line.quantity <= 0) continue
    const day = line.occurred_at.slice(0, 10)
    const acc = byDay.get(day) ?? { cost: 0, qty: 0 }
    acc.cost += line.food_cost_amount
    acc.qty += line.quantity
    byDay.set(day, acc)
  }
  return [...byDay.entries()]
    .map(([day, { cost, qty }]) => ({ day, unitCost: Math.round(cost / qty) }))
    .sort((a, b) => a.day.localeCompare(b.day))
}

// Alerta de costo de un insumo desde su histórico de compras (ascendente). El
// cambio % es primera vs última compra; ``stale`` marca que la última compra es
// más vieja que el umbral (el costo de reposición puede estar desactualizado).
export interface IngredientCostAlert {
  changePct: number | null // primera→última compra; null si <2 compras
  lastCost: number | null // última compra (costo de reposición)
  daysSinceLast: number | null // días desde la última compra
  stale: boolean // última compra > STALE_PURCHASE_DAYS
}

export function ingredientCostAlert(
  points: IngredientCostPointDTO[],
  nowMs: number
): IngredientCostAlert {
  if (points.length === 0) {
    return { changePct: null, lastCost: null, daysSinceLast: null, stale: false }
  }
  const first = points[0]
  const last = points[points.length - 1]
  const changePct =
    points.length >= 2 && first.unit_cost_amount > 0
      ? Math.round(
          ((last.unit_cost_amount - first.unit_cost_amount) / first.unit_cost_amount) * 100
        )
      : null
  const lastMs = Date.parse(last.occurred_at)
  const daysSinceLast = Number.isNaN(lastMs)
    ? null
    : Math.floor((nowMs - lastMs) / DAY_MS)
  const stale = daysSinceLast != null && daysSinceLast > STALE_PURCHASE_DAYS
  return { changePct, lastCost: last.unit_cost_amount, daysSinceLast, stale }
}

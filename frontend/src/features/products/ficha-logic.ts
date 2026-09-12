import type { IngredientCostPointDTO } from "@/api/types-inventory"

// Lógica pura de la Ficha del producto (Fase 7). Deriva del dato ya congelado
// (sale_facts / cost-history), sin recalcular históricos. Testeable sin backend.
//
// La serie de costo por día **ya no se arma acá**: la calcula el backend en SQL
// (`ProductDetailDTO.cost_series`). Se mudó al acotar `lines`, porque derivarla
// de un listado con tope le habría comido los días más viejos en silencio.

const DAY_MS = 86_400_000
export const STALE_PURCHASE_DAYS = 60

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

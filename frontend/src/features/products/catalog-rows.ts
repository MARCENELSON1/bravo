// Productos v3 Fase 1 (B6/B7): arma las filas del catálogo cruzando el listado
// de productos con el food cost (costo/margen por plato, de todos los que tienen
// receta) y la performance del período (unidades vendidas). Lógica pura y testeable.

import type { ProductPerformanceRowDTO } from "@/api/types-analytics"
import type { FoodCostRowDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"

export interface CatalogRow {
  product: ProductDTO
  cost: number | null // food_cost_amount (null = sin receta / costo desconocido)
  margin: number | null // "te deja" en minor units (null = sin costo)
  marginBps: number | null // margen sobre precio en bps (7000 = 70%)
  units: number // vendidos en el período
}

export function mergeCatalogRows(
  products: ProductDTO[],
  foodCost: FoodCostRowDTO[],
  performance: ProductPerformanceRowDTO[],
): CatalogRow[] {
  const costById = new Map(foodCost.map((r) => [r.product_id, r]))
  const soldById = new Map(performance.map((r) => [r.product_id, r.units_sold]))
  return products.map((product) => {
    const fc = costById.get(product.id)
    return {
      product,
      cost: fc ? fc.food_cost_amount : null,
      margin: fc ? fc.margin_amount : null,
      // food_cost_ratio_bps = costo/precio; margen sobre precio = 10000 - ratio.
      marginBps: fc ? 10000 - fc.food_cost_ratio_bps : null,
      units: soldById.get(product.id) ?? 0,
    }
  })
}

export type CatalogStatus = "all" | "active" | "inactive"

export interface CatalogFilters {
  q: string
  category: string // "" = todas
  status: CatalogStatus
}

export function filterCatalog(rows: CatalogRow[], filters: CatalogFilters): CatalogRow[] {
  const q = filters.q.trim().toLowerCase()
  return rows.filter((r) => {
    if (q && !r.product.name.toLowerCase().includes(q)) return false
    if (filters.category && (r.product.category ?? "") !== filters.category) return false
    if (filters.status === "active" && !r.product.active) return false
    if (filters.status === "inactive" && r.product.active) return false
    return true
  })
}

export function catalogCategories(products: ProductDTO[]): string[] {
  const set = new Set(
    products.map((p) => p.category).filter((c): c is string => Boolean(c)),
  )
  return [...set].sort()
}

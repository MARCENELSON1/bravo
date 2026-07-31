import type { ProductPerformanceRowDTO } from "@/api/types-analytics"

// Menu engineering (Productos v2 Tanda A): clasifica cada plato en una de 5
// categorías de acción a partir del margen y el volumen que YA calcula el motor
// (GetProductPerformance). Determinista — no inventa nada.

export type MenuCategory = "funciona" | "oportunidad" | "estable" | "revisar" | "no_vendido"

export interface ClassifiedProduct {
  id: string
  name: string
  units: number
  sales: number
  foodCost: number
  margin: number // "te deja" (minor units)
  marginPct: number // 0..1
  unitPrice: number // sales / units (minor units)
  unitCost: number // foodCost / units
  category: MenuCategory
}

// Umbrales (ajustables). El doc toma ~58% como margen sano promedio.
const HIGH_MARGIN = 0.55
const LOW_MARGIN = 0.45

export function classifyMenu(rows: ProductPerformanceRowDTO[]): ClassifiedProduct[] {
  const withUnits = rows.filter((r) => r.units_sold > 0)
  const avgUnits =
    withUnits.length > 0
      ? withUnits.reduce((s, r) => s + r.units_sold, 0) / withUnits.length
      : 0

  return rows.map((r) => {
    const marginPct = r.sales_amount > 0 ? r.margin_amount / r.sales_amount : 0
    const highVolume = r.units_sold >= avgUnits
    let category: MenuCategory
    if (r.units_sold === 0) {
      category = "no_vendido"
    } else if (marginPct < LOW_MARGIN) {
      category = "revisar" // vende pero deja poco (asesino de margen)
    } else if (marginPct >= HIGH_MARGIN && highVolume) {
      category = "funciona"
    } else if (marginPct >= HIGH_MARGIN && !highVolume) {
      category = "oportunidad" // buen margen, poco volumen → empujar
    } else {
      category = "estable" // tu base
    }
    return {
      id: r.product_id,
      name: r.product_name,
      units: r.units_sold,
      sales: r.sales_amount,
      foodCost: r.food_cost_amount,
      margin: r.margin_amount,
      marginPct,
      unitPrice: r.units_sold > 0 ? Math.round(r.sales_amount / r.units_sold) : 0,
      unitCost: r.units_sold > 0 ? Math.round(r.food_cost_amount / r.units_sold) : 0,
      category,
    }
  })
}

// Top 3 platos que más plata dejan (margin desc).
export function topEarners(products: ClassifiedProduct[]): ClassifiedProduct[] {
  return [...products].sort((a, b) => b.margin - a.margin).slice(0, 3)
}

// Asesinos de margen: venden (units>0) pero margen < sano.
export function marginKillers(products: ClassifiedProduct[]): ClassifiedProduct[] {
  return products
    .filter((p) => p.units > 0 && p.marginPct < LOW_MARGIN)
    .sort((a, b) => a.marginPct - b.marginPct)
}

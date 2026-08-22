import type { ProductPerformanceRowDTO } from "@/api/types-analytics"

// Menu engineering (Productos v2 Tanda A): clasifica cada plato en una de 5
// categorías de acción a partir del margen y el volumen que YA calcula el motor
// (GetProductPerformance). Determinista — no inventa nada.

export type MenuCategory =
  | "funciona"
  | "oportunidad"
  | "estable"
  | "revisar"
  | "no_vendido"
  | "sin_datos"

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
  menuCategory: string // categoría de carta normalizada (para agrupar/comparar)
  costConfirmed: boolean // Fase 3: costo respaldado por compras (no entra a la plata si false)
  ratioSane: boolean // Guarda Insumos: ratio plausible; si false no entra a la plata
}

// Umbrales (ajustables). El doc toma ~58% como margen sano promedio.
const HIGH_MARGIN = 0.55
const LOW_MARGIN = 0.45
// Fase 4 (T3.1): categorías de carta con menos productos que esto se colapsan a
// "Otros" — no tiene sentido comparar un plato contra 1-2 vecinos.
const MIN_CATEGORY_SIZE = 4
// Piso mínimo de unidades del período para clasificar (T3.2). Default 10/mes; la
// vista lo escala por el largo del período. Por debajo → SIN DATOS (no inventamos).
const DEFAULT_MIN_UNITS = 10

function normalizedCategory(raw: string | null | undefined): string {
  const c = raw?.trim()
  return c ? c : "Otros"
}

// Fase 4 (T3.1): comparo cada plato contra el promedio de SU categoría de carta
// (un café no compite en volumen con una milanesa). `categoryById` mapea
// product_id → categoría; sin él, todo cae en "Otros" (comparación global, como
// antes). `minUnits` es el piso para clasificar (SIN DATOS por debajo).
export function classifyMenu(
  rows: ProductPerformanceRowDTO[],
  estimatedIds?: Set<string>,
  insaneIds?: Set<string>,
  categoryById?: Map<string, string | null>,
  minUnits: number = DEFAULT_MIN_UNITS,
): ClassifiedProduct[] {
  // Categoría cruda por producto + cuántos productos tiene cada una.
  const rawCat = (id: string) => normalizedCategory(categoryById?.get(id))
  const catCount = new Map<string, number>()
  for (const r of rows) {
    const c = rawCat(r.product_id)
    catCount.set(c, (catCount.get(c) ?? 0) + 1)
  }
  // Categoría de comparación: las chicas (<4) se agrupan en "Otros".
  const compareCat = (id: string) =>
    (catCount.get(rawCat(id)) ?? 0) >= MIN_CATEGORY_SIZE ? rawCat(id) : "Otros"

  // Promedio de unidades por categoría de comparación (solo platos que vendieron).
  const sold = new Map<string, { sum: number; n: number }>()
  for (const r of rows) {
    if (r.units_sold <= 0) continue
    const c = compareCat(r.product_id)
    const acc = sold.get(c) ?? { sum: 0, n: 0 }
    acc.sum += r.units_sold
    acc.n += 1
    sold.set(c, acc)
  }
  const avgUnitsOf = (c: string) => {
    const acc = sold.get(c)
    return acc && acc.n > 0 ? acc.sum / acc.n : 0
  }

  return rows.map((r) => {
    const marginPct = r.sales_amount > 0 ? r.margin_amount / r.sales_amount : 0
    // Fase 3: estimado solo si tiene costo estimado; sin receta → confirmado.
    // Sin estimatedIds → todo confirmado (paridad).
    const costConfirmed = estimatedIds ? !estimatedIds.has(r.product_id) : true
    // Guarda Insumos: fuera de banda (5–95%) → receta incompleta. Sin set → sano.
    const ratioSane = insaneIds ? !insaneIds.has(r.product_id) : true
    const cmp = compareCat(r.product_id)
    const highVolume = r.units_sold >= avgUnitsOf(cmp)
    let category: MenuCategory
    if (r.units_sold === 0) {
      category = "no_vendido"
    } else if (!costConfirmed || !ratioSane || r.units_sold < minUnits) {
      // Sin costo sólido, o con muy pocas ventas → no clasificamos (honestidad).
      category = "sin_datos"
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
      menuCategory: compareCat(r.product_id),
      costConfirmed,
      ratioSane,
    }
  })
}

// ¿Este plato entra a las conclusiones de plata? Solo si su costo está confirmado
// (Fase 3) Y el ratio es plausible (guarda Insumos). Nunca sumamos plata sobre un
// costo estimado ni sobre una receta incompleta (food cost 0%/100%).
function countsInMoney(p: ClassifiedProduct): boolean {
  return p.costConfirmed && p.ratioSane
}

// Top 3 platos que más plata dejan (margin desc). Excluye estimados y recetas
// incompletas — no se rankea plata sobre costos que no son sólidos.
export function topEarners(products: ClassifiedProduct[]): ClassifiedProduct[] {
  return [...products]
    .filter(countsInMoney)
    .sort((a, b) => b.margin - a.margin)
    .slice(0, 3)
}

// Total "te dejan" del período — solo platos con costo confirmado y ratio plausible.
export function confirmedMargin(products: ClassifiedProduct[]): number {
  return products.reduce((s, p) => (countsInMoney(p) ? s + p.margin : s), 0)
}

// Asesinos de margen: venden (units>0) pero margen < sano.
export function marginKillers(products: ClassifiedProduct[]): ClassifiedProduct[] {
  return products
    .filter((p) => p.units > 0 && p.marginPct < LOW_MARGIN)
    .sort((a, b) => a.marginPct - b.marginPct)
}

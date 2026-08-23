// DTOs for the inventory API (stock / suppliers / recipe / food cost).
// Quantities are integers in milésimas of the ingredient's base unit
// (1500 = 1.5 of the unit). Costs/prices are integer minor units (centavos).

export type UnitOfMeasure = "G" | "KG" | "ML" | "L" | "UNIT"

export interface IngredientDTO {
  id: string
  name: string
  unit: UnitOfMeasure
  stock_qty: number
  min_qty: number
  unit_cost_amount: number
  currency: string
  yield_pct: number // rendimiento/merma en bps (10000 = 100%)
  cost_includes_tax: boolean // ¿el costo cargado incluye IVA?
  recipe_unit: UnitOfMeasure | null // Fase 2C: unidad fina para receta (KG→G, L→ML)
  active: boolean
  is_below_min: boolean
}

export interface CreateIngredientBody {
  name: string
  unit: UnitOfMeasure
  min_qty: number
  unit_cost_amount: number
  stock_qty: number
  yield_pct?: number // bps; default 10000 (100%) en el backend
  price_includes_tax?: boolean // ¿el costo incluye IVA? default true
  recipe_unit?: UnitOfMeasure | null // Fase 2C: unidad de receta (misma familia, más fina)
}

export interface UpdateIngredientBody {
  name?: string
  min_qty?: number
  active?: boolean
  yield_pct?: number
  cost_includes_tax?: boolean
}

export interface CreateIngredientResponse {
  ingredient_id: string
}

export interface PurchaseBody {
  qty: number
  unit_cost_amount: number
  price_includes_tax?: boolean // ¿el costo de compra incluye IVA? default true
  supplier_id?: string | null // proveedor de la compra (opcional)
}

export interface WasteBody {
  qty: number
  note?: string | null
}

export interface SupplierDTO {
  id: string
  name: string
  contact: string | null
  phone: string | null
  notes: string | null
  active: boolean
}

export interface CreateSupplierBody {
  name: string
  contact?: string | null
  phone?: string | null
  notes?: string | null
}

export interface UpdateSupplierBody {
  name: string
  contact?: string | null
  phone?: string | null
  notes?: string | null
  active: boolean
}

export interface SupplierPurchasesDTO {
  supplier_id: string
  currency: string
  total_spent: number // minor units
  purchase_count: number
  last_purchase_at: string | null // ISO-8601
}

export interface CreateSupplierResponse {
  supplier_id: string
}

export interface RecipeItemDTO {
  // Un ítem apunta a un insumo O a una preparación (receta madre), no ambos.
  ingredient_id?: string | null
  preparation_id?: string | null
  qty: number
}

export interface RecipeDTO {
  product_id: string
  has_recipe: boolean
  items: RecipeItemDTO[]
  version?: number // Fase 2D: versión de la receta (incrementa en cada guardado)
}

// Fase 7 (Ficha): un punto del histórico de costo de un insumo (una compra).
export interface IngredientCostPointDTO {
  occurred_at: string // ISO
  unit_cost_amount: number
  currency: string
}

export interface SetRecipeBody {
  items: RecipeItemDTO[]
}

// --- Preparaciones (recetas madre, Productos v2 Tanda C) ---------------------

export interface PreparationDTO {
  id: string
  name: string
  yield_qty: number // rendimiento en milésimas de la unidad de la preparación
  used_in_products: number // en cuántos platos se usa
  items: RecipeItemDTO[]
}

export interface SavePreparationBody {
  name: string
  yield_qty: number
  items: RecipeItemDTO[]
}

export interface CreatePreparationResponse {
  preparation_id: string
}

export interface FoodCostRowDTO {
  product_id: string
  product_name: string
  price_amount: number
  food_cost_amount: number
  margin_amount: number
  food_cost_ratio_bps: number
  currency: string
  cost_confirmed: boolean // Fase 3: todo el food cost respaldado por compras
  coverage_bps: number // Fase 3: cobertura de costo confirmado (bps)
  ratio_sane: boolean // Guarda Insumos: ratio food-cost dentro de [5%, 95%]
}

export interface FoodCostReportDTO {
  currency: string
  rows: FoodCostRowDTO[]
  coverage_bps: number // Fase 3: cobertura del tenant (platos confirmados)
  confirmed_count: number
  total_count: number
  coverage_ok: boolean // Fase 6: ¿la cobertura llega al umbral del hero (≥70%)?
}

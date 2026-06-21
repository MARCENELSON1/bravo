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
  active: boolean
  is_below_min: boolean
}

export interface CreateIngredientBody {
  name: string
  unit: UnitOfMeasure
  min_qty: number
  unit_cost_amount: number
  stock_qty: number
}

export interface UpdateIngredientBody {
  name?: string
  min_qty?: number
  active?: boolean
}

export interface CreateIngredientResponse {
  ingredient_id: string
}

export interface PurchaseBody {
  qty: number
  unit_cost_amount: number
}

export interface WasteBody {
  qty: number
  note?: string | null
}

export interface SupplierDTO {
  id: string
  name: string
  contact: string | null
  active: boolean
}

export interface CreateSupplierBody {
  name: string
  contact?: string | null
}

export interface CreateSupplierResponse {
  supplier_id: string
}

export interface RecipeItemDTO {
  ingredient_id: string
  qty: number
}

export interface RecipeDTO {
  product_id: string
  has_recipe: boolean
  items: RecipeItemDTO[]
}

export interface SetRecipeBody {
  items: RecipeItemDTO[]
}

export interface FoodCostRowDTO {
  product_id: string
  product_name: string
  price_amount: number
  food_cost_amount: number
  margin_amount: number
  food_cost_ratio_bps: number
  currency: string
}

export interface FoodCostReportDTO {
  currency: string
  rows: FoodCostRowDTO[]
}

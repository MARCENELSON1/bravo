import type { HttpClient } from "@/api/http-client"
import type {
  CreateIngredientBody,
  CreateIngredientResponse,
  CreateSupplierBody,
  CreateSupplierResponse,
  FoodCostReportDTO,
  IngredientDTO,
  PurchaseBody,
  RecipeDTO,
  SetRecipeBody,
  SupplierDTO,
  UpdateIngredientBody,
  WasteBody,
} from "@/api/types-inventory"

// Data client for inventory: ingredients (stock), purchases/waste, low-stock
// alerts, suppliers, per-product recipe (opt-in) and food cost. OWNER/MANAGER.
export class InventoryApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  listIngredients(): Promise<IngredientDTO[]> {
    return this.http.request<IngredientDTO[]>("GET", "/inventory/ingredients", { auth: true })
  }

  createIngredient(body: CreateIngredientBody): Promise<CreateIngredientResponse> {
    return this.http.request<CreateIngredientResponse>("POST", "/inventory/ingredients", {
      body,
      auth: true,
    })
  }

  updateIngredient(id: string, body: UpdateIngredientBody): Promise<IngredientDTO> {
    return this.http.request<IngredientDTO>("PATCH", `/inventory/ingredients/${id}`, {
      body,
      auth: true,
    })
  }

  purchase(id: string, body: PurchaseBody): Promise<IngredientDTO> {
    return this.http.request<IngredientDTO>("POST", `/inventory/ingredients/${id}/purchase`, {
      body,
      auth: true,
    })
  }

  waste(id: string, body: WasteBody): Promise<IngredientDTO> {
    return this.http.request<IngredientDTO>("POST", `/inventory/ingredients/${id}/waste`, {
      body,
      auth: true,
    })
  }

  listLowStock(): Promise<IngredientDTO[]> {
    return this.http.request<IngredientDTO[]>("GET", "/inventory/low-stock", { auth: true })
  }

  foodCost(): Promise<FoodCostReportDTO> {
    return this.http.request<FoodCostReportDTO>("GET", "/inventory/food-cost", { auth: true })
  }

  listSuppliers(): Promise<SupplierDTO[]> {
    return this.http.request<SupplierDTO[]>("GET", "/inventory/suppliers", { auth: true })
  }

  createSupplier(body: CreateSupplierBody): Promise<CreateSupplierResponse> {
    return this.http.request<CreateSupplierResponse>("POST", "/inventory/suppliers", {
      body,
      auth: true,
    })
  }

  getRecipe(productId: string): Promise<RecipeDTO> {
    return this.http.request<RecipeDTO>("GET", `/products/${productId}/recipe`, { auth: true })
  }

  setRecipe(productId: string, body: SetRecipeBody): Promise<RecipeDTO> {
    return this.http.request<RecipeDTO>("PUT", `/products/${productId}/recipe`, {
      body,
      auth: true,
    })
  }
}

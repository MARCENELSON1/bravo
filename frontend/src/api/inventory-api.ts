import type { HttpClient } from "@/api/http-client"
import type {
  CreateIngredientBody,
  CreateIngredientResponse,
  CreatePreparationResponse,
  CreateSupplierBody,
  CreateSupplierResponse,
  FoodCostReportDTO,
  IngredientCostPointDTO,
  IngredientDTO,
  PreparationDTO,
  PurchaseBody,
  RecipeDTO,
  SavePreparationBody,
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

  ingredientCostHistory(id: string): Promise<IngredientCostPointDTO[]> {
    return this.http.request<IngredientCostPointDTO[]>(
      "GET",
      `/inventory/ingredients/${id}/cost-history`,
      { auth: true }
    )
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

  // --- Preparaciones (recetas madre) -----------------------------------------

  listPreparations(): Promise<PreparationDTO[]> {
    return this.http.request<PreparationDTO[]>("GET", "/inventory/preparations", {
      auth: true,
    })
  }

  createPreparation(body: SavePreparationBody): Promise<CreatePreparationResponse> {
    return this.http.request<CreatePreparationResponse>("POST", "/inventory/preparations", {
      body,
      auth: true,
    })
  }

  updatePreparation(id: string, body: SavePreparationBody): Promise<PreparationDTO> {
    return this.http.request<PreparationDTO>("PUT", `/inventory/preparations/${id}`, {
      body,
      auth: true,
    })
  }

  deletePreparation(id: string): Promise<void> {
    return this.http.request<void>("DELETE", `/inventory/preparations/${id}`, {
      auth: true,
    })
  }
}

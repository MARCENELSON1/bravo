import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { InventoryApi } from "@/api/inventory-api"

describe("InventoryApi", () => {
  it("creates an ingredient via POST with the body + auth", async () => {
    const request = vi.fn().mockResolvedValue({ ingredient_id: "i1" })
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.createIngredient({
      name: "Harina",
      unit: "KG",
      min_qty: 1000,
      unit_cost_amount: 50000,
      stock_qty: 5000,
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/inventory/ingredients")
    expect(options).toMatchObject({ auth: true, body: { name: "Harina", unit: "KG" } })
  })

  it("registers a purchase against the ingredient id", async () => {
    const request = vi.fn().mockResolvedValue({ id: "i1", stock_qty: 8000 })
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.purchase("i1", { qty: 3000, unit_cost_amount: 60000 })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/inventory/ingredients/i1/purchase")
    expect(options.body).toMatchObject({ qty: 3000, unit_cost_amount: 60000 })
  })

  it("registers waste against the ingredient id", async () => {
    const request = vi.fn().mockResolvedValue({ id: "i1", stock_qty: 3000 })
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.waste("i1", { qty: 2000, note: "rotura" })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/inventory/ingredients/i1/waste")
    expect(options.body).toMatchObject({ qty: 2000 })
  })

  it("fetches low-stock alerts", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.listLowStock()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/inventory/low-stock")
    expect(options).toMatchObject({ auth: true })
  })

  it("fetches the food cost report", async () => {
    const request = vi.fn().mockResolvedValue({ currency: "ARS", rows: [] })
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.foodCost()

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/inventory/food-cost")
  })

  it("sets a product recipe via PUT", async () => {
    const request = vi.fn().mockResolvedValue({ product_id: "p1", has_recipe: true, items: [] })
    const api = new InventoryApi({ request } as unknown as HttpClient)

    await api.setRecipe("p1", { items: [{ ingredient_id: "i1", qty: 200 }] })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("PUT")
    expect(path).toBe("/products/p1/recipe")
    expect(options.body).toMatchObject({ items: [{ ingredient_id: "i1", qty: 200 }] })
  })
})

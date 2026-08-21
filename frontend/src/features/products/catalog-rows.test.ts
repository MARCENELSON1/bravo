import { describe, expect, it } from "vitest"

import type { ProductPerformanceRowDTO } from "@/api/types-analytics"
import type { FoodCostRowDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"

import { catalogCategories, filterCatalog, mergeCatalogRows } from "./catalog-rows"

function product(over: Partial<ProductDTO> = {}): ProductDTO {
  return {
    id: "p1",
    name: "Milanesa",
    price_amount: 100000,
    currency: "ARS",
    category: "Cocina",
    station: "KITCHEN",
    active: true,
    ...over,
  }
}

function fc(over: Partial<FoodCostRowDTO> = {}): FoodCostRowDTO {
  return {
    product_id: "p1",
    product_name: "Milanesa",
    price_amount: 100000,
    food_cost_amount: 30000,
    margin_amount: 70000,
    food_cost_ratio_bps: 3000,
    currency: "ARS",
    cost_confirmed: true,
    coverage_bps: 10000,
    ratio_sane: true,
    ...over,
  }
}

function perf(over: Partial<ProductPerformanceRowDTO> = {}): ProductPerformanceRowDTO {
  return {
    product_id: "p1",
    product_name: "Milanesa",
    units_sold: 12,
    sales_amount: 1200000,
    food_cost_amount: 360000,
    margin_amount: 840000,
    currency: "ARS",
    ...over,
  }
}

describe("mergeCatalogRows", () => {
  it("junta costo/margen/vendidos por product_id", () => {
    const rows = mergeCatalogRows([product()], [fc()], [perf()])
    expect(rows[0].cost).toBe(30000)
    expect(rows[0].margin).toBe(70000)
    expect(rows[0].marginBps).toBe(7000) // 10000 - 3000
    expect(rows[0].units).toBe(12)
    expect(rows[0].costConfirmed).toBe(true)
    expect(rows[0].coverageBps).toBe(10000)
    expect(rows[0].ratioSane).toBe(true)
  })

  it("Guarda Insumos: refleja ratio_sane; sin receta → sano", () => {
    const insane = mergeCatalogRows([product()], [fc({ ratio_sane: false })], [])
    expect(insane[0].ratioSane).toBe(false)
    const noRecipe = mergeCatalogRows([product({ id: "p2" })], [], [])
    expect(noRecipe[0].ratioSane).toBe(true)
  })

  it("Fase 3: refleja el estado de confirmación; sin receta → confirmado (sin costo)", () => {
    const estimated = mergeCatalogRows(
      [product()],
      [fc({ cost_confirmed: false, coverage_bps: 5000 })],
      [],
    )
    expect(estimated[0].costConfirmed).toBe(false)
    expect(estimated[0].coverageBps).toBe(5000)
    // Sin fila de food cost (sin receta) → no hay costo que confirmar.
    const noRecipe = mergeCatalogRows([product({ id: "p2" })], [], [])
    expect(noRecipe[0].costConfirmed).toBe(true)
    expect(noRecipe[0].coverageBps).toBeNull()
  })

  it("producto sin receta → costo/margen null y vendidos 0", () => {
    const rows = mergeCatalogRows([product({ id: "p2", name: "Agua" })], [fc()], [perf()])
    expect(rows[0].cost).toBeNull()
    expect(rows[0].margin).toBeNull()
    expect(rows[0].marginBps).toBeNull()
    expect(rows[0].units).toBe(0)
  })
})

describe("filterCatalog", () => {
  const rows = mergeCatalogRows(
    [
      product({ id: "a", name: "Milanesa napolitana", category: "Cocina", active: true }),
      product({ id: "b", name: "Agua mineral", category: "Bebidas", active: false }),
    ],
    [],
    [],
  )

  it("busca por nombre (case-insensitive)", () => {
    const out = filterCatalog(rows, { q: "nap", category: "", status: "all" })
    expect(out.map((r) => r.product.id)).toEqual(["a"])
  })

  it("filtra por categoría", () => {
    const out = filterCatalog(rows, { q: "", category: "Bebidas", status: "all" })
    expect(out.map((r) => r.product.id)).toEqual(["b"])
  })

  it("filtra por estado", () => {
    expect(filterCatalog(rows, { q: "", category: "", status: "active" }).map((r) => r.product.id)).toEqual(["a"])
    expect(filterCatalog(rows, { q: "", category: "", status: "inactive" }).map((r) => r.product.id)).toEqual(["b"])
  })
})

describe("catalogCategories", () => {
  it("devuelve categorías únicas ordenadas, sin nulls", () => {
    expect(
      catalogCategories([
        product({ category: "Cocina" }),
        product({ category: "Bebidas" }),
        product({ category: null }),
        product({ category: "Cocina" }),
      ]),
    ).toEqual(["Bebidas", "Cocina"])
  })
})

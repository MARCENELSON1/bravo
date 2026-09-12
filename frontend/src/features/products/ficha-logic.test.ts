import { describe, expect, it } from "vitest"

import type { IngredientCostPointDTO } from "@/api/types-inventory"

import { ingredientCostAlert } from "./ficha-logic"

// `costSeriesByDay` se eliminó: la serie por día ahora la agrega el backend en
// SQL sobre la ventana entera. Su cobertura vive en el test de integración
// `test_product_drill_down_cost_series_comes_from_the_window`.

function point(occurred_at: string, cost: number): IngredientCostPointDTO {
  return { occurred_at, unit_cost_amount: cost, currency: "ARS" }
}

describe("ingredientCostAlert", () => {
  const now = Date.parse("2026-08-10T00:00:00Z")

  it("calcula el cambio % de primera a última compra", () => {
    const a = ingredientCostAlert(
      [point("2026-08-01T00:00:00Z", 1000), point("2026-08-08T00:00:00Z", 1200)],
      now
    )
    expect(a.changePct).toBe(20)
    expect(a.lastCost).toBe(1200)
    expect(a.daysSinceLast).toBe(2)
    expect(a.stale).toBe(false)
  })

  it("marca stale cuando la última compra supera el umbral", () => {
    const a = ingredientCostAlert([point("2026-05-01T10:00:00Z", 1000)], now)
    expect(a.changePct).toBeNull() // una sola compra
    expect(a.stale).toBe(true)
    expect(a.daysSinceLast).toBeGreaterThan(60)
  })

  it("sin compras → sin alerta", () => {
    expect(ingredientCostAlert([], now)).toEqual({
      changePct: null,
      lastCost: null,
      daysSinceLast: null,
      stale: false,
    })
  })
})

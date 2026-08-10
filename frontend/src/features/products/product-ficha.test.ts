import { describe, expect, it } from "vitest"

import type { IngredientCostPointDTO } from "@/api/types-inventory"
import type { ProductSaleLineDTO } from "@/api/types-operations"

import { costSeriesByDay, ingredientCostAlert } from "./product-ficha"

function line(occurred_at: string, quantity: number, food: number | null): ProductSaleLineDTO {
  return {
    order_id: "o",
    occurred_at,
    quantity,
    line_amount: 0,
    food_cost_amount: food,
    margin_amount: 0,
  }
}

function point(occurred_at: string, cost: number): IngredientCostPointDTO {
  return { occurred_at, unit_cost_amount: cost, currency: "ARS" }
}

describe("costSeriesByDay", () => {
  it("promedia el costo unitario por día y ordena ascendente", () => {
    const series = costSeriesByDay([
      line("2026-08-02T20:00:00Z", 2, 200), // 100/u
      line("2026-08-01T13:00:00Z", 1, 150), // 150/u
      line("2026-08-02T21:00:00Z", 2, 300), // se agrega al día 02
    ])
    // día 02: (200+300)/(2+2) = 125
    expect(series).toEqual([
      { day: "2026-08-01", unitCost: 150 },
      { day: "2026-08-02", unitCost: 125 },
    ])
  })

  it("ignora líneas sin food cost o sin cantidad", () => {
    expect(costSeriesByDay([line("2026-08-01T10:00:00Z", 0, 100)])).toEqual([])
    expect(costSeriesByDay([line("2026-08-01T10:00:00Z", 1, null)])).toEqual([])
  })
})

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

import { describe, expect, it } from "vitest"

import { coverageGate } from "@/features/products/coverage-gate"
import type { FoodCostReportDTO } from "@/api/types-inventory"

function report(over: Partial<FoodCostReportDTO>): FoodCostReportDTO {
  return {
    currency: "ARS",
    rows: [],
    coverage_bps: 10000,
    confirmed_count: 0,
    total_count: 0,
    coverage_ok: true,
    ...over,
  }
}

describe("coverageGate", () => {
  it("sin report → abierto (paridad, no gatea mientras carga)", () => {
    const g = coverageGate(undefined)
    expect(g.open).toBe(true)
    expect(g.missing).toBe(0)
  })

  it("coverage_ok true → abierto", () => {
    const g = coverageGate(report({ coverage_ok: true, confirmed_count: 8, total_count: 10 }))
    expect(g.open).toBe(true)
    expect(g.missing).toBe(2)
    expect(g.confirmed).toBe(8)
    expect(g.total).toBe(10)
  })

  it("coverage_ok false → cerrado, con los que faltan", () => {
    const g = coverageGate(report({ coverage_ok: false, confirmed_count: 3, total_count: 10 }))
    expect(g.open).toBe(false)
    expect(g.missing).toBe(7)
    expect(g.confirmed).toBe(3)
    expect(g.total).toBe(10)
  })

  it("nunca da missing negativo", () => {
    const g = coverageGate(report({ confirmed_count: 5, total_count: 3 }))
    expect(g.missing).toBe(0)
  })
})

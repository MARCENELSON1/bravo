import { describe, expect, it } from "vitest"

import { classifyMenu, marginKillers, topEarners } from "@/features/products/menu-engineering"
import type { ProductPerformanceRowDTO } from "@/api/types-analytics"

function row(
  id: string,
  units: number,
  sales: number,
  foodCost: number
): ProductPerformanceRowDTO {
  return {
    product_id: id,
    product_name: id,
    units_sold: units,
    sales_amount: sales,
    food_cost_amount: foodCost,
    margin_amount: sales - foodCost,
    currency: "ARS",
  }
}

describe("classifyMenu", () => {
  it("no vendido cuando units == 0", () => {
    const [p] = classifyMenu([row("a", 0, 0, 0)])
    expect(p.category).toBe("no_vendido")
  })

  it("revisar cuando margen < 45% aunque venda", () => {
    // margen 40% (deja poco), alto volumen
    const rows = [row("killer", 100, 10000, 6000), row("otro", 1, 1000, 100)]
    const killer = classifyMenu(rows).find((p) => p.id === "killer")!
    expect(killer.category).toBe("revisar")
  })

  it("funciona = alto margen + alto volumen", () => {
    const rows = [row("star", 100, 10000, 3000), row("bajo", 1, 100, 30)]
    const star = classifyMenu(rows).find((p) => p.id === "star")!
    expect(star.category).toBe("funciona") // 70% margen, volumen alto
  })

  it("oportunidad = alto margen + bajo volumen", () => {
    const rows = [row("hidden", 1, 1000, 300), row("popular", 100, 10000, 3000)]
    const hidden = classifyMenu(rows).find((p) => p.id === "hidden")!
    expect(hidden.category).toBe("oportunidad")
  })

  it("calcula precio y costo unitario", () => {
    const [p] = classifyMenu([row("a", 2, 20000, 8000)])
    expect(p.unitPrice).toBe(10000)
    expect(p.unitCost).toBe(4000)
    expect(p.margin).toBe(12000)
  })
})

describe("topEarners / marginKillers", () => {
  const products = classifyMenu([
    row("a", 10, 10000, 2000), // deja 8000
    row("b", 10, 20000, 4000), // deja 16000
    row("c", 50, 10000, 7000), // 30% margen → killer
  ])
  it("top earners por margen desc", () => {
    expect(topEarners(products)[0].id).toBe("b")
  })
  it("margin killers son los de margen bajo", () => {
    expect(marginKillers(products).map((p) => p.id)).toContain("c")
  })
})

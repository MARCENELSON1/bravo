import { describe, expect, it } from "vitest"

import {
  classifyMenu,
  confirmedMargin,
  marginKillers,
  topEarners,
} from "@/features/products/menu-engineering"
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

  it("oportunidad = alto margen + bajo volumen (dentro de su categoría)", () => {
    const rows = [row("hidden", 15, 15000, 4500), row("popular", 100, 100000, 30000)]
    const hidden = classifyMenu(rows).find((p) => p.id === "hidden")!
    expect(hidden.category).toBe("oportunidad")
  })

  it("calcula precio y costo unitario", () => {
    const [p] = classifyMenu([row("a", 2, 20000, 8000)])
    expect(p.unitPrice).toBe(10000)
    expect(p.unitCost).toBe(4000)
    expect(p.margin).toBe(12000)
  })

  it("Fase 4: sin datos cuando vende menos que el piso mínimo", () => {
    // 3 unidades con minUnits 10 → no alcanza para clasificar.
    const [p] = classifyMenu([row("thin", 3, 6000, 1500)], undefined, undefined, undefined, 10)
    expect(p.category).toBe("sin_datos")
  })

  it("Fase 4: sin datos cuando el costo no está confirmado", () => {
    const rows = [row("est", 50, 100000, 30000)]
    const [p] = classifyMenu(rows, new Set(["est"]))
    expect(p.category).toBe("sin_datos") // costo estimado → no clasificamos
  })

  it("Fase 4: compara el volumen dentro de la categoría de carta", () => {
    // 4 cafés (categoría propia) + 4 platos. Un café de 40u es alto DENTRO de cafés
    // aunque en toda la carta sea bajo frente a los platos de 200u.
    const rows = [
      row("cafe1", 40, 40000, 8000),
      row("cafe2", 10, 10000, 2000),
      row("cafe3", 12, 12000, 2400),
      row("cafe4", 11, 11000, 2200),
      row("plato1", 200, 400000, 120000),
      row("plato2", 210, 420000, 126000),
      row("plato3", 190, 380000, 114000),
      row("plato4", 205, 410000, 123000),
    ]
    const cat = new Map<string, string | null>([
      ["cafe1", "Café"],
      ["cafe2", "Café"],
      ["cafe3", "Café"],
      ["cafe4", "Café"],
      ["plato1", "Platos"],
      ["plato2", "Platos"],
      ["plato3", "Platos"],
      ["plato4", "Platos"],
    ])
    const cafe1 = classifyMenu(rows, undefined, undefined, cat).find((p) => p.id === "cafe1")!
    // margen 80% + alto volumen entre cafés (avg cafés ≈ 18) → funciona, no oportunidad.
    expect(cafe1.menuCategory).toBe("Café")
    expect(cafe1.category).toBe("funciona")
  })

  it("Fase 4: categorías con menos de 4 productos caen en Otros", () => {
    const rows = [row("solo", 20, 20000, 5000), row("x", 30, 30000, 8000)]
    const cat = new Map<string, string | null>([
      ["solo", "Postres"],
      ["x", "Platos"],
    ])
    const [p] = classifyMenu(rows, undefined, undefined, cat).filter((r) => r.id === "solo")
    expect(p.menuCategory).toBe("Otros")
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

describe("Fase 3: costo confirmado/estimado", () => {
  it("sin estimatedIds → todo confirmado (paridad)", () => {
    const ps = classifyMenu([row("a", 5, 10000, 3000)])
    expect(ps[0].costConfirmed).toBe(true)
  })

  it("estimatedIds marca estimados y los excluye de la plata", () => {
    const rows = [row("conf", 5, 10000, 3000), row("est", 5, 10000, 3000)]
    const ps = classifyMenu(rows, new Set(["est"]))
    expect(ps.find((p) => p.id === "conf")!.costConfirmed).toBe(true)
    expect(ps.find((p) => p.id === "est")!.costConfirmed).toBe(false)
    // topEarners y confirmedMargin no cuentan al estimado.
    expect(topEarners(ps).map((p) => p.id)).toEqual(["conf"])
    expect(confirmedMargin(ps)).toBe(7000) // solo el confirmado (10000-3000)
  })
})

describe("Guarda Insumos: receta incompleta (ratio_sane)", () => {
  it("sin insaneIds → todo sano (paridad)", () => {
    const ps = classifyMenu([row("a", 5, 10000, 3000)])
    expect(ps[0].ratioSane).toBe(true)
  })

  it("insaneIds marca incompletas y las excluye de la plata", () => {
    const rows = [row("ok", 5, 10000, 3000), row("bad", 5, 10000, 300)]
    const ps = classifyMenu(rows, undefined, new Set(["bad"]))
    expect(ps.find((p) => p.id === "ok")!.ratioSane).toBe(true)
    expect(ps.find((p) => p.id === "bad")!.ratioSane).toBe(false)
    // "bad" deja más plata pero es incompleta → no entra al ranking ni al total.
    expect(topEarners(ps).map((p) => p.id)).toEqual(["ok"])
    expect(confirmedMargin(ps)).toBe(7000) // solo "ok" (10000-3000)
  })
})

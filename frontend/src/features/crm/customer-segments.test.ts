import { describe, expect, it } from "vitest"

import type { CustomerStatsRowDTO } from "@/api/customers-api"
import {
  classifyCustomers,
  coverage,
  todaysActions,
} from "@/features/crm/customer-segments"

const NOW = Date.parse("2026-08-23T00:00:00Z")

function row(over: Partial<CustomerStatsRowDTO> & { customer_id: string }): CustomerStatsRowDTO {
  return {
    name: over.customer_id,
    phone: null,
    visits: 0,
    total_spent: 0,
    first_visit_at: null,
    last_visit_at: null,
    ...over,
  }
}

const daysAgo = (n: number) => new Date(NOW - n * 86_400_000).toISOString()

describe("classifyCustomers", () => {
  it("sin compras cuando no hay visitas", () => {
    const [c] = classifyCustomers([row({ customer_id: "a" })], NOW)
    expect(c.segment).toBe("sin_compras")
  })

  it("nuevo: primera visita reciente y pocas visitas", () => {
    const [c] = classifyCustomers(
      [row({ customer_id: "a", visits: 1, total_spent: 5000, first_visit_at: daysAgo(5), last_visit_at: daysAgo(5) })],
      NOW
    )
    expect(c.segment).toBe("nuevo")
  })

  it("en riesgo: recurrente que no viene hace >45 días", () => {
    const [c] = classifyCustomers(
      [row({ customer_id: "a", visits: 4, total_spent: 20000, first_visit_at: daysAgo(200), last_visit_at: daysAgo(60) })],
      NOW
    )
    expect(c.segment).toBe("en_riesgo")
  })

  it("recurrente: 3+ visitas, viene seguido", () => {
    const [c] = classifyCustomers(
      [row({ customer_id: "a", visits: 5, total_spent: 30000, first_visit_at: daysAgo(120), last_visit_at: daysAgo(5) })],
      NOW
    )
    expect(c.segment).toBe("recurrente")
  })

  it("vip: top gastador (rank) con 2+ visitas", () => {
    const rows = [
      row({ customer_id: "big", visits: 3, total_spent: 1_000_000, first_visit_at: daysAgo(90), last_visit_at: daysAgo(3) }),
      ...Array.from({ length: 9 }, (_, i) =>
        row({ customer_id: `s${i}`, visits: 2, total_spent: 10_000, first_visit_at: daysAgo(90), last_visit_at: daysAgo(3) })
      ),
    ]
    const big = classifyCustomers(rows, NOW).find((c) => c.customer_id === "big")!
    expect(big.segment).toBe("vip")
  })

  it("en riesgo tiene prioridad sobre vip", () => {
    const rows = [
      row({ customer_id: "big", visits: 5, total_spent: 1_000_000, first_visit_at: daysAgo(300), last_visit_at: daysAgo(90) }),
      row({ customer_id: "s", visits: 2, total_spent: 10_000, first_visit_at: daysAgo(90), last_visit_at: daysAgo(3) }),
    ]
    const big = classifyCustomers(rows, NOW).find((c) => c.customer_id === "big")!
    expect(big.segment).toBe("en_riesgo")
  })
})

describe("todaysActions", () => {
  const atRisk = (id: string, spent: number, phone: string | null = "111") =>
    row({
      customer_id: id,
      visits: 3,
      total_spent: spent,
      phone,
      first_visit_at: daysAgo(200),
      last_visit_at: daysAgo(60),
    })

  it("prioriza a los en-riesgo por plata en juego (gasto), top N", () => {
    const rows = [atRisk("a", 10_000), atRisk("b", 90_000), atRisk("c", 50_000)]
    const out = todaysActions(rows, new Set(), new Set(), NOW, 2)
    expect(out.map((c) => c.customer_id)).toEqual(["b", "c"])
  })

  it("excluye opt-out, ya-contactados y sin teléfono", () => {
    const rows = [
      atRisk("optout", 100_000),
      atRisk("reciente", 90_000),
      atRisk("sintel", 80_000, null),
      atRisk("ok", 10_000),
    ]
    const out = todaysActions(rows, new Set(["optout"]), new Set(["reciente"]), NOW)
    expect(out.map((c) => c.customer_id)).toEqual(["ok"])
  })

  it("no infla la lista: si no hay en-riesgo, no sugiere a nadie", () => {
    const rows = [
      row({ customer_id: "nuevo", visits: 1, total_spent: 5000, phone: "1", first_visit_at: daysAgo(3), last_visit_at: daysAgo(3) }),
    ]
    expect(todaysActions(rows, new Set(), new Set(), NOW)).toHaveLength(0)
  })
})

describe("coverage", () => {
  it("cuenta cuántos tienen compras vs total", () => {
    const rows = [
      row({ customer_id: "a", visits: 1 }),
      row({ customer_id: "b" }),
      row({ customer_id: "c", visits: 3 }),
    ]
    expect(coverage(rows)).toEqual({ withPurchases: 2, total: 3 })
  })
})

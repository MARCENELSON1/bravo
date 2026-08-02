import { describe, expect, it } from "vitest"

import type { PricingRowDTO } from "@/api/types-operations"
import { bpsToPct, pricingSummary, weekdayLabel } from "@/features/products/pricing"

function row(id: string, gapBps: number, lagging: boolean): PricingRowDTO {
  return {
    product_id: id,
    product_name: id,
    current_price_amount: 100000,
    suggested_price_amount: 100000 + gapBps * 10,
    gap_amount: gapBps * 10,
    gap_bps: gapBps,
    days_since_change: 30,
    lagging,
  }
}

describe("weekdayLabel", () => {
  it("mapea 0..6 a Lun..Dom", () => {
    expect(weekdayLabel(0)).toBe("Lun")
    expect(weekdayLabel(6)).toBe("Dom")
  })
  it("devuelve ? fuera de rango", () => {
    expect(weekdayLabel(9)).toBe("?")
  })
})

describe("bpsToPct", () => {
  it("convierte basis points a porcentaje", () => {
    expect(bpsToPct(2000)).toBe("20.0%")
    expect(bpsToPct(550, 0)).toBe("6%")
  })
})

describe("pricingSummary", () => {
  it("cuenta los rezagados y elige el peor", () => {
    const rows = [row("a", 800, true), row("b", 200, false), row("c", 1500, true)]
    const summary = pricingSummary(rows)
    expect(summary.laggingCount).toBe(2)
    expect(summary.worst?.product_id).toBe("c")
  })
  it("sin rezagados, worst es null", () => {
    const summary = pricingSummary([row("a", 100, false)])
    expect(summary.laggingCount).toBe(0)
    expect(summary.worst).toBeNull()
  })
})

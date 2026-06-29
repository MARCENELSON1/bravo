import { describe, expect, it } from "vitest"

import { rangeWindow } from "@/lib/finance-range"

// 15 de junio de 2026, 14:30 (hora local). Junio = mes 5, Q2 arranca en abril.
const NOW = new Date(2026, 5, 15, 14, 30)

describe("rangeWindow", () => {
  it("month → desde el 1° del mes hasta ahora", () => {
    const w = rangeWindow("month", NOW)
    const from = new Date(w.from)
    expect(from.getMonth()).toBe(5)
    expect(from.getDate()).toBe(1)
    expect(new Date(w.to).getTime()).toBe(NOW.getTime())
  })

  it("today → arranca a las 00:00 del día", () => {
    const from = new Date(rangeWindow("today", NOW).from)
    expect(from.getDate()).toBe(15)
    expect(from.getHours()).toBe(0)
  })

  it("quarter → primer día del trimestre (abril en Q2)", () => {
    const from = new Date(rangeWindow("quarter", NOW).from)
    expect(from.getMonth()).toBe(3)
    expect(from.getDate()).toBe(1)
  })

  it("week → arranca un lunes", () => {
    const from = new Date(rangeWindow("week", NOW).from)
    expect(from.getDay()).toBe(1) // 1 = lunes
  })
})

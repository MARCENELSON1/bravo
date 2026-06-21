import { describe, expect, it } from "vitest"

import { formatMoney } from "@/lib/money"

describe("formatMoney", () => {
  it("renders minor units as a localized currency amount", () => {
    expect(formatMoney(150050, "ARS").replace(/\s/g, "")).toContain("1.500,50")
  })

  it("renders zero", () => {
    expect(formatMoney(0, "ARS").replace(/\s/g, "")).toContain("0,00")
  })
})

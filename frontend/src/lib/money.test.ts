import { describe, expect, it } from "vitest"

import { formatMoney } from "@/lib/money"

describe("formatMoney", () => {
  it("renders minor units as a localized currency amount", () => {
    expect(formatMoney(150050, "ARS").replace(/\s/g, "")).toContain("1.500,50")
  })

  it("renders zero", () => {
    expect(formatMoney(0, "ARS").replace(/\s/g, "")).toContain("0,00")
  })

  it("uses US conventions for USD (period decimal, thousands comma)", () => {
    const out = formatMoney(150050, "USD")
    expect(out).toContain("1,500.50")
    expect(out).toContain("$")
  })

  it("keeps AR conventions for ARS (paridad: comma decimal)", () => {
    // ARS must stay on es-AR — a US tenant's locale never leaks into AR rendering.
    expect(formatMoney(150050, "ARS").replace(/\s/g, "")).toContain("1.500,50")
  })

  it("falls back to es-AR for an unknown currency", () => {
    expect(formatMoney(150050, "UYU").replace(/\s/g, "")).toContain("1.500,50")
  })

  it("honors fractionDigits across locales", () => {
    expect(formatMoney(150000, "USD", 0)).toContain("1,500")
    expect(formatMoney(150000, "USD", 0)).not.toContain(".00")
  })
})

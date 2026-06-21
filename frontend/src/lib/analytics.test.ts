import { describe, expect, it } from "vitest"

import { directionLabel, methodLabel } from "@/lib/analytics"

describe("analytics labels", () => {
  it("labels payment methods in Spanish", () => {
    expect(methodLabel("CASH")).toBe("Efectivo")
    expect(methodLabel("MERCADOPAGO")).toBe("MercadoPago")
  })

  it("falls back to the raw method when unknown", () => {
    expect(methodLabel("CRYPTO")).toBe("CRYPTO")
  })

  it("labels the direction (ingreso / egreso)", () => {
    expect(directionLabel("INFLOW")).toBe("Ingreso")
    expect(directionLabel("OUTFLOW")).toBe("Egreso")
  })
})

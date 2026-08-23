import { describe, expect, it } from "vitest"

import { homeAlerts, type AlertCounts } from "@/features/dashboard/home-alerts"

const base: AlertCounts = {
  toServe: 0,
  toCharge: 0,
  occupied: 0,
  cashOpen: true,
  lowStock: 0,
  atRisk: 0,
}

describe("homeAlerts", () => {
  it("nada que hacer → sin alertas", () => {
    expect(homeAlerts(base)).toEqual([])
  })

  it("mesas para servir y cobrar, en ese orden", () => {
    const out = homeAlerts({ ...base, toServe: 2, toCharge: 1 })
    expect(out.map((a) => a.key)).toEqual(["to_serve", "to_charge"])
    expect(out[0].label).toContain("2 mesas para servir")
    expect(out[1].label).toContain("1 mesa para cobrar")
  })

  it("caja: solo molesta si el local está operando (hay ocupadas)", () => {
    expect(homeAlerts({ ...base, cashOpen: false, occupied: 0 })).toEqual([])
    const out = homeAlerts({ ...base, cashOpen: false, occupied: 3 })
    expect(out.map((a) => a.key)).toEqual(["cash"])
  })

  it("caja desconocida (null) no genera alerta", () => {
    expect(homeAlerts({ ...base, cashOpen: null, occupied: 3 })).toEqual([])
  })

  it("stock bajo y clientes en riesgo", () => {
    const out = homeAlerts({ ...base, lowStock: 4, atRisk: 1 })
    expect(out.map((a) => a.key)).toEqual(["low_stock", "at_risk"])
    expect(out[0].label).toContain("4 insumos por reponer")
    expect(out[1].label).toContain("1 cliente en riesgo")
  })
})

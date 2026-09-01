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

    expect(out[0].labelKey).toBe("dashboard.alerts.toServe")
    expect(out[0].count).toBe(2)
    expect(out[0].to).toBe("/app/floor")
    expect(out[0].tone).toBe("attention")

    expect(out[1].labelKey).toBe("dashboard.alerts.toCharge")
    expect(out[1].count).toBe(1)
    expect(out[1].to).toBe("/app/floor?cobrar=1")
    expect(out[1].tone).toBe("attention")
  })

  it("caja: solo molesta si el local está operando (hay ocupadas)", () => {
    expect(homeAlerts({ ...base, cashOpen: false, occupied: 0 })).toEqual([])
    const out = homeAlerts({ ...base, cashOpen: false, occupied: 3 })
    expect(out.map((a) => a.key)).toEqual(["cash"])

    expect(out[0].labelKey).toBe("dashboard.alerts.cashClosed")
    expect(out[0].count).toBeUndefined() // la caja no pluraliza
    expect(out[0].to).toBe("/app/caja")
    expect(out[0].tone).toBe("attention")
  })

  it("caja desconocida (null) no genera alerta", () => {
    expect(homeAlerts({ ...base, cashOpen: null, occupied: 3 })).toEqual([])
  })

  it("stock bajo y clientes en riesgo", () => {
    const out = homeAlerts({ ...base, lowStock: 4, atRisk: 1 })
    expect(out.map((a) => a.key)).toEqual(["low_stock", "at_risk"])

    expect(out[0].labelKey).toBe("dashboard.alerts.lowStock")
    expect(out[0].count).toBe(4)
    expect(out[0].to).toBe("/app/stock")
    expect(out[0].tone).toBe("normal")

    expect(out[1].labelKey).toBe("dashboard.alerts.atRisk")
    expect(out[1].count).toBe(1)
    expect(out[1].to).toBe("/app/clientes")
    expect(out[1].tone).toBe("normal")
  })

  it("servir escala a crítico cuando se acumulan platos listos", () => {
    expect(homeAlerts({ ...base, toServe: 2 })[0].tone).toBe("attention")
    expect(homeAlerts({ ...base, toServe: 3 })[0].tone).toBe("critical")
  })

  it("el stock bajo sube a urgente cuando son muchos insumos", () => {
    expect(homeAlerts({ ...base, lowStock: 4 })[0].tone).toBe("normal")
    expect(homeAlerts({ ...base, lowStock: 5 })[0].tone).toBe("attention")
  })

  it("muestra lo más urgente primero", () => {
    const out = homeAlerts({ ...base, atRisk: 2, lowStock: 6, toServe: 3 })
    expect(out.map((a) => a.tone)).toEqual(["critical", "attention", "normal"])
    expect(out.map((a) => a.key)).toEqual(["to_serve", "low_stock", "at_risk"])
  })
})

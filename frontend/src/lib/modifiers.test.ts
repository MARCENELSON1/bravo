import { describe, expect, it } from "vitest"

import type { ModifierGroupDTO } from "@/api/types-operations"
import {
  needsChoice,
  optionsDelta,
  selectionValid,
  snapshotOptions,
  toggleOption,
} from "@/lib/modifiers"

const punto: ModifierGroupDTO = {
  id: "g-punto",
  name: "Punto",
  min_select: 1,
  max_select: 1,
  required: true,
  options: [
    { id: "jugoso", name: "Jugoso", price_delta: 0 },
    { id: "apunto", name: "A punto", price_delta: 0 },
  ],
}

const extras: ModifierGroupDTO = {
  id: "g-extras",
  name: "Agregados",
  min_select: 0,
  max_select: 2,
  required: false,
  options: [
    { id: "panceta", name: "+Panceta", price_delta: 1200 },
    { id: "queso", name: "+Queso", price_delta: 800 },
    { id: "huevo", name: "+Huevo", price_delta: 500 },
  ],
}

const groups = [punto, extras]

describe("modifiers", () => {
  it("needsChoice only when a group is required", () => {
    expect(needsChoice(groups)).toBe(true)
    expect(needsChoice([extras])).toBe(false)
    expect(needsChoice([])).toBe(false)
  })

  it("selectionValid enforces the required group and the max", () => {
    expect(selectionValid(groups, new Set())).toBe(false) // falta el punto
    expect(selectionValid(groups, new Set(["jugoso"]))).toBe(true)
    expect(selectionValid(groups, new Set(["jugoso", "panceta", "queso"]))).toBe(true)
    // 3 agregados > max_select 2
    expect(selectionValid(groups, new Set(["jugoso", "panceta", "queso", "huevo"]))).toBe(false)
    expect(selectionValid([], new Set())).toBe(true) // sin grupos, siempre válido
  })

  it("optionsDelta only adds what was chosen", () => {
    expect(optionsDelta(groups, new Set(["jugoso"]))).toBe(0)
    expect(optionsDelta(groups, new Set(["jugoso", "panceta", "huevo"]))).toBe(1700)
  })

  it("snapshotOptions keeps name + delta in menu order", () => {
    const snap = snapshotOptions(groups, new Set(["queso", "jugoso"]))
    expect(snap.map((o) => o.name)).toEqual(["Jugoso", "+Queso"])
    expect(snap.map((o) => o.price_delta)).toEqual([0, 800])
  })

  describe("toggleOption", () => {
    it("pick-one replaces the choice inside its group", () => {
      const first = toggleOption(punto, "jugoso", new Set())
      expect([...first]).toEqual(["jugoso"])
      const second = toggleOption(punto, "apunto", first)
      expect([...second]).toEqual(["apunto"]) // reemplaza, no acumula
    })

    it("multi-select toggles off and respects the max", () => {
      let sel: ReadonlySet<string> = new Set<string>()
      sel = toggleOption(extras, "panceta", sel)
      sel = toggleOption(extras, "queso", sel)
      expect(sel.size).toBe(2)
      sel = toggleOption(extras, "huevo", sel) // 3 > max 2 → se ignora
      expect(sel.size).toBe(2)
      sel = toggleOption(extras, "panceta", sel) // destildar
      expect([...sel]).toEqual(["queso"])
    })

    it("does not touch other groups", () => {
      const sel = toggleOption(extras, "panceta", new Set(["jugoso"]))
      expect(sel.has("jugoso")).toBe(true)
    })
  })
})

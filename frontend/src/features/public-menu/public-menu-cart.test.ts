import { describe, expect, it } from "vitest"

import type { PublicMenuItemDTO } from "@/api/public-menu-api"
import {
  buildLine,
  cartCount,
  cartTotal,
  isSelectionValid,
  lineKey,
  toOrderLines,
} from "@/features/public-menu/public-menu-cart"

const BIFE: PublicMenuItemDTO = {
  id: "p1",
  name: "Bife",
  price_amount: 1200000,
  modifier_groups: [
    {
      id: "g1",
      name: "Cocción",
      min_select: 1,
      max_select: 1,
      required: true,
      options: [
        { id: "rare", name: "Jugosa", price_delta: 0 },
        { id: "bacon", name: "Con panceta", price_delta: 300000 },
      ],
    },
  ],
}

describe("public-menu cart", () => {
  it("keys identical lines together regardless of option order", () => {
    expect(lineKey("p1", ["a", "b"])).toBe(lineKey("p1", ["b", "a"]))
    expect(lineKey("p1", ["a"])).not.toBe(lineKey("p1", ["a", "b"]))
  })

  it("builds a line folding the option delta into the unit price", () => {
    const line = buildLine(BIFE, ["bacon"])
    expect(line.unitPrice).toBe(1500000) // 1200000 + 300000
    expect(line.optionsLabel).toBe("Con panceta")
    expect(line.optionIds).toEqual(["bacon"])
    expect(line.quantity).toBe(1)
  })

  it("computes count and total across lines", () => {
    const lines = [
      { ...buildLine(BIFE, ["rare"]), quantity: 2 },
      { ...buildLine(BIFE, ["bacon"]), quantity: 1 },
    ]
    expect(cartCount(lines)).toBe(3)
    expect(cartTotal(lines)).toBe(1200000 * 2 + 1500000)
  })

  it("emits order lines with only ids (never prices)", () => {
    const lines = [{ ...buildLine(BIFE, ["bacon"]), quantity: 2 }]
    expect(toOrderLines(lines)).toEqual([
      { product_id: "p1", quantity: 2, option_ids: ["bacon"] },
    ])
  })

  it("omits option_ids for a plain line", () => {
    const line = buildLine({ id: "p2", name: "Agua", price_amount: 500 }, [])
    expect(toOrderLines([line])).toEqual([{ product_id: "p2", quantity: 1 }])
  })

  it("validates min/max per group", () => {
    const groups = BIFE.modifier_groups!
    expect(isSelectionValid(groups, [])).toBe(false) // requerido
    expect(isSelectionValid(groups, ["rare"])).toBe(true)
    expect(isSelectionValid(groups, ["rare", "bacon"])).toBe(false) // max 1
  })
})

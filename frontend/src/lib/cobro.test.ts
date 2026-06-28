import { describe, expect, it } from "vitest"

import type { OrderItemDTO } from "@/api/types-operations"
import { presetAmounts, sumLineItems } from "@/lib/cobro"

const item = (id: string, price: number, qty: number): OrderItemDTO => ({
  id,
  product_id: "p",
  name: id,
  unit_price_amount: price,
  quantity: qty,
  note: null,
  status: "PENDING",
  station: "KITCHEN",
  sent_at: null,
})

describe("presetAmounts", () => {
  it("offers total, half and third (rounded up)", () => {
    expect(presetAmounts(3000)).toEqual([
      { label: "Total", amount: 3000 },
      { label: "½", amount: 1500 },
      { label: "⅓", amount: 1000 },
    ])
  })

  it("is empty when nothing is owed", () => {
    expect(presetAmounts(0)).toEqual([])
  })
})

describe("sumLineItems", () => {
  it("sums only the selected items' line totals", () => {
    const items = [item("a", 1000, 2), item("b", 500, 1), item("c", 800, 3)]
    expect(sumLineItems(items, new Set(["a", "c"]))).toBe(2000 + 2400)
  })

  it("is zero with no selection", () => {
    expect(sumLineItems([item("a", 1000, 1)], new Set())).toBe(0)
  })
})

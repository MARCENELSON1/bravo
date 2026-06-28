import { describe, expect, it } from "vitest"

import type { OrderDTO, OrderItemDTO } from "@/api/types-operations"
import { kdsDelay, kdsTickets } from "@/lib/kds"

describe("kdsDelay", () => {
  const base = Date.parse("2026-06-24T20:00:00Z")

  it("is fresh under 5 minutes", () => {
    const d = kdsDelay("2026-06-24T19:58:00Z", base)
    expect(d.minutes).toBe(2)
    expect(d.level).toBe("fresh")
  })

  it("warns between 5 and 10 minutes", () => {
    expect(kdsDelay("2026-06-24T19:53:00Z", base).level).toBe("warn")
  })

  it("is late at 10+ minutes", () => {
    expect(kdsDelay("2026-06-24T19:49:00Z", base).level).toBe("late")
  })

  it("is safe with null or invalid timestamps", () => {
    expect(kdsDelay(null, base)).toEqual({ minutes: 0, level: "fresh" })
    expect(kdsDelay("not-a-date", base)).toEqual({ minutes: 0, level: "fresh" })
  })
})

describe("kdsTickets", () => {
  const mkItem = (over: Partial<OrderItemDTO>): OrderItemDTO => ({
    id: "i",
    product_id: "p",
    name: "x",
    unit_price_amount: 100,
    quantity: 1,
    note: null,
    status: "SENT",
    station: "KITCHEN",
    sent_at: null,
    ...over,
  })
  const order = (id: string, items: OrderItemDTO[]): OrderDTO => ({
    id,
    table_id: `t-${id}`,
    waiter_id: "w",
    status: "SENT",
    currency: "ARS",
    items,
    total_amount: 0,
    created_at: null,
  })

  it("keeps only active items of the requested station", () => {
    const orders = [
      order("o1", [
        mkItem({ id: "a", station: "KITCHEN", status: "SENT" }),
        mkItem({ id: "b", station: "BAR", status: "SENT" }), // other station
        mkItem({ id: "c", station: "KITCHEN", status: "SERVED" }), // done
        mkItem({ id: "d", station: "KITCHEN", status: "PENDING" }), // not marched
      ]),
    ]
    expect(kdsTickets(orders, "KITCHEN").map((t) => t.item.id)).toEqual(["a"])
    expect(kdsTickets(orders, "BAR").map((t) => t.item.id)).toEqual(["b"])
  })

  it("orders tickets oldest marched first (by sent_at)", () => {
    const orders = [
      order("o1", [mkItem({ id: "new", sent_at: "2026-06-24T20:10:00Z" })]),
      order("o2", [mkItem({ id: "old", sent_at: "2026-06-24T20:00:00Z" })]),
    ]
    expect(kdsTickets(orders, "KITCHEN").map((t) => t.item.id)).toEqual(["old", "new"])
  })

  it("carries the order + table context on each ticket", () => {
    const orders = [order("o9", [mkItem({ id: "a" })])]
    const [ticket] = kdsTickets(orders, "KITCHEN")
    expect(ticket.orderId).toBe("o9")
    expect(ticket.tableId).toBe("t-o9")
  })
})

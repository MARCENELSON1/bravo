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
    source: "WAITER",
    created_at: null,
    customer_id: null,
  })

  const itemIds = (tickets: { items: OrderItemDTO[] }[]): string[] =>
    tickets.flatMap((ticket) => ticket.items.map((item) => item.id))

  it("keeps only active items of the requested station", () => {
    const orders = [
      order("o1", [
        mkItem({ id: "a", station: "KITCHEN", status: "SENT" }),
        mkItem({ id: "b", station: "BAR", status: "SENT" }), // other station
        mkItem({ id: "c", station: "KITCHEN", status: "SERVED" }), // done
        mkItem({ id: "d", station: "KITCHEN", status: "PENDING" }), // not marched
      ]),
    ]
    expect(itemIds(kdsTickets(orders, "KITCHEN"))).toEqual(["a"])
    expect(itemIds(kdsTickets(orders, "BAR"))).toEqual(["b"])
  })

  it("orders tickets oldest marched first (by sent_at)", () => {
    const orders = [
      order("o1", [mkItem({ id: "new", sent_at: "2026-06-24T20:10:00Z" })]),
      order("o2", [mkItem({ id: "old", sent_at: "2026-06-24T20:00:00Z" })]),
    ]
    expect(itemIds(kdsTickets(orders, "KITCHEN"))).toEqual(["old", "new"])
  })

  it("carries the order + table context on each ticket", () => {
    const orders = [order("o9", [mkItem({ id: "a" })])]
    const [ticket] = kdsTickets(orders, "KITCHEN")
    expect(ticket.orderId).toBe("o9")
    expect(ticket.tableId).toBe("t-o9")
  })

  // --- Tiempos de servicio (cursos) ---

  it("groups every dish of a course into ONE ticket", () => {
    const orders = [
      order("o1", [
        mkItem({ id: "prov", course: "STARTER" }),
        mkItem({ id: "rabas", course: "STARTER" }),
        mkItem({ id: "bife", course: "MAIN" }),
      ]),
    ]
    const tickets = kdsTickets(orders, "KITCHEN")
    expect(tickets).toHaveLength(2)
    expect(tickets[0].course).toBe("STARTER")
    expect(tickets[0].items.map((i) => i.id)).toEqual(["prov", "rabas"])
    expect(tickets[1].course).toBe("MAIN")
  })

  it("shows HELD courses (mise en place) but sends them to the end", () => {
    const orders = [
      order("o1", [
        mkItem({ id: "bife", course: "MAIN", status: "HELD", sent_at: null }),
        mkItem({
          id: "prov",
          course: "STARTER",
          status: "SENT",
          sent_at: "2026-06-24T20:00:00Z",
        }),
      ]),
    ]
    const tickets = kdsTickets(orders, "KITCHEN")
    expect(tickets.map((t) => t.course)).toEqual(["STARTER", "MAIN"])
    expect(tickets[0].held).toBe(false)
    expect(tickets[1].held).toBe(true) // en espera: se ve, no apura
  })

  it("canStart while any dish is still SENT, then it's 'Listo'", () => {
    const mixed = kdsTickets(
      [order("o1", [mkItem({ id: "a", status: "PREPARING" }), mkItem({ id: "b", status: "SENT" })])],
      "KITCHEN"
    )
    expect(mixed[0].canStart).toBe(true)

    const cooking = kdsTickets(
      [order("o2", [mkItem({ id: "a", status: "PREPARING" })])],
      "KITCHEN"
    )
    expect(cooking[0].canStart).toBe(false)
  })
})

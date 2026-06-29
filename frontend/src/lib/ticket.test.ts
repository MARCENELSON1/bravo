import { describe, expect, it } from "vitest"

import type { OrderDTO, OrderItemDTO } from "@/api/types-operations"
import { receiptHtml, ticketHtml } from "@/lib/ticket"

const mkItem = (over: Partial<OrderItemDTO>): OrderItemDTO => ({
  id: "i",
  product_id: "p",
  name: "Milanesa",
  unit_price_amount: 1000,
  quantity: 1,
  note: null,
  status: "SENT",
  station: "KITCHEN",
  sent_at: null,
  ...over,
})

const order = (items: OrderItemDTO[]): OrderDTO => ({
  id: "o1",
  table_id: "t1",
  waiter_id: "w",
  status: "SENT",
  currency: "ARS",
  items,
  total_amount: 0,
  created_at: null,
})

describe("ticketHtml", () => {
  it("groups items under their station header", () => {
    const html = ticketHtml(
      order([
        mkItem({ id: "a", name: "Milanesa", station: "KITCHEN", quantity: 2 }),
        mkItem({ id: "b", name: "Café", station: "BAR" }),
      ]),
      "Mesa 5",
      "27/06 20:00"
    )
    expect(html).toContain("Mesa 5")
    expect(html).toContain("COCINA")
    expect(html).toContain("BARRA")
    expect(html).toContain("2×")
    expect(html).toContain("Milanesa")
    expect(html).toContain("Café")
  })

  it("filters to a single station when given one", () => {
    const html = ticketHtml(
      order([
        mkItem({ id: "a", name: "Milanesa", station: "KITCHEN" }),
        mkItem({ id: "b", name: "Café", station: "BAR" }),
      ]),
      "Mesa 5",
      "27/06 20:00",
      "BAR"
    )
    expect(html).toContain("Café")
    expect(html).not.toContain("Milanesa")
    expect(html).not.toContain("COCINA")
  })

  it("renders the note and escapes HTML", () => {
    const html = ticketHtml(
      order([mkItem({ id: "a", name: "Té <b>", note: "sin azúcar" })]),
      "Mesa 1",
      "27/06"
    )
    expect(html).toContain("sin azúcar")
    expect(html).toContain("Té &lt;b&gt;")
    expect(html).not.toContain("<b>")
  })

  it("shows a placeholder when there are no items for the station", () => {
    const html = ticketHtml(order([mkItem({ station: "KITCHEN" })]), "Mesa 1", "27/06", "BAR")
    expect(html).toContain("sin ítems")
  })
})

describe("receiptHtml", () => {
  const item: OrderItemDTO = {
    id: "a",
    product_id: "p",
    name: "Milanesa",
    unit_price_amount: 150000,
    quantity: 2,
    note: null,
    status: "SERVED",
    station: "KITCHEN",
    sent_at: null,
  }
  const order: OrderDTO = {
    id: "o1",
    table_id: "t1",
    waiter_id: "w",
    status: "PAID",
    currency: "ARS",
    items: [item],
    total_amount: 300000,
    created_at: null,
  }

  it("renders items, the total and how it was paid", () => {
    const html = receiptHtml(order, "Mesa 5", "28/06 21:00", [
      { label: "Efectivo", amount: 300000 },
    ])
    expect(html).toContain("RECIBO NO FISCAL")
    expect(html).toContain("Mesa 5")
    expect(html).toContain("Milanesa")
    expect(html).toContain("TOTAL")
    expect(html).toContain("Efectivo")
  })

  it("shows a tip line when there's a tip, and omits it otherwise", () => {
    const withTip = receiptHtml(order, "Mesa 5", "28/06 21:00", [], 5000)
    expect(withTip).toContain("Propina")
    const noTip = receiptHtml(order, "Mesa 5", "28/06 21:00", [])
    expect(noTip).not.toContain("Propina")
  })
})

import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { OrdersApi } from "@/api/orders-api"

describe("OrdersApi", () => {
  it("creates an order with the table id (and optional client id) in the body", async () => {
    const request = vi.fn().mockResolvedValue({ order_id: "o1" })
    const api = new OrdersApi({ request } as unknown as HttpClient)

    await api.create("tbl-1", "ord-9")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/orders")
    expect(options).toMatchObject({ body: { table_id: "tbl-1", id: "ord-9" }, auth: true })
  })

  it("adds an item with its client id, product, quantity and note", async () => {
    const request = vi.fn().mockResolvedValue({})
    const api = new OrdersApi({ request } as unknown as HttpClient)

    await api.addItem("o1", "it-7", "p1", 2, null)

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/orders/o1/items")
    expect(options).toMatchObject({
      body: { id: "it-7", product_id: "p1", quantity: 2, note: null },
      auth: true,
    })
  })

  it("adds items in batch with an optional send flag", async () => {
    const request = vi.fn().mockResolvedValue({})
    const api = new OrdersApi({ request } as unknown as HttpClient)

    const items = [{ id: "it-1", product_id: "p1", quantity: 1, note: null }]
    await api.addItemsBatch("o1", items, true)

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/orders/o1/items/batch")
    expect(options).toMatchObject({ body: { items, send: true }, auth: true })
  })

  it("hits the KDS endpoint", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new OrdersApi({ request } as unknown as HttpClient)

    await api.kds()

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/kds/orders")
  })
})

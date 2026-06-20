import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { PaymentsApi } from "@/api/payments-api"

describe("PaymentsApi", () => {
  it("registers a cobro for an order with method + amount", async () => {
    const request = vi.fn().mockResolvedValue({ id: "p1", status: "CONFIRMED" })
    const api = new PaymentsApi({ request } as unknown as HttpClient)

    await api.registerForOrder("o1", { method: "CASH", amount: 300000 })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/orders/o1/payments")
    expect(options).toMatchObject({ body: { method: "CASH", amount: 300000 }, auth: true })
  })

  it("registers an egreso against /expenses", async () => {
    const request = vi.fn().mockResolvedValue({ id: "e1", direction: "OUTFLOW" })
    const api = new PaymentsApi({ request } as unknown as HttpClient)

    await api.registerExpense({
      method: "TRANSFER",
      amount: 500000,
      category: "Proveedores",
      counterparty: "Frigorífico Sur",
      description: null,
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/expenses")
    expect(options).toMatchObject({ auth: true })
    expect(options.body).toMatchObject({ method: "TRANSFER", amount: 500000 })
  })

  it("lists payments for an order", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new PaymentsApi({ request } as unknown as HttpClient)

    await api.listForOrder("o1")

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/orders/o1/payments")
  })
})

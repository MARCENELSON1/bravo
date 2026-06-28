import { describe, expect, it, vi } from "vitest"

import { CashApi } from "@/api/cash-api"
import type { HttpClient } from "@/api/http-client"

describe("CashApi", () => {
  it("opens a session with the opening float", async () => {
    const request = vi.fn().mockResolvedValue({})
    const api = new CashApi({ request } as unknown as HttpClient)

    await api.open(50000)

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/cashier/session/open")
    expect(options).toMatchObject({
      body: { opening_float_amount: 50000, note: null },
      auth: true,
    })
  })

  it("reads the current session", async () => {
    const request = vi.fn().mockResolvedValue(null)
    const api = new CashApi({ request } as unknown as HttpClient)

    await api.current()

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/cashier/session/current")
  })

  it("closes a session with the counted amounts per method", async () => {
    const request = vi.fn().mockResolvedValue({})
    const api = new CashApi({ request } as unknown as HttpClient)

    await api.close("s1", { CASH: 79500, CARD: 20000 })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/cashier/session/s1/close")
    expect(options).toMatchObject({
      body: { counted: { CASH: 79500, CARD: 20000 }, note: null },
      auth: true,
    })
  })
})

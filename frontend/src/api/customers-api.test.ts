import { describe, expect, it, vi } from "vitest"

import { CustomersApi } from "@/api/customers-api"
import type { HttpClient } from "@/api/http-client"

describe("CustomersApi", () => {
  it("lists customers with a search query", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new CustomersApi({ request } as unknown as HttpClient)

    await api.list("juan")
    expect(request.mock.calls[0][1]).toBe("/customers?search=juan")

    await api.list()
    expect(request.mock.calls[1][1]).toBe("/customers")
  })

  it("creates a customer", async () => {
    const request = vi.fn().mockResolvedValue({ id: "c1" })
    const api = new CustomersApi({ request } as unknown as HttpClient)

    await api.create({ name: "Ana", phone: "1122334455" })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/customers")
    expect(options).toMatchObject({ body: { name: "Ana", phone: "1122334455" }, auth: true })
  })
})

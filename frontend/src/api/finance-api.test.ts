import { describe, expect, it, vi } from "vitest"

import { FinanceApi } from "@/api/finance-api"
import type { HttpClient } from "@/api/http-client"

describe("FinanceApi", () => {
  it("fetches the overview without a window", async () => {
    const request = vi.fn().mockResolvedValue({ kpis: [] })
    const api = new FinanceApi({ request } as unknown as HttpClient)

    await api.overview()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/finance/overview")
    expect(options).toMatchObject({ auth: true })
  })

  it("passes the from/to window as query params", async () => {
    const request = vi.fn().mockResolvedValue({ kpis: [] })
    const api = new FinanceApi({ request } as unknown as HttpClient)

    await api.overview({ from: "2026-06-01T00:00:00Z", to: "2026-06-30T00:00:00Z" })

    const path = request.mock.calls[0][1]
    expect(path).toContain("from=")
    expect(path).toContain("to=")
  })
})

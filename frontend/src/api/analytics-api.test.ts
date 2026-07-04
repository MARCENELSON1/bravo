import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { AnalyticsApi } from "@/api/analytics-api"

describe("AnalyticsApi", () => {
  it("requests the revenue summary with the period", async () => {
    const request = vi.fn().mockResolvedValue({ currency: "ARS", sales_amount: 0 })
    const api = new AnalyticsApi({ request } as unknown as HttpClient)

    await api.revenue({ from: "2026-06-01T00:00:00.000Z", to: "2026-06-30T23:59:59.000Z" })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/analytics/revenue?")
    expect(path).toContain("from=2026-06-01")
    expect(options).toMatchObject({ auth: true })
  })

  it("omits the query string when no period is given", async () => {
    const request = vi.fn().mockResolvedValue({ currency: "ARS" })
    const api = new AnalyticsApi({ request } as unknown as HttpClient)

    await api.revenue()

    expect(request.mock.calls[0][1]).toBe("/analytics/revenue")
  })

  it("requests the daily revenue series with the period", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new AnalyticsApi({ request } as unknown as HttpClient)

    await api.revenueDaily({ from: "2026-06-28T00:00:00.000Z" })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/analytics/revenue/daily?")
    expect(path).toContain("from=2026-06-28")
    expect(options).toMatchObject({ auth: true })
  })

  it("passes the limit to product performance", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new AnalyticsApi({ request } as unknown as HttpClient)

    await api.products({ limit: 5 })

    expect(request.mock.calls[0][1]).toContain("limit=5")
  })

  it("triggers a rebuild via POST", async () => {
    const request = vi.fn().mockResolvedValue({ projected: 3 })
    const api = new AnalyticsApi({ request } as unknown as HttpClient)

    await api.rebuild()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/analytics/rebuild")
    expect(options).toMatchObject({ auth: true })
  })
})

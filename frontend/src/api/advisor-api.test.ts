import { describe, expect, it, vi } from "vitest"

import { AdvisorApi } from "@/api/advisor-api"
import type { HttpClient } from "@/api/http-client"

describe("AdvisorApi", () => {
  it("requests the report with the period", async () => {
    const request = vi.fn().mockResolvedValue({ kpis: {}, insights: [], summary: null })
    const api = new AdvisorApi({ request } as unknown as HttpClient)

    await api.report({ from: "2026-06-01T00:00:00.000Z", to: "2026-06-30T23:59:59.000Z" })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/advisor/report?")
    expect(path).toContain("from=2026-06-01")
    expect(options).toMatchObject({ auth: true })
  })

  it("omits the query string when no period is given", async () => {
    const request = vi.fn().mockResolvedValue({})
    const api = new AdvisorApi({ request } as unknown as HttpClient)

    await api.report()

    expect(request.mock.calls[0][1]).toBe("/advisor/report")
  })

  it("updates the cost settings via PUT", async () => {
    const request = vi.fn().mockResolvedValue({ configured: true })
    const api = new AdvisorApi({ request } as unknown as HttpClient)

    await api.updateSettings({
      monthly_labor_cost: 9_000_000,
      monthly_other_fixed_costs: 6_000_000,
      target_food_cost_bps: 3000,
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("PUT")
    expect(path).toBe("/advisor/settings")
    expect(options.body).toMatchObject({ monthly_labor_cost: 9_000_000 })
  })
})

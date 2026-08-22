import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { ReportsApi } from "@/api/reports-api"

describe("ReportsApi.exportCsv", () => {
  it("downloads the CSV export with the period window", async () => {
    const download = vi.fn().mockResolvedValue({ blob: new Blob(), filename: "ventas.csv" })
    const api = new ReportsApi({ request: vi.fn(), download } as unknown as HttpClient)

    await api.exportCsv("sales", { from: "2026-01-01T00:00:00Z", to: "2026-01-31T00:00:00Z" })

    const [path, options] = download.mock.calls[0]
    expect(path).toContain("/reports/export/sales.csv")
    expect(path).toContain("from=")
    expect(path).toContain("to=")
    expect(options).toMatchObject({ auth: true })
  })

  it("omits the query string when no window is given", async () => {
    const download = vi.fn().mockResolvedValue({ blob: new Blob(), filename: null })
    const api = new ReportsApi({ request: vi.fn(), download } as unknown as HttpClient)

    await api.exportCsv("vat_sales")

    expect(download.mock.calls[0][0]).toBe("/reports/export/vat_sales.csv")
  })
})

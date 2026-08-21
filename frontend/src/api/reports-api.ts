import type { HttpClient } from "@/api/http-client"
import type { DashboardSummaryDTO } from "@/api/types-operations"

export class ReportsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  getDashboard(params: { from?: string; to?: string } = {}): Promise<DashboardSummaryDTO> {
    const qs = new URLSearchParams()
    if (params.from) qs.set("from", params.from)
    if (params.to) qs.set("to", params.to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.request<DashboardSummaryDTO>("GET", `/reports/dashboard${suffix}`, {
      auth: true,
    })
  }
}

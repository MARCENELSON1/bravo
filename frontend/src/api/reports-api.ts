import type { HttpClient } from "@/api/http-client"
import type { DashboardSummaryDTO } from "@/api/types-operations"

export class ReportsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  getDashboard(): Promise<DashboardSummaryDTO> {
    return this.http.request<DashboardSummaryDTO>("GET", "/reports/dashboard", { auth: true })
  }
}

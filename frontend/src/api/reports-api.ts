import type { DownloadResult, HttpClient } from "@/api/http-client"
import type { DashboardSummaryDTO } from "@/api/types-operations"

export type ReportExportKind = "sales" | "expenses" | "vat_sales"

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

  // Descarga un CSV para el contador (ventas / gastos / libro IVA) del período.
  exportCsv(
    kind: ReportExportKind,
    params: { from?: string; to?: string } = {}
  ): Promise<DownloadResult> {
    const qs = new URLSearchParams()
    if (params.from) qs.set("from", params.from)
    if (params.to) qs.set("to", params.to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.download(`/reports/export/${kind}.csv${suffix}`, { auth: true })
  }
}

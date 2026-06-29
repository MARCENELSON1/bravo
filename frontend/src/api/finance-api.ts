import type { HttpClient } from "@/api/http-client"
import type { FinanceOverviewDTO } from "@/api/types-operations"

export interface FinanceQuery {
  from?: string // ISO
  to?: string // ISO
}

// Data client de la Pantalla Finanzas: un solo payload con los KPIs vitales,
// comparativo, diagnósticos y margen por producto.
export class FinanceApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  overview(query: FinanceQuery = {}): Promise<FinanceOverviewDTO> {
    const params = new URLSearchParams()
    if (query.from) params.set("from", query.from)
    if (query.to) params.set("to", query.to)
    const qs = params.toString()
    return this.http.request<FinanceOverviewDTO>(
      "GET",
      `/finance/overview${qs ? `?${qs}` : ""}`,
      { auth: true }
    )
  }
}

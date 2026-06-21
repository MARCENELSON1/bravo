import type { HttpClient } from "@/api/http-client"
import type {
  AnalyticsQuery,
  PaymentMixRowDTO,
  ProductPerformanceRowDTO,
  RevenueSummaryDTO,
} from "@/api/types-analytics"

// Data client for analytics: KPIs read from the canonical model. OWNER/MANAGER.
export class AnalyticsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  private period(query: AnalyticsQuery): string {
    const qs = new URLSearchParams()
    if (query.from) qs.set("from", query.from)
    if (query.to) qs.set("to", query.to)
    if (query.limit) qs.set("limit", String(query.limit))
    return qs.toString() ? `?${qs.toString()}` : ""
  }

  revenue(query: AnalyticsQuery = {}): Promise<RevenueSummaryDTO> {
    return this.http.request<RevenueSummaryDTO>("GET", `/analytics/revenue${this.period(query)}`, {
      auth: true,
    })
  }

  paymentMix(query: AnalyticsQuery = {}): Promise<PaymentMixRowDTO[]> {
    return this.http.request<PaymentMixRowDTO[]>(
      "GET",
      `/analytics/payment-mix${this.period(query)}`,
      { auth: true }
    )
  }

  products(query: AnalyticsQuery = {}): Promise<ProductPerformanceRowDTO[]> {
    return this.http.request<ProductPerformanceRowDTO[]>(
      "GET",
      `/analytics/products${this.period(query)}`,
      { auth: true }
    )
  }

  rebuild(): Promise<{ projected: number }> {
    return this.http.request<{ projected: number }>("POST", "/analytics/rebuild", { auth: true })
  }
}

import type { HttpClient } from "@/api/http-client"
import type {
  AdvisorQuery,
  AdvisorReportDTO,
  AdvisorSettingsDTO,
  UpdateAdvisorSettingsBody,
} from "@/api/types-advisor"

// Data client for the financial advisor: KPIs + insights + cost settings.
export class AdvisorApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  report(query: AdvisorQuery = {}): Promise<AdvisorReportDTO> {
    const qs = new URLSearchParams()
    if (query.from) qs.set("from", query.from)
    if (query.to) qs.set("to", query.to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.request<AdvisorReportDTO>("GET", `/advisor/report${suffix}`, { auth: true })
  }

  settings(): Promise<AdvisorSettingsDTO> {
    return this.http.request<AdvisorSettingsDTO>("GET", "/advisor/settings", { auth: true })
  }

  updateSettings(body: UpdateAdvisorSettingsBody): Promise<AdvisorSettingsDTO> {
    return this.http.request<AdvisorSettingsDTO>("PUT", "/advisor/settings", {
      body,
      auth: true,
    })
  }
}

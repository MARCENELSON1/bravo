import type { HttpClient } from "@/api/http-client"
import type { SelfOrderSettingsDTO } from "@/api/types-operations"

// Config del autopedido (Carta QR F2). Lado dueño (OWNER/MANAGER): prender el
// autopedido por QR + el gate de confirmación del mozo.
export class SelfOrderApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  settings(): Promise<SelfOrderSettingsDTO> {
    return this.http.request<SelfOrderSettingsDTO>("GET", "/self-order/settings", {
      auth: true,
    })
  }

  updateSettings(settings: SelfOrderSettingsDTO): Promise<SelfOrderSettingsDTO> {
    return this.http.request<SelfOrderSettingsDTO>("PUT", "/self-order/settings", {
      body: settings,
      auth: true,
    })
  }
}

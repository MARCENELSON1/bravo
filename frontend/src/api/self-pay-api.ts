import type { HttpClient } from "@/api/http-client"
import type { SelfPaySettingsDTO } from "@/api/types-operations"

// Config del pago desde la mesa (Carta QR F3). Lado dueño (OWNER/MANAGER): prender
// el cobro online del comensal + decidir si la pantalla de pago ofrece propina.
export class SelfPayApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  settings(): Promise<SelfPaySettingsDTO> {
    return this.http.request<SelfPaySettingsDTO>("GET", "/self-pay/settings", {
      auth: true,
    })
  }

  updateSettings(settings: SelfPaySettingsDTO): Promise<SelfPaySettingsDTO> {
    return this.http.request<SelfPaySettingsDTO>("PUT", "/self-pay/settings", {
      body: settings,
      auth: true,
    })
  }
}

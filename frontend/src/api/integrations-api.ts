import type { HttpClient } from "@/api/http-client"
import type { MpConnectionDTO } from "@/api/types-operations"

// Data client for payment-provider connections (Fase 3.5: MercadoPago OAuth).
export class IntegrationsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  getMpStatus(): Promise<MpConnectionDTO> {
    return this.http.request<MpConnectionDTO>("GET", "/integrations/mercadopago", { auth: true })
  }

  getMpConnectUrl(): Promise<{ url: string }> {
    return this.http.request<{ url: string }>("GET", "/integrations/mercadopago/connect", {
      auth: true,
    })
  }

  disconnectMp(): Promise<void> {
    return this.http.request<void>("DELETE", "/integrations/mercadopago", { auth: true })
  }
}

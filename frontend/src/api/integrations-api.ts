import type { HttpClient } from "@/api/http-client"
import type { AfipConnectBody, AfipConnectionDTO } from "@/api/types-invoicing"
import type { MpConnectionDTO } from "@/api/types-operations"

// Data client for provider connections: MercadoPago (Fase 3.5, OAuth) and AFIP
// (Fase 4, per-tenant cert/key).
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

  getAfipStatus(): Promise<AfipConnectionDTO> {
    return this.http.request<AfipConnectionDTO>("GET", "/integrations/afip", { auth: true })
  }

  connectAfip(body: AfipConnectBody): Promise<void> {
    return this.http.request<void>("PUT", "/integrations/afip", { body, auth: true })
  }

  disconnectAfip(): Promise<void> {
    return this.http.request<void>("DELETE", "/integrations/afip", { auth: true })
  }
}

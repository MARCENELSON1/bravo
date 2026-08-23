import type { HttpClient } from "@/api/http-client"
import type { FiscalAddressInput, FiscalSettingsDTO } from "@/api/types-tenant"

// Datos fiscales del local: régimen/moneda + la dirección que usa el motor de
// impuestos (TaxJar) para calcular la tasa por zona. OWNER/MANAGER.
export class TenantsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  fiscalSettings(): Promise<FiscalSettingsDTO> {
    return this.http.request<FiscalSettingsDTO>("GET", "/tenants/fiscal-settings", {
      auth: true,
    })
  }

  updateFiscalAddress(body: FiscalAddressInput): Promise<FiscalSettingsDTO> {
    return this.http.request<FiscalSettingsDTO>("PUT", "/tenants/fiscal-address", {
      body,
      auth: true,
    })
  }
}

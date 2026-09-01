import type { HttpClient } from "@/api/http-client"

// Carta pública (QR de mesa). Endpoint SIN auth: el token firmado porta el tenant.
export interface PublicMenuItemDTO {
  id: string
  name: string
  price_amount: number
}

export interface PublicMenuCategoryDTO {
  // null = productos sin categoría (la UI les pone una etiqueta).
  name: string | null
  items: PublicMenuItemDTO[]
}

export interface PublicMenuDTO {
  tenant_name: string
  currency: string
  locale: string
  categories: PublicMenuCategoryDTO[]
}

export class PublicMenuApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  // Sin `auth: true`: la carta es pública y el token es el scope del tenant.
  getMenu(token: string): Promise<PublicMenuDTO> {
    return this.http.request<PublicMenuDTO>(
      "GET",
      `/public/menu?token=${encodeURIComponent(token)}`
    )
  }
}

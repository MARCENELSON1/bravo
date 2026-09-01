import type { HttpClient } from "@/api/http-client"

// Carta pública (QR de mesa). Endpoint SIN auth: el token firmado porta el tenant.
export interface PublicMenuItemDTO {
  id: string
  name: string
  price_amount: number
  // Enriquecimiento (Carta QR F2). Opcionales → una carta vieja sigue andando.
  image_url?: string | null
  description?: string | null
  available_today?: boolean
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
  // Gate del autopedido (Carta QR F2). `enabled` off → la carta no muestra carrito;
  // `requires_confirmation` → el pedido espera al mozo (si no, va directo a cocina).
  self_order_enabled?: boolean
  self_order_requires_confirmation?: boolean
}

// El comensal manda solo id + cantidad (+ nota). El precio lo resuelve el server
// desde el catálogo — un carrito manipulado NUNCA cambia el total.
export interface CustomerOrderLineDTO {
  product_id: string
  quantity: number
  note?: string | null
}

export interface CustomerOrderResultDTO {
  order_id: string
  status: string
  requires_confirmation: boolean
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

  // "Llamar al mozo" / "Pedir la cuenta": notifican al salón en vivo (sin crear
  // orden). El token porta el tenant + la mesa.
  callWaiter(token: string): Promise<void> {
    return this.http.request<void>("POST", "/public/table/call-waiter", { body: { token } })
  }

  requestBill(token: string): Promise<void> {
    return this.http.request<void>("POST", "/public/table/request-bill", { body: { token } })
  }

  // Autopedido: el comensal envía su carrito → cae como una comanda real. Sin auth;
  // el token porta el tenant + la mesa. El server valida disponibilidad y precio.
  submitOrder(token: string, lines: CustomerOrderLineDTO[]): Promise<CustomerOrderResultDTO> {
    return this.http.request<CustomerOrderResultDTO>("POST", "/public/table/order", {
      body: { token, lines },
    })
  }
}

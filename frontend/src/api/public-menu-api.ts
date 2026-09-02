import type { HttpClient } from "@/api/http-client"

// Carta pública (QR de mesa). Endpoint SIN auth: el token firmado porta el tenant.
export interface PublicMenuModifierOptionDTO {
  id: string
  name: string
  price_delta: number
}

export interface PublicMenuModifierGroupDTO {
  id: string
  name: string
  min_select: number
  max_select: number
  required: boolean
  options: PublicMenuModifierOptionDTO[]
}

export interface PublicMenuItemDTO {
  id: string
  name: string
  price_amount: number
  // Enriquecimiento (Carta QR F2). Opcionales → una carta vieja sigue andando.
  image_url?: string | null
  description?: string | null
  available_today?: boolean
  modifier_groups?: PublicMenuModifierGroupDTO[]
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
  option_ids?: string[]
}

export interface CustomerOrderResultDTO {
  order_id: string
  status: string
  requires_confirmation: boolean
}

// --- Pago desde la mesa (Carta QR F3) ---------------------------------------
export interface TableBillOptionDTO {
  name: string
  price_delta: number
}

export interface TableBillItemDTO {
  name: string
  quantity: number
  unit_price: number
  selected_options?: TableBillOptionDTO[]
}

// La cuenta de la mesa (todo server-side, en minor units). `online_pay_available`
// = el local prendió el cobro Y tiene MercadoPago conectado; si no, se cae al
// "Pedir la cuenta" de F1. `tips_enabled` muestra/oculta el selector de propina.
export interface TableBillDTO {
  currency: string
  items: TableBillItemDTO[]
  total: number
  paid: number
  balance: number
  online_pay_available: boolean
  tips_enabled: boolean
}

export interface TablePayResultDTO {
  payment_id: string
  order_id: string
  status: string
  amount: number
  tip: number
  // A dónde mandar al comensal a pagar online; null si el cobro ya se confirmó.
  checkout_url?: string | null
}

export interface PublicPaymentStatusDTO {
  payment_id: string
  status: string
  amount: number
  tip: number
}

export interface PublicReceiptItemDTO {
  name: string
  quantity: number
  unit_price: number
  selected_options?: TableBillOptionDTO[]
}

// Recibo NO fiscal del comensal tras pagar (no es factura AFIP).
export interface PublicPaymentReceiptDTO {
  venue_name: string
  currency: string
  items: PublicReceiptItemDTO[]
  amount: number
  tip: number
  method: string
  paid_at?: string | null
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

  // La cuenta corriente de la mesa (total/pagado/saldo). Solo lectura.
  bill(token: string): Promise<TableBillDTO> {
    return this.http.request<TableBillDTO>(
      "GET",
      `/public/table/bill?token=${encodeURIComponent(token)}`
    )
  }

  // Inicia el pago de la mesa. El server acota el monto (saldo de la orden); el
  // cliente manda propina, una clave de idempotencia (contra el doble-tap) y, para
  // dividir la cuenta, un `amount` parcial opcional (null = pagar todo el saldo).
  // Si vuelve `checkout_url`, hay que mandar al comensal ahí (MercadoPago).
  pay(
    token: string,
    tip: number,
    amount: number | null,
    idempotencyKey: string
  ): Promise<TablePayResultDTO> {
    return this.http.request<TablePayResultDTO>("POST", "/public/table/pay", {
      body: { token, tip, amount, idempotency_key: idempotencyKey },
    })
  }

  // Poll del estado del pago (el estado autoritativo es el webhook, no el charge).
  paymentStatus(token: string, paymentId: string): Promise<PublicPaymentStatusDTO> {
    return this.http.request<PublicPaymentStatusDTO>(
      "GET",
      `/public/table/payment/${paymentId}?token=${encodeURIComponent(token)}`
    )
  }

  // Recibo del pago confirmado (local + ítems + monto + propina). Solo con el pago
  // ya confirmado; 404 si no.
  receipt(token: string, paymentId: string): Promise<PublicPaymentReceiptDTO> {
    return this.http.request<PublicPaymentReceiptDTO>(
      "GET",
      `/public/table/receipt/${paymentId}?token=${encodeURIComponent(token)}`
    )
  }
}

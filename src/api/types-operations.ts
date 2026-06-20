// DTOs for Fase 2 (comandas + KDS), mirroring the backend contract.

export type OrderStatus =
  | "OPEN"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
  | "PAID"
  | "CANCELLED"

export interface ProductDTO {
  id: string
  name: string
  price_amount: number // minor units (e.g. centavos)
  currency: string
  category: string | null
  active: boolean
}

export interface CreateProductResponse {
  product_id: string
}

export interface TableDTO {
  id: string
  number: number
  name: string | null
  active: boolean
}

export interface CreateTableResponse {
  table_id: string
}

export interface OrderItemDTO {
  id: string
  product_id: string
  name: string
  unit_price_amount: number
  quantity: number
  note: string | null
}

export interface OrderDTO {
  id: string
  table_id: string
  waiter_id: string
  status: OrderStatus
  currency: string
  items: OrderItemDTO[]
  total_amount: number
}

export interface CreateOrderResponse {
  order_id: string
}

// --- Fase 3: pagos (ingresos/egresos) ---

export type PaymentMethod = "CASH" | "CARD" | "TRANSFER" | "MERCADOPAGO" | "QR"
export type PaymentStatus = "PENDING" | "CONFIRMED" | "FAILED" | "REFUNDED"
export type PaymentDirection = "INFLOW" | "OUTFLOW"

export interface PaymentDTO {
  id: string
  direction: PaymentDirection
  order_id: string | null
  method: PaymentMethod
  amount: number // minor units (e.g. centavos)
  currency: string
  status: PaymentStatus
  category: string | null
  counterparty: string | null
  description: string | null
  // Present only for online charges awaiting confirmation (MercadoPago link/QR).
  checkout_url: string | null
}

export interface RegisterPaymentBody {
  method: PaymentMethod
  amount: number // minor units
}

export interface RegisterExpenseBody {
  method: PaymentMethod
  amount: number // minor units
  category: string | null
  counterparty: string | null
  description: string | null
}

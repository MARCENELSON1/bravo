// DTOs for Fase 2 (comandas + KDS), mirroring the backend contract.

export type OrderStatus =
  | "OPEN"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
  | "PAID"
  | "CANCELLED"

// Per-item kitchen lifecycle (Fase 14) + the station that prepares it.
export type ItemStatus =
  | "PENDING"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
  | "CANCELLED"
export type Station = "KITCHEN" | "BAR"

export interface ProductDTO {
  id: string
  name: string
  price_amount: number // minor units (e.g. centavos)
  currency: string
  category: string | null
  station: Station
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
  status: ItemStatus
  station: Station
  sent_at: string | null // ISO-8601; how long the item has waited on the KDS
}

// One item flattened with its order context — the unit the KDS board renders.
export interface KdsTicket {
  orderId: string
  tableId: string
  item: OrderItemDTO
}

export interface OrderDTO {
  id: string
  table_id: string
  waiter_id: string
  status: OrderStatus
  currency: string
  items: OrderItemDTO[]
  total_amount: number
  created_at: string | null // ISO-8601; used by the KDS waiting timer
}

export interface CreateOrderResponse {
  order_id: string
}

export interface FloorTableDTO {
  id: string
  number: number
  name: string | null
  status: "FREE" | "OCCUPIED"
  active_order: OrderDTO | null
}

export interface BatchOrderItemInput {
  id?: string // client-generated → idempotent
  product_id: string
  quantity: number
  note: string | null
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
  tip_amount: number // propina cobrada encima del amount (minor units)
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
  tip?: number // propina encima del amount (minor units); 0 si no se manda
}

export interface RegisterExpenseBody {
  method: PaymentMethod
  amount: number // minor units
  category: string | null
  counterparty: string | null
  description: string | null
}

// --- Fase 3.5: conexión de pasarela por tenant ---

export interface MpConnectionDTO {
  connected: boolean
  nickname: string | null
  external_account_id: string | null
  live_mode: boolean
}

// --- Fase 14: caja / arqueo Z ---

export interface CashSessionDTO {
  id: string
  status: "OPEN" | "CLOSED"
  currency: string
  opening_float_amount: number
  opened_at: string | null
}

export interface CashReportLineDTO {
  method: PaymentMethod
  expected: number // minor units
  tips: number // propina incluida en expected (minor units)
  counted: number | null
  difference: number | null
}

export interface CashReportDTO {
  session_id: string
  status: "OPEN" | "CLOSED"
  currency: string
  opening_float: number
  opened_at: string | null
  closed_at: string | null
  lines: CashReportLineDTO[]
  expected_total: number
  counted_total: number | null
  difference_total: number | null
  tips_total: number // total de propinas del turno (para repartir)
}

// --- Reporting ---

export interface DashboardSummaryDTO {
  currency: string
  sales: number // minor units
  expenses: number
  net: number
  active_orders: number
  paid_orders: number
  avg_ticket: number
  payment_count: number
}

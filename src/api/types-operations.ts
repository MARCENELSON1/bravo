// DTOs for Fase 2 (comandas + KDS), mirroring the backend contract.

export type OrderStatus =
  | "OPEN"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
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

import type { HttpClient } from "@/api/http-client"
import type {
  BatchOrderItemInput,
  Course,
  CreateOrderResponse,
  OrderDTO,
  Station,
} from "@/api/types-operations"
import type { TaxQuoteDTO } from "@/api/types-tenant"

export type OrderAction = "preparing" | "ready" | "served" | "cancel"
// Per-item bump/recall along the kitchen lifecycle.
export type ItemAction = "preparing" | "ready" | "served" | "recall"
// Un CURSO entero de una vez: el "Listo" del KDS por tiempo (no plato por plato).
export type CourseAction = "preparing" | "ready" | "served"

export class OrdersApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<OrderDTO[]> {
    return this.http.request<OrderDTO[]>("GET", "/orders", { auth: true })
  }

  get(id: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("GET", `/orders/${id}`, { auth: true })
  }

  // Impuesto a sumar sobre la orden (sales tax US vía TaxJar; 0 en AR/IVA).
  taxQuote(id: string): Promise<TaxQuoteDTO> {
    return this.http.request<TaxQuoteDTO>("GET", `/orders/${id}/tax-quote`, { auth: true })
  }

  create(tableId: string, id?: string): Promise<CreateOrderResponse> {
    return this.http.request<CreateOrderResponse>("POST", "/orders", {
      body: { table_id: tableId, ...(id ? { id } : {}) },
      auth: true,
    })
  }

  // CRM: atribuir (o desatribuir con null) el cliente de la comanda.
  assignCustomer(orderId: string, customerId: string | null): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("PUT", `/orders/${orderId}/customer`, {
      body: { customer_id: customerId },
      auth: true,
    })
  }

  addItem(
    orderId: string,
    itemId: string,
    productId: string,
    quantity: number,
    note: string | null
  ): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${orderId}/items`, {
      body: { id: itemId, product_id: productId, quantity, note },
      auth: true,
    })
  }

  removeItem(orderId: string, itemId: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("DELETE", `/orders/${orderId}/items/${itemId}`, {
      auth: true,
    })
  }

  setItemQuantity(orderId: string, itemId: string, quantity: number): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("PATCH", `/orders/${orderId}/items/${itemId}`, {
      body: { quantity },
      auth: true,
    })
  }

  // Add several items (and optionally send) in one round-trip. Each line carries
  // an optional client id so a replay is idempotent — used by the offline queue.
  addItemsBatch(
    orderId: string,
    items: BatchOrderItemInput[],
    send: boolean
  ): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${orderId}/items/batch`, {
      body: { items, send },
      auth: true,
    })
  }

  send(id: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/send`, { auth: true })
  }

  // Move this order to another table.
  transfer(id: string, tableId: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/transfer`, {
      body: { table_id: tableId },
      auth: true,
    })
  }

  // Absorb another order into this one (this order is the destination).
  merge(id: string, sourceOrderId: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/merge`, {
      body: { source_order_id: sourceOrderId },
      auth: true,
    })
  }

  // Reabrir una comanda pagada: revierte venta/stock; el backend bloquea si ya
  // tiene un comprobante fiscal autorizado.
  reopen(id: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/reopen`, { auth: true })
  }

  advance(id: string, action: OrderAction): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/${action}`, { auth: true })
  }

  // Bump (or recall) a single item along its kitchen lifecycle — drives the
  // per-station KDS board.
  advanceItem(orderId: string, itemId: string, action: ItemAction): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${orderId}/items/${itemId}/${action}`, {
      auth: true,
    })
  }

  // "Marchar principal": manda al fuego el curso en espera más bajo. El mozo lo
  // dispara cuando ve que la mesa terminó el tiempo anterior.
  fireNext(id: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/fire-next`, { auth: true })
  }

  // "Marchar todo": pendientes y en espera al fuego (la mesa quiere todo junto).
  fireAll(id: string): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/fire-all`, { auth: true })
  }

  // Bumpea un curso entero. `station` acota al tablero que lo pide.
  advanceCourse(
    orderId: string,
    course: Course,
    action: CourseAction,
    station?: Station
  ): Promise<OrderDTO> {
    const qs = station ? `?station=${station}` : ""
    return this.http.request<OrderDTO>(
      "POST",
      `/orders/${orderId}/courses/${course}/${action}${qs}`,
      { auth: true }
    )
  }

  // Override del tiempo de una línea ("la provoleta como principal").
  setItemCourse(orderId: string, itemId: string, course: Course): Promise<OrderDTO> {
    return this.http.request<OrderDTO>(
      "PATCH",
      `/orders/${orderId}/items/${itemId}/course`,
      { auth: true, body: { course } }
    )
  }

  kds(station?: Station): Promise<OrderDTO[]> {
    const path = station ? `/kds/orders?station=${station}` : "/kds/orders"
    return this.http.request<OrderDTO[]>("GET", path, { auth: true })
  }
}

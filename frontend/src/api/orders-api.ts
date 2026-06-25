import type { HttpClient } from "@/api/http-client"
import type {
  BatchOrderItemInput,
  CreateOrderResponse,
  OrderDTO,
} from "@/api/types-operations"

export type OrderAction = "preparing" | "ready" | "served" | "cancel"

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

  create(tableId: string, id?: string): Promise<CreateOrderResponse> {
    return this.http.request<CreateOrderResponse>("POST", "/orders", {
      body: { table_id: tableId, ...(id ? { id } : {}) },
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

  advance(id: string, action: OrderAction): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/${action}`, { auth: true })
  }

  kds(): Promise<OrderDTO[]> {
    return this.http.request<OrderDTO[]>("GET", "/kds/orders", { auth: true })
  }
}

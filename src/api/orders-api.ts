import type { HttpClient } from "@/api/http-client"
import type { CreateOrderResponse, OrderDTO } from "@/api/types-operations"

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

  create(tableId: string): Promise<CreateOrderResponse> {
    return this.http.request<CreateOrderResponse>("POST", "/orders", {
      body: { table_id: tableId },
      auth: true,
    })
  }

  addItem(id: string, productId: string, quantity: number, note: string | null): Promise<OrderDTO> {
    return this.http.request<OrderDTO>("POST", `/orders/${id}/items`, {
      body: { product_id: productId, quantity, note },
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

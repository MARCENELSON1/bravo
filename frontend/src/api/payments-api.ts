import type { HttpClient } from "@/api/http-client"
import type {
  PaymentDTO,
  RegisterExpenseBody,
  RegisterPaymentBody,
} from "@/api/types-operations"

// Data client for cobros (INFLOW, tied to an order) and egresos (OUTFLOW).
export class PaymentsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  registerForOrder(orderId: string, body: RegisterPaymentBody): Promise<PaymentDTO> {
    return this.http.request<PaymentDTO>("POST", `/orders/${orderId}/payments`, {
      body,
      auth: true,
    })
  }

  listForOrder(orderId: string): Promise<PaymentDTO[]> {
    return this.http.request<PaymentDTO[]>("GET", `/orders/${orderId}/payments`, { auth: true })
  }

  // Anular/reembolsar un cobro confirmado (money-only → pasa a REFUNDED).
  refund(paymentId: string): Promise<PaymentDTO> {
    return this.http.request<PaymentDTO>("POST", `/payments/${paymentId}/refund`, { auth: true })
  }

  registerExpense(body: RegisterExpenseBody): Promise<PaymentDTO> {
    return this.http.request<PaymentDTO>("POST", "/expenses", { body, auth: true })
  }

  listExpenses(): Promise<PaymentDTO[]> {
    return this.http.request<PaymentDTO[]>("GET", "/expenses", { auth: true })
  }
}

import { isApiError } from "@/api/api-error"
import type { HttpClient } from "@/api/http-client"
import type { InvoiceDTO, IssueInvoiceBody } from "@/api/types-invoicing"

// Data client for comprobantes (Fase 4: facturación electrónica AFIP).
export class InvoicesApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  issueForOrder(orderId: string, body: IssueInvoiceBody): Promise<InvoiceDTO> {
    return this.http.request<InvoiceDTO>("POST", `/orders/${orderId}/invoice`, {
      body,
      auth: true,
    })
  }

  // Returns null when the order has no invoice yet (the backend 404s).
  async getForOrder(orderId: string): Promise<InvoiceDTO | null> {
    try {
      return await this.http.request<InvoiceDTO>("GET", `/orders/${orderId}/invoice`, {
        auth: true,
      })
    } catch (error) {
      if (isApiError(error) && error.status === 404) return null
      throw error
    }
  }

  list(): Promise<InvoiceDTO[]> {
    return this.http.request<InvoiceDTO[]>("GET", "/invoices", { auth: true })
  }
}

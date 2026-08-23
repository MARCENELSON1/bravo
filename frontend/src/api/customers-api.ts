import type { HttpClient } from "@/api/http-client"

export interface CustomerDTO {
  id: string
  name: string
  phone: string | null
  email: string | null
  notes: string | null
  no_contactar: boolean
}

export interface CustomerInput {
  name: string
  phone?: string | null
  email?: string | null
  notes?: string | null
  no_contactar?: boolean
}

export interface CustomerHistoryDTO {
  customer_id: string
  currency: string
  visits: number
  total_spent: number // minor units
  last_visit_at: string | null // ISO-8601
}

export interface CustomerStatsRowDTO {
  customer_id: string
  name: string
  phone: string | null
  visits: number
  total_spent: number // minor units
  first_visit_at: string | null // ISO-8601
  last_visit_at: string | null // ISO-8601
}

export interface CustomerStatsDTO {
  currency: string
  rows: CustomerStatsRowDTO[]
}

// CRM (Fase 12): clientes del local. Manual por ahora; segmentos + acciones vienen
// después. El contacto es por wa.me (deep link, sin proveedor).
export class CustomersApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(search?: string): Promise<CustomerDTO[]> {
    const qs = search ? `?search=${encodeURIComponent(search)}` : ""
    return this.http.request<CustomerDTO[]>("GET", `/customers${qs}`, { auth: true })
  }

  create(input: CustomerInput): Promise<CustomerDTO> {
    return this.http.request<CustomerDTO>("POST", "/customers", { auth: true, body: input })
  }

  update(id: string, input: CustomerInput): Promise<CustomerDTO> {
    return this.http.request<CustomerDTO>("PUT", `/customers/${id}`, { auth: true, body: input })
  }

  remove(id: string): Promise<void> {
    return this.http.request<void>("DELETE", `/customers/${id}`, { auth: true })
  }

  history(id: string): Promise<CustomerHistoryDTO> {
    return this.http.request<CustomerHistoryDTO>("GET", `/customers/${id}/history`, {
      auth: true,
    })
  }

  stats(): Promise<CustomerStatsDTO> {
    return this.http.request<CustomerStatsDTO>("GET", "/customers/stats", { auth: true })
  }
}

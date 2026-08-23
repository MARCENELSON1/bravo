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
}

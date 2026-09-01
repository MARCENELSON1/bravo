import type { HttpClient } from "@/api/http-client"
import type { CreateTableResponse, TableDTO } from "@/api/types-operations"

// Token firmado + deep link que codifica el QR de una mesa (carta pública).
export interface TableQrDTO {
  token: string
  url: string
}

export class TablesApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<TableDTO[]> {
    return this.http.request<TableDTO[]>("GET", "/tables", { auth: true })
  }

  // Token/URL del QR de la mesa (idempotente; el token es determinístico).
  qr(tableId: string): Promise<TableQrDTO> {
    return this.http.request<TableQrDTO>("GET", `/tables/${tableId}/qr`, { auth: true })
  }

  create(number: number, name: string | null): Promise<CreateTableResponse> {
    return this.http.request<CreateTableResponse>("POST", "/tables", {
      body: { number, name },
      auth: true,
    })
  }

  // Partial update: only the keys present are touched (sector_id/capacity). Pass
  // null to clear a field; omit it to leave it as is.
  update(
    tableId: string,
    patch: { sector_id?: string | null; capacity?: number | null }
  ): Promise<TableDTO> {
    return this.http.request<TableDTO>("PATCH", `/tables/${tableId}`, {
      body: patch,
      auth: true,
    })
  }
}

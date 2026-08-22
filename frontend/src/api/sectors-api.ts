import type { HttpClient } from "@/api/http-client"
import type { SectorDTO } from "@/api/types-operations"

export interface SectorInput {
  name: string
  color?: string | null
  sort_order?: number
}

// Salon sectors (zones): group tables on the floor and, later, bill by sector.
export class SectorsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<SectorDTO[]> {
    return this.http.request<SectorDTO[]>("GET", "/sectors", { auth: true })
  }

  create(input: SectorInput): Promise<SectorDTO> {
    return this.http.request<SectorDTO>("POST", "/sectors", { auth: true, body: input })
  }

  update(id: string, input: SectorInput): Promise<SectorDTO> {
    return this.http.request<SectorDTO>("PUT", `/sectors/${id}`, { auth: true, body: input })
  }

  remove(id: string): Promise<void> {
    return this.http.request<void>("DELETE", `/sectors/${id}`, { auth: true })
  }
}

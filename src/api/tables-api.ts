import type { HttpClient } from "@/api/http-client"
import type { CreateTableResponse, TableDTO } from "@/api/types-operations"

export class TablesApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<TableDTO[]> {
    return this.http.request<TableDTO[]>("GET", "/tables", { auth: true })
  }

  create(number: number, name: string | null): Promise<CreateTableResponse> {
    return this.http.request<CreateTableResponse>("POST", "/tables", {
      body: { number, name },
      auth: true,
    })
  }
}

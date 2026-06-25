import type { HttpClient } from "@/api/http-client"
import type { FloorTableDTO } from "@/api/types-operations"

// Read model for the salon: every table with its derived status (free/occupied)
// and, when occupied, the active order embedded (so a tap opens it instead of
// creating a duplicate).
export class FloorApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<FloorTableDTO[]> {
    return this.http.request<FloorTableDTO[]>("GET", "/floor", { auth: true })
  }
}

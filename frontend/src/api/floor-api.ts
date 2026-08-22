import type { HttpClient } from "@/api/http-client"
import type { FloorTableDTO, SessionResponseDTO } from "@/api/types-operations"

// Read model for the salon: every table with its derived status (free/occupied),
// its session-aware live view (state/timer/pax), and, when occupied, the active
// order embedded (so a tap opens it instead of creating a duplicate).
export class FloorApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<FloorTableDTO[]> {
    return this.http.request<FloorTableDTO[]>("GET", "/floor", { auth: true })
  }

  openSession(input: {
    table_id: string
    pax?: number | null
    waiter_id?: string | null
  }): Promise<SessionResponseDTO> {
    return this.http.request<SessionResponseDTO>("POST", "/floor/sessions", {
      auth: true,
      body: input,
    })
  }

  requestBill(sessionId: string): Promise<SessionResponseDTO> {
    return this.http.request<SessionResponseDTO>(
      "POST",
      `/floor/sessions/${sessionId}/bill`,
      { auth: true }
    )
  }

  setPax(sessionId: string, pax: number): Promise<SessionResponseDTO> {
    return this.http.request<SessionResponseDTO>(
      "PATCH",
      `/floor/sessions/${sessionId}/pax`,
      { auth: true, body: { pax } }
    )
  }
}

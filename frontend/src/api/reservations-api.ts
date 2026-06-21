import type { HttpClient } from "@/api/http-client"
import type {
  CreateReservationBody,
  CreateReservationResponse,
  ReservationDTO,
  ReservationsQuery,
  UpdateReservationBody,
} from "@/api/types-reservations"

// Data client for reservations (agenda + lifecycle). Front of house.
export class ReservationsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(query: ReservationsQuery = {}): Promise<ReservationDTO[]> {
    const qs = new URLSearchParams()
    if (query.from) qs.set("from", query.from)
    if (query.to) qs.set("to", query.to)
    if (query.turn) qs.set("turn", query.turn)
    if (query.status) qs.set("status", query.status)
    if (query.tableId) qs.set("table_id", query.tableId)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.request<ReservationDTO[]>("GET", `/reservations${suffix}`, { auth: true })
  }

  create(body: CreateReservationBody): Promise<CreateReservationResponse> {
    return this.http.request<CreateReservationResponse>("POST", "/reservations", {
      body,
      auth: true,
    })
  }

  get(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("GET", `/reservations/${id}`, { auth: true })
  }

  update(id: string, body: UpdateReservationBody): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("PATCH", `/reservations/${id}`, { body, auth: true })
  }

  confirm(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("POST", `/reservations/${id}/confirm`, { auth: true })
  }

  seat(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("POST", `/reservations/${id}/seat`, { auth: true })
  }

  complete(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("POST", `/reservations/${id}/complete`, {
      auth: true,
    })
  }

  cancel(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("POST", `/reservations/${id}/cancel`, { auth: true })
  }

  noShow(id: string): Promise<ReservationDTO> {
    return this.http.request<ReservationDTO>("POST", `/reservations/${id}/no-show`, {
      auth: true,
    })
  }
}

// DTOs for the reservations API.

export type ReservationStatus =
  | "PENDING"
  | "CONFIRMED"
  | "SEATED"
  | "COMPLETED"
  | "CANCELLED"
  | "NO_SHOW"

export type ServiceTurn = "LUNCH" | "DINNER"

export interface ReservationDTO {
  id: string
  customer_name: string
  customer_phone: string | null
  party_size: number
  reserved_at: string
  turn: ServiceTurn
  table_id: string | null
  status: ReservationStatus
  note: string | null
  created_at: string | null
}

export interface CreateReservationBody {
  customer_name: string
  party_size: number
  reserved_at: string
  turn: ServiceTurn
  customer_phone?: string | null
  table_id?: string | null
  note?: string | null
}

export interface CreateReservationResponse {
  reservation_id: string
}

export interface UpdateReservationBody {
  party_size: number
  reserved_at: string
  turn: ServiceTurn
  table_id?: string | null
}

export interface ReservationsQuery {
  from?: string
  to?: string
  turn?: ServiceTurn
  status?: ReservationStatus
  tableId?: string
}

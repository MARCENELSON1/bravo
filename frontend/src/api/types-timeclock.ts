export type ShiftStatus = "OPEN" | "CLOSED"
export type ShiftSource = "SELF" | "PRESENCE" | "MANAGER"

export interface ShiftDTO {
  id: string
  user_id: string
  clock_in_at: string
  clock_out_at: string | null
  status: ShiftStatus
  source: ShiftSource
  worked_minutes: number | null
  note: string | null
  adjusted_by: string | null
}

export interface MyTimeclockDTO {
  open_shift: ShiftDTO | null
  recent: ShiftDTO[]
}

export interface AdjustShiftBody {
  clock_in_at: string
  clock_out_at: string | null
}

export interface ShiftsQuery {
  userId?: string
  from?: string
  to?: string
}

export interface StaffReportRowDTO {
  user_id: string
  email: string
  worked_minutes: number
  overtime_minutes: number
  tables_served: number
  sales_amount: number
  hourly_rate_amount: number | null // valor/hora en minor units; null → sin cargar
  currency: string
}

export interface StaffReportDTO {
  currency: string
  rows: StaffReportRowDTO[]
}

export interface PresenceChallengeDTO {
  qr_payload: string
  code: string
  expires_at: string
}

export interface PresenceDeviceDTO {
  device_token: string
}

import type { ReservationStatus } from "@/api/types-reservations"
import { dateLocale } from "@/lib/format"

// Los textos de estado y turno viven en el diccionario i18n
// (`reservations.statusLabels.*` y `reservations.turnLabels.*`); el consumidor
// los resuelve con `t()`. Acá solo queda lo que es código (variantes, formato).

type BadgeVariant = "default" | "secondary" | "outline" | "destructive"

export const RESERVATION_STATUS_VARIANT: Record<ReservationStatus, BadgeVariant> = {
  PENDING: "outline",
  CONFIRMED: "default",
  SEATED: "secondary",
  COMPLETED: "secondary",
  CANCELLED: "destructive",
  NO_SHOW: "destructive",
}

// ISO instant → HH:mm in local time (the agenda shows the hour of the turn).
export function formatReservedTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(dateLocale(), { hour: "2-digit", minute: "2-digit" })
}

// A date (YYYY-MM-DD) + time (HH:mm) typed by the user → ISO-8601 for the API.
export function toReservedAtIso(date: string, time: string): string {
  return new Date(`${date}T${time}`).toISOString()
}

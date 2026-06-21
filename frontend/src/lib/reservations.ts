import type { ReservationStatus, ServiceTurn } from "@/api/types-reservations"

export const RESERVATION_STATUS_LABELS: Record<ReservationStatus, string> = {
  PENDING: "Pendiente",
  CONFIRMED: "Confirmada",
  SEATED: "Sentada",
  COMPLETED: "Completada",
  CANCELLED: "Cancelada",
  NO_SHOW: "No-show",
}

export const SERVICE_TURN_LABELS: Record<ServiceTurn, string> = {
  LUNCH: "Almuerzo",
  DINNER: "Cena",
}

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
  return new Date(iso).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
}

// A date (YYYY-MM-DD) + time (HH:mm) typed by the user → ISO-8601 for the API.
export function toReservedAtIso(date: string, time: string): string {
  return new Date(`${date}T${time}`).toISOString()
}

// Formatting helpers for fichaje (kept out of component files so pages can
// export only components — Fast Refresh / eslint react-refresh rule).

export function formatMinutes(total: number): string {
  const hours = Math.floor(total / 60)
  const mins = total % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

export function formatClock(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })
}

// True when two instants fall on different calendar days (a shift that crosses
// midnight — common in hospitality). Lets the table flag the salida as "+1d".
export function isNextDay(fromIso: string, toIso: string): boolean {
  return new Date(fromIso).toDateString() !== new Date(toIso).toDateString()
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export const SHIFT_SOURCE_LABELS: Record<string, string> = {
  SELF: "Propio",
  PRESENCE: "Presencial",
  MANAGER: "Corrección",
}

// Minutes elapsed between an ISO instant and now (never negative).
export function minutesSince(iso: string, now: number): number {
  return Math.max(0, Math.floor((now - new Date(iso).getTime()) / 60000))
}

// ISO instant → value for a <input type="datetime-local"> (local tz, no seconds).
export function toDateTimeLocal(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`
}

// <input type="datetime-local"> value (local) → ISO-8601 for the API.
export function fromDateTimeLocal(value: string): string {
  return new Date(value).toISOString()
}

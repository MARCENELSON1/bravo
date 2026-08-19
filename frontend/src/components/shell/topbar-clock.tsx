import { useEffect, useState } from "react"

// Hora actual en vivo (HH:MM, formato Argentina). Se actualiza cada segundo.
export function TopbarClock() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const time = now.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })

  return <span className="text-sm font-medium tabular-nums text-muted-foreground">{time}</span>
}

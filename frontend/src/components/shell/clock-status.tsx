import { useEffect, useState } from "react"
import { Clock } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useMyTimeclock } from "@/hooks/use-timeclock"
import { formatMinutes, minutesSince } from "@/lib/timeclock"

// Topbar status indicator (read-only re: punching): shows whether the logged-in
// user is on a shift and for how long. It does NOT clock in/out — that goes
// through the presence flow (QR / code) so presence is actually proven. Tapping
// it just navigates to the Fichar page.
export function ClockStatus() {
  const me = useMyTimeclock()
  const navigate = useNavigate()
  const [now, setNow] = useState(() => Date.now())

  const openShift = me.data?.open_shift ?? null

  useEffect(() => {
    if (!openShift) return
    const id = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(id)
  }, [openShift])

  // Never block the shell if the timeclock can't load.
  if (me.isPending || me.isError) return null

  return (
    <Button
      variant={openShift ? "default" : "outline"}
      size="sm"
      onClick={() => navigate("/app/fichar")}
      className="gap-2"
      title="Ir a Fichar"
    >
      <Clock className="size-4" />
      {openShift ? (
        <span className="tabular-nums">
          En turno · {formatMinutes(minutesSince(openShift.clock_in_at, now))}
        </span>
      ) : (
        "Fuera de turno"
      )}
    </Button>
  )
}

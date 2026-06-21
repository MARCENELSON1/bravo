import { useEffect, useState } from "react"
import { Clock } from "lucide-react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import { useMyTimeclock, usePunch } from "@/hooks/use-timeclock"
import { formatMinutes, minutesSince } from "@/lib/timeclock"

// Topbar widget: one button that toggles the worker's own shift (entrada/salida)
// and shows the running time while a shift is open. Every logged-in employee
// fiches themselves (identity = the session user).
export function ClockToggle() {
  const me = useMyTimeclock()
  const punch = usePunch()
  const [now, setNow] = useState(() => Date.now())

  const openShift = me.data?.open_shift ?? null

  useEffect(() => {
    if (!openShift) return
    const id = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(id)
  }, [openShift])

  // Never block the shell if the timeclock can't load.
  if (me.isPending || me.isError) return null

  const handle = () => {
    punch.mutate(undefined, {
      onSuccess: (shift) =>
        toast.success(shift.status === "OPEN" ? "Entrada registrada." : "Salida registrada."),
      onError: (error) =>
        toast.error(isApiError(error) ? error.message : "No pudimos registrar el fichaje."),
    })
  }

  return (
    <Button
      variant={openShift ? "default" : "outline"}
      size="sm"
      onClick={handle}
      disabled={punch.isPending}
      className="gap-2"
    >
      <Clock className="size-4" />
      {openShift ? (
        <span className="tabular-nums">
          Salida · {formatMinutes(minutesSince(openShift.clock_in_at, now))}
        </span>
      ) : (
        "Fichar entrada"
      )}
    </Button>
  )
}

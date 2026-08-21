import { useEffect, useRef, useState } from "react"
import { Clock } from "lucide-react"
import { useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useMyTimeclock } from "@/hooks/use-timeclock"
import { formatMinutes, minutesSince } from "@/lib/timeclock"

// Estado de turno en el topbar. En desktop: botón con el texto completo que lleva a
// Fichar. En móvil: un relojito compacto que, al tocarlo, muestra la info en un
// popover (así no ocupa toda la barra). No fichas desde acá — eso va por presencia.
export function ClockStatus() {
  const me = useMyTimeclock()
  const navigate = useNavigate()
  const [now, setNow] = useState(() => Date.now())
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  const openShift = me.data?.open_shift ?? null

  useEffect(() => {
    if (!openShift) return
    const id = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(id)
  }, [openShift])

  useEffect(() => {
    if (!open) return
    const onDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false)
    }
    document.addEventListener("pointerdown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("pointerdown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  // Never block the shell if the timeclock can't load.
  if (me.isPending || me.isError) return null

  const duration = openShift ? formatMinutes(minutesSince(openShift.clock_in_at, now)) : null
  const label = openShift ? `En turno · ${duration}` : "Fuera de turno"

  return (
    <>
      {/* Desktop: botón completo que va a Fichar */}
      <Button
        variant={openShift ? "default" : "outline"}
        size="sm"
        onClick={() => navigate("/app/fichar")}
        className="hidden gap-2 sm:inline-flex"
        title="Ir a Fichar"
      >
        <Clock className="size-4" />
        <span className="tabular-nums">{label}</span>
      </Button>

      {/* Móvil: relojito compacto; al tocarlo muestra la info */}
      <div ref={rootRef} className="relative sm:hidden">
        <Button
          variant={openShift ? "default" : "outline"}
          size="icon-sm"
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label={label}
          title={label}
        >
          <Clock className="size-4" />
        </Button>

        {open ? (
          <div
            role="menu"
            className="absolute right-0 top-full z-40 mt-2 w-44 overflow-hidden rounded-xl border border-black/10 bg-white/95 p-1.5 shadow-xl backdrop-blur-2xl dark:border-white/10 dark:bg-black/85"
          >
            <div className="px-2.5 py-1.5">
              <p className="text-sm font-medium text-foreground">
                {openShift ? "En turno" : "Fuera de turno"}
              </p>
              {duration ? (
                <p className="text-xs tabular-nums text-muted-foreground">Hace {duration}</p>
              ) : null}
            </div>
            <div className="my-1 h-px bg-black/10 dark:bg-white/10" />
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false)
                navigate("/app/fichar")
              }}
              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-foreground/80 transition duration-200 ease-out hover:bg-accent hover:text-foreground active:scale-[0.97]"
            >
              <Clock className="size-4 shrink-0" />
              Ir a Fichar
            </button>
          </div>
        ) : null}
      </div>
    </>
  )
}

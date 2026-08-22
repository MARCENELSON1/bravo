import { useEffect, useMemo, useRef, useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { Bell, CalendarDays, ChevronLeft, ChevronRight, Plus, X } from "lucide-react"

import { TopbarSheet } from "@/components/shell/topbar-sheet"
import { Button } from "@/components/ui/button"
import { useReduceMotion } from "@/lib/reduce-motion"
import { cn } from "@/lib/utils"

// Agenda del equipo (por ahora, solo la UI de front). Crear/ver eventos con
// recordatorio queda en estado local; recordatorios reales que notifiquen con la
// app cerrada necesitan backend. Animación de apertura estilo iOS.
type EventItem = { id: string; date: string; title: string; time: string; reminder: boolean }

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"]

function keyOf(d: Date) {
  const p = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function sameDay(a: Date, b: Date) {
  return keyOf(a) === keyOf(b)
}

// Primer día de la grilla (lunes de la semana del día 1 del mes visible).
function gridStart(view: Date) {
  const first = new Date(view.getFullYear(), view.getMonth(), 1)
  const dow = (first.getDay() + 6) % 7 // 0 = lunes … 6 = domingo
  const start = new Date(first)
  start.setDate(first.getDate() - dow)
  return start
}

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

// La grilla del mes entra/sale hacia el lado de la navegación (izq/der).
const monthVariants = {
  enter: (d: number) => ({ opacity: 0, x: d >= 0 ? 26 : -26 }),
  center: { opacity: 1, x: 0 },
  exit: (d: number) => ({ opacity: 0, x: d >= 0 ? -26 : 26 }),
}

function initialEvents(): EventItem[] {
  const today = new Date()
  const plus = (n: number) => {
    const d = new Date(today)
    d.setDate(d.getDate() + n)
    return d
  }
  return [
    { id: "s1", date: keyOf(today), title: "Reunión de equipo", time: "11:00", reminder: true },
    { id: "s2", date: keyOf(plus(2)), title: "Pedido a proveedor", time: "09:30", reminder: true },
    { id: "s3", date: keyOf(plus(5)), title: "Control de stock", time: "18:00", reminder: false },
  ]
}

export function CalendarMenu() {
  const reduce = useReduceMotion()
  const today = useMemo(() => new Date(), [])
  const [events, setEvents] = useState<EventItem[]>(initialEvents)
  const [open, setOpen] = useState(false)
  const [view, setView] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1))
  const [selected, setSelected] = useState<Date>(today)
  const [title, setTitle] = useState("")
  const [time, setTime] = useState("12:00")
  const [reminder, setReminder] = useState(true)
  const [dir, setDir] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)

  const selectedKey = keyOf(selected)
  const dayEvents = useMemo(
    () => events.filter((e) => e.date === selectedKey).sort((a, b) => a.time.localeCompare(b.time)),
    [events, selectedKey]
  )
  const eventDates = useMemo(() => new Set(events.map((e) => e.date)), [events])
  const remindersTodayCount = useMemo(
    () => events.filter((e) => e.date === keyOf(today) && e.reminder).length,
    [events, today]
  )

  const days = useMemo(() => {
    const start = gridStart(view)
    return Array.from({ length: 42 }, (_, i) => {
      const d = new Date(start)
      d.setDate(start.getDate() + i)
      return d
    })
  }, [view])

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

  const shiftMonth = (delta: number) => {
    setDir(delta)
    setView((v) => new Date(v.getFullYear(), v.getMonth() + delta, 1))
  }

  const addEvent = () => {
    const t = title.trim()
    if (!t) return
    setEvents((prev) => [
      ...prev,
      { id: `e${Date.now()}`, date: selectedKey, title: t, time, reminder },
    ])
    setTitle("")
  }

  const removeEvent = (id: string) => setEvents((prev) => prev.filter((e) => e.id !== id))

  return (
    <div ref={rootRef} className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Calendario"
        title="Calendario"
      >
        <CalendarDays className="size-4" />
        {/* Puntito rojo chico si hay recordatorios para hoy (sin número) */}
        {remindersTodayCount > 0 ? (
          <span className="absolute right-0 top-0 size-1.5 rounded-full bg-red-500 ring-2 ring-white dark:ring-[#111]" />
        ) : null}
      </Button>

      <TopbarSheet open={open} onClose={() => setOpen(false)} anchorRef={rootRef}>
            {/* Cabecera del mes con navegación */}
            <div className="flex items-center justify-between gap-2 border-b border-black/10 px-2 py-2 dark:border-white/10">
              <button
                type="button"
                onClick={() => shiftMonth(-1)}
                aria-label="Mes anterior"
                className="grid size-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground active:scale-95"
              >
                <ChevronLeft className="size-4" />
              </button>
              <p className="text-sm font-semibold text-foreground">
                {cap(view.toLocaleDateString("es-AR", { month: "long", year: "numeric" }))}
              </p>
              <button
                type="button"
                onClick={() => shiftMonth(1)}
                aria-label="Mes siguiente"
                className="grid size-8 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground active:scale-95"
              >
                <ChevronRight className="size-4" />
              </button>
            </div>

            {/* Grilla del mes (se desliza al cambiar de mes) */}
            <div className="overflow-hidden p-2">
              <div className="grid grid-cols-7">
                {WEEKDAYS.map((w, i) => (
                  <span
                    key={i}
                    className="grid h-7 place-items-center text-[11px] font-medium text-muted-foreground"
                  >
                    {w}
                  </span>
                ))}
              </div>
              <AnimatePresence mode="wait" initial={false} custom={dir}>
                <motion.div
                  key={`${view.getFullYear()}-${view.getMonth()}`}
                  custom={dir}
                  variants={monthVariants}
                  initial={reduce ? false : "enter"}
                  animate="center"
                  exit={reduce ? { opacity: 0 } : "exit"}
                  transition={reduce ? { duration: 0 } : { duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
                  className="grid grid-cols-7"
                >
                  {days.map((d) => {
                    const inMonth = d.getMonth() === view.getMonth()
                    const isToday = sameDay(d, today)
                    const isSelected = sameDay(d, selected)
                    const hasEvents = eventDates.has(keyOf(d))
                    return (
                      <button
                        key={keyOf(d)}
                        type="button"
                        onClick={() => setSelected(new Date(d))}
                        className={cn(
                          "relative mx-auto grid size-9 place-items-center rounded-lg text-sm transition-colors",
                          isSelected
                            ? "font-medium text-primary-foreground"
                            : isToday
                              ? "font-semibold text-primary hover:bg-accent"
                              : inMonth
                                ? "text-foreground hover:bg-accent"
                                : "text-muted-foreground/40 hover:bg-accent"
                        )}
                      >
                        {isSelected ? (
                          <motion.span
                            key={selectedKey}
                            initial={reduce ? false : { scale: 0.5, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={
                              reduce
                                ? { duration: 0 }
                                : { type: "spring", stiffness: 500, damping: 26 }
                            }
                            className="absolute inset-0 rounded-lg bg-primary"
                          />
                        ) : null}
                        <span className="relative z-10">{d.getDate()}</span>
                        {hasEvents && !isSelected ? (
                          <span className="absolute bottom-1 z-10 size-1 rounded-full bg-red-500" />
                        ) : null}
                      </button>
                    )
                  })}
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Eventos del día seleccionado + alta */}
            <div className="border-t border-black/10 p-3 dark:border-white/10">
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                {cap(
                  selected.toLocaleDateString("es-AR", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                  })
                )}
              </p>

              {dayEvents.length > 0 ? (
                <ul className="mb-2 flex max-h-40 flex-col gap-1 overflow-y-auto">
                  <AnimatePresence initial={false}>
                    {dayEvents.map((e) => (
                      <motion.li
                        key={e.id}
                        layout={!reduce}
                        initial={reduce ? false : { opacity: 0, y: -6, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={reduce ? { opacity: 0 } : { opacity: 0, x: 12, scale: 0.95 }}
                        transition={
                          reduce ? { duration: 0 } : { type: "spring", stiffness: 500, damping: 32 }
                        }
                        className="group flex items-center gap-2 rounded-lg bg-accent/50 px-2.5 py-1.5"
                      >
                        <span className="w-11 shrink-0 text-xs tabular-nums text-muted-foreground">
                          {e.time}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-sm text-foreground">
                          {e.title}
                        </span>
                        {e.reminder ? (
                          <Bell className="size-3.5 shrink-0 text-primary" aria-label="Con recordatorio" />
                        ) : null}
                        <button
                          type="button"
                          onClick={() => removeEvent(e.id)}
                          aria-label="Eliminar evento"
                          className="grid size-5 shrink-0 place-items-center rounded text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                        >
                          <X className="size-3.5" />
                        </button>
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </ul>
              ) : (
                <p className="mb-2 text-xs text-muted-foreground">No hay eventos este día.</p>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  addEvent()
                }}
                className="flex items-center gap-1.5"
              >
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Nuevo evento…"
                  aria-label="Título del evento"
                  className="h-9 min-w-0 flex-1 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
                />
                <input
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  aria-label="Hora"
                  className="h-9 shrink-0 rounded-lg border border-input bg-transparent px-2 text-sm tabular-nums outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
                />
                <button
                  type="button"
                  onClick={() => setReminder((v) => !v)}
                  aria-pressed={reminder}
                  aria-label={reminder ? "Recordatorio activado" : "Recordatorio desactivado"}
                  title={reminder ? "Con recordatorio" : "Sin recordatorio"}
                  className={cn(
                    "grid size-9 shrink-0 place-items-center rounded-lg border transition-colors",
                    reminder
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-input text-muted-foreground hover:bg-accent"
                  )}
                >
                  <Bell className="size-4" />
                </button>
                <Button type="submit" size="icon" disabled={!title.trim()} aria-label="Agregar evento">
                  <Plus className="size-4" />
                </Button>
              </form>
            </div>
      </TopbarSheet>
    </div>
  )
}

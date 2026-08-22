import { useEffect, useMemo, useRef, useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { ArrowLeft, Mail, Send } from "lucide-react"

import { TopbarSheet } from "@/components/shell/topbar-sheet"
import { Button } from "@/components/ui/button"
import { useReduceMotion } from "@/lib/reduce-motion"
import { cn } from "@/lib/utils"

// Mensajería interna del equipo (por ahora, solo la UI de front). La bandeja real
// —enviar/recibir entre miembros logueados, en vivo y persistido— necesita backend;
// esto deja lista la vista: bandeja con no-leídos y, al entrar a un chat, el hilo
// con el cuadro para escribir. Los mensajes enviados quedan en estado local.
// Animaciones estilo iOS (abrir/cerrar, push lista↔chat, pop de burbujas).
type Bubble = { id: string; mine: boolean; text: string; time: string }
type Conversation = {
  id: string
  from: string
  role: string
  time: string
  unread: boolean
  thread: Bubble[]
}

const SEED: Conversation[] = [
  {
    id: "1",
    from: "Sofía",
    role: "Mesera",
    time: "2 min",
    unread: true,
    thread: [{ id: "a", mine: false, text: "Hola! Mesa 7 pidió la cuenta 🙌", time: "14:20" }],
  },
  {
    id: "2",
    from: "Diego",
    role: "Cocina",
    time: "15 min",
    unread: true,
    thread: [
      { id: "a", mine: false, text: "Se nos está por acabar la milanesa napo.", time: "14:05" },
      { id: "b", mine: false, text: "¿Bajo el plato del menú de hoy?", time: "14:06" },
    ],
  },
  {
    id: "3",
    from: "Caja",
    role: "Cajero",
    time: "1 h",
    unread: false,
    thread: [{ id: "a", mine: false, text: "Cierre de caja listo para que lo revises.", time: "13:05" }],
  },
  {
    id: "4",
    from: "Martín",
    role: "Encargado",
    time: "Ayer",
    unread: false,
    thread: [{ id: "a", mine: false, text: "Reunión de equipo mañana a las 11.", time: "Ayer" }],
  },
]

function initials(name: string) {
  return name.trim().slice(0, 2).toUpperCase()
}

export function Messages() {
  const reduce = useReduceMotion()
  const [conversations, setConversations] = useState<Conversation[]>(SEED)
  const [open, setOpen] = useState(false)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [draft, setDraft] = useState("")
  const rootRef = useRef<HTMLDivElement>(null)
  const threadRef = useRef<HTMLDivElement>(null)

  const unread = useMemo(() => conversations.filter((c) => c.unread).length, [conversations])
  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? null,
    [conversations, activeId]
  )

  // Cerrar con click afuera / Escape (Escape primero vuelve a la lista si hay chat).
  useEffect(() => {
    if (!open) return
    const onDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return
      if (activeId) setActiveId(null)
      else setOpen(false)
    }
    document.addEventListener("pointerdown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("pointerdown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open, activeId])

  // Al cerrar el popover, volvemos a la bandeja.
  useEffect(() => {
    if (!open) {
      setActiveId(null)
      setDraft("")
    }
  }, [open])

  // Al abrir un chat o mandar, bajamos al último mensaje.
  useEffect(() => {
    if (activeId && threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [activeId, active?.thread.length])

  const openChat = (id: string) => {
    setActiveId(id)
    setDraft("")
    setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, unread: false } : c)))
  }

  const markAllRead = () => setConversations((prev) => prev.map((c) => ({ ...c, unread: false })))

  const send = () => {
    const text = draft.trim()
    if (!text || !activeId) return
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeId
          ? {
              ...c,
              time: "ahora",
              thread: [...c.thread, { id: `m${Date.now()}`, mine: true, text, time: "ahora" }],
            }
          : c
      )
    )
    setDraft("")
  }

  const bubbleTransition = reduce
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 500, damping: 30, mass: 0.6 }

  return (
    <div ref={rootRef} className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={unread > 0 ? `Mensajes (${unread} sin leer)` : "Mensajes"}
        title="Mensajes"
      >
        <Mail className="size-4" />
        {/* Circulito rojo de notificaciones (no-leídos), con pop al cambiar */}
        <AnimatePresence>
          {unread > 0 ? (
            <motion.span
              key={unread}
              initial={reduce ? false : { scale: 0 }}
              animate={{ scale: 1 }}
              exit={reduce ? { opacity: 0 } : { scale: 0 }}
              transition={reduce ? { duration: 0 } : { type: "spring", stiffness: 500, damping: 22 }}
              className="absolute -right-0.5 -top-0.5 grid min-w-[1.05rem] place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold leading-[1.05rem] text-white ring-2 ring-white dark:ring-[#111]"
            >
              {unread}
            </motion.span>
          ) : null}
        </AnimatePresence>
      </Button>

      <TopbarSheet open={open} onClose={() => setOpen(false)} mobileAsModal={false}>
            {/* Push/pop lista ↔ chat: se deslizan superpuestos (estilo iOS). La
                altura la define la vista visible (popLayout), así el popover crece
                con el contenido y no queda fijo/largo. */}
            <AnimatePresence mode="popLayout" initial={false}>
              {active ? (
                <motion.div
                  key="chat"
                  className="flex flex-col"
                  initial={reduce ? false : { x: "100%" }}
                  animate={{ x: 0 }}
                  exit={reduce ? { opacity: 0 } : { x: "100%" }}
                  transition={reduce ? { duration: 0 } : { duration: 0.34, ease: [0.32, 0.72, 0, 1] }}
                >
                  <div className="flex shrink-0 items-center gap-2 border-b border-black/10 px-2 py-2 dark:border-white/10">
                    <button
                      type="button"
                      onClick={() => setActiveId(null)}
                      aria-label="Volver a la bandeja"
                      className="grid size-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground active:scale-95"
                    >
                      <ArrowLeft className="size-4" />
                    </button>
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      {initials(active.from)}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">{active.from}</p>
                      <p className="truncate text-xs text-muted-foreground">{active.role}</p>
                    </div>
                  </div>

                  <div
                    ref={threadRef}
                    className="flex max-h-[18rem] min-h-[7rem] flex-col gap-2 overflow-y-auto p-3"
                  >
                    {active.thread.map((b) => (
                      <motion.div
                        key={b.id}
                        layout={!reduce}
                        initial={reduce ? false : { opacity: 0, y: 8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={bubbleTransition}
                        className={cn("flex flex-col", b.mine ? "items-end" : "items-start")}
                      >
                        <div
                          className={cn(
                            "max-w-[80%] rounded-2xl px-3 py-2 text-sm",
                            b.mine
                              ? "rounded-br-sm bg-primary text-primary-foreground"
                              : "rounded-bl-sm bg-muted text-foreground"
                          )}
                        >
                          {b.text}
                        </div>
                        <span className="mt-0.5 px-1 text-[10px] tabular-nums text-muted-foreground">
                          {b.time}
                        </span>
                      </motion.div>
                    ))}
                  </div>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      send()
                    }}
                    className="flex shrink-0 items-center gap-2 border-t border-black/10 p-2 dark:border-white/10"
                  >
                    <input
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      placeholder="Escribí un mensaje…"
                      aria-label="Escribí un mensaje"
                      className="h-9 min-w-0 flex-1 rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
                    />
                    <Button type="submit" size="icon" disabled={!draft.trim()} aria-label="Enviar">
                      <Send className="size-4" />
                    </Button>
                  </form>
                </motion.div>
              ) : (
                <motion.div
                  key="list"
                  className="flex flex-col"
                  initial={reduce ? false : { x: "-100%" }}
                  animate={{ x: 0 }}
                  exit={reduce ? { opacity: 0 } : { x: "-100%" }}
                  transition={reduce ? { duration: 0 } : { duration: 0.34, ease: [0.32, 0.72, 0, 1] }}
                >
                  <div className="flex shrink-0 items-center justify-between gap-2 border-b border-black/10 px-3 py-2.5 dark:border-white/10">
                    <p className="text-sm font-semibold text-foreground">Mensajes</p>
                    {unread > 0 ? (
                      <button
                        type="button"
                        onClick={markAllRead}
                        className="text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
                      >
                        Marcar todas como leídas
                      </button>
                    ) : null}
                  </div>

                  {conversations.length > 0 ? (
                    <ul className="max-h-[22rem] divide-y divide-black/5 overflow-y-auto dark:divide-white/5">
                      {conversations.map((c) => {
                        const last = c.thread[c.thread.length - 1]
                        return (
                          <li key={c.id}>
                            <button
                              type="button"
                              role="menuitem"
                              onClick={() => openChat(c.id)}
                              className={cn(
                                "flex w-full items-start gap-3 px-3 py-2.5 text-left transition-colors hover:bg-accent",
                                c.unread && "bg-primary/[0.04]"
                              )}
                            >
                              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                                {initials(c.from)}
                              </span>
                              <span className="min-w-0 flex-1">
                                <span className="flex items-center gap-2">
                                  <span className="truncate text-sm font-medium text-foreground">
                                    {c.from}
                                  </span>
                                  <span className="truncate text-xs text-muted-foreground">
                                    · {c.role}
                                  </span>
                                  <span className="ml-auto shrink-0 text-[11px] tabular-nums text-muted-foreground">
                                    {c.time}
                                  </span>
                                </span>
                                <span className="mt-0.5 line-clamp-2 block text-xs text-muted-foreground">
                                  {last?.mine ? "Vos: " : ""}
                                  {last?.text}
                                </span>
                              </span>
                              {c.unread ? (
                                <span className="mt-1.5 size-2 shrink-0 rounded-full bg-red-500" />
                              ) : null}
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p className="px-3 py-8 text-center text-sm text-muted-foreground">
                      No tenés mensajes.
                    </p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
      </TopbarSheet>
    </div>
  )
}

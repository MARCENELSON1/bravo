import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { LogOut, Settings } from "lucide-react"
import { NavLink } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { useReduceMotion } from "@/lib/reduce-motion"
import { ROLE_LABELS } from "@/lib/role-labels"
import { cn } from "@/lib/utils"

// "Juan Pérez" → "JP"; fallback: primera letra del email.
function initials(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/)
    const first = parts[0]?.[0] ?? ""
    const last = parts.length > 1 ? (parts[parts.length - 1][0] ?? "") : ""
    return (first + last).toUpperCase() || email[0]?.toUpperCase() || "?"
  }
  return email[0]?.toUpperCase() || "?"
}

const ITEM =
  "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-sidebar-foreground/80 transition duration-200 ease-out hover:bg-sidebar-accent/15 hover:text-sidebar-foreground active:scale-[0.97]"

// Fila de cuenta al pie de la sidebar; al tocarla abre un menú de opciones útiles.
export function UserMenu({ onNavigate }: { onNavigate?: () => void }) {
  const { session, logout } = useAuth()
  const reduce = useReduceMotion()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

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

  if (!session) return null
  const goNavigate = () => {
    setOpen(false)
    onNavigate?.()
  }

  return (
    <div ref={rootRef} className="relative border-t border-black/10 p-3 dark:border-white/10">
      <AnimatePresence>
        {open ? (
          <motion.div
            role="menu"
            initial={reduce ? false : { opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, y: 6, scale: 0.98 }}
            transition={reduce ? { duration: 0 } : { duration: 0.15, ease: "easeOut" }}
            className={cn(
              "absolute bottom-full left-3 right-3 z-20 mb-2 origin-bottom overflow-hidden rounded-xl p-1.5 shadow-xl",
              "border border-black/10 bg-white/98 backdrop-blur-3xl dark:border-white/10 dark:bg-black/92"
            )}
          >
            <div className="px-2.5 py-2">
              <p className="truncate text-sm font-semibold text-sidebar-foreground">
                {session.name ?? session.email}
              </p>
              <p className="truncate text-xs text-sidebar-foreground/50">{session.email}</p>
            </div>
            <div className="my-1 h-px bg-black/10 dark:bg-white/10" />
            <NavLink to="/app/config" onClick={goNavigate} className={ITEM} role="menuitem">
              <Settings className="size-4 shrink-0" />
              Configuración
            </NavLink>
            <div className="my-1 h-px bg-black/10 dark:bg-white/10" />
            <button
              type="button"
              role="menuitem"
              onClick={() => void logout()}
              className={cn(ITEM, "text-red-500 hover:bg-red-500/10 hover:text-red-500")}
            >
              <LogOut className="size-4 shrink-0" />
              Cerrar sesión
            </button>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex w-full items-center gap-3 rounded-xl px-2 py-1.5 text-left transition-colors hover:bg-sidebar-accent/15"
      >
        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
          {initials(session.name, session.email)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-sidebar-foreground">
            {session.name ?? session.email}
          </span>
          <span className="block truncate text-xs text-sidebar-foreground/50">
            {ROLE_LABELS[session.role]}
          </span>
        </span>
      </button>
    </div>
  )
}

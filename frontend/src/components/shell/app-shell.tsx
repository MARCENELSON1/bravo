import { useState } from "react"
import { Bell, ChevronsUpDown, LogOut, Menu, Search, Store } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { NAV_ITEMS } from "@/components/shell/nav-config"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// Mock branding for the design pass (no backend wiring yet).
const TENANT_NAME = "Restaurante Villapaz"
const USER_INITIALS = "JM"
const USER_NAME = "Juan Martínez"
const USER_FIRST_NAME = USER_NAME.split(" ")[0]
const UNREAD_NOTIFICATIONS = 3

// Etiquetas de rol para la UX (código EN → español mostrado).
const ROLE_LABELS: Record<string, string> = {
  OWNER: "Dueño",
  MANAGER: "Encargado",
  WAITER: "Mozo",
  KITCHEN: "Cocina",
  CASHIER: "Cajero",
}

// Wellnod console layout: persistent role-based sidebar + topbar + content area.
// Wraps the protected /app/* routes (rendered via <Outlet/>).
export function AppShell() {
  const { session, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!session) return null
  const role = session.role
  const roleLabel = ROLE_LABELS[role] ?? role
  const items = NAV_ITEMS.filter((item) => item.roles.includes(role))

  const sidebar = (
    <div className="flex h-full w-64 flex-col rounded-2xl border border-white/10 bg-black/30 text-sidebar-foreground backdrop-blur-2xl">
      <div className="flex h-16 items-center gap-1 px-5">
        <WellnodMark className="h-9 w-auto text-[#8FA8A2]" />
        <span className="-ml-1 translate-y-0.5 font-heading text-lg tracking-tight">
          <span className="font-bold text-sidebar-foreground">Well</span>
          <span className="-ml-px font-light text-sidebar-foreground/55">nod</span>
        </span>
      </div>

      {/* Selector de espacio de trabajo (tenant) */}
      <div className="px-3">
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-xl border border-sidebar-border bg-sidebar-accent/10 px-3 py-2.5 text-left transition-colors hover:bg-sidebar-accent/20"
        >
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-sidebar-primary/20 text-sidebar-primary">
            <Store className="size-4" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-[10px] font-medium uppercase tracking-wide text-sidebar-foreground/40">
              Espacio de trabajo
            </span>
            <span className="block truncate text-sm font-semibold text-sidebar-foreground">
              {TENANT_NAME}
            </span>
          </span>
          <ChevronsUpDown className="size-4 shrink-0 text-sidebar-foreground/40" />
        </button>
      </div>

      {/* Buscador */}
      <div className="px-3 pt-3">
        <label className="flex items-center gap-2 rounded-xl border border-sidebar-border bg-black/20 px-3 py-2 text-sidebar-foreground/50 focus-within:border-sidebar-ring/50">
          <Search className="size-4 shrink-0" />
          <input
            type="search"
            placeholder="Buscar…"
            className="w-full bg-transparent text-sm text-sidebar-foreground placeholder:text-sidebar-foreground/40 focus:outline-none"
          />
        </label>
      </div>

      <p className="px-4 pb-1.5 pt-4 text-[10px] font-medium uppercase tracking-wide text-sidebar-foreground/40">
        Navegación
      </p>
      <nav className="flex flex-1 flex-col gap-1 overflow-auto px-3 pb-4">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setDrawerOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/15 hover:text-sidebar-foreground"
              )
            }
          >
            <item.icon className="size-[18px] shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Cuenta de usuario */}
      <div className="px-3 pb-3">
        <p className="px-1 pb-1.5 text-[10px] font-medium uppercase tracking-wide text-sidebar-foreground/40">
          Cuenta
        </p>
        <div className="flex items-center gap-3 rounded-xl border border-sidebar-border bg-sidebar-accent/10 px-3 py-2.5">
          <span className="grid size-9 shrink-0 place-items-center rounded-full bg-sidebar-primary text-sm font-semibold text-sidebar-primary-foreground">
            {USER_INITIALS}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-semibold text-sidebar-foreground">
              {USER_NAME}
            </span>
            <span className="block truncate text-xs text-sidebar-foreground/50">{roleLabel}</span>
          </span>
          <button
            type="button"
            onClick={() => void logout()}
            title="Cerrar sesión"
            aria-label="Cerrar sesión"
            className="grid size-8 shrink-0 place-items-center rounded-lg text-sidebar-foreground/50 transition-colors hover:bg-sidebar-accent/20 hover:text-sidebar-foreground"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </div>

    </div>
  )

  return (
    <div className="relative flex h-svh gap-3 overflow-hidden p-3">
      {/* Scenic backdrop — the frosted panels float over the brand photo */}
      <div
        aria-hidden
        className="fixed inset-0 -z-10 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/app-bg.png')" }}
      />
      <div aria-hidden className="fixed inset-0 -z-10 bg-black/25" />

      <aside className="hidden h-full md:block">{sidebar}</aside>

      {drawerOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Cerrar menú"
            className="absolute inset-0 bg-black/50"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 p-3 shadow-xl">{sidebar}</div>
        </div>
      ) : null}

      <div className="flex h-full min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-white/10 bg-black/30 backdrop-blur-2xl">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-white/10 px-6">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Abrir menú"
            onClick={() => setDrawerOpen(true)}
          >
            <Menu className="size-4" />
          </Button>
          <span className="font-display text-xl font-bold text-foreground">
            Buen día, {USER_FIRST_NAME}
          </span>
          <div className="flex-1" />

          <button
            type="button"
            aria-label="Notificaciones"
            className="relative grid size-9 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <Bell className="size-5" />
            {UNREAD_NOTIFICATIONS > 0 ? (
              <span className="absolute -right-0.5 -top-0.5 grid size-4 place-items-center rounded-full bg-destructive text-[10px] font-semibold text-white">
                {UNREAD_NOTIFICATIONS}
              </span>
            ) : null}
          </button>
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

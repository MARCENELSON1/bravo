import { useState } from "react"
import { Bell, LogOut, Menu } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { NAV_ITEMS } from "@/components/shell/nav-config"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// Mock branding for the design pass (no backend wiring yet).
const TENANT_NAME = "Restaurante Villapaz"
const USER_INITIALS = "JM"
const PLAN_NAME = "Plan Pro"
const PLAN_RENEWAL = "Vence 28 jun"
const UNREAD_NOTIFICATIONS = 3

// Wellnod console layout: persistent role-based sidebar + topbar + content area.
// Wraps the protected /app/* routes (rendered via <Outlet/>).
export function AppShell() {
  const { session, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!session) return null
  const role = session.role
  const items = NAV_ITEMS.filter((item) => item.roles.includes(role))

  const sidebar = (
    <div className="flex h-full w-64 flex-col rounded-2xl border border-white/10 bg-black/30 text-sidebar-foreground backdrop-blur-2xl">
      <div className="flex h-16 items-center gap-2 px-5">
        <WellnodMark className="h-9 w-auto text-[#8a9d94]" />
        <span className="font-heading text-lg tracking-tight">
          <span className="font-bold text-sidebar-foreground">Well</span>
          <span className="font-light text-sidebar-foreground/55">nod</span>
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-auto px-3 py-4">
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

      <div className="p-3">
        <div className="rounded-xl border border-sidebar-border bg-sidebar-accent/10 px-4 py-3">
          <p className="text-sm font-semibold text-sidebar-foreground">{PLAN_NAME}</p>
          <p className="text-xs text-sidebar-foreground/50">{PLAN_RENEWAL}</p>
        </div>
      </div>
    </div>
  )

  return (
    <div className="relative flex h-svh gap-3 overflow-hidden p-3">
      {/* Scenic backdrop — the frosted panels float over it (swap for a real photo later) */}
      <div
        aria-hidden
        className="fixed inset-0 -z-10 bg-[radial-gradient(120%_120%_at_15%_10%,#9fb0aa_0%,#63736b_28%,#2c3833_58%,#101915_82%,#0a0f0c_100%)]"
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
          <span className="text-sm font-medium text-muted-foreground">{TENANT_NAME}</span>
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

          <button
            type="button"
            onClick={() => void logout()}
            title="Cerrar sesión"
            className="group relative grid size-9 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground"
            aria-label="Cerrar sesión"
          >
            <span className="group-hover:opacity-0">{USER_INITIALS}</span>
            <LogOut className="absolute size-4 opacity-0 transition-opacity group-hover:opacity-100" />
          </button>
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

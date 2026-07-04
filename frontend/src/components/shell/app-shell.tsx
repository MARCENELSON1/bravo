import { useState } from "react"
import { LogOut, Menu } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { ClockStatus } from "@/components/shell/clock-status"
import { NAV_GROUPS, NAV_ITEMS } from "@/components/shell/nav-config"
import type { NavItem } from "@/components/shell/nav-config"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { cn } from "@/lib/utils"
import { ROLE_LABELS } from "@/lib/role-labels"

// Wellnod console layout: floating glass panels (sidebar + content) over a
// scenic gradient backdrop. Light and dark variants — the theme follows the OS.
// Wraps the protected /app/* routes (rendered via <Outlet/>).

const GLASS_PANEL =
  "rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl " +
  "dark:border-white/10 dark:bg-black/30"

// "Juan Pérez" → "JP"; fallback: first letter of the email.
function initials(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/)
    const first = parts[0]?.[0] ?? ""
    const last = parts.length > 1 ? (parts[parts.length - 1][0] ?? "") : ""
    return (first + last).toUpperCase() || email[0]?.toUpperCase() || "?"
  }
  return email[0]?.toUpperCase() || "?"
}

export function AppShell() {
  const { session, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!session) return null
  const role = session.role
  const topItems = NAV_ITEMS.filter((item) => item.roles.includes(role))

  const renderItem = (item: NavItem) => (
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
  )

  const sidebar = (
    <div className={cn("flex h-full w-64 flex-col text-sidebar-foreground", GLASS_PANEL)}>
      <div className="flex h-16 items-center gap-2 px-5">
        <WellnodMark className="h-9 w-auto text-[#5c7a6e] dark:text-[#8a9d94]" />
        <span className="font-heading text-lg tracking-tight">
          <span className="font-bold text-sidebar-foreground">Well</span>
          <span className="font-light text-sidebar-foreground/55">nod</span>
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-auto px-3 py-4">
        {topItems.map(renderItem)}
        {NAV_GROUPS.map((group) => {
          const items = group.items.filter((item) => item.roles.includes(role))
          if (items.length === 0) return null
          return (
            <div key={group.label} className="mt-5 flex flex-col gap-1">
              <p className="px-3 pb-1 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/40">
                {group.label}
              </p>
              {items.map(renderItem)}
            </div>
          )
        })}
      </nav>
    </div>
  )

  return (
    <div className="relative flex h-svh gap-3 overflow-hidden p-3">
      {/* Scenic backdrop — the frosted panels float over it (swap for a real photo later) */}
      <div
        aria-hidden
        className="fixed inset-0 -z-10 bg-[radial-gradient(120%_120%_at_15%_10%,#eef2f0_0%,#d8e2dd_35%,#c4d2cb_65%,#a9bcb2_100%)] dark:bg-[radial-gradient(120%_120%_at_15%_10%,#9fb0aa_0%,#63736b_28%,#2c3833_58%,#101915_82%,#0a0f0c_100%)]"
      />
      <div aria-hidden className="fixed inset-0 -z-10 bg-white/10 dark:bg-black/25" />

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

      <div
        className={cn("flex h-full min-w-0 flex-1 flex-col overflow-hidden", GLASS_PANEL)}
      >
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-black/10 px-6 dark:border-white/10">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Abrir menú"
            onClick={() => setDrawerOpen(true)}
          >
            <Menu className="size-4" />
          </Button>
          <span className="truncate text-sm font-medium text-muted-foreground">
            {session.tenantName}
          </span>
          <div className="flex-1" />
          <ClockStatus />
          <ThemeToggle />
          <button
            type="button"
            onClick={() => void logout()}
            title={`${ROLE_LABELS[role]} — cerrar sesión`}
            aria-label="Cerrar sesión"
            className="group relative grid size-9 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground"
          >
            <span className="group-hover:opacity-0">
              {initials(session.name, session.email)}
            </span>
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

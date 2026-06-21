import { useState } from "react"
import { LogOut, Menu } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { useAuth } from "@/auth/auth-context"
import { NAV_GROUPS } from "@/components/shell/nav-config"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { cn } from "@/lib/utils"
import { ROLE_LABELS } from "@/lib/role-labels"

// CRM console layout: persistent role-based sidebar + topbar + content area.
// Wraps the protected /app/* routes (rendered via <Outlet/>).
export function AppShell() {
  const { session, logout } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)

  if (!session) return null
  const role = session.role

  const sidebar = (
    <div className="flex h-full w-64 flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="size-7 rounded-md bg-sidebar-primary" />
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="font-heading text-sm font-semibold">NÚCLEO</span>
          <span className="truncate text-xs text-sidebar-foreground/50">El cerebro del local</span>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-5 overflow-auto px-3 py-4">
        {NAV_GROUPS.map((group) => {
          const items = group.items.filter((item) => item.roles.includes(role))
          if (items.length === 0) return null
          return (
            <div key={group.label} className="flex flex-col gap-1">
              <p className="px-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/40">
                {group.label}
              </p>
              {items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={() => setDrawerOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60"
                    )
                  }
                >
                  <item.icon className="size-4 shrink-0" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          )
        })}
      </nav>

      <div className="flex items-center justify-between gap-2 border-t border-sidebar-border p-3">
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="text-xs font-medium">{ROLE_LABELS[role]}</span>
          <span className="truncate font-mono text-[10px] text-sidebar-foreground/50">
            {session.tenantId}
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Cerrar sesión"
          onClick={() => void logout()}
        >
          <LogOut className="size-4" />
        </Button>
      </div>
    </div>
  )

  return (
    <div className="flex min-h-svh bg-background">
      <aside className="hidden border-r border-sidebar-border md:block">{sidebar}</aside>

      {drawerOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Cerrar menú"
            className="absolute inset-0 bg-black/50"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 border-r border-sidebar-border shadow-xl">
            {sidebar}
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-border bg-background/80 px-4 backdrop-blur">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Abrir menú"
            onClick={() => setDrawerOpen(true)}
          >
            <Menu className="size-4" />
          </Button>
          <div className="flex-1" />
          <ThemeToggle />
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

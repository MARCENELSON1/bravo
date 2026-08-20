import { useRef, useState } from "react"
import { motion } from "motion/react"
import { Menu } from "lucide-react"
import type { OverlayScrollbars } from "overlayscrollbars"
import {
  OverlayScrollbarsComponent,
  type OverlayScrollbarsComponentRef,
} from "overlayscrollbars-react"
import { NavLink, Outlet, useLocation } from "react-router-dom"

const OS_OPTIONS = {
  scrollbars: { theme: "os-theme-wellnod", autoHide: "scroll", autoHideDelay: 800 },
} as const

// Fade proporcional al scroll: el degradé de cada borde crece desde 0 a medida
// que hay contenido oculto de ese lado (progresivo, sigue el scroll).
const FADE_MAX = 28
function updateNavFade(instance: OverlayScrollbars) {
  const { host, viewport } = instance.elements()
  const top = Math.min(viewport.scrollTop, FADE_MAX)
  const bottomDist = viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop
  const bottom = Math.min(Math.max(bottomDist, 0), FADE_MAX)
  host.style.setProperty("--fade-top", `${top}px`)
  host.style.setProperty("--fade-bottom", `${bottom}px`)
}

import { useAuth } from "@/auth/auth-context"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { AppBackground } from "@/components/shell/app-background"
import { ClockStatus } from "@/components/shell/clock-status"
import { TopbarClock } from "@/components/shell/topbar-clock"
import { NAV_GROUPS, NAV_ITEMS } from "@/components/shell/nav-config"
import type { NavItem } from "@/components/shell/nav-config"
import { UserMenu } from "@/components/shell/user-menu"
import { Button } from "@/components/ui/button"
import { useEdgePeek } from "@/lib/edge-peek"
import { useReduceMotion } from "@/lib/reduce-motion"
import { cn } from "@/lib/utils"

// Wellnod console layout: floating glass panels (sidebar + content) over a
// scenic gradient backdrop. Light and dark variants — the theme follows the OS.
// Wraps the protected /app/* routes (rendered via <Outlet/>).

const GLASS_PANEL =
  "rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl " +
  "dark:border-white/10 dark:bg-black/30"

export function AppShell() {
  const { session } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()
  const reduce = useReduceMotion()
  const mainOsRef = useRef<OverlayScrollbarsComponentRef>(null)
  const navOsRef = useRef<OverlayScrollbarsComponentRef>(null)
  useEdgePeek(mainOsRef)
  useEdgePeek(navOsRef)

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
          "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition duration-200 ease-out active:scale-[0.97]",
          isActive
            ? "text-sidebar-accent-foreground"
            : "text-sidebar-foreground/70 hover:bg-sidebar-accent/15 hover:text-sidebar-foreground"
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive ? (
            <motion.span
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={reduce ? { duration: 0 } : { duration: 0.15, ease: "easeOut" }}
              className="absolute inset-0 rounded-xl bg-sidebar-accent shadow-sm"
            />
          ) : null}
          <item.icon className="relative z-10 size-[18px] shrink-0" />
          <span className="relative z-10">{item.label}</span>
        </>
      )}
    </NavLink>
  )

  const sidebar = (
    <div className={cn("flex h-full w-64 flex-col text-sidebar-foreground", GLASS_PANEL)}>
      <div className="flex h-14 translate-y-1 items-center gap-3 px-6">
        <WellnodMark className="h-11 w-auto shrink-0 text-black dark:text-white" />
        <span className="font-heading translate-y-0.5 text-3xl leading-none">
          <span className="font-bold text-sidebar-foreground">Well</span>
          <span className="-ml-[3px] font-light text-sidebar-foreground/55">nod</span>
        </span>
      </div>

      <OverlayScrollbarsComponent
        ref={navOsRef}
        element="nav"
        className="nav-scroll-fade min-h-0 flex-1 px-3"
        options={OS_OPTIONS}
        events={{ initialized: updateNavFade, updated: updateNavFade, scroll: updateNavFade }}
        defer
      >
        <div className="flex flex-col gap-1 pb-4 pt-1">
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
        </div>
      </OverlayScrollbarsComponent>

      {/* Cuenta de usuario (abre menú de opciones) */}
      <UserMenu onNavigate={() => setDrawerOpen(false)} />
    </div>
  )

  return (
    <motion.div
      className="relative flex h-svh gap-3 overflow-hidden p-3"
      initial={reduce ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={reduce ? { duration: 0 } : { duration: 0.4, ease: "easeOut" }}
    >
      <AppBackground />

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
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-black/10 px-4 sm:px-6 dark:border-white/10">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Abrir menú"
            onClick={() => setDrawerOpen(true)}
          >
            <Menu className="size-4" />
          </Button>
          <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
            {session.tenantName}
          </span>
          <div className="flex-1" />
          <ClockStatus />
          <TopbarClock />
        </header>
        <OverlayScrollbarsComponent
          ref={mainOsRef}
          element="main"
          className="min-h-0 flex-1"
          options={OS_OPTIONS}
          defer
        >
          <motion.div
            key={location.pathname}
            initial={reduce ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={reduce ? { duration: 0 } : { duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            <Outlet />
          </motion.div>
        </OverlayScrollbarsComponent>
      </div>
    </motion.div>
  )
}

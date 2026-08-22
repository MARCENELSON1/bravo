import { useEffect, useRef, useState, type Ref, type ReactNode } from "react"
import {
  Calculator,
  ChefHat,
  Coins,
  FileText,
  Home,
  Lightbulb,
  LineChart,
  Package,
  QrCode,
  Sparkles,
  UtensilsCrossed,
  Users,
} from "lucide-react"

import { WellnodMark } from "@/presentation/components/brand/wellnod-mark"
import { cn } from "@/presentation/lib/cn"

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      {/* Glow verde de fondo */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-32 left-1/2 h-[38rem] w-[90%] -translate-x-1/2 rounded-[50%] bg-primary/20 blur-[140px]" />
      </div>

      {/* Título grande, centrado, con animación de entrada */}
      <div className="mx-auto max-w-6xl px-5 pt-20 text-center md:pt-28">
        <h1
          className="hero-title font-display text-6xl font-bold leading-[1.02] tracking-tight text-balance sm:text-7xl lg:text-8xl"
          style={{ animationDelay: "0ms" }}
        >
          Todo tu restaurante, <span className="text-primary">en una sola app</span>.
        </h1>
        <p
          className="hero-anim mx-auto mt-5 max-w-3xl text-lg text-balance text-muted-foreground sm:text-xl"
          style={{ animationDelay: "90ms" }}
        >
          Operás, cobrás y facturás en un solo lugar — con un copiloto que responde lo
          que le preguntás y un asesor que te da recomendaciones en base a cómo va tu
          negocio.
        </p>
      </div>

      {/* Pantalla interactiva de Wellnod */}
      <div className="hero-screen relative mx-auto mt-8 max-w-7xl px-4" style={{ animationDelay: "300ms" }}>
        <AppMockup />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-28 bg-gradient-to-b from-transparent to-background"
        />
      </div>
    </section>
  )
}

const NAV_MAIN = [
  { label: "Inicio", icon: Home },
  { label: "Finanzas", icon: LineChart },
  { label: "Clientes", icon: Users },
  { label: "Productos", icon: Package },
  { label: "IA Insights", icon: Lightbulb },
  { label: "Asesor", icon: Sparkles },
  { label: "Reportes", icon: FileText },
]
const NAV_OPS = [
  { label: "Mesas", icon: UtensilsCrossed },
  { label: "Cocina", icon: ChefHat },
  { label: "Caja", icon: Calculator },
  { label: "Propinas", icon: Coins },
  { label: "Fichar", icon: QrCode },
]

// Réplica interactiva del interfaz de Wellnod, con el contenido real de cada sección.
function AppMockup() {
  const reduced = prefersReducedMotion()
  const rootRef = useRef<HTMLDivElement>(null)
  const asesorNavRef = useRef<HTMLButtonElement>(null)
  const tryCopilotRef = useRef<HTMLButtonElement>(null)

  const [screen, setScreen] = useState(reduced ? "Asesor" : "Inicio")
  const [cursor, setCursor] = useState({ x: 0, y: 0, visible: false, snap: true, press: false })

  const started = useRef(false)
  const cancelled = useRef(false)
  const timers = useRef<number[]>([])

  const clearTimers = () => {
    timers.current.forEach((t) => window.clearTimeout(t))
    timers.current = []
  }
  // Programa un paso del tour (se saltea si el usuario ya interactuó).
  const at = (ms: number, fn: () => void) => {
    timers.current.push(window.setTimeout(() => !cancelled.current && fn(), ms))
  }
  // Punto (relativo a la raíz) al que apunta la punta del cursor sobre un elemento.
  const pointAt = (el: HTMLElement | null) => {
    const root = rootRef.current
    if (!root || !el) return null
    const r = root.getBoundingClientRect()
    const b = el.getBoundingClientRect()
    return { x: b.left - r.left + Math.min(22, b.width * 0.35), y: b.top - r.top + b.height / 2 }
  }

  // Tour guiado (una vez, al entrar en viewport): Inicio → click en Asesor → click
  // en el banner del Copiloto → IA Insights → el cursor va hasta "Preguntar" y
  // desaparece, para que la persona entienda que tiene que tocarlo.
  const runDemo = () => {
    // 1) Aparece junto a "Asesor" y hace click → pantalla Asesor.
    at(150, () => {
      const p = pointAt(asesorNavRef.current)
      if (p) setCursor({ x: p.x + 34, y: p.y + 24, visible: true, snap: true, press: false })
    })
    at(450, () => {
      const p = pointAt(asesorNavRef.current)
      if (p) setCursor({ x: p.x, y: p.y, visible: true, snap: false, press: false })
    })
    at(1200, () => setCursor((c) => ({ ...c, press: true })))
    at(1450, () => {
      setCursor((c) => ({ ...c, press: false }))
      setScreen("Asesor")
    })
    // 2) Se queda un rato en Asesor (que la persona lo lea) y lleva el cursor hasta
    //    el banner del Copiloto, donde desaparece SIN clickear: la persona tiene que
    //    tocarlo para entrar a IA Insights.
    at(3150, () => {
      const p = pointAt(tryCopilotRef.current)
      if (p) setCursor((c) => ({ ...c, x: p.x, y: p.y, snap: false }))
    })
    at(4200, () => setCursor((c) => ({ ...c, visible: false, press: false })))
  }

  // Dispara el tour cuando el mockup ya se ve bien en viewport (≥55%), una sola vez.
  useEffect(() => {
    if (reduced) return
    const el = rootRef.current
    if (!el) return
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || started.current || cancelled.current) return
        started.current = true
        io.disconnect()
        runDemo()
      },
      { threshold: 0.55 }
    )
    io.observe(el)
    return () => {
      io.disconnect()
      clearTimers()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduced])

  const onNav = (label: string) => {
    cancelled.current = true
    started.current = true
    clearTimers()
    setCursor((c) => ({ ...c, visible: false, press: false }))
    setScreen(label)
  }

  return (
    // `dark`: el mockup muestra siempre el tema oscuro del software (mismo fondo y
    // colores que la app real), sin importar el tema de la landing.
    <div
      ref={rootRef}
      className="dark relative overflow-hidden rounded-2xl border border-border bg-card shadow-2xl shadow-primary/10"
    >
      {/* Barra del navegador */}
      <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-3">
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="ml-3 rounded-md bg-muted px-2.5 py-1 text-[11px] text-muted-foreground">
          app.wellnod.com
        </span>
      </div>

      {/* Shell: fondo verde + textura de la app + grano + paneles de glass */}
      <div className="relative flex h-[30rem] gap-3 bg-[radial-gradient(125%_125%_at_18%_12%,#d7e6df_0%,#aec7bb_50%,#85a394_100%)] p-3 dark:bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)]">
        {/* Misma textura de imagen que usa el fondo del software */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light"
          style={{ backgroundImage: "url('/app-bg-dark.png')" }}
        />
        {/* Grano/ruido sutil, igual que en la app */}
        <div
          aria-hidden
          className="bg-grain pointer-events-none absolute inset-0 opacity-[0.18] mix-blend-overlay"
        />
        {/* Sidebar (navegable, con "más opciones" difuminadas abajo) */}
        <aside className="relative hidden w-52 flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl sm:flex dark:border-white/10 dark:bg-black/30">
          {/* Logo con la misma proporción que la sidebar real del software
              (hélix h-9 + título text-2xl, kerning pegado). */}
          <div className="flex h-14 shrink-0 items-center px-4">
            <span className="inline-flex items-center gap-2.5 text-foreground">
              <WellnodMark className="h-9 w-auto" />
              <span className="font-brand translate-y-0.5 text-2xl leading-none tracking-tight">
                <span className="font-bold">Well</span>
                <span className="-ml-[2px] font-light text-foreground/55">nod</span>
              </span>
            </span>
          </div>
          {/* La lista se corta abajo con un fundido: sugiere que hay más, pero no scrollea */}
          <nav className="min-h-0 flex-1 overflow-hidden [mask-image:linear-gradient(to_bottom,#000_calc(100%-2rem),transparent)]">
            <div className="flex flex-col gap-1 px-3 pb-3">
              {NAV_MAIN.map((it) => {
                const active = screen === it.label
                return (
                  <button
                    key={it.label}
                    ref={it.label === "Asesor" ? asesorNavRef : undefined}
                    type="button"
                    onClick={() => onNav(it.label)}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "relative flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition-colors active:scale-[0.98]",
                      active
                        ? "bg-primary font-medium text-primary-foreground shadow-sm"
                        : "text-foreground/70 hover:bg-accent hover:text-foreground"
                    )}
                  >
                    <it.icon className="size-[18px] shrink-0" />
                    {it.label}
                  </button>
                )
              })}
              <p className="px-3 pt-3 pb-1 text-[10px] font-medium tracking-wider text-muted-foreground/50 uppercase">
                Operación
              </p>
              {NAV_OPS.map((it) => (
                <div
                  key={it.label}
                  className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-foreground/70"
                >
                  <it.icon className="size-[18px] shrink-0" />
                  {it.label}
                </div>
              ))}
            </div>
          </nav>
          <div className="flex shrink-0 items-center gap-2.5 border-t border-black/10 p-3 dark:border-white/10">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              JP
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">Juan Pérez</p>
              <p className="truncate text-xs text-muted-foreground">Dueño</p>
            </div>
          </div>
        </aside>

        {/* Contenido */}
        <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl dark:border-white/10 dark:bg-black/30">
          {/* Topbar */}
          <header className="flex h-14 shrink-0 items-center gap-3 border-b border-black/10 px-5 dark:border-white/10">
            <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
              Restaurante Villa Paz
            </span>
            <div className="flex-1" />
            <span className="text-sm tabular-nums text-muted-foreground">14:32</span>
            <span className="rounded-lg bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground">
              En turno
            </span>
          </header>

          {/* La pantalla cambia según la sidebar (fade al cambiar). Sin scroll: se ve la parte de arriba. */}
          <div key={screen} className="screen-fade min-h-0 flex-1 overflow-hidden p-5 text-left">
            {screen === "Inicio" ? (
              <InicioScreen />
            ) : screen === "Finanzas" ? (
              <FinanzasScreen />
            ) : screen === "Clientes" ? (
              <ClientesScreen />
            ) : screen === "Productos" ? (
              <ProductosScreen />
            ) : screen === "IA Insights" ? (
              <CopilotScreen />
            ) : screen === "Reportes" ? (
              <ReportesScreen />
            ) : (
              <AsesorScreen
                buttonRef={tryCopilotRef}
                onTryCopilot={() => onNav("IA Insights")}
              />
            )}
          </div>
        </div>
      </div>

      {/* Cursor del tour guiado: overlay que se mueve entre los botones y "clickea". */}
      {!reduced ? (
        <div
          aria-hidden
          className="pointer-events-none absolute left-0 top-0 z-30"
          style={{
            transform: `translate(${cursor.x}px, ${cursor.y}px)`,
            opacity: cursor.visible ? 1 : 0,
            transition: cursor.snap
              ? "opacity 0.25s ease"
              : "transform 0.7s cubic-bezier(0.22,1,0.36,1), opacity 0.25s ease",
          }}
        >
          <span className="relative block">
            <span
              className={cn(
                "absolute left-0 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-primary transition-all duration-300 ease-out",
                cursor.press ? "size-10 opacity-60" : "size-2 opacity-0"
              )}
            />
            <span
              className="block transition-transform duration-150"
              style={{ transform: cursor.press ? "scale(0.82)" : "scale(1)" }}
            >
              <CursorIcon />
            </span>
          </span>
        </div>
      ) : null}
    </div>
  )
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  )
}

// Cursor de puntero para el autoplay del demo (relleno blanco con borde oscuro).
function CursorIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 16 16"
      fill="none"
      className="drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)]"
    >
      <path
        d="M2 1.5 L2 12.5 L5 9.7 L7.1 14 L9 13.1 L6.9 8.9 L11 8.9 Z"
        fill="#ffffff"
        stroke="#0f172a"
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function Pill({ children, tone }: { children: ReactNode; tone: "green" | "amber" | "red" | "muted" }) {
  const tones = {
    green: "bg-primary/12 text-primary",
    amber: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    red: "bg-destructive/12 text-destructive",
    muted: "bg-muted text-muted-foreground",
  }
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", tones[tone])}>
      {children}
    </span>
  )
}

type Col = { h: string; right?: boolean }
function MiniTable({ cols, rows }: { cols: Col[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {cols.map((c) => (
              <th
                key={c.h}
                className={cn(
                  "px-3 py-2 text-xs font-medium text-muted-foreground",
                  c.right ? "text-right" : "text-left"
                )}
              >
                {c.h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri} className={ri > 0 ? "border-t border-border/60" : ""}>
              {r.map((cell, ci) => (
                <td
                  key={ci}
                  className={cn(
                    "px-3 py-2 text-foreground",
                    cols[ci]?.right ? "text-right tabular-nums" : ""
                  )}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ScreenHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="font-display text-xl font-bold text-foreground">{title}</h2>
        {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {right}
    </div>
  )
}

function RangeChips() {
  const ranges = ["Hoy", "Semana", "Mes", "Año"]
  return (
    <div className="flex gap-1">
      {ranges.map((r) => (
        <span
          key={r}
          className={cn(
            "rounded-lg px-2.5 py-1 text-xs font-medium",
            r === "Mes"
              ? "bg-primary text-primary-foreground"
              : "border border-border text-muted-foreground"
          )}
        >
          {r}
        </span>
      ))}
    </div>
  )
}

// ── Pantallas ───────────────────────────────────────────────────────────────
function InicioScreen() {
  const kpis = [
    { l: "Facturaste hoy", v: "$482.500" },
    { l: "Gastaste hoy", v: "$96.200" },
    { l: "Tu margen hoy", v: "$386.300" },
  ]
  const canales = [
    { m: "MercadoPago", w: "72%" },
    { m: "Efectivo", w: "18%" },
    { m: "Tarjeta", w: "10%" },
  ]
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-sm text-muted-foreground">Tu ganancia de hoy</p>
        <p className="text-3xl font-bold tabular-nums text-foreground sm:text-4xl">$386.300</p>
        <p className="mt-1 text-sm font-medium text-primary">Vas 18% arriba de ayer 🎉</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {kpis.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-border p-4">
        <p className="text-sm font-semibold text-foreground">Cobros de hoy por canal</p>
        <div className="mt-3 flex flex-col gap-2">
          {canales.map((r) => (
            <div key={r.m} className="flex items-center gap-3 text-xs">
              <span className="w-24 shrink-0 text-muted-foreground">{r.m}</span>
              <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                <span className="block h-full rounded-full bg-primary" style={{ width: r.w }} />
              </span>
              <span className="w-8 shrink-0 text-right tabular-nums text-muted-foreground">
                {r.w}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FinanzasScreen() {
  const cards = [
    { l: "Margen neto", v: "$612k", dot: "bg-emerald-500", act: "Mantener" },
    { l: "Food cost", v: "34%", dot: "bg-amber-500", act: "Revisar" },
    { l: "Costo de personal", v: "$410k", dot: "bg-emerald-500", act: "Mantener" },
    { l: "Mermas", v: "$58k", dot: "bg-red-500", act: "Actuar" },
  ]
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title="Finanzas" right={<RangeChips />} />
      <div className="rounded-xl border border-border p-4">
        <p className="text-sm text-muted-foreground">Tu ganancia neta del período</p>
        <p className="text-2xl font-bold tabular-nums text-foreground sm:text-3xl">$612.300</p>
        <p className="mt-1 text-sm text-primary">▲ $84.200 vs período anterior</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {cards.map((c) => (
          <div key={c.l} className="flex flex-col gap-1 rounded-xl border border-border p-4">
            <span className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className={cn("size-2 rounded-full", c.dot)} />
              {c.l}
            </span>
            <span className="text-lg font-bold tabular-nums text-foreground">{c.v}</span>
            <span className="text-xs text-muted-foreground">{c.act}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ClientesScreen() {
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader
        title="Reservas"
        subtitle="Agenda del servicio por día y turno."
        right={
          <span className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">
            Nueva reserva
          </span>
        }
      />
      <MiniTable
        cols={[
          { h: "Hora" },
          { h: "Cliente" },
          { h: "Personas", right: true },
          { h: "Turno" },
          { h: "Mesa" },
          { h: "Estado" },
        ]}
        rows={[
          ["20:30", "Familia Gómez", "4", "Cena", "Mesa 7", <Pill tone="green">Confirmada</Pill>],
          ["21:00", "Laura Díaz", "2", "Cena", "Mesa 3", <Pill tone="muted">Sentada</Pill>],
          ["21:15", "Grupo Empresa", "8", "Cena", "Salón", <Pill tone="green">Confirmada</Pill>],
          ["13:30", "Martín Ruiz", "3", "Almuerzo", "Mesa 5", <Pill tone="red">No-show</Pill>],
        ]}
      />
    </div>
  )
}

function ProductosScreen() {
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title="Productos" subtitle="Tu catálogo y precios." right={<RangeChips />} />
      <MiniTable
        cols={[
          { h: "Nombre" },
          { h: "Precio", right: true },
          { h: "Te deja", right: true },
          { h: "Vendidos", right: true },
          { h: "Estado" },
        ]}
        rows={[
          ["Milanesa napolitana", "$8.900", "$6.340 · 71%", "128", <Pill tone="green">Activo</Pill>],
          ["Papas fritas", "$3.500", "$2.480 · 71%", "96", <Pill tone="green">Activo</Pill>],
          ["IPA Artesanal", "$2.800", "$1.900 · 68%", "84", <Pill tone="green">Activo</Pill>],
          ["Ojo de bife", "$12.400", "$7.100 · 57%", "41", <Pill tone="green">Activo</Pill>],
          ["Flan casero", "$2.200", "$1.540 · 70%", "38", <Pill tone="muted">Inactivo</Pill>],
        ]}
      />
    </div>
  )
}

function ReportesScreen() {
  const kpis = [
    { l: "Ventas", v: "$2,48M" },
    { l: "Cobrado", v: "$2,41M" },
    { l: "Egresos", v: "$1,87M" },
    { l: "Margen bruto", v: "$1,02M" },
    { l: "Ticket promedio", v: "$13,2k" },
    { l: "Food cost", v: "34%" },
  ]
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader title="Reportes" right={<RangeChips />} />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {kpis.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-foreground">Mix de medios de pago</h3>
        <MiniTable
          cols={[
            { h: "Medio" },
            { h: "Tipo" },
            { h: "Operaciones", right: true },
            { h: "Monto", right: true },
          ]}
          rows={[
            ["MercadoPago", "Ingreso", "142", "$1,78M"],
            ["Efectivo", "Ingreso", "38", "$446k"],
            ["Tarjeta", "Ingreso", "21", "$248k"],
          ]}
        />
      </div>
    </div>
  )
}

const KPIS = [
  { l: "Ventas", v: "$2,48M" },
  { l: "Margen bruto", v: "$1,02M" },
  { l: "Margen neto", v: "$612k" },
  { l: "Food cost", v: "34%" },
  { l: "Prime cost", v: "58%" },
  { l: "Punto de equilibrio", v: "$1,9M" },
]

function AsesorScreen({
  onTryCopilot,
  buttonRef,
}: {
  onTryCopilot: () => void
  buttonRef?: Ref<HTMLButtonElement>
}) {
  return (
    <div className="flex flex-col gap-4">
      <ScreenHeader
        title="Asesor"
        subtitle="Cómo te fue y qué hacer. Por defecto, este mes."
        right={
          <div className="flex flex-wrap items-end gap-2">
            <span className="rounded-lg border border-border px-2.5 py-1.5 text-xs text-muted-foreground">
              Jul 2026
            </span>
            <span className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground">
              Configurar costos
            </span>
          </div>
        }
      />

      <button
        ref={buttonRef}
        type="button"
        onClick={onTryCopilot}
        className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-primary/10"
      >
        <Sparkles className="size-4 shrink-0 text-primary" />
        ¿Querés preguntarle a tu negocio? Probá el <b>Copiloto</b> en IA Insights →
      </button>

      <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
        <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
        <p className="text-sm text-foreground">
          Vendiste <b>$2.480.900</b> este mes, un <b className="text-primary">18% más</b>. Tu margen
          neto va en <b>$612.300</b> — sólido, pero el food cost de cocina está alto.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {KPIS.map((k) => (
          <div key={k.l} className="rounded-xl border border-border p-4">
            <p className="text-xs text-muted-foreground">{k.l}</p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-foreground">{k.v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

const QA: { q: string; a: ReactNode }[] = [
  {
    q: "¿Cuánto vendí este mes?",
    a: (
      <>
        Vendiste <b>$2.480.900</b> este mes — un <b className="text-primary">18% más</b> que el mes
        pasado.
      </>
    ),
  },
  {
    q: "¿Mis 5 más vendidos?",
    a: (
      <>
        Milanesa napolitana, papas, IPA, ojo de bife y flan casero — juntos, el <b>41%</b> de tus
        ventas.
      </>
    ),
  },
  {
    q: "¿Qué mozo facturó más?",
    a: (
      <>
        Sofía, con <b>$412.300</b> en 87 mesas — el <b className="text-primary">22%</b> del salón.
      </>
    ),
  },
  {
    q: "¿Reservas de mañana?",
    a: (
      <>
        Tenés <b>14 reservas</b> (38 cubiertos), la mayoría entre las 21 y 22 h.
      </>
    ),
  },
]

function CopilotScreen() {
  const [sel, setSel] = useState(0)
  const [answered, setAnswered] = useState(false)

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="font-display text-xl font-bold text-foreground">Copiloto</h2>
        <p className="text-sm text-muted-foreground">
          Preguntá sobre tu negocio. Te muestro la respuesta y de dónde sale.
        </p>
      </div>

      <div className="flex gap-2">
        <div className="min-w-0 flex-1 truncate rounded-lg border border-border px-3 py-2 text-sm text-foreground">
          {QA[sel].q}
        </div>
        <button
          type="button"
          onClick={() => setAnswered(true)}
          className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition active:scale-[0.97]"
        >
          Preguntar
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {QA.map((item, i) => (
          <button
            key={item.q}
            type="button"
            onClick={() => {
              setSel(i)
              setAnswered(false)
            }}
            className={cn(
              "rounded-lg border px-2.5 py-1 text-xs transition-colors active:scale-[0.98]",
              i === sel
                ? "border-primary bg-primary/10 text-foreground"
                : "border-border text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            {item.q}
          </button>
        ))}
      </div>

      {answered ? (
        <div
          key={sel}
          className="screen-fade flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4"
        >
          <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
          <p className="text-sm text-foreground">{QA[sel].a}</p>
        </div>
      ) : null}
    </div>
  )
}

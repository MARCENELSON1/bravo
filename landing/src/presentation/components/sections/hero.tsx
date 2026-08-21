import { Home, Lightbulb, LineChart, Package, Sparkles, Users } from "lucide-react"

import { WellnodLogo } from "@/presentation/components/brand/wellnod-mark"
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
          style={{ animationDelay: "140ms" }}
        >
          Operás, cobrás y facturás en un solo lugar — con un copiloto que responde lo
          que le preguntás y un asesor que te dice cómo vas y qué hacer.
        </p>
      </div>

      {/* La pantalla del interfaz de Wellnod, debajo del título (réplica de la app) */}
      <div className="hero-screen relative mx-auto mt-14 max-w-7xl px-4" style={{ animationDelay: "300ms" }}>
        <AppMockup />
        {/* Fade inferior: la pantalla "emerge" hacia la siguiente sección */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-28 bg-gradient-to-b from-transparent to-background"
        />
      </div>
    </section>
  )
}

const NAV = [
  { label: "Inicio", icon: Home },
  { label: "Finanzas", icon: LineChart },
  { label: "Clientes", icon: Users },
  { label: "Productos", icon: Package },
  { label: "IA Insights", icon: Lightbulb },
  { label: "Asesor", icon: Sparkles, active: true },
]

const KPIS = [
  { l: "Ventas", v: "$2,48M" },
  { l: "Margen neto", v: "$612k" },
  { l: "Food cost", v: "34%" },
  { l: "Punto de equilibrio", v: "$1,9M" },
]

// Réplica del interfaz de Wellnod: shell de glass sobre el fondo verde, sidebar con
// la marca + navegación, topbar y la página del Asesor (KPIs + qué hacer). Vista
// ilustrativa; el reporte "se arma" con la animación de entrada.
function AppMockup() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border shadow-2xl shadow-primary/10">
      {/* Barra del navegador */}
      <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-3">
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="size-2.5 rounded-full bg-muted-foreground/25" />
        <span className="ml-3 rounded-md bg-muted px-2.5 py-1 text-[11px] text-muted-foreground">
          app.wellnod.com
        </span>
      </div>

      {/* Shell: fondo verde + paneles de glass, igual que el software */}
      <div className="flex gap-3 bg-[radial-gradient(125%_125%_at_18%_12%,#d7e6df_0%,#aec7bb_50%,#85a394_100%)] p-3 dark:bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)]">
        {/* Sidebar */}
        <aside className="hidden w-52 flex-col rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl sm:flex dark:border-white/10 dark:bg-black/30">
          <div className="flex h-14 items-center px-4">
            <WellnodLogo />
          </div>
          <nav className="flex flex-col gap-1 px-3 pb-3">
            {NAV.map((it) => (
              <div
                key={it.label}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm",
                  it.active
                    ? "bg-primary font-medium text-primary-foreground shadow-sm"
                    : "text-foreground/70"
                )}
              >
                <it.icon className="size-[18px] shrink-0" />
                {it.label}
              </div>
            ))}
          </nav>
          <div className="mt-auto flex items-center gap-2.5 border-t border-black/10 p-3 dark:border-white/10">
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
        <div className="flex min-w-0 flex-1 flex-col rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl dark:border-white/10 dark:bg-black/30">
          {/* Topbar */}
          <header className="flex h-14 items-center gap-3 border-b border-black/10 px-5 dark:border-white/10">
            <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
              Restaurante Villa Paz
            </span>
            <div className="flex-1" />
            <span className="text-sm tabular-nums text-muted-foreground">14:32</span>
            <span className="rounded-lg bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground">
              En turno
            </span>
          </header>

          {/* Página del Asesor */}
          <div className="flex flex-col gap-4 p-5 text-left">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">Asesor</h2>
                <p className="text-sm text-muted-foreground">
                  Cómo te fue y qué hacer. Por defecto, este mes.
                </p>
              </div>
              <span className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground">
                Configurar costos
              </span>
            </div>

            {/* Resumen (cómo te fue) */}
            <div
              className="hero-pop flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4"
              style={{ animationDelay: "1100ms" }}
            >
              <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
              <p className="text-sm text-foreground">
                Vendiste <b>$2.480.900</b> este mes, un <b className="text-primary">18% más</b>. Tu
                margen neto va en <b>$612.300</b> — sólido, pero el food cost de cocina está alto.
              </p>
            </div>

            {/* KPIs */}
            <div
              className="hero-pop grid grid-cols-2 gap-3 sm:grid-cols-4"
              style={{ animationDelay: "1250ms" }}
            >
              {KPIS.map((k) => (
                <div key={k.l} className="rounded-xl border border-border p-3">
                  <p className="text-[11px] text-muted-foreground">{k.l}</p>
                  <p className="mt-0.5 text-base font-semibold tabular-nums text-foreground">{k.v}</p>
                </div>
              ))}
            </div>

            {/* Qué hacer (recomendación) */}
            <div
              className="hero-pop rounded-xl border border-border p-4"
              style={{ animationDelay: "1400ms" }}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-foreground">Food cost alto en cocina</span>
                <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                  atención
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                La milanesa napolitana quedó 8 pts abajo de tu objetivo de margen.
              </p>
              <p className="mt-1 text-sm text-foreground">
                → Subí $250 el precio: recuperás el margen sin frenar las ventas.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

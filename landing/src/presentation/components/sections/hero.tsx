import { Home, Lightbulb, LineChart, Package, Sparkles, Users } from "lucide-react"

import { WellnodLogo } from "@/presentation/components/brand/wellnod-mark"
import { useContainer } from "@/presentation/providers/container-provider"
import type { Locale } from "@/domain/value-objects/region"
import { cn } from "@/presentation/lib/cn"

const COPY = {
  "es-AR": {
    titleBefore: "Todo tu restaurante, ",
    titleHighlight: "en una sola app",
    subtitle:
      "Operás, cobrás y facturás en un solo lugar — con un copiloto que responde lo que le preguntás y un asesor que te dice cómo vas y qué hacer.",
    nav: ["Inicio", "Finanzas", "Clientes", "Productos", "IA Insights", "Asesor"],
    ownerName: "Juan Pérez",
    ownerRole: "Dueño",
    venue: "Restaurante Villa Paz",
    onShift: "En turno",
    advisorTitle: "Asesor",
    advisorSubtitle: "Cómo te fue y qué hacer. Por defecto, este mes.",
    configCosts: "Configurar costos",
    kpis: [
      { l: "Ventas", v: "$2,48M" },
      { l: "Margen neto", v: "$612k" },
      { l: "Food cost", v: "34%" },
      { l: "Punto de equilibrio", v: "$1,9M" },
    ],
    recoTitle: "Food cost alto en cocina",
    recoBadge: "atención",
    recoBody: "La milanesa napolitana quedó 8 pts abajo de tu objetivo de margen.",
    recoAction: "→ Subí $250 el precio: recuperás el margen sin frenar las ventas.",
  },
  "en-US": {
    titleBefore: "Your whole restaurant, ",
    titleHighlight: "in one app",
    subtitle:
      "Take orders, get paid, and stay tax-ready in one place — with a copilot that answers whatever you ask and an advisor that tells you how you're doing and what to do next.",
    nav: ["Home", "Finance", "Customers", "Products", "AI Insights", "Advisor"],
    ownerName: "John Smith",
    ownerRole: "Owner",
    venue: "Villa Paz Bistro",
    onShift: "On shift",
    advisorTitle: "Advisor",
    advisorSubtitle: "How you're doing and what to do. This month by default.",
    configCosts: "Configure costs",
    kpis: [
      { l: "Sales", v: "$248k" },
      { l: "Net margin", v: "$61.2k" },
      { l: "Food cost", v: "34%" },
      { l: "Break-even", v: "$190k" },
    ],
    recoTitle: "High food cost in the kitchen",
    recoBadge: "attention",
    recoBody: "The classic cheeseburger came in 8 pts below your margin target.",
    recoAction: "→ Raise the price by $1: you recover the margin without slowing sales.",
  },
} as const

const NAV_ICONS = [Home, LineChart, Users, Package, Lightbulb, Sparkles]

export function Hero() {
  const locale = useContainer().locale
  const t = COPY[locale]

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
          {t.titleBefore}
          <span className="text-primary">{t.titleHighlight}</span>.
        </h1>
        <p
          className="hero-anim mx-auto mt-5 max-w-3xl text-lg text-balance text-muted-foreground sm:text-xl"
          style={{ animationDelay: "140ms" }}
        >
          {t.subtitle}
        </p>
      </div>

      {/* La pantalla del interfaz de Wellnod, debajo del título (réplica de la app) */}
      <div className="hero-screen relative mx-auto mt-14 max-w-7xl px-4" style={{ animationDelay: "300ms" }}>
        <AppMockup locale={locale} />
        {/* Fade inferior: la pantalla "emerge" hacia la siguiente sección */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-28 bg-gradient-to-b from-transparent to-background"
        />
      </div>
    </section>
  )
}

// Réplica del interfaz de Wellnod: shell de glass sobre el fondo verde, sidebar con
// la marca + navegación, topbar y la página del Asesor (KPIs + qué hacer). Vista
// ilustrativa; el reporte "se arma" con la animación de entrada.
function AppMockup({ locale }: { locale: Locale }) {
  const t = COPY[locale]
  const isEn = locale === "en-US"

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
            {t.nav.map((label, i) => {
              const Icon = NAV_ICONS[i]
              const active = i === t.nav.length - 1
              return (
                <div
                  key={label}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2 text-sm",
                    active
                      ? "bg-primary font-medium text-primary-foreground shadow-sm"
                      : "text-foreground/70",
                  )}
                >
                  <Icon className="size-[18px] shrink-0" />
                  {label}
                </div>
              )
            })}
          </nav>
          <div className="mt-auto flex items-center gap-2.5 border-t border-black/10 p-3 dark:border-white/10">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              {t.ownerName
                .split(" ")
                .map((w) => w[0])
                .join("")}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">{t.ownerName}</p>
              <p className="truncate text-xs text-muted-foreground">{t.ownerRole}</p>
            </div>
          </div>
        </aside>

        {/* Contenido */}
        <div className="flex min-w-0 flex-1 flex-col rounded-2xl border border-black/10 bg-white/60 backdrop-blur-2xl dark:border-white/10 dark:bg-black/30">
          {/* Topbar */}
          <header className="flex h-14 items-center gap-3 border-b border-black/10 px-5 dark:border-white/10">
            <span className="min-w-0 truncate text-sm font-medium text-muted-foreground">
              {t.venue}
            </span>
            <div className="flex-1" />
            <span className="text-sm tabular-nums text-muted-foreground">14:32</span>
            <span className="rounded-lg bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground">
              {t.onShift}
            </span>
          </header>

          {/* Página del Asesor */}
          <div className="flex flex-col gap-4 p-5 text-left">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">{t.advisorTitle}</h2>
                <p className="text-sm text-muted-foreground">{t.advisorSubtitle}</p>
              </div>
              <span className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground">
                {t.configCosts}
              </span>
            </div>

            {/* Resumen (cómo te fue) */}
            <div
              className="hero-pop flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4"
              style={{ animationDelay: "1100ms" }}
            >
              <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
              <p className="text-sm text-foreground">
                {isEn ? (
                  <>
                    You sold <b>$248,090</b> this month, <b className="text-primary">up 18%</b>. Your
                    net margin is at <b>$61,230</b> — solid, but kitchen food cost is running high.
                  </>
                ) : (
                  <>
                    Vendiste <b>$2.480.900</b> este mes, un <b className="text-primary">18% más</b>.
                    Tu margen neto va en <b>$612.300</b> — sólido, pero el food cost de cocina está
                    alto.
                  </>
                )}
              </p>
            </div>

            {/* KPIs */}
            <div
              className="hero-pop grid grid-cols-2 gap-3 sm:grid-cols-4"
              style={{ animationDelay: "1250ms" }}
            >
              {t.kpis.map((k) => (
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
                <span className="text-sm font-medium text-foreground">{t.recoTitle}</span>
                <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                  {t.recoBadge}
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{t.recoBody}</p>
              <p className="mt-1 text-sm text-foreground">{t.recoAction}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

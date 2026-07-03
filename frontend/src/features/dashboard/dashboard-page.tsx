import type { ComponentType, ReactNode } from "react"
import { ArrowUp, Plus } from "lucide-react"

// ── Mock data (design pass — no backend wiring yet) ──────────────────────────
const USER_FIRST_NAME = "Juan"

const KPIS = [
  { label: "Facturación hoy", value: 284500, hint: "+12% vs ayer", trend: "up" as const },
  { label: "Gastos del día", value: 98200, hint: "34% de la facturación" },
  { label: "Margen bruto", value: 186300, hint: "65,5% margen", accent: true },
  { label: "Ticket promedio", value: 11380, hint: "25 tickets" },
]

const WEEKLY_REVENUE = [
  { day: "Mar", value: 192000 },
  { day: "Mié", value: 164000 },
  { day: "Jue", value: 208000 },
  { day: "Vie", value: 286000 },
  { day: "Sáb", value: 372000 },
  { day: "Dom", value: 231000 },
  { day: "Lun", value: 234500 },
]
const CHART_MAX = 380000
const CHART_TICKS = [380000, 285000, 190000, 95000, 0]
const WEEKLY_TOTAL = WEEKLY_REVENUE.reduce((sum, d) => sum + d.value, 0)

const RECOMMENDATIONS = [
  {
    kind: "OPORTUNIDAD",
    tone: "positive" as const,
    text: "Lomo al malbec tiene 71% margen pero solo 4% de ventas. Sugerí destacarlo.",
  },
  {
    kind: "ALERTA",
    tone: "negative" as const,
    text: "Costo de Frigorífico Sur subió 18% este mes.",
  },
  {
    kind: "CLIENTE",
    tone: "positive" as const,
    text: "Familia González (LTV $1,2M) no vino hace 60 días.",
  },
]

const PAYMENT_METHODS = [
  { label: "Mercado Pago", amount: 142300, share: 50 },
  { label: "Efectivo", amount: 85300, share: 30 },
  { label: "Tarjeta", amount: 56900, share: 20 },
]

const BREAK_EVEN = { current: 4860000, target: 7200000 }

// ── Helpers ──────────────────────────────────────────────────────────────────
const WEEKDAYS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

const ars = (n: number) => `$${n.toLocaleString("es-AR")}`

function todayLabel(): string {
  const now = new Date()
  return `${WEEKDAYS[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]} ${now.getFullYear()}`
}

// ── Page ─────────────────────────────────────────────────────────────────────
export function DashboardPage() {
  const breakEvenPct = Math.round((BREAK_EVEN.current / BREAK_EVEN.target) * 1000) / 10
  const breakEvenLeft = BREAK_EVEN.target - BREAK_EVEN.current

  return (
    <div className="relative isolate mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8">
      {/* Ambient glow so the frosted-glass cards have something to refract */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-24 left-8 size-[30rem] rounded-full bg-primary/20 blur-[110px]" />
        <div className="absolute bottom-0 right-4 size-[26rem] rounded-full bg-primary/10 blur-[130px]" />
      </div>

      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
            Buen día, {USER_FIRST_NAME}
          </h1>
          <p className="text-sm text-muted-foreground">Esto es lo que pasa hoy en tu negocio</p>
        </div>
        <p className="text-sm text-muted-foreground">{todayLabel()}</p>
      </header>

      {/* KPIs */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPIS.map((kpi) => (
          <Card key={kpi.label} className="p-5">
            <p className="text-sm text-muted-foreground">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{ars(kpi.value)}</p>
            <p
              className={
                kpi.trend === "up" || kpi.accent
                  ? "mt-1 flex items-center gap-1 text-xs font-medium text-primary"
                  : "mt-1 text-xs text-muted-foreground"
              }
            >
              {kpi.trend === "up" ? <ArrowUp className="size-3" /> : null}
              {kpi.hint}
            </p>
          </Card>
        ))}
      </section>

      {/* Chart + AI recommendations */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-base font-semibold text-foreground">Facturación últimos 7 días</h2>
            <p className="text-sm text-muted-foreground">{ars(WEEKLY_TOTAL)} total</p>
          </div>
          <RevenueChart />
        </Card>

        <Card className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">Recomendaciones IA</h2>
          <div className="flex flex-col gap-3">
            {RECOMMENDATIONS.map((rec) => (
              <RecommendationCard key={rec.kind} {...rec} />
            ))}
          </div>
        </Card>
      </section>

      {/* Payment methods + break-even */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">Medios de pago hoy</h2>
          <div className="flex flex-col gap-4">
            {PAYMENT_METHODS.map((pm) => (
              <div key={pm.label} className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-medium text-foreground">{pm.label}</span>
                  <span className="tabular-nums text-muted-foreground">
                    {ars(pm.amount)} · {pm.share}%
                  </span>
                </div>
                <ProgressBar value={pm.share} />
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-base font-semibold text-foreground">Punto de equilibrio del mes</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Llevás {ars(BREAK_EVEN.current)} de {ars(BREAK_EVEN.target)}
          </p>
          <div className="mt-4">
            <ProgressBar value={breakEvenPct} />
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="font-semibold tabular-nums text-foreground">
              {breakEvenPct.toLocaleString("es-AR")}%
            </span>
            <span className="font-medium text-primary">✓ Vas adelantado</span>
            <span className="tabular-nums text-muted-foreground">Faltan {ars(breakEvenLeft)}</span>
          </div>
        </Card>
      </section>

      {/* Floating action button */}
      <button
        type="button"
        aria-label="Acción rápida"
        className="fixed bottom-6 right-6 grid size-14 place-items-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105"
      >
        <Plus className="size-6" />
      </button>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────
function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-white/[0.045] shadow-xl shadow-black/20 backdrop-blur-2xl ${className ?? ""}`}
    >
      {children}
    </div>
  )
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full bg-primary"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

function RevenueChart() {
  return (
    <div className="flex gap-3">
      {/* Y axis */}
      <div className="flex flex-col justify-between py-1 text-right text-[11px] text-muted-foreground">
        {CHART_TICKS.map((tick) => (
          <span key={tick}>{tick === 0 ? "$0" : `$${Math.round(tick / 1000)}k`}</span>
        ))}
      </div>
      {/* Plot */}
      <div className="relative flex-1">
        <div className="absolute inset-0 flex flex-col justify-between">
          {CHART_TICKS.map((tick) => (
            <div key={tick} className="border-t border-dashed border-border/60" />
          ))}
        </div>
        <div className="relative flex h-52 items-end justify-around gap-2">
          {WEEKLY_REVENUE.map((d) => (
            <div key={d.day} className="flex flex-1 flex-col items-center gap-2">
              <div
                className="w-8 rounded-t-md bg-primary transition-all"
                style={{ height: `${(d.value / CHART_MAX) * 100}%` }}
                title={ars(d.value)}
              />
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-around gap-2">
          {WEEKLY_REVENUE.map((d) => (
            <span key={d.day} className="flex-1 text-center text-xs text-muted-foreground">
              {d.day}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

const RECO_TONES: Record<
  "positive" | "negative",
  { border: string; label: string }
> = {
  positive: { border: "border-l-primary", label: "text-primary" },
  negative: { border: "border-l-destructive", label: "text-destructive" },
}

function RecommendationCard({
  kind,
  tone,
  text,
}: {
  kind: string
  tone: "positive" | "negative"
  text: string
  icon?: ComponentType
}) {
  const t = RECO_TONES[tone]
  return (
    <div
      className={`rounded-xl border border-white/10 border-l-2 ${t.border} bg-white/[0.03] p-4 backdrop-blur-md`}
    >
      <p className={`text-xs font-semibold uppercase tracking-wide ${t.label}`}>{kind}</p>
      <p className="mt-1.5 text-sm leading-snug text-foreground/90">{text}</p>
    </div>
  )
}

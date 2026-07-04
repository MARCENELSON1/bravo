import type { ReactNode } from "react"
import { ArrowRight, Plus } from "lucide-react"
import { Link } from "react-router-dom"

import type { FinanceDiagnosticDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { AnimatedNumber } from "@/components/ui/animated-number"
import { useDashboard } from "@/hooks/use-dashboard"
import { usePaymentMix, useRevenueDaily } from "@/hooks/use-analytics"
import { useFinanceOverview } from "@/hooks/use-finance"
import { formatMoney } from "@/lib/money"

// Dashboard Wellnod (solo OWNER/MANAGER — RoleLanding redirige al resto):
// saludo + KPIs del día + facturación 7 días + diagnósticos del Asesor +
// medios de pago + proyección de cierre. Todo con datos reales.

const WEEKDAYS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

const METHOD_LABELS: Record<string, string> = {
  CASH: "Efectivo",
  CARD: "Tarjeta",
  TRANSFER: "Transferencia",
  MERCADOPAGO: "MercadoPago",
  QR: "QR",
}

function todayLabel(): string {
  const now = new Date()
  return `${WEEKDAYS[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]} ${now.getFullYear()}`
}

function startOfTodayIso(): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d.toISOString()
}

function sevenDaysAgoIso(): string {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - 6)
  return d.toISOString()
}

// Compact ARS for chart ticks ("$120 mil" queda largo; "120k" alcanza).
function compact(amountMinor: number): string {
  const pesos = amountMinor / 100
  if (pesos >= 1_000_000) return `$${(pesos / 1_000_000).toLocaleString("es-AR", { maximumFractionDigits: 1 })}M`
  if (pesos >= 1_000) return `$${Math.round(pesos / 1_000)}k`
  return `$${Math.round(pesos)}`
}

export function DashboardPage() {
  const { session } = useAuth()
  const summary = useDashboard()
  const daily = useRevenueDaily({ from: sevenDaysAgoIso() })
  const mix = usePaymentMix({ from: startOfTodayIso() })
  const overview = useFinanceOverview({})

  const d = summary.data
  const currency = d?.currency ?? "ARS"
  const money = (n: number) => formatMoney(Math.round(n), currency)
  const count = (n: number) => String(Math.round(n))
  const firstName = session?.name ? session.name.trim().split(/\s+/)[0] : null

  const kpis = [
    { label: "Ventas cobradas", value: d?.sales, format: money, hint: `${d?.payment_count ?? 0} cobros` },
    { label: "Comandas activas", value: d?.active_orders, format: count, hint: "En curso" },
    { label: "Ticket promedio", value: d?.avg_ticket, format: money, hint: `${d?.paid_orders ?? 0} pagadas` },
    { label: "Egresos", value: d?.expenses, format: money, hint: "Salidas registradas" },
    { label: "Neto", value: d?.net, format: money, hint: "Ventas − egresos" },
  ]

  const inflows = (mix.data ?? []).filter((row) => row.direction === "INFLOW")
  const inflowTotal = inflows.reduce((sum, row) => sum + row.amount, 0)

  const projection = overview.data?.projection ?? null
  const diagnostics = topDiagnostics(overview.data?.diagnostics ?? [])

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
            Buen día{firstName ? `, ${firstName}` : ""}
          </h1>
          <p className="text-sm text-muted-foreground">Esto es lo que pasa hoy en tu negocio</p>
        </div>
        <p className="text-sm text-muted-foreground">{todayLabel()}</p>
      </header>

      {/* KPIs */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {kpis.map((kpi) => (
          <Card key={kpi.label} className="p-5">
            <p className="text-sm text-muted-foreground">{kpi.label}</p>
            <div className="mt-1 text-2xl font-bold tabular-nums text-foreground">
              {summary.isPending || kpi.value === undefined ? (
                <span className="text-muted-foreground">—</span>
              ) : (
                <AnimatedNumber value={kpi.value} format={kpi.format} />
              )}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{kpi.hint}</p>
          </Card>
        ))}
      </section>

      {/* Chart + AI recommendations */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-base font-semibold text-foreground">Facturación últimos 7 días</h2>
            <p className="text-sm text-muted-foreground">
              {daily.data
                ? `${money(daily.data.reduce((sum, p) => sum + p.sales_amount, 0))} total`
                : " "}
            </p>
          </div>
          <RevenueChart points={daily.data ?? []} pending={daily.isPending} currency={currency} />
        </Card>

        <Card className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">Recomendaciones IA</h2>
          <div className="flex flex-col gap-3">
            {overview.isPending ? (
              <p className="text-sm text-muted-foreground">Analizando tu negocio…</p>
            ) : diagnostics.length > 0 ? (
              diagnostics.map((diag) => <RecommendationCard key={diag.code} diag={diag} />)
            ) : (
              <p className="text-sm text-muted-foreground">
                {overview.data?.configured === false
                  ? "Cargá tus costos fijos en el Asesor para recibir diagnósticos."
                  : "Sin señales por ahora — todo en orden."}
              </p>
            )}
          </div>
          <Link
            to="/app/finanzas"
            className="group mt-4 flex items-center gap-1 text-sm font-medium text-primary"
          >
            Ver Finanzas
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </Card>
      </section>

      {/* Payment methods + month-end projection */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">Medios de pago hoy</h2>
          {inflows.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {mix.isPending ? "Cargando…" : "Todavía no hubo cobros hoy."}
            </p>
          ) : (
            <div className="flex flex-col gap-4">
              {inflows.map((row) => {
                const share = inflowTotal > 0 ? Math.round((row.amount / inflowTotal) * 100) : 0
                return (
                  <div key={row.method} className="flex flex-col gap-2">
                    <div className="flex items-baseline justify-between text-sm">
                      <span className="font-medium text-foreground">
                        {METHOD_LABELS[row.method] ?? row.method}
                      </span>
                      <span className="tabular-nums text-muted-foreground">
                        {money(row.amount)} · {share}%
                      </span>
                    </div>
                    <ProgressBar value={share} />
                  </div>
                )
              })}
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-base font-semibold text-foreground">Proyección de cierre del mes</h2>
          {projection ? (
            <>
              <p className="mt-1 text-sm text-muted-foreground">
                Si seguís así, cerrás en{" "}
                <span className="font-semibold text-foreground">
                  {formatMoney(projection.sales_amount, overview.data?.currency ?? currency)}
                </span>
              </p>
              <div className="mt-4">
                <ProgressBar
                  value={
                    projection.month_days > 0
                      ? (projection.elapsed_days / projection.month_days) * 100
                      : 0
                  }
                />
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm">
                <span className="tabular-nums text-muted-foreground">
                  Día {projection.elapsed_days} de {projection.month_days}
                </span>
                <span className="font-medium text-primary">
                  Margen neto proyectado:{" "}
                  {formatMoney(projection.net_margin_amount, overview.data?.currency ?? currency)}
                </span>
              </div>
            </>
          ) : (
            <p className="mt-1 text-sm text-muted-foreground">
              {overview.isPending
                ? "Calculando…"
                : "Sin datos suficientes este mes para proyectar."}
            </p>
          )}
        </Card>
      </section>

      {/* Floating quick action */}
      <Link
        to="/app/expenses"
        aria-label="Registrar egreso"
        title="Registrar egreso"
        className="fixed bottom-6 right-6 grid size-14 place-items-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105"
      >
        <Plus className="size-6" />
      </Link>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

// Frosted-glass card, light and dark variants (the shell backdrop shows through).
function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-black/10 bg-white/55 shadow-xl shadow-black/5 backdrop-blur-2xl dark:border-white/10 dark:bg-white/[0.045] dark:shadow-black/20 ${className ?? ""}`}
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

// alert primero, después warn, después el resto; top 3.
function topDiagnostics(diagnostics: FinanceDiagnosticDTO[]): FinanceDiagnosticDTO[] {
  const rank = (severity: string) => (severity === "alert" ? 0 : severity === "warn" ? 1 : 2)
  return [...diagnostics].sort((a, b) => rank(a.severity) - rank(b.severity)).slice(0, 3)
}

const DIAG_TONES: Record<string, { border: string; label: string }> = {
  alert: { border: "border-l-destructive", label: "text-destructive" },
  warn: { border: "border-l-amber-500", label: "text-amber-600 dark:text-amber-400" },
}
const DIAG_DEFAULT_TONE = { border: "border-l-primary", label: "text-primary" }

function RecommendationCard({ diag }: { diag: FinanceDiagnosticDTO }) {
  const tone = DIAG_TONES[diag.severity] ?? DIAG_DEFAULT_TONE
  return (
    <div
      className={`rounded-xl border border-black/10 border-l-2 ${tone.border} bg-white/40 p-4 backdrop-blur-md dark:border-white/10 dark:bg-white/[0.03]`}
    >
      <p className={`text-xs font-semibold uppercase tracking-wide ${tone.label}`}>{diag.title}</p>
      <p className="mt-1.5 text-sm leading-snug text-foreground/90">{diag.body}</p>
      {diag.action ? (
        <p className="mt-1 text-xs text-muted-foreground">{diag.action}</p>
      ) : null}
    </div>
  )
}

// Last 7 calendar days, filling the gaps with zeros (the API omits empty days).
function lastSevenDays(points: { day: string; sales_amount: number }[]) {
  const byDay = new Map(points.map((p) => [p.day, p.sales_amount]))
  const days: { key: string; label: string; value: number }[] = []
  const cursor = new Date()
  cursor.setHours(0, 0, 0, 0)
  cursor.setDate(cursor.getDate() - 6)
  for (let i = 0; i < 7; i += 1) {
    const key = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`
    days.push({
      key,
      label: WEEKDAYS[cursor.getDay()].slice(0, 3),
      value: byDay.get(key) ?? 0,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}

function RevenueChart({
  points,
  pending,
  currency,
}: {
  points: { day: string; sales_amount: number }[]
  pending: boolean
  currency: string
}) {
  const days = lastSevenDays(points)
  const max = Math.max(...days.map((d) => d.value), 1)
  const hasSales = days.some((d) => d.value > 0)

  if (!pending && !hasSales) {
    return (
      <p className="grid h-52 place-items-center text-sm text-muted-foreground">
        Sin ventas en los últimos 7 días.
      </p>
    )
  }

  const ticks = [max, max / 2, 0]
  return (
    <div className="flex gap-3">
      {/* Y axis */}
      <div className="flex flex-col justify-between py-1 text-right text-[11px] text-muted-foreground">
        {ticks.map((tick) => (
          <span key={tick}>{compact(tick)}</span>
        ))}
      </div>
      {/* Plot */}
      <div className="relative flex-1">
        <div className="absolute inset-0 flex flex-col justify-between">
          {ticks.map((tick) => (
            <div key={tick} className="border-t border-dashed border-border/60" />
          ))}
        </div>
        <div className="relative flex h-52 items-end justify-around gap-2">
          {days.map((d) => (
            <div key={d.key} className="flex flex-1 flex-col items-center gap-2">
              <div
                className="w-8 rounded-t-md bg-primary transition-all"
                style={{ height: `${(d.value / max) * 100}%` }}
                title={formatMoney(d.value, currency)}
              />
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-around gap-2">
          {days.map((d) => (
            <span key={d.key} className="flex-1 text-center text-xs text-muted-foreground">
              {d.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

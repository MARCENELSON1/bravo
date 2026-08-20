import { useState } from "react"
import { ArrowRight, Plus } from "lucide-react"
import { Link } from "react-router-dom"

import type { FinanceDiagnosticDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { AnimatedNumber } from "@/components/ui/animated-number"
import { GlassCard } from "@/components/ui/glass-card"
import { dailyVerdict } from "@/features/dashboard/daily-verdict"
import { tomorrowTask } from "@/features/dashboard/tomorrow-task"
import { RecentMovements } from "@/features/finance/recent-movements"
import { useDashboard } from "@/hooks/use-dashboard"
import { usePaymentMix, useRevenueDaily } from "@/hooks/use-analytics"
import { useFinanceOverview, useRecentMovements } from "@/hooks/use-finance"
import { formatMoney } from "@/lib/money"

// Home Wellnod (solo OWNER/MANAGER — RoleLanding redirige al resto): jerarquía de
// 7 niveles del spec. "Arrancás viendo lo único que importa": la ganancia del día.

const WEEKDAYS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
const METHOD_LABELS: Record<string, string> = {
  CASH: "Efectivo",
  CARD: "Tarjeta",
  TRANSFER: "Transferencia",
  MERCADOPAGO: "MercadoPago",
  QR: "QR",
}
const TONE_STYLE: Record<string, string> = {
  good: "text-emerald-500",
  ok: "text-amber-500",
  bad: "text-red-500",
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
function compact(amountMinor: number): string {
  const pesos = amountMinor / 100
  if (pesos >= 1_000_000)
    return `$${(pesos / 1_000_000).toLocaleString("es-AR", { maximumFractionDigits: 1 })}M`
  if (pesos >= 1_000) return `$${Math.round(pesos / 1_000)}k`
  return `$${Math.round(pesos)}`
}

const SEVERITY_RANK: Record<string, number> = { alert: 0, warn: 1, healthy: 2 }
function topAlert(diagnostics: FinanceDiagnosticDTO[]): FinanceDiagnosticDTO | null {
  const urgent = diagnostics
    .filter((d) => d.severity === "alert" || d.severity === "warn")
    .sort((a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9))
  return urgent[0] ?? null
}

export function DashboardPage() {
  const { session } = useAuth()
  const summary = useDashboard()
  const daily = useRevenueDaily({ from: sevenDaysAgoIso() })
  const mix = usePaymentMix({ from: startOfTodayIso() })
  const overview = useFinanceOverview({})
  const movements = useRecentMovements({ from: startOfTodayIso() }, true)
  const [taskDone, setTaskDone] = useState(false)

  const d = summary.data
  const currency = d?.currency ?? "ARS"
  const money = (n: number) => formatMoney(Math.round(n), currency)
  const firstName = session?.name ? session.name.trim().split(/\s+/)[0] : null

  const net = d?.net ?? 0
  const sales = d?.sales ?? 0
  const expenses = d?.expenses ?? 0
  const pctVsYesterday = revenuePctVsYesterday(daily.data ?? [])
  const verdict = dailyVerdict(net, pctVsYesterday)
  const marginPer100 = sales > 0 ? Math.round((net / sales) * 100) : 0

  const inflows = (mix.data ?? []).filter((row) => row.direction === "INFLOW")
  const inflowTotal = inflows.reduce((sum, row) => sum + row.amount, 0)

  const diagnostics = overview.data?.diagnostics ?? []
  const alert = topAlert(diagnostics)
  const task = tomorrowTask(diagnostics)
  const projection = overview.data?.projection ?? null

  return (
    <div className="relative isolate mx-auto flex w-full max-w-5xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-40 left-1/2 h-[26rem] w-[80%] -translate-x-1/2 rounded-[50%] bg-primary/22 blur-[130px]" />
      </div>

      <header className="flex flex-wrap items-start justify-between gap-2">
        <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
          Buen día{firstName ? `, ${firstName}` : ""}
        </h1>
        <p className="text-sm text-muted-foreground">{todayLabel()}</p>
      </header>

      {/* NIVEL 1 — Tu ganancia de hoy */}
      <GlassCard className="p-6">
        <p className="text-sm text-muted-foreground">Tu ganancia de hoy</p>
        <div
          className={`mt-1 text-4xl font-bold tabular-nums ${net < 0 ? "text-red-500" : "text-foreground"}`}
        >
          {summary.isPending ? (
            <span className="text-muted-foreground">—</span>
          ) : (
            <AnimatedNumber value={net} format={money} />
          )}
        </div>
        <p className={`mt-2 text-sm font-medium ${TONE_STYLE[verdict.tone]}`}>{verdict.message}</p>
      </GlassCard>

      {/* NIVEL 2 — Los 3 números que lo explican */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">Facturaste hoy</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{money(sales)}</p>
          <p className="mt-1 text-xs text-muted-foreground">{d?.payment_count ?? 0} cobros</p>
        </GlassCard>
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">Gastaste hoy</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{money(expenses)}</p>
          <p className="mt-1 text-xs text-muted-foreground">Egresos registrados</p>
        </GlassCard>
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">Tu margen hoy</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{money(net)}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {sales > 0 ? `De cada $100, $${marginPer100} son ganancia` : "Sin ventas aún"}
          </p>
        </GlassCard>
      </section>

      {/* NIVEL 3 — Cobros del día por canal (bruto) */}
      <GlassCard className="p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">Cobros de hoy por canal</h2>
        <p className="mb-4 text-xs text-muted-foreground">
          Montos brutos (aún no descontamos comisiones de Mercado Pago / tarjeta).
        </p>
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
      </GlassCard>

      {/* NIVEL 4 — Alerta del día (máx 1) */}
      {alert ? (
        <GlassCard className="border-l-2 border-l-destructive p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-destructive">
            Atención hoy
          </p>
          <p className="mt-1.5 text-sm font-medium text-foreground">{alert.title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{alert.body}</p>
        </GlassCard>
      ) : null}

      {/* NIVEL 5 — Progreso del mes */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="p-6 lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-base font-semibold text-foreground">Facturación últimos 7 días</h2>
            <p className="text-sm text-muted-foreground">
              {daily.data
                ? `${money(daily.data.reduce((sum, p) => sum + p.sales_amount, 0))} total`
                : " "}
            </p>
          </div>
          <RevenueChart points={daily.data ?? []} pending={daily.isPending} currency={currency} />
        </GlassCard>
        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-foreground">Cierre del mes</h2>
          {projection ? (
            <>
              <p className="mt-1 text-sm text-muted-foreground">
                Si seguís así, cerrás en{" "}
                <span className="font-semibold text-foreground">
                  {money(projection.sales_amount)}
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
              <p className="mt-2 text-xs text-muted-foreground">
                Día {projection.elapsed_days} de {projection.month_days}
              </p>
            </>
          ) : (
            <p className="mt-1 text-sm text-muted-foreground">
              {overview.isPending ? "Calculando…" : "Sin datos suficientes para proyectar."}
            </p>
          )}
          <Link
            to="/app/finanzas"
            className="group mt-4 flex items-center gap-1 text-sm font-medium text-primary"
          >
            Ver Finanzas
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </GlassCard>
      </section>

      {/* NIVEL 6 — Últimos movimientos (5) */}
      <RecentMovements
        movements={(movements.data ?? []).slice(0, 5)}
        currency={currency}
        pending={movements.isPending}
      />

      {/* NIVEL 7 — Tu tarea para mañana */}
      {task && !taskDone ? (
        <GlassCard className="p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            Tu tarea para mañana
          </p>
          <p className="mt-1.5 text-sm text-foreground">{task}</p>
          <button
            type="button"
            onClick={() => setTaskDone(true)}
            className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            Entendido
          </button>
        </GlassCard>
      ) : null}

      <Link
        to="/app/expenses"
        aria-label="Registrar egreso"
        title="Registrar egreso"
        className="fixed bottom-6 right-6 grid size-14 place-items-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform duration-200 ease-out hover:scale-105 active:scale-[0.97]"
      >
        <Plus className="size-6" />
      </Link>
    </div>
  )
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

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

// Facturación de hoy vs ayer (últimos dos días de la serie), % o null.
function revenuePctVsYesterday(points: { day: string; sales_amount: number }[]): number | null {
  const byDay = new Map(points.map((p) => [p.day, p.sales_amount]))
  const key = (offset: number) => {
    const c = new Date()
    c.setHours(0, 0, 0, 0)
    c.setDate(c.getDate() - offset)
    return `${c.getFullYear()}-${String(c.getMonth() + 1).padStart(2, "0")}-${String(c.getDate()).padStart(2, "0")}`
  }
  const today = byDay.get(key(0)) ?? 0
  const yesterday = byDay.get(key(1)) ?? 0
  if (yesterday <= 0) return null
  return ((today - yesterday) / yesterday) * 100
}

function lastSevenDays(points: { day: string; sales_amount: number }[]) {
  const byDay = new Map(points.map((p) => [p.day, p.sales_amount]))
  const days: { key: string; label: string; value: number }[] = []
  const cursor = new Date()
  cursor.setHours(0, 0, 0, 0)
  cursor.setDate(cursor.getDate() - 6)
  for (let i = 0; i < 7; i += 1) {
    const key = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`
    days.push({ key, label: WEEKDAYS[cursor.getDay()].slice(0, 3), value: byDay.get(key) ?? 0 })
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
  const max = Math.max(...days.map((x) => x.value), 1)
  const hasSales = days.some((x) => x.value > 0)
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
      <div className="flex flex-col justify-between py-1 text-right text-[11px] text-muted-foreground">
        {ticks.map((tick) => (
          <span key={tick}>{compact(tick)}</span>
        ))}
      </div>
      <div className="relative flex-1">
        <div className="absolute inset-0 flex flex-col justify-between">
          {ticks.map((tick) => (
            <div key={tick} className="border-t border-dashed border-border/60" />
          ))}
        </div>
        <div className="relative flex h-52 items-end justify-around gap-2">
          {days.map((x) => (
            <div key={x.key} className="flex flex-1 flex-col items-center gap-2">
              <div
                className="w-8 rounded-t-md bg-primary transition-all"
                style={{ height: `${(x.value / max) * 100}%` }}
                title={formatMoney(x.value, currency)}
              />
            </div>
          ))}
        </div>
        <div className="mt-2 flex justify-around gap-2">
          {days.map((x) => (
            <span key={x.key} className="flex-1 text-center text-xs text-muted-foreground">
              {x.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

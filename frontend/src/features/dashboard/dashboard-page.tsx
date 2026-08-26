import { useState } from "react"
import type { TFunction } from "i18next"
import { ArrowRight, Plus } from "lucide-react"

import { numberLocale } from "@/lib/format"
import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"

import type { FinanceDiagnosticDTO } from "@/api/types-operations"
import { useAuth } from "@/auth/auth-context"
import { AnimatedNumber } from "@/components/ui/animated-number"
import { GlassCard } from "@/components/ui/glass-card"
import { dailyVerdict } from "@/features/dashboard/daily-verdict"
import {
  CashSnapshot,
  SalonSnapshot,
} from "@/features/dashboard/operational-snapshots"
import { RequiresAttention } from "@/features/dashboard/requires-attention"
import { tomorrowTask } from "@/features/dashboard/tomorrow-task"
import { RecentMovements } from "@/features/finance/recent-movements"
import { useDashboard } from "@/hooks/use-dashboard"
import { usePaymentMix, useRevenueDaily } from "@/hooks/use-analytics"
import { useFinanceOverview, useRecentMovements } from "@/hooks/use-finance"
import { formatMoney } from "@/lib/money"

// Home Wellnod (solo OWNER/MANAGER — RoleLanding redirige al resto): jerarquía de
// 7 niveles del spec. "Arrancás viendo lo único que importa": la ganancia del día.

const TONE_STYLE: Record<string, string> = {
  good: "text-emerald-500",
  ok: "text-amber-500",
  bad: "text-red-500",
}

function todayLabel(t: TFunction): string {
  const now = new Date()
  const weekdays = t("dashboard.weekdays", { returnObjects: true }) as unknown as string[]
  const months = t("dashboard.months", { returnObjects: true }) as unknown as string[]
  return t("dashboard.todayFormat", {
    weekday: weekdays[now.getDay()],
    day: now.getDate(),
    month: months[now.getMonth()],
    year: now.getFullYear(),
  })
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
    return `$${(pesos / 1_000_000).toLocaleString(numberLocale(), { maximumFractionDigits: 1 })}M`
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
  const { t } = useTranslation()
  const { session } = useAuth()
  // Guarda C: el Home es "hoy" — acotamos a hoy para que el hero cuadre con
  // "Cobros por canal" (antes sumaba all-time rotulado "hoy").
  const summary = useDashboard({ from: startOfTodayIso() })
  const daily = useRevenueDaily({ from: sevenDaysAgoIso() })
  const mix = usePaymentMix({ from: startOfTodayIso() })
  const overview = useFinanceOverview({})
  const movements = useRecentMovements({ from: startOfTodayIso() }, true)
  const [taskDone, setTaskDone] = useState(false)

  const d = summary.data
  const currency = d?.currency ?? "ARS"
  const money = (n: number) => formatMoney(Math.round(n), currency, 0)
  const firstName = session?.name ? session.name.trim().split(/\s+/)[0] : null

  const sales = d?.sales ?? 0
  const expenses = d?.expenses ?? 0
  // Comisiones (slice B): la ganancia REAL resta las comisiones de pasarela. Sin
  // tasas cargadas, collected_net == sales → net == sales − expenses (paridad).
  const feesTotal = d?.fees_total ?? 0
  const net = (d?.collected_net ?? sales) - expenses
  const pctVsYesterday = revenuePctVsYesterday(daily.data ?? [])
  const verdict = dailyVerdict(net, pctVsYesterday)
  const verdictVs = verdict.vsKey
    ? t(`dashboard.verdict.${verdict.vsKey}`, { pct: verdict.pct })
    : ""
  const verdictMessage = t(`dashboard.verdict.${verdict.tone}`, { vs: verdictVs })
  const marginPer100 = sales > 0 ? Math.round((net / sales) * 100) : 0
  // Guarda C: hubo ventas pero cero egresos → el margen = ventas es un número
  // inflado (todavía no cargaste gastos). Lo mostramos provisorio, no como sólido.
  const marginTentative = sales > 0 && expenses === 0

  const inflows = (mix.data ?? []).filter((row) => row.direction === "INFLOW")
  const inflowTotal = inflows.reduce((sum, row) => sum + row.amount, 0)

  const diagnostics = overview.data?.diagnostics ?? []
  const alert = topAlert(diagnostics)
  const alertIsWarn = alert?.severity === "warn"
  const task = tomorrowTask(diagnostics)
  const projection = overview.data?.projection ?? null

  return (
    <div className="relative isolate mx-auto flex w-full max-w-5xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-40 left-1/2 h-[26rem] w-[80%] -translate-x-1/2 rounded-[50%] bg-primary/22 blur-[130px]" />
      </div>

      <header className="flex flex-wrap items-start justify-between gap-2">
        <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
          {firstName ? t("dashboard.greetingNamed", { name: firstName }) : t("dashboard.greeting")}
        </h1>
        <p className="text-sm text-muted-foreground">{todayLabel(t)}</p>
      </header>

      {/* NIVEL 1 — Tu ganancia de hoy */}
      <GlassCard className="p-6">
        <p className="text-sm text-muted-foreground">{t("dashboard.todayProfit")}</p>
        <div
          className={`mt-1 text-3xl font-bold tabular-nums sm:text-4xl ${net < 0 ? "text-red-500" : "text-foreground"}`}
        >
          {summary.isPending ? (
            <span className="text-muted-foreground">—</span>
          ) : (
            <AnimatedNumber value={net} format={money} />
          )}
        </div>
        <p className={`mt-2 text-sm font-medium ${TONE_STYLE[verdict.tone]}`}>{verdictMessage}</p>
        {marginTentative ? (
          <p className="mt-1 text-xs text-amber-500">{t("dashboard.profitTentative")}</p>
        ) : null}
        {feesTotal > 0 ? (
          <p className="mt-1 text-xs text-muted-foreground">
            {t("dashboard.feesDeducted", { amount: money(feesTotal) })}
          </p>
        ) : null}
      </GlassCard>

      {/* Requiere tu atención — la franja operativa (mesas / caja / stock / clientes) */}
      <RequiresAttention />

      {/* Snapshots operativos: salón en vivo + estado de la caja del día */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <SalonSnapshot />
        <CashSnapshot />
      </section>

      {/* NIVEL 2 — Los 3 números que lo explican */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">{t("dashboard.billedToday")}</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{money(sales)}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("dashboard.paymentsCount", { n: d?.payment_count ?? 0 })}
          </p>
        </GlassCard>
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">{t("dashboard.spentToday")}</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">{money(expenses)}</p>
          <p className="mt-1 text-xs text-muted-foreground">{t("dashboard.expensesRegistered")}</p>
        </GlassCard>
        <GlassCard className="p-5">
          <p className="text-sm text-muted-foreground">{t("dashboard.marginToday")}</p>
          {marginTentative ? (
            <>
              <p className="mt-1 text-2xl font-bold tabular-nums text-muted-foreground">—</p>
              <p className="mt-1 text-xs text-amber-500">
                {t("dashboard.loadExpensesForMargin")}
              </p>
            </>
          ) : (
            <>
              {/* Dedupe (B4): el $ de la ganancia vive en el hero; acá el margen %. */}
              <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">
                {sales > 0 ? `${marginPer100}%` : "—"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {sales > 0
                  ? t("dashboard.marginExplain", { margin: marginPer100 })
                  : t("dashboard.noSalesYet")}
              </p>
            </>
          )}
        </GlassCard>
      </section>

      {/* NIVEL 3 — Cobros del día por canal (bruto) */}
      <GlassCard className="p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">
          {t("dashboard.channelsTitle")}
        </h2>
        <p className="mb-4 text-xs text-muted-foreground">{t("dashboard.channelsSubtitle")}</p>
        {inflows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {mix.isPending ? t("dashboard.loading") : t("dashboard.noPaymentsToday")}
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {inflows.map((row) => {
              const share = inflowTotal > 0 ? Math.round((row.amount / inflowTotal) * 100) : 0
              return (
                <div key={row.method} className="flex flex-col gap-2">
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="font-medium text-foreground">
                      {t(`dashboard.methods.${row.method}`, { defaultValue: row.method })}
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
        <GlassCard
          className={`border-l-2 p-6 ${alertIsWarn ? "border-l-amber-500" : "border-l-destructive"}`}
        >
          <p
            className={`text-xs font-semibold uppercase tracking-wide ${alertIsWarn ? "text-amber-600 dark:text-amber-400" : "text-destructive"}`}
          >
            {t("dashboard.attentionToday")}
          </p>
          <p className="mt-1.5 text-sm font-medium text-foreground">{alert.title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{alert.body}</p>
        </GlassCard>
      ) : null}

      {/* NIVEL 5 — Progreso del mes */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <GlassCard className="p-6 lg:col-span-2">
          <div className="mb-6">
            <h2 className="text-base font-semibold text-foreground">
              {t("dashboard.revenue7dTitle")}
            </h2>
            <p className="text-sm text-muted-foreground">
              {daily.data
                ? t("dashboard.totalSuffix", {
                    amount: money(daily.data.reduce((sum, p) => sum + p.sales_amount, 0)),
                  })
                : " "}
            </p>
          </div>
          <RevenueChart points={daily.data ?? []} pending={daily.isPending} currency={currency} />
        </GlassCard>
        <GlassCard className="p-6">
          <h2 className="text-base font-semibold text-foreground">{t("dashboard.monthClose")}</h2>
          {projection ? (
            <>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("dashboard.onTrackToClose")}{" "}
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
                {t("dashboard.dayOfMonth", {
                  elapsed: projection.elapsed_days,
                  total: projection.month_days,
                })}
              </p>
            </>
          ) : (
            <p className="mt-1 text-sm text-muted-foreground">
              {overview.isPending ? t("dashboard.calculating") : t("dashboard.notEnoughData")}
            </p>
          )}
          <Link
            to="/app/finanzas"
            className="group mt-4 flex items-center gap-1 text-sm font-medium text-primary"
          >
            {t("dashboard.viewFinance")}
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </GlassCard>
      </section>

      {/* NIVEL 6 — Últimos movimientos (5) */}
      <RecentMovements
        movements={(movements.data ?? []).slice(0, 5)}
        currency={currency}
        pending={movements.isPending}
        fractionDigits={0}
      />

      {/* NIVEL 7 — Tu tarea para mañana */}
      {task && !taskDone ? (
        <GlassCard className="p-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {t("dashboard.tomorrowTaskTitle")}
          </p>
          <p className="mt-1.5 text-sm text-foreground">{task}</p>
          <button
            type="button"
            onClick={() => setTaskDone(true)}
            className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            {t("dashboard.gotIt")}
          </button>
        </GlassCard>
      ) : null}

      <Link
        to="/app/expenses"
        aria-label={t("dashboard.registerExpense")}
        title={t("dashboard.registerExpense")}
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

function lastSevenDays(points: { day: string; sales_amount: number }[], weekdays: string[]) {
  const byDay = new Map(points.map((p) => [p.day, p.sales_amount]))
  const days: { key: string; label: string; value: number }[] = []
  const cursor = new Date()
  cursor.setHours(0, 0, 0, 0)
  cursor.setDate(cursor.getDate() - 6)
  for (let i = 0; i < 7; i += 1) {
    const key = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`
    days.push({ key, label: weekdays[cursor.getDay()].slice(0, 3), value: byDay.get(key) ?? 0 })
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
  const { t } = useTranslation()
  const weekdays = t("dashboard.weekdays", { returnObjects: true }) as unknown as string[]
  const days = lastSevenDays(points, weekdays)
  const max = Math.max(...days.map((x) => x.value), 1)
  const hasSales = days.some((x) => x.value > 0)
  if (!pending && !hasSales) {
    return (
      <p className="grid h-52 place-items-center text-sm text-muted-foreground">
        {t("dashboard.noSales7d")}
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
                title={formatMoney(x.value, currency, 0)}
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

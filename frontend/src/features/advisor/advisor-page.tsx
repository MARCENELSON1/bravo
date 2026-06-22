import { useState } from "react"
import { Sparkles } from "lucide-react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { AdvisorKpisDTO, AdvisorSettingsDTO } from "@/api/types-advisor"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import {
  useAdvisorReport,
  useAdvisorSettings,
  useUpdateAdvisorSettings,
} from "@/hooks/use-advisor"
import { BUCKET_LABELS, BUCKET_ORDER, formatPct, SEVERITY_VARIANT } from "@/lib/advisor"
import { formatMoney } from "@/lib/money"

function KpiCard({
  label,
  value,
  hint,
  negative,
}: {
  label: string
  value: string
  hint?: string
  negative?: boolean
}) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-border p-4">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={`text-xl font-semibold tabular-nums ${negative ? "text-destructive" : "text-foreground"}`}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  )
}

function SettingsForm({
  initial,
  onDone,
}: {
  initial: AdvisorSettingsDTO
  onDone: () => void
}) {
  const update = useUpdateAdvisorSettings()
  const [labor, setLabor] = useState(() => String(initial.monthly_labor_cost / 100))
  const [other, setOther] = useState(() => String(initial.monthly_other_fixed_costs / 100))
  const [target, setTarget] = useState(() => String(initial.target_food_cost_bps / 100))

  const submit = () => {
    const laborMinor = Math.round(Number(labor) * 100)
    const otherMinor = Math.round(Number(other) * 100)
    const targetBps = Math.round(Number(target) * 100)
    if (
      !Number.isFinite(laborMinor) ||
      laborMinor < 0 ||
      !Number.isFinite(otherMinor) ||
      otherMinor < 0 ||
      !Number.isFinite(targetBps) ||
      targetBps < 0 ||
      targetBps > 10000
    ) {
      toast.error("Revisá los montos y el objetivo de food cost.")
      return
    }
    update.mutate(
      {
        monthly_labor_cost: laborMinor,
        monthly_other_fixed_costs: otherMinor,
        target_food_cost_bps: targetBps,
      },
      {
        onSuccess: () => {
          toast.success("Costos guardados.")
          onDone()
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos guardar los costos."),
      }
    )
  }

  return (
    <div className="flex flex-col gap-3 px-4 pb-4">
      <label className="flex flex-col gap-1 text-sm">
        Sueldos del mes
        <Input
          type="number"
          min={0}
          step="0.01"
          value={labor}
          onChange={(e) => setLabor(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Otros costos fijos del mes (alquiler, servicios…)
        <Input
          type="number"
          min={0}
          step="0.01"
          value={other}
          onChange={(e) => setOther(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Objetivo de food cost (%)
        <Input
          type="number"
          min={0}
          max={100}
          step="0.1"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        />
      </label>
      <Button onClick={submit} disabled={update.isPending}>
        {update.isPending ? "Guardando…" : "Guardar costos"}
      </Button>
    </div>
  )
}

function SettingsSheet() {
  const settings = useAdvisorSettings()
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline">Configurar costos</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Costos del mes</SheetTitle>
          <SheetDescription>
            Sueldos y costos fijos para calcular margen neto, prime cost y punto de equilibrio.
          </SheetDescription>
        </SheetHeader>
        {open && settings.data ? (
          <SettingsForm initial={settings.data} onDone={() => setOpen(false)} />
        ) : (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}

function KpiGrid({ kpis }: { kpis: AdvisorKpisDTO }) {
  const money = (amount: number) => formatMoney(amount, kpis.currency)
  const lockedHint = kpis.configured ? undefined : "Configurá costos"
  const locked = (value: string) => (kpis.configured ? value : "—")
  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      <KpiCard label="Ventas" value={money(kpis.sales_amount)} />
      <KpiCard label="Margen bruto" value={money(kpis.gross_margin_amount)} />
      <KpiCard
        label="Margen neto"
        value={locked(money(kpis.net_margin_amount))}
        hint={lockedHint}
        negative={kpis.configured && kpis.net_margin_amount < 0}
      />
      <KpiCard label="Food cost" value={formatPct(kpis.food_cost_ratio_bps)} />
      <KpiCard
        label="Prime cost"
        value={locked(formatPct(kpis.prime_cost_ratio_bps))}
        hint={lockedHint}
      />
      <KpiCard
        label="Punto de equilibrio"
        value={locked(money(kpis.break_even_amount))}
        hint={lockedHint}
      />
    </section>
  )
}

export function AdvisorPage() {
  const [from, setFrom] = useState("")
  const [to, setTo] = useState("")
  const fromIso = from ? new Date(`${from}T00:00:00`).toISOString() : undefined
  const toIso = to ? new Date(`${to}T23:59:59`).toISOString() : undefined
  const report = useAdvisorReport({ from: fromIso, to: toIso })

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Asesor
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            Cómo te fue en pesos y qué hacer. Por defecto, este mes.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Desde
            <Input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-auto"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Hasta
            <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="w-auto" />
          </label>
          <SettingsSheet />
        </div>
      </header>

      {report.isPending ? (
        <div className="flex justify-center p-10">
          <Spinner className="size-5 text-muted-foreground" />
        </div>
      ) : report.data ? (
        <>
          {report.data.summary ? (
            <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
              <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
              <p className="text-sm text-foreground">{report.data.summary}</p>
            </div>
          ) : null}

          <KpiGrid kpis={report.data.kpis} />

          <div className="flex flex-col gap-6">
            {BUCKET_ORDER.map((bucket) => {
              const items = report.data.insights.filter((i) => i.bucket === bucket)
              if (items.length === 0) return null
              return (
                <section key={bucket} className="flex flex-col gap-3">
                  <h2 className="text-sm font-semibold text-foreground">
                    {BUCKET_LABELS[bucket]}
                  </h2>
                  <div className="flex flex-col gap-2">
                    {items.map((insight) => (
                      <div
                        key={insight.code}
                        className="flex flex-col gap-1 rounded-xl border border-border p-4"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-foreground">{insight.title}</span>
                          <Badge variant={SEVERITY_VARIANT[insight.severity] ?? "outline"}>
                            {insight.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{insight.body}</p>
                        <p className="text-sm text-foreground">→ {insight.action}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        </>
      ) : null}
    </div>
  )
}

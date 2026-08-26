import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Sparkles } from "lucide-react"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
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
import { BUCKET_ORDER, formatPct, SEVERITY_VARIANT } from "@/lib/advisor"
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
        className={`text-lg font-semibold tabular-nums sm:text-xl ${negative ? "text-destructive" : "text-foreground"}`}
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
  const { t } = useTranslation()
  const update = useUpdateAdvisorSettings()
  const [labor, setLabor] = useState(() => String(initial.monthly_labor_cost / 100))
  const [other, setOther] = useState(() => String(initial.monthly_other_fixed_costs / 100))
  const [target, setTarget] = useState(() => String(initial.target_food_cost_bps / 100))
  const [seats, setSeats] = useState(() => String(initial.seats || ""))
  const [openHours, setOpenHours] = useState(() =>
    initial.daily_open_minutes ? String(initial.daily_open_minutes / 60) : ""
  )
  const [inflation, setInflation] = useState(() =>
    initial.monthly_inflation_bps ? String(initial.monthly_inflation_bps / 100) : ""
  )
  const [vat, setVat] = useState(() =>
    initial.default_vat_bps ? String(initial.default_vat_bps / 100) : ""
  )

  const submit = () => {
    const laborMinor = Math.round(Number(labor) * 100)
    const otherMinor = Math.round(Number(other) * 100)
    const targetBps = Math.round(Number(target) * 100)
    const seatsN = seats.trim() === "" ? 0 : Math.round(Number(seats))
    const openMin = openHours.trim() === "" ? 0 : Math.round(Number(openHours) * 60)
    const inflationBps = inflation.trim() === "" ? 0 : Math.round(Number(inflation) * 100)
    const vatBps = vat.trim() === "" ? 0 : Math.round(Number(vat) * 100)
    if (
      !Number.isFinite(laborMinor) ||
      laborMinor < 0 ||
      !Number.isFinite(otherMinor) ||
      otherMinor < 0 ||
      !Number.isFinite(targetBps) ||
      targetBps < 0 ||
      targetBps > 10000
    ) {
      toast.error(t("advisor.settings.errors.amounts"))
      return
    }
    if (!Number.isFinite(seatsN) || seatsN < 0 || !Number.isFinite(openMin) || openMin < 0 || openMin > 1440) {
      toast.error(t("advisor.settings.errors.seatsHours"))
      return
    }
    if (!Number.isFinite(inflationBps) || inflationBps < 0 || inflationBps > 100000) {
      toast.error(t("advisor.settings.errors.inflation"))
      return
    }
    if (!Number.isFinite(vatBps) || vatBps < 0 || vatBps > 10000) {
      toast.error(t("advisor.settings.errors.vat"))
      return
    }
    update.mutate(
      {
        monthly_labor_cost: laborMinor,
        monthly_other_fixed_costs: otherMinor,
        target_food_cost_bps: targetBps,
        seats: seatsN,
        daily_open_minutes: openMin,
        monthly_inflation_bps: inflationBps,
        default_vat_bps: vatBps,
      },
      {
        onSuccess: () => {
          toast.success(t("advisor.settings.saved"))
          onDone()
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("advisor.settings.saveError"))),
      }
    )
  }

  return (
    <div className="flex flex-col gap-3 px-4 pb-4">
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.labor")}
        <Input
          type="number"
          min={0}
          step="0.01"
          value={labor}
          onChange={(e) => setLabor(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.otherFixed")}
        <Input
          type="number"
          min={0}
          step="0.01"
          value={other}
          onChange={(e) => setOther(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.targetFoodCost")}
        <Input
          type="number"
          min={0}
          max={100}
          step="0.1"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.seats")}
        <Input
          type="number"
          min={0}
          step="1"
          placeholder={t("advisor.settings.seatsPlaceholder")}
          value={seats}
          onChange={(e) => setSeats(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.openHours")}
        <Input
          type="number"
          min={0}
          max={24}
          step="0.5"
          placeholder={t("advisor.settings.openHoursPlaceholder")}
          value={openHours}
          onChange={(e) => setOpenHours(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.inflation")}
        <Input
          type="number"
          min={0}
          step="0.1"
          placeholder={t("advisor.settings.inflationPlaceholder")}
          value={inflation}
          onChange={(e) => setInflation(e.target.value)}
        />
        <span className="text-xs text-muted-foreground">
          {t("advisor.settings.inflationHint")}
        </span>
      </label>
      <label className="flex flex-col gap-1 text-sm">
        {t("advisor.settings.vat")}
        <Input
          type="number"
          min={0}
          max={100}
          step="0.5"
          placeholder={t("advisor.settings.vatPlaceholder")}
          value={vat}
          onChange={(e) => setVat(e.target.value)}
        />
        <span className="text-xs text-muted-foreground">
          {t("advisor.settings.vatHint")}
        </span>
      </label>
      <Button onClick={submit} disabled={update.isPending}>
        {update.isPending ? t("advisor.settings.saving") : t("advisor.settings.save")}
      </Button>
    </div>
  )
}

function SettingsSheet() {
  const { t } = useTranslation()
  const settings = useAdvisorSettings()
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline">{t("advisor.settings.trigger")}</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("advisor.settings.sheetTitle")}</SheetTitle>
          <SheetDescription>{t("advisor.settings.sheetDescription")}</SheetDescription>
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
  const { t } = useTranslation()
  const money = (amount: number) => formatMoney(amount, kpis.currency)
  const lockedHint = kpis.configured ? undefined : t("advisor.kpis.configureCosts")
  const locked = (value: string) => (kpis.configured ? value : "—")
  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      <KpiCard label={t("advisor.kpis.sales")} value={money(kpis.sales_amount)} />
      <KpiCard label={t("advisor.kpis.grossMargin")} value={money(kpis.gross_margin_amount)} />
      <KpiCard
        label={t("advisor.kpis.netMargin")}
        value={locked(money(kpis.net_margin_amount))}
        hint={lockedHint}
        negative={kpis.configured && kpis.net_margin_amount < 0}
      />
      <KpiCard label={t("advisor.kpis.foodCost")} value={formatPct(kpis.food_cost_ratio_bps)} />
      <KpiCard
        label={t("advisor.kpis.primeCost")}
        value={locked(formatPct(kpis.prime_cost_ratio_bps))}
        hint={lockedHint}
      />
      <KpiCard
        label={t("advisor.kpis.breakEven")}
        value={locked(money(kpis.break_even_amount))}
        hint={lockedHint}
      />
    </section>
  )
}

export function AdvisorPage() {
  const { t } = useTranslation()
  const [from, setFrom] = useState("")
  const [to, setTo] = useState("")
  const fromIso = from ? new Date(`${from}T00:00:00`).toISOString() : undefined
  const toIso = to ? new Date(`${to}T23:59:59`).toISOString() : undefined
  const report = useAdvisorReport({ from: fromIso, to: toIso })

  const controls = (
    <div className="flex flex-wrap items-end gap-2">
      <label className="flex flex-col gap-1 text-xs text-muted-foreground">
        {t("advisor.controls.from")}
        <Input
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          className="w-auto"
        />
      </label>
      <label className="flex flex-col gap-1 text-xs text-muted-foreground">
        {t("advisor.controls.to")}
        <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="w-auto" />
      </label>
      <SettingsSheet />
    </div>
  )

  const body = report.isPending ? (
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
                {t(`advisor.bucketLabels.${bucket}`)}
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
  ) : null

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("advisor.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">{t("advisor.subtitle")}</p>
        </div>
        {controls}
      </header>

      {body}
    </div>
  )
}

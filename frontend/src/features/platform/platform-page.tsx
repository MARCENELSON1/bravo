import { useState } from "react"
import { Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { FeatureDTO, PlatformPlanDTO, PlatformPlanInput } from "@/api/types-platform"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useDeletePlan,
  usePlatformFeatures,
  usePlatformPlans,
  useSavePlan,
} from "@/hooks/use-platform"
import { formatMoney } from "@/lib/money"
import { cn } from "@/lib/utils"

const TIERS = ["BASIC", "PRO", "ENTERPRISE"]
const REGIONS = ["AR", "INTL"]
const INTERVALS = ["MONTH", "YEAR"]
const CURRENCY_BY_REGION: Record<string, string> = { AR: "ARS", INTL: "USD" }

const selectCls =
  "rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"

// El form arranca su estado del plan a editar (o vacío). Se remonta por `key`
// cuando cambia el plan editado → sin sincronizar estado con efectos.
function PlanForm({
  plan,
  features,
  onDone,
}: {
  plan: PlatformPlanDTO | null
  features: FeatureDTO[]
  onDone: () => void
}) {
  const save = useSavePlan()
  const [tier, setTier] = useState(plan?.tier ?? "PRO")
  const [region, setRegion] = useState(plan?.region ?? "INTL")
  const [interval, setInterval] = useState(plan?.interval ?? "MONTH")
  const [amount, setAmount] = useState(plan ? String(plan.amount / 100) : "")
  const [active, setActive] = useState(plan?.active ?? true)
  const [selected, setSelected] = useState<Set<string>>(new Set(plan?.features ?? []))

  const currency = CURRENCY_BY_REGION[region] ?? "USD"

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const submit = () => {
    const major = Number.parseFloat(amount)
    if (!Number.isFinite(major) || major < 0) {
      toast.error("Ingresá un precio válido.")
      return
    }
    const body: PlatformPlanInput = {
      id: plan?.id ?? null,
      tier,
      region,
      amount: Math.round(major * 100),
      currency,
      interval,
      features: [...selected],
      active,
    }
    save.mutate(body, {
      onSuccess: () => {
        toast.success(plan ? "Plan actualizado." : "Plan creado.")
        onDone()
      },
      onError: (e) =>
        toast.error(isApiError(e) ? e.message : "No pudimos guardar el plan."),
    })
  }

  return (
    <GlassCard className="flex flex-col gap-4 p-6">
      <h2 className="text-base font-semibold text-foreground">
        {plan ? "Editar plan" : "Nuevo plan"}
      </h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm text-muted-foreground">
          Plan
          <select className={selectCls} value={tier} onChange={(e) => setTier(e.target.value)}>
            {TIERS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted-foreground">
          Región
          <select
            className={selectCls}
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {REGIONS.map((r) => (
              <option key={r} value={r}>
                {r === "AR" ? "Argentina (ARS)" : "Internacional (USD)"}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted-foreground">
          Precio ({currency})
          <Input
            inputMode="decimal"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted-foreground">
          Ciclo
          <select
            className={selectCls}
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
          >
            {INTERVALS.map((i) => (
              <option key={i} value={i}>
                {i === "MONTH" ? "Mensual" : "Anual"}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-foreground">Incluye</p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {features.map((f) => (
            <label key={f.key} className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={selected.has(f.key)}
                onChange={() => toggle(f.key)}
                className="size-4 rounded border-border"
              />
              {f.label}
            </label>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={active}
          onChange={(e) => setActive(e.target.checked)}
          className="size-4 rounded border-border"
        />
        Activo (visible en el pricing)
      </label>

      <div className="flex gap-2">
        <Button onClick={submit} disabled={save.isPending}>
          {save.isPending ? "Guardando…" : plan ? "Guardar cambios" : "Crear plan"}
        </Button>
        {plan ? (
          <Button variant="outline" onClick={onDone}>
            Cancelar
          </Button>
        ) : null}
      </div>
    </GlassCard>
  )
}

export function PlatformPage() {
  const plans = usePlatformPlans()
  const features = usePlatformFeatures()
  const del = useDeletePlan()
  const [editing, setEditing] = useState<PlatformPlanDTO | null>(null)
  // Cambiar de plan editado remonta el form (key) con estado fresco.
  const [formKey, setFormKey] = useState(0)

  const edit = (plan: PlatformPlanDTO | null) => {
    setEditing(plan)
    setFormKey((k) => k + 1)
  }

  const remove = (plan: PlatformPlanDTO) => {
    del.mutate(plan.id, {
      onSuccess: () => toast.success("Plan borrado."),
      onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos borrar el plan."),
    })
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            to="/app"
            className="text-muted-foreground transition hover:text-foreground"
            aria-label="Volver"
          >
            <ArrowLeft className="size-5" />
          </Link>
          <GradientHeading>Plataforma · Planes</GradientHeading>
        </div>
        <Button size="sm" variant="outline" onClick={() => edit(null)}>
          Nuevo plan
        </Button>
      </header>

      <GlassCard className="p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">Catálogo</h2>
        {plans.isPending ? (
          <Spinner />
        ) : (plans.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">
            Todavía no hay planes. Creá el primero con “Nuevo plan”.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b text-xs font-medium text-muted-foreground">
                  <th className="py-1 text-left">Plan</th>
                  <th className="py-1 text-left">Región</th>
                  <th className="py-1 text-right">Precio</th>
                  <th className="py-1 text-left">Ciclo</th>
                  <th className="py-1 text-right">Features</th>
                  <th className="py-1 text-center">Activo</th>
                  <th className="py-1" />
                </tr>
              </thead>
              <tbody>
                {plans.data?.map((p) => (
                  <tr key={p.id} className="border-b border-border/50">
                    <td className="py-2 font-medium text-foreground">{p.tier}</td>
                    <td className="py-2 text-muted-foreground">{p.region}</td>
                    <td className="py-2 text-right tabular-nums text-foreground">
                      {formatMoney(p.amount, p.currency)}
                    </td>
                    <td className="py-2 text-muted-foreground">
                      {p.interval === "MONTH" ? "Mensual" : "Anual"}
                    </td>
                    <td className="py-2 text-right text-muted-foreground">{p.features.length}</td>
                    <td className="py-2 text-center">
                      <span
                        className={cn(
                          "inline-block size-2 rounded-full",
                          p.active ? "bg-emerald-500" : "bg-muted-foreground/40"
                        )}
                      />
                    </td>
                    <td className="py-2 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => edit(p)}
                          className="text-xs font-medium text-foreground underline underline-offset-2"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => remove(p)}
                          disabled={del.isPending}
                          className="text-xs font-medium text-destructive underline underline-offset-2"
                        >
                          Borrar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      <PlanForm
        key={formKey}
        plan={editing}
        features={features.data ?? []}
        onDone={() => edit(null)}
      />
    </div>
  )
}

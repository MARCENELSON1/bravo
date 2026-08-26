import { Link } from "react-router-dom"
import { ArrowLeft, Check } from "lucide-react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { BillingPlanDTO } from "@/api/types-billing"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import {
  useBillingPlans,
  useCancelSubscription,
  useCheckout,
  useSubscription,
} from "@/hooks/use-billing"
import { useFiscalSettings } from "@/hooks/use-tenant"
import { formatMoney } from "@/lib/money"

const STATUS_LABEL: Record<string, string> = {
  TRIALING: "En prueba",
  ACTIVE: "Activa",
  PAST_DUE: "Pago pendiente",
  INCOMPLETE: "Incompleta",
  CANCELED: "Cancelada",
}

function PlanCard({ plan }: { plan: BillingPlanDTO }) {
  const checkout = useCheckout()

  const subscribe = () => {
    checkout.mutate(plan.id, {
      onSuccess: (r) => {
        window.location.href = r.url // al checkout hosteado (Stripe / MercadoPago)
      },
      onError: (e) =>
        toast.error(isApiError(e) ? e.message : "No pudimos iniciar el pago."),
    })
  }

  return (
    <GlassCard className="flex flex-col gap-4 p-6">
      <div>
        <h3 className="text-lg font-semibold text-foreground">{plan.tier}</h3>
        <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">
          {formatMoney(plan.amount, plan.currency)}
          <span className="text-sm font-normal text-muted-foreground">
            {" "}
            / {plan.interval === "MONTH" ? "mes" : "año"}
          </span>
        </p>
      </div>
      {plan.features.length > 0 ? (
        <ul className="flex flex-col gap-1.5">
          {plan.features.map((f) => (
            <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="size-4 text-emerald-500" />
              {f}
            </li>
          ))}
        </ul>
      ) : null}
      <Button onClick={subscribe} disabled={checkout.isPending} className="mt-auto">
        {checkout.isPending ? "Redirigiendo…" : "Suscribirme"}
      </Button>
    </GlassCard>
  )
}

export function SubscriptionPage() {
  const fiscal = useFiscalSettings()
  const region = fiscal.data ? (fiscal.data.country === "AR" ? "AR" : "INTL") : null
  const subscription = useSubscription()
  const plans = useBillingPlans(region)
  const cancel = useCancelSubscription()

  const doCancel = () => {
    if (!window.confirm("¿Seguro que querés cancelar la suscripción?")) return
    cancel.mutate(undefined, {
      onSuccess: () => toast.success("Suscripción cancelada."),
      onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos cancelar."),
    })
  }

  const sub = subscription.data
  const active = Boolean(sub?.grants_access)

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex items-center gap-3">
        <Link
          to="/app"
          className="text-muted-foreground transition hover:text-foreground"
          aria-label="Volver"
        >
          <ArrowLeft className="size-5" />
        </Link>
        <GradientHeading>Suscripción</GradientHeading>
      </header>

      {fiscal.isPending || subscription.isPending ? (
        <Spinner />
      ) : active && sub ? (
        <GlassCard className="flex flex-col gap-3 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">Plan activo</h2>
              <p className="text-sm text-muted-foreground">
                Estado: {STATUS_LABEL[sub.status] ?? sub.status}
                {sub.current_period_end
                  ? ` · renueva el ${new Date(sub.current_period_end).toLocaleDateString()}`
                  : ""}
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-sm font-medium text-emerald-600 dark:text-emerald-400">
              <Check className="size-4" /> Activa
            </span>
          </div>
          <div>
            <Button variant="outline" onClick={doCancel} disabled={cancel.isPending}>
              {cancel.isPending ? "Cancelando…" : "Cancelar suscripción"}
            </Button>
          </div>
        </GlassCard>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            Elegí un plan para activar tu suscripción. El pago es seguro y se procesa
            en {region === "AR" ? "MercadoPago" : "Stripe"}.
          </p>
          {plans.isPending ? (
            <Spinner />
          ) : (plans.data?.length ?? 0) === 0 ? (
            <GlassCard className="p-6">
              <p className="text-sm text-muted-foreground">
                Todavía no hay planes disponibles para tu región.
              </p>
            </GlassCard>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {plans.data?.map((p) => (
                <PlanCard key={p.id} plan={p} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

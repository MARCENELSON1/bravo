import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { ArrowLeft, Check } from "lucide-react"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import { dateLocale } from "@/lib/format"
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

function PlanCard({ plan }: { plan: BillingPlanDTO }) {
  const { t } = useTranslation()
  const checkout = useCheckout()

  const subscribe = () => {
    checkout.mutate(plan.id, {
      onSuccess: (r) => {
        window.location.href = r.url // al checkout hosteado (Stripe / MercadoPago)
      },
      onError: (e) =>
        toast.error(apiErrorText(e, t, t("billing.checkoutError"))),
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
            / {plan.interval === "MONTH" ? t("billing.interval.month") : t("billing.interval.year")}
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
        {checkout.isPending ? t("billing.redirecting") : t("billing.subscribe")}
      </Button>
    </GlassCard>
  )
}

export function SubscriptionPage() {
  const { t } = useTranslation()
  const fiscal = useFiscalSettings()
  const region = fiscal.data ? (fiscal.data.country === "AR" ? "AR" : "INTL") : null
  const subscription = useSubscription()
  const plans = useBillingPlans(region)
  const cancel = useCancelSubscription()

  const doCancel = () => {
    if (!window.confirm(t("billing.cancelConfirm"))) return
    cancel.mutate(undefined, {
      onSuccess: () => toast.success(t("billing.cancelSuccess")),
      onError: (e) => toast.error(apiErrorText(e, t, t("billing.cancelError"))),
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
          aria-label={t("billing.back")}
        >
          <ArrowLeft className="size-5" />
        </Link>
        <GradientHeading>{t("billing.title")}</GradientHeading>
      </header>

      {fiscal.isPending || subscription.isPending ? (
        <Spinner />
      ) : active && sub ? (
        <GlassCard className="flex flex-col gap-3 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-foreground">{t("billing.activePlan")}</h2>
              <p className="text-sm text-muted-foreground">
                {t("billing.statusLine", {
                  value: t(`billing.statusLabels.${sub.status}`, { defaultValue: sub.status }),
                })}
                {sub.current_period_end
                  ? t("billing.renewsOn", {
                      date: new Date(sub.current_period_end).toLocaleDateString(dateLocale()),
                    })
                  : ""}
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-sm font-medium text-emerald-600 dark:text-emerald-400">
              <Check className="size-4" /> {t("billing.statusLabels.ACTIVE")}
            </span>
          </div>
          <div>
            <Button variant="outline" onClick={doCancel} disabled={cancel.isPending}>
              {cancel.isPending ? t("billing.canceling") : t("billing.cancelSubscription")}
            </Button>
          </div>
        </GlassCard>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            {t("billing.chooseIntro", { gateway: region === "AR" ? "MercadoPago" : "Stripe" })}
          </p>
          {plans.isPending ? (
            <Spinner />
          ) : (plans.data?.length ?? 0) === 0 ? (
            <GlassCard className="p-6">
              <p className="text-sm text-muted-foreground">
                {t("billing.noPlans")}
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

import { useState } from "react"
import { Check, X } from "lucide-react"

import type { BillingPeriod, Plan } from "@/domain/entities/plan"
import { priceFor } from "@/domain/entities/plan"
import { formatMoney } from "@/domain/value-objects/money"
import type { Locale } from "@/domain/value-objects/region"
import { useAuthLinks } from "@/presentation/hooks/use-auth-links"
import { usePricingPlans } from "@/presentation/hooks/use-pricing-plans"
import { useContainer } from "@/presentation/providers/container-provider"
import { buttonVariants } from "@/presentation/components/ui/button"
import { Reveal } from "@/presentation/components/ui/reveal"
import { SectionHeading } from "@/presentation/components/ui/section-heading"
import { cn } from "@/presentation/lib/cn"

const COPY = {
  "es-AR": {
    eyebrow: "Planes",
    heading: "Precios simples, sin sorpresas",
    sub: "Todos los planes arrancan con 30 días de prueba — con tarjeta, se cobra recién al terminar. Cancelás cuando quieras.",
    monthly: "Mensual",
    yearly: "Anual",
    yearlyHint: "−2 meses",
    perMonth: "/mes",
    forever: "Para siempre",
    perLocationYearly: "por local · facturado anual",
    perLocationMonthly: "por local · facturado mensual",
  },
  "en-US": {
    eyebrow: "Plans",
    heading: "Simple pricing, no surprises",
    sub: "Every plan starts with a 30-day free trial — card required, we only charge when it ends. Cancel anytime.",
    monthly: "Monthly",
    yearly: "Yearly",
    yearlyHint: "2 months free",
    perMonth: "/mo",
    forever: "Forever",
    perLocationYearly: "per location · billed yearly",
    perLocationMonthly: "per location · billed monthly",
  },
} as const

// El plan "hablá con ventas" enruta al formulario en vez de al signup. Se detecta por
// la etiqueta del CTA, en los dos idiomas (ventas / sales).
function isSalesCta(label: string): boolean {
  const l = label.toLowerCase()
  return l.includes("ventas") || l.includes("sales")
}

export function Pricing() {
  const { plans, loading } = usePricingPlans()
  const locale = useContainer().locale
  const t = COPY[locale]
  const [period, setPeriod] = useState<BillingPeriod>("monthly")

  return (
    <section id="planes" className="border-t border-border/60">
      <div className="mx-auto max-w-6xl px-5 py-28 md:py-36">
        <SectionHeading eyebrow={t.eyebrow} heading={t.heading} sub={t.sub} />

        <div className="mt-10 flex justify-center">
          <PeriodToggle period={period} onChange={setPeriod} locale={locale} />
        </div>

        <div className="mt-14 grid items-stretch gap-6 lg:grid-cols-3">
          {loading
            ? Array.from({ length: 3 }).map((_, i) => <PlanSkeleton key={i} />)
            : plans.map((plan, i) => (
                <Reveal key={plan.id} style={{ transitionDelay: `${i * 80}ms` }} className="h-full">
                  <PlanCard plan={plan} period={period} locale={locale} />
                </Reveal>
              ))}
        </div>
      </div>
    </section>
  )
}

function PeriodToggle({
  period,
  onChange,
  locale,
}: {
  period: BillingPeriod
  onChange: (p: BillingPeriod) => void
  locale: Locale
}) {
  const t = COPY[locale]
  return (
    <div className="inline-flex items-center rounded-full border border-border bg-card p-1">
      {(["monthly", "yearly"] as const).map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          className={cn(
            "rounded-full px-4 py-1.5 text-sm font-medium transition",
            period === value
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {value === "monthly" ? t.monthly : t.yearly}
          {value === "yearly" ? (
            <span className={cn("ml-1.5 text-xs", period === value ? "opacity-80" : "text-primary")}>
              {t.yearlyHint}
            </span>
          ) : null}
        </button>
      ))}
    </div>
  )
}

function PlanCard({ plan, period, locale }: { plan: Plan; period: BillingPeriod; locale: Locale }) {
  const { register } = useAuthLinks()
  const t = COPY[locale]
  const price = priceFor(plan, period)
  const isSales = isSalesCta(plan.ctaLabel)
  const href = isSales ? "#contacto" : register
  const isFree = price.amount === 0

  return (
    <div
      className={cn(
        "flex h-full flex-col rounded-2xl border p-7",
        plan.featured ? "border-primary/50" : "border-border/70",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">{plan.name}</h3>
        {plan.badge ? (
          <span className="rounded-full bg-primary px-2.5 py-0.5 text-xs font-medium text-primary-foreground">
            {plan.badge}
          </span>
        ) : null}
      </div>
      <p className="mt-1 text-sm text-muted-foreground">{plan.tagline}</p>

      <div className="mt-5 flex items-baseline gap-1">
        <span className="font-display text-4xl font-bold tracking-tight tabular-nums">
          {formatMoney(price, locale)}
        </span>
        {!isFree ? <span className="text-sm text-muted-foreground">{t.perMonth}</span> : null}
      </div>
      <p className="mt-1 h-5 text-xs text-muted-foreground">
        {isFree
          ? t.forever
          : period === "yearly"
            ? t.perLocationYearly
            : t.perLocationMonthly}
      </p>

      <a
        href={href}
        className={cn(
          buttonVariants({ variant: plan.featured ? "primary" : "outline", size: "md" }),
          "mt-6 w-full",
        )}
      >
        {plan.ctaLabel}
      </a>

      <ul className="mt-6 flex flex-col gap-3 border-t border-border pt-6">
        {plan.features.map((feature) => (
          <li
            key={feature.label}
            className={cn(
              "flex items-start gap-2.5 text-sm",
              feature.included ? "text-foreground" : "text-muted-foreground/70",
            )}
          >
            {feature.included ? (
              <Check className="mt-0.5 size-4 shrink-0 text-primary" />
            ) : (
              <X className="mt-0.5 size-4 shrink-0 text-muted-foreground/50" />
            )}
            <span className={cn(!feature.included && "line-through")}>{feature.label}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function PlanSkeleton() {
  return (
    <div className="h-[520px] animate-pulse rounded-2xl border border-border bg-card p-6">
      <div className="h-5 w-24 rounded bg-muted" />
      <div className="mt-4 h-10 w-32 rounded bg-muted" />
      <div className="mt-6 h-11 w-full rounded-xl bg-muted" />
      <div className="mt-6 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 w-full rounded bg-muted" />
        ))}
      </div>
    </div>
  )
}

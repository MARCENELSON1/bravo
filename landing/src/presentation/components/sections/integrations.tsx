import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { Reveal } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const COPY = {
  "es-AR": {
    eyebrow: "Integraciones",
    heading: "Se conecta con lo que ya usás",
    sub: "Cobros, facturación e impresión listos para funcionar. Sin integraciones eternas.",
  },
  "en-US": {
    eyebrow: "Integrations",
    heading: "Works with what you already use",
    sub: "Payments, tax, and printing ready to go. No endless integrations.",
  },
} as const

export function Integrations() {
  const { integrations } = useLandingContent()
  const t = COPY[useContainer().locale]

  return (
    <section className="mx-auto max-w-6xl px-5 py-20 md:py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-primary">
          {t.eyebrow}
        </p>
        <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-balance sm:text-4xl">
          {t.heading}
        </h2>
        <p className="mt-4 text-lg text-muted-foreground">{t.sub}</p>
      </Reveal>

      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {integrations.map((integration, i) => (
          <Reveal
            key={integration.id}
            style={{ transitionDelay: `${(i % 3) * 70}ms` }}
            className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5"
          >
            <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary/12 font-display text-lg font-bold text-primary">
              {integration.name.charAt(0)}
            </span>
            <div>
              <p className="font-semibold">{integration.name}</p>
              <p className="text-sm text-muted-foreground">{integration.description}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  )
}

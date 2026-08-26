import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { FEATURE_ICONS } from "@/presentation/lib/feature-icons"
import { Reveal } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const COPY = {
  "es-AR": {
    eyebrow: "Producto",
    heading: "Una sola herramienta para operar todo el local",
    sub: "Desde que el mozo toma el pedido hasta que cobrás y facturás. Todo conectado, en tiempo real.",
  },
  "en-US": {
    eyebrow: "Product",
    heading: "One tool to run the whole restaurant",
    sub: "From the moment your server takes the order to the moment you charge and file tax. All connected, in real time.",
  },
} as const

export function Features() {
  const { features } = useLandingContent()
  const t = COPY[useContainer().locale]

  return (
    <section id="producto" className="mx-auto max-w-6xl px-5 py-20 md:py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-wider text-primary">{t.eyebrow}</p>
        <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-balance sm:text-4xl">
          {t.heading}
        </h2>
        <p className="mt-4 text-lg text-muted-foreground">{t.sub}</p>
      </Reveal>

      <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, i) => {
          const Icon = FEATURE_ICONS[feature.icon]
          return (
            <Reveal
              key={feature.id}
              style={{ transitionDelay: `${(i % 3) * 80}ms` }}
              className="group h-full rounded-2xl border border-border bg-card p-6 transition hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5"
            >
              <span className="flex size-11 items-center justify-center rounded-xl bg-primary/12 text-primary transition group-hover:bg-primary group-hover:text-primary-foreground">
                <Icon className="size-5" />
              </span>
              <h3 className="mt-4 text-lg font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {feature.description}
              </p>
            </Reveal>
          )
        })}
      </div>
    </section>
  )
}

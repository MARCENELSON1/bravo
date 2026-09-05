import type { Feature, FeatureGroup } from "@/domain/entities/feature"
import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { FEATURE_ICONS } from "@/presentation/lib/feature-icons"
import { SectionHeading } from "@/presentation/components/ui/section-heading"
import { Reveal, Stagger } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const COPY = {
  "es-AR": {
    eyebrow: "Wellnod",
    heading: "Una sola herramienta para operar todo el local",
    sub: "Nada de apps sueltas ni de exportar planillas de un lado a otro. Comandas, cocina, caja, facturación, carta, stock, reservas, clientes, fichaje, finanzas, reportes y tu copiloto trabajan con los mismos datos.",
    groups: {
      operation: "El turno",
      management: "El negocio",
      intelligence: "Las decisiones",
    },
  },
  "en-US": {
    eyebrow: "Wellnod",
    heading: "One tool to run the whole restaurant",
    sub: "No more scattered apps or exporting spreadsheets back and forth. Orders, kitchen, register, tax, menu, inventory, reservations, guests, time tracking, finance, reports, and your copilot all run on the same data.",
    groups: {
      operation: "The shift",
      management: "The business",
      intelligence: "The decisions",
    },
  },
} as const

// De lo inmediato a lo estratégico: así es como se usa el software durante el día.
const ORDER: readonly FeatureGroup[] = ["operation", "management", "intelligence"]

// Las doce áreas, en tres bloques. Doce ítems en una grilla plana son un muro sin
// jerarquía; agrupados se recorren de lo que pasa ahora a lo que se decide después.
// Los bloques son 3 / 6 / 3, así ninguna fila queda coja.
export function Features() {
  const { features } = useLandingContent()
  const t = COPY[useContainer().locale]

  return (
    <section id="producto" className="mx-auto max-w-5xl px-5 py-28 md:py-36">
      <SectionHeading eyebrow={t.eyebrow} heading={t.heading} sub={t.sub} />

      <div className="mt-20 flex flex-col gap-16">
        {ORDER.map((group) => {
          const items = features.filter((feature) => feature.group === group)
          if (items.length === 0) return null
          return (
            <div key={group}>
              <Reveal anim="fade">
                <h3 className="border-b border-border/70 pb-3 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {t.groups[group]}
                </h3>
              </Reveal>
              <Stagger className="mt-8 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((feature) => (
                  <FeatureItem key={feature.id} feature={feature} />
                ))}
              </Stagger>
            </div>
          )
        })}
      </div>
    </section>
  )
}

// El ícono va en la misma línea que el título. Arriba quedaba flotando solo y
// abría un hueco que hacía ver la grilla despareja.
function FeatureItem({ feature }: { feature: Feature }) {
  const Icon = FEATURE_ICONS[feature.icon]
  return (
    <article>
      <div className="flex items-center gap-2.5">
        <Icon className="size-[18px] shrink-0 text-primary" />
        <h4 className="font-semibold tracking-tight">{feature.title}</h4>
      </div>
      <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
        {feature.description}
      </p>
    </article>
  )
}

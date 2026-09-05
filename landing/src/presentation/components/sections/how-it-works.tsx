import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { SectionHeading } from "@/presentation/components/ui/section-heading"
import { Stagger } from "@/presentation/components/ui/reveal"
import { useContainer } from "@/presentation/providers/container-provider"

const COPY = {
  "es-AR": { eyebrow: "Cómo funciona", heading: "De la mesa a la decisión, en cinco pasos" },
  "en-US": { eyebrow: "How it works", heading: "From table to decision, in five steps" },
} as const

// Cinco pasos numerados, sin línea conectora ni nodos. El número ya dice que es
// una secuencia; dibujarle un riel encima era decir lo mismo dos veces. Entran
// en orden, que es la única animación con significado acá.
export function HowItWorks() {
  const { steps } = useLandingContent()
  const t = COPY[useContainer().locale]

  return (
    <section id="como-funciona" className="mx-auto max-w-6xl px-5 py-28 md:py-36">
      <SectionHeading eyebrow={t.eyebrow} heading={t.heading} />

      <Stagger as="ol" className="mt-20 grid gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((step, i) => (
          <li key={step.id}>
            <span className="font-display text-sm font-bold tabular-nums text-primary">
              {String(i + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-4 font-semibold tracking-tight">{step.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {step.description}
            </p>
          </li>
        ))}
      </Stagger>
    </section>
  )
}

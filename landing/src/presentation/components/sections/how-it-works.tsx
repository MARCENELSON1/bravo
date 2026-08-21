import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { Reveal } from "@/presentation/components/ui/reveal"

export function HowItWorks() {
  const { steps } = useLandingContent()

  return (
    <section id="como-funciona" className="border-t border-border bg-muted/30">
      <div className="mx-auto max-w-6xl px-5 py-20 md:py-24">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">
            Cómo funciona
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-balance sm:text-4xl">
            De la mesa al reporte, en cuatro pasos
          </h2>
        </Reveal>

        <ol className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <Reveal key={step.id} style={{ transitionDelay: `${i * 80}ms` }}>
              <li className="flex h-full flex-col rounded-2xl border border-border bg-card p-6">
                <span className="font-display text-3xl font-bold tabular-nums text-primary/25">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-3 font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {step.description}
                </p>
              </li>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  )
}

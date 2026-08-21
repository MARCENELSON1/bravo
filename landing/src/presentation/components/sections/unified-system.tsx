import { Check } from "lucide-react"

import { useLandingContent } from "@/presentation/hooks/use-landing-content"
import { WellnodMark } from "@/presentation/components/brand/wellnod-mark"
import { Reveal } from "@/presentation/components/ui/reveal"
import { FEATURE_ICONS } from "@/presentation/lib/feature-icons"

const POINTS = ["Un solo login para todo el equipo", "Un solo panel, en tiempo real", "Los mismos datos en cada módulo"]

// Sección "plataforma unificada": el mensaje de que todo vive en un solo sistema.
// Reutiliza los módulos que expone el ContentRepository (no los duplica).
export function UnifiedSystem() {
  const { features } = useLandingContent()

  return (
    <section className="border-y border-border bg-muted/30">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-20 md:py-24 lg:grid-cols-2">
        <Reveal>
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">
            Plataforma unificada
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold leading-tight tracking-tight text-balance sm:text-4xl">
            El salón y la cocina, por fin en un solo sistema
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Nada de apps sueltas ni de exportar planillas de un lado a otro. Comandas, cocina,
            caja, facturación, fichaje y tu copiloto trabajan con los mismos datos.
          </p>
          <ul className="mt-6 flex flex-col gap-3">
            {POINTS.map((point) => (
              <li key={point} className="flex items-center gap-3 text-sm">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/12 text-primary">
                  <Check className="size-3.5" />
                </span>
                {point}
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal style={{ transitionDelay: "120ms" }}>
          <div className="rounded-2xl border border-border bg-card p-5 shadow-xl shadow-primary/5">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <span className="inline-flex items-center gap-2">
                <WellnodMark className="h-6 w-auto text-primary" />
                <span className="font-display font-semibold">Wellnod</span>
              </span>
              <span className="rounded-full bg-primary/12 px-2.5 py-1 text-xs font-medium text-primary">
                Un solo panel
              </span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {features.map((feature) => {
                const Icon = FEATURE_ICONS[feature.icon]
                return (
                  <div
                    key={feature.id}
                    className="flex items-center gap-2.5 rounded-xl bg-muted px-3 py-3 text-sm"
                  >
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/12 text-primary">
                      <Icon className="size-4" />
                    </span>
                    <span className="font-medium leading-tight">{feature.title}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

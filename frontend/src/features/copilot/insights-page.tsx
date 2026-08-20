import { AdvisorPage } from "@/features/advisor/advisor-page"
import { CopilotPage } from "@/features/copilot/copilot-page"

// "IA Insights" (sidebar) combina, sin burbujas, el Copiloto (preguntas en lenguaje
// natural) y el Diagnóstico (KPIs + recomendaciones, lo que antes era "Asesor"),
// ambos alineados al mismo ancho.
export function InsightsPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-8">
      <CopilotPage embedded />
      <AdvisorPage embedded />
    </div>
  )
}

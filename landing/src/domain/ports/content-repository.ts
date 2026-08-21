import type { Faq } from "@/domain/entities/faq"
import type { Feature } from "@/domain/entities/feature"
import type { Integration } from "@/domain/entities/integration"
import type { Step } from "@/domain/entities/step"

// Puerto (driven port): contenido editorial de la landing (features, pasos,
// integraciones y FAQs). Separado de PlanRepository (ISP): quien solo necesita
// contenido no arrastra la lógica de planes.
export interface ContentRepository {
  getFeatures(): Promise<readonly Feature[]>
  getSteps(): Promise<readonly Step[]>
  getIntegrations(): Promise<readonly Integration[]>
  getFaqs(): Promise<readonly Faq[]>
}

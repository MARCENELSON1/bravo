import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"

// Puerto (driven port): contenido editorial de la landing (features y pasos).
// Separado de PlanRepository (ISP): quien solo necesita
// contenido no arrastra la lógica de planes.
export interface ContentRepository {
  getFeatures(): Promise<readonly Feature[]>
  getSteps(): Promise<readonly Step[]>
}

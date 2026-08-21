import type { Plan } from "@/domain/entities/plan"

// Puerto (driven port): fuente de los planes de precios. La app depende de esta
// abstracción; el adapter concreto (estático hoy, HTTP mañana) vive en infrastructure.
export interface PlanRepository {
  getAll(): Promise<readonly Plan[]>
}

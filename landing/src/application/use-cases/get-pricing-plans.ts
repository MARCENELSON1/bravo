import type { Plan } from "@/domain/entities/plan"
import type { PlanRepository } from "@/domain/ports/plan-repository"

// Caso de uso: obtener los planes de precios. Depende del puerto (DIP), no del
// adapter. Responsabilidad única (SRP): orquestar la lectura de planes.
export class GetPricingPlans {
  constructor(private readonly plans: PlanRepository) {}

  execute(): Promise<readonly Plan[]> {
    return this.plans.getAll()
  }
}

import type { Plan } from "@/domain/entities/plan"
import type { PlanRepository } from "@/domain/ports/plan-repository"
import { money, type Currency } from "@/domain/value-objects/money"
import type { Region } from "@/domain/value-objects/region"
import { presentationFor } from "@/infrastructure/repositories/plan-presentation"

// Forma del DTO público del backend (GET /public/plans). El amount viene en unidades
// MENORES (centavos), como en todo el billing.
interface PublicPlanDTO {
  readonly tier: string
  readonly amount: number
  readonly currency: Currency
  readonly interval: string
}

// Descuento anual: ~2 meses gratis (pagás 10, usás 12) — igual que el repo estático.
const yearly = (monthly: number) => Math.round((monthly * 10) / 12)

// Adapter HTTP del puerto PlanRepository: el PRECIO sale del catálogo del backend
// (editable desde el panel /platform → una sola fuente de verdad, nunca hardcodeado),
// y se mergea con la PRESENTACIÓN de marketing por tier (copy de vidriera). Cumple el
// mismo puerto que StaticPlanRepository, así que casos de uso y UI no cambian (OCP).
export class HttpPlanRepository implements PlanRepository {
  constructor(
    private readonly apiUrl: string,
    private readonly region: Region,
  ) {}

  async getAll(): Promise<readonly Plan[]> {
    const res = await fetch(`${this.apiUrl}/public/plans?region=${this.region}`)
    if (!res.ok) {
      throw new Error(`plans_unavailable_${res.status}`)
    }
    const dtos = (await res.json()) as PublicPlanDTO[]
    return dtos.flatMap((dto) => {
      const pres = presentationFor(this.region, dto.tier)
      // Un tier del backend sin presentación en la landing se omite (no rompe la
      // pantalla): la vidriera solo muestra los planes que sabe presentar.
      if (!pres) return []
      const monthly = Math.round(dto.amount / 100) // centavos → unidades mayores
      const plan: Plan = {
        id: `${this.region}-${dto.tier}`.toLowerCase(),
        name: pres.name,
        tagline: pres.tagline,
        monthlyPrice: money(monthly, dto.currency),
        yearlyPrice: money(yearly(monthly), dto.currency),
        featured: pres.featured,
        badge: pres.badge,
        ctaLabel: pres.ctaLabel,
        features: pres.features,
      }
      return [plan]
    })
  }
}

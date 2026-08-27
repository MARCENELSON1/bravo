import type { Plan } from "@/domain/entities/plan"
import type { PlanRepository } from "@/domain/ports/plan-repository"
import { money } from "@/domain/value-objects/money"

// Descuento anual: ~2 meses gratis (pagás 10, usás 12).
const YEARLY = (monthly: number) => money(Math.round((monthly * 10) / 12))

// Adapter estático (in-memory). Implementa el puerto PlanRepository con los planes
// del producto. Para conectar a la API real, se crea otro adapter (HTTP) que cumpla
// el mismo puerto — sin tocar casos de uso ni UI (OCP).
//
// 👉 Editá acá los precios/límites de tus planes.
const PLANS: readonly Plan[] = [
  {
    id: "emprende",
    name: "Emprendé",
    tagline: "Para arrancar y digitalizar tu local.",
    monthlyPrice: money(0),
    yearlyPrice: money(0),
    featured: false,
    ctaLabel: "Empezá gratis",
    features: [
      { label: "1 local", included: true },
      { label: "Comandas digitales (mozo → cocina)", included: true },
      { label: "Cobros y facturación ARCA", included: true },
      { label: "Hasta 3 usuarios", included: true },
      { label: "Copiloto IA", included: false },
      { label: "Reportes avanzados", included: false },
    ],
  },
  {
    id: "profesional",
    name: "Profesional",
    tagline: "El local que quiere crecer con datos.",
    monthlyPrice: money(29900),
    yearlyPrice: YEARLY(29900),
    featured: true,
    badge: "Más elegido",
    ctaLabel: "Empezá gratis",
    features: [
      { label: "1 local", included: true },
      { label: "Todo lo de Emprendé", included: true },
      { label: "Copiloto IA en español", included: true },
      { label: "KDS de cocina y barra", included: true },
      { label: "Fichaje de empleados", included: true },
      { label: "Reportes en tiempo real", included: true },
      { label: "Usuarios ilimitados", included: true },
    ],
  },
  {
    id: "multi-local",
    name: "Multi-local",
    tagline: "Para cadenas y varios puntos de venta.",
    monthlyPrice: money(59900),
    yearlyPrice: YEARLY(59900),
    featured: false,
    ctaLabel: "Hablá con ventas",
    features: [
      { label: "Locales ilimitados", included: true },
      { label: "Todo lo de Profesional", included: true },
      { label: "Panel consolidado multi-local", included: true },
      { label: "Roles y permisos avanzados", included: true },
      { label: "Integraciones y API", included: true },
      { label: "Soporte prioritario", included: true },
    ],
  },
]

export class StaticPlanRepository implements PlanRepository {
  async getAll(): Promise<readonly Plan[]> {
    return PLANS
  }
}

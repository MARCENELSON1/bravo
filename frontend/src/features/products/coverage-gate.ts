// Fase 6: el gate de cobertura del hero "Tu carta". Si la cobertura del tenant no
// llega al umbral (COVERAGE_GATE_BPS, definido en el dominio y expuesto como
// `coverage_ok`), el hero NO muestra conclusiones de plata — las reemplaza por
// "te faltan N platos con costo confirmado". Ethos: nunca mostrar un número
// inflado como si fuera sólido.
//
// Sin report (aún cargando el food cost) → `open: true` → paridad: el hero se
// comporta como hoy y no parpadea mientras `useFoodCost` resuelve.

import type { FoodCostReportDTO } from "@/api/types-inventory"

export interface CoverageGate {
  open: boolean // ¿mostrar conclusiones de plata? (cobertura ≥ umbral)
  missing: number // platos con costo estimado que faltan confirmar
  confirmed: number // platos con costo confirmado
  total: number // platos con receta
}

export function coverageGate(report?: FoodCostReportDTO): CoverageGate {
  const confirmed = report?.confirmed_count ?? 0
  const total = report?.total_count ?? 0
  return {
    // El backend decide el umbral (Regla 6). Sin report → abierto (paridad).
    open: report?.coverage_ok ?? true,
    missing: Math.max(0, total - confirmed),
    confirmed,
    total,
  }
}

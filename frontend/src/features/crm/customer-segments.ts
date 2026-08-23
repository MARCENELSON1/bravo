import type { CustomerStatsRowDTO } from "@/api/customers-api"

// Segmenta clientes a partir de sus stats de compra (visitas, gasto, primera/
// última visita). Determinista y honesto: un cliente sin compras atribuidas cae
// en "sin_compras" (no se lo fuerza a un segmento), y el gasto se usa en absoluto
// (rank), nunca como % del total. Puro → testeable, sin llamadas.

export type CustomerSegment =
  | "nuevo"
  | "recurrente"
  | "vip"
  | "en_riesgo"
  | "ocasional"
  | "sin_compras"

export interface SegmentedCustomer extends CustomerStatsRowDTO {
  segment: CustomerSegment
  daysSinceLast: number | null
}

const DAY = 86_400_000
// Un cliente con ≥2 visitas que no viene hace más de esto → en riesgo.
const AT_RISK_DAYS = 45
// Primera visita dentro de esto (y pocas visitas) → nuevo.
const NEW_DAYS = 30
// ≥ esto → recurrente.
const RECURRENT_VISITS = 3

function daysSince(iso: string | null, nowMs: number): number | null {
  if (!iso) return null
  const t = Date.parse(iso)
  if (Number.isNaN(t)) return null
  return Math.floor((nowMs - t) / DAY)
}

// Mínimo de compradores para que el tier VIP tenga sentido (mínimo estadístico:
// con pocos, "top 20%" es ruido y todos saldrían VIP).
const VIP_MIN_COHORT = 5

// Umbral de gasto VIP: el corte del ~top 20% por gasto entre los que compraron
// (rank, no %). Infinity si el cohorte es chico → nadie es VIP.
function vipThreshold(rows: CustomerStatsRowDTO[]): number {
  const spends = rows
    .filter((r) => r.visits > 0)
    .map((r) => r.total_spent)
    .sort((a, b) => b - a)
  if (spends.length < VIP_MIN_COHORT) return Number.POSITIVE_INFINITY
  return spends[Math.floor(spends.length * 0.2)] ?? spends[spends.length - 1]
}

export function classifyCustomers(
  rows: CustomerStatsRowDTO[],
  nowMs: number
): SegmentedCustomer[] {
  const vipCut = vipThreshold(rows)
  return rows.map((r) => {
    const daysSinceLast = daysSince(r.last_visit_at, nowMs)
    const daysSinceFirst = daysSince(r.first_visit_at, nowMs)
    let segment: CustomerSegment
    if (r.visits === 0) {
      segment = "sin_compras"
    } else if (r.visits >= 2 && daysSinceLast !== null && daysSinceLast > AT_RISK_DAYS) {
      segment = "en_riesgo" // venía y dejó de venir
    } else if (r.visits >= 2 && r.total_spent >= vipCut) {
      segment = "vip"
    } else if (r.visits <= 2 && daysSinceFirst !== null && daysSinceFirst <= NEW_DAYS) {
      segment = "nuevo"
    } else if (r.visits >= RECURRENT_VISITS) {
      segment = "recurrente"
    } else {
      segment = "ocasional"
    }
    return { ...r, segment, daysSinceLast }
  })
}

export interface Coverage {
  withPurchases: number
  total: number
}

// Cobertura: cuántos clientes tienen al menos una compra atribuida (para mostrar
// junto a los segmentos y no inflar — "segmentamos N de M").
export function coverage(rows: CustomerStatsRowDTO[]): Coverage {
  return {
    withPurchases: rows.filter((r) => r.visits > 0).length,
    total: rows.length,
  }
}

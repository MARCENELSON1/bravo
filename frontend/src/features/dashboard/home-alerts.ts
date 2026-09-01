// "Requiere tu atención": junta en una sola franja lo accionable de HOY, a partir
// de datos que ya existen (mesas / caja / stock / clientes). Puro y determinista:
// solo entra lo que realmente exige acción (count > 0); nada de ruido ni relleno.
//
// Contrato i18n: no arma texto. Cada alerta devuelve `labelKey` (clave i18next) y,
// en las que pluralizan, `count`. El componente resuelve el label con `t()`.

// Escala de urgencia, de menor a mayor:
//   good      verde   — las cosas están bien
//   normal    gris    — algo para revisar, sin urgencia
//   attention ámbar   — algo para revisar con urgencia
//   critical  rojo    — algo peligroso, hay que cambiarlo ya
export type AlertTone = "good" | "normal" | "attention" | "critical"

export interface HomeAlert {
  key: string
  labelKey: string // clave i18next del texto de la alerta
  count?: number // para las alertas que pluralizan (la de caja no lleva)
  to: string // adónde te lleva a resolverlo
  tone: AlertTone
}

export interface AlertCounts {
  toServe: number // mesas para servir (comida lista esperando)
  toCharge: number // mesas para cobrar (servidas / pidieron la cuenta)
  occupied: number // mesas ocupadas (para decidir si tiene sentido pedir abrir caja)
  cashOpen: boolean | null // hay caja abierta; null = desconocido/cargando
  lowStock: number // insumos bajo el mínimo
  atRisk: number // clientes en riesgo para contactar
}

// Umbrales de escalada. No son arbitrarios: UNA mesa con la comida lista pasa
// en cualquier servicio, TRES a la vez significa que el pase se trabó y hay
// platos enfriándose — eso sí es "peligroso, cambialo ya".
const TO_SERVE_CRITICAL = 3
// Un insumo bajo el mínimo se repone sin drama; cinco es que la compra se atrasó
// y mañana te quedás sin vender algo.
const LOW_STOCK_ATTENTION = 5

// Orden de la escala, para mostrar lo más urgente primero.
const SEVERITY: Record<AlertTone, number> = {
  critical: 0,
  attention: 1,
  normal: 2,
  good: 3,
}

export function homeAlerts(c: AlertCounts): HomeAlert[] {
  const out: HomeAlert[] = []

  if (c.toServe > 0) {
    out.push({
      key: "to_serve",
      labelKey: "dashboard.alerts.toServe",
      count: c.toServe,
      to: "/app/floor",
      tone: c.toServe >= TO_SERVE_CRITICAL ? "critical" : "attention",
    })
  }
  if (c.toCharge > 0) {
    out.push({
      key: "to_charge",
      labelKey: "dashboard.alerts.toCharge",
      count: c.toCharge,
      to: "/app/floor?cobrar=1",
      tone: "attention",
    })
  }
  // Solo molesta con la caja si el local está operando (hay mesas ocupadas).
  if (c.cashOpen === false && c.occupied > 0) {
    out.push({
      key: "cash",
      labelKey: "dashboard.alerts.cashClosed",
      to: "/app/caja",
      tone: "attention",
    })
  }
  if (c.lowStock > 0) {
    out.push({
      key: "low_stock",
      labelKey: "dashboard.alerts.lowStock",
      count: c.lowStock,
      to: "/app/stock",
      tone: c.lowStock >= LOW_STOCK_ATTENTION ? "attention" : "normal",
    })
  }
  if (c.atRisk > 0) {
    out.push({
      key: "at_risk",
      labelKey: "dashboard.alerts.atRisk",
      count: c.atRisk,
      to: "/app/clientes",
      tone: "normal",
    })
  }
  // Lo más urgente primero: los chips se acomodan en varias filas y el ojo va
  // arriba a la izquierda. `sort` es estable, así que a igual nivel se conserva
  // el orden en que se agregaron.
  return out.sort((a, b) => SEVERITY[a.tone] - SEVERITY[b.tone])
}

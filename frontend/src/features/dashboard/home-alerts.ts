// "Requiere tu atención": junta en una sola franja lo accionable de HOY, a partir
// de datos que ya existen (mesas / caja / stock / clientes). Puro y determinista:
// solo entra lo que realmente exige acción (count > 0); nada de ruido ni relleno.
//
// Contrato i18n: no arma texto. Cada alerta devuelve `labelKey` (clave i18next) y,
// en las que pluralizan, `count`. El componente resuelve el label con `t()`.

export type AlertTone = "attention" | "warn" | "info"

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

export function homeAlerts(c: AlertCounts): HomeAlert[] {
  const out: HomeAlert[] = []

  if (c.toServe > 0) {
    out.push({
      key: "to_serve",
      labelKey: "dashboard.alerts.toServe",
      count: c.toServe,
      to: "/app/floor",
      tone: "attention",
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
      tone: "warn",
    })
  }
  if (c.lowStock > 0) {
    out.push({
      key: "low_stock",
      labelKey: "dashboard.alerts.lowStock",
      count: c.lowStock,
      to: "/app/stock",
      tone: "info",
    })
  }
  if (c.atRisk > 0) {
    out.push({
      key: "at_risk",
      labelKey: "dashboard.alerts.atRisk",
      count: c.atRisk,
      to: "/app/clientes",
      tone: "info",
    })
  }
  return out
}

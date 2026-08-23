// "Requiere tu atención": junta en una sola franja lo accionable de HOY, a partir
// de datos que ya existen (mesas / caja / stock / clientes). Puro y determinista:
// solo entra lo que realmente exige acción (count > 0); nada de ruido ni relleno.

export type AlertTone = "attention" | "warn" | "info"

export interface HomeAlert {
  key: string
  label: string
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

function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`
}

export function homeAlerts(c: AlertCounts): HomeAlert[] {
  const out: HomeAlert[] = []

  if (c.toServe > 0) {
    out.push({
      key: "to_serve",
      label: `${plural(c.toServe, "mesa para servir", "mesas para servir")} ⚡`,
      to: "/app/floor",
      tone: "attention",
    })
  }
  if (c.toCharge > 0) {
    out.push({
      key: "to_charge",
      label: plural(c.toCharge, "mesa para cobrar", "mesas para cobrar"),
      to: "/app/floor?cobrar=1",
      tone: "attention",
    })
  }
  // Solo molesta con la caja si el local está operando (hay mesas ocupadas).
  if (c.cashOpen === false && c.occupied > 0) {
    out.push({
      key: "cash",
      label: "Caja sin abrir",
      to: "/app/caja",
      tone: "warn",
    })
  }
  if (c.lowStock > 0) {
    out.push({
      key: "low_stock",
      label: plural(c.lowStock, "insumo por reponer", "insumos por reponer"),
      to: "/app/stock",
      tone: "info",
    })
  }
  if (c.atRisk > 0) {
    out.push({
      key: "at_risk",
      label: plural(c.atRisk, "cliente en riesgo", "clientes en riesgo"),
      to: "/app/clientes",
      tone: "info",
    })
  }
  return out
}

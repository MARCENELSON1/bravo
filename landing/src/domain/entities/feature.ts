// Entidad de dominio: una capacidad del producto que se muestra en la landing.
// `icon` es una clave semántica (string) — el dominio no conoce lucide ni React;
// la capa de presentación traduce la clave a un componente de ícono.
export type FeatureIcon =
  | "orders"
  | "kds"
  | "payments"
  | "invoices"
  | "menu"
  | "inventory"
  | "reservations"
  | "timeclock"
  | "finance"
  | "reports"
  | "copilot"
  | "advisor"

// Los tres bloques en que se agrupa la lista. "operation" y "management" usan
// los mismos nombres que la sidebar del software (Operación / Gestión), para que
// quien pasa de la landing a la app reconozca la estructura.
export type FeatureGroup = "operation" | "management" | "intelligence"

export interface Feature {
  readonly id: string
  readonly title: string
  readonly description: string
  readonly icon: FeatureIcon
  readonly group: FeatureGroup
}

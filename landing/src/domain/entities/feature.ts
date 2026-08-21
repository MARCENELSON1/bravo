// Entidad de dominio: una capacidad del producto que se muestra en la landing.
// `icon` es una clave semántica (string) — el dominio no conoce lucide ni React;
// la capa de presentación traduce la clave a un componente de ícono.
export type FeatureIcon =
  | "orders"
  | "payments"
  | "copilot"
  | "kds"
  | "timeclock"
  | "reports"

export interface Feature {
  readonly id: string
  readonly title: string
  readonly description: string
  readonly icon: FeatureIcon
}

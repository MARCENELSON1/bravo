// Entidad de dominio: una integración externa que se muestra en la landing.
export interface Integration {
  readonly id: string
  readonly name: string
  readonly description: string
}

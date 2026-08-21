// Entidad de dominio: un paso del flujo "cómo funciona". El orden lo da la posición
// en la lista; la numeración visual (01, 02…) la agrega la presentación.
export interface Step {
  readonly id: string
  readonly title: string
  readonly description: string
}

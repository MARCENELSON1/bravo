// Un lead de contacto capturado en la landing (formulario de "hablá con ventas").
export interface Lead {
  readonly email: string
  readonly name?: string
  readonly message?: string
}

// Puerto (driven port): destino de los leads. Hoy lo implementa un adapter sin
// backend (log/simulado); mañana un adapter HTTP contra la API — sin tocar el caso de uso.
export interface LeadGateway {
  submit(lead: Lead): Promise<void>
}

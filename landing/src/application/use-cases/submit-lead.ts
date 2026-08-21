import type { Lead, LeadGateway } from "@/domain/ports/lead-gateway"

export class InvalidLeadError extends Error {
  constructor(message = "invalid_email") {
    super(message)
    this.name = "InvalidLeadError"
  }
}

// Caso de uso: registrar un lead de contacto. Valida la regla de negocio mínima
// (email con formato razonable) y delega el envío al puerto.
export class SubmitLead {
  constructor(private readonly gateway: LeadGateway) {}

  async execute(lead: Lead): Promise<void> {
    const email = lead.email.trim()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new InvalidLeadError()
    }
    await this.gateway.submit({ ...lead, email })
  }
}

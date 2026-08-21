import type { Lead, LeadGateway } from "@/domain/ports/lead-gateway"

// Adapter HTTP: manda el lead al backend, que es quien habla con el CRM.
// La landing es un bundle público, así que NO puede sostener la credencial del
// CRM: si la llevara, cualquiera la leería del JS. Por eso el salto intermedio.
export class HttpLeadGateway implements LeadGateway {
  constructor(private readonly apiUrl: string) {}

  async submit(lead: Lead): Promise<void> {
    const response = await fetch(`${this.apiUrl}/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: lead.email,
        name: lead.name || null,
        message: lead.message || null,
      }),
    })
    // Si no llegó, se propaga: el formulario muestra el error real en vez de
    // prometerle al visitante un contacto que nadie va a hacer.
    if (!response.ok) {
      throw new Error(`lead_not_delivered_${response.status}`)
    }
  }
}

import type { Lead, LeadGateway } from "@/domain/ports/lead-gateway"

// Adapter HTTP: manda el lead al backend, que es quien habla con el CRM.
// La landing es un bundle público, así que NO puede sostener la credencial del
// CRM: si la llevara, cualquiera la leería del JS. Por eso el salto intermedio.

// El endpoint público acepta solo email, name y message: los campos que no
// declara los descarta en silencio. Para que el negocio y el teléfono LLEGUEN
// igual, se anteponen al mensaje. Traducir el modelo del dominio al formato que
// entiende el sistema externo es el trabajo de un adapter — el día que la API
// acepte los campos sueltos, se cambia solo acá.
function composeMessage(lead: Lead): string | null {
  const lines: string[] = []
  if (lead.business) lines.push(`Negocio: ${lead.business}`)
  if (lead.phone) lines.push(`Teléfono: ${lead.phone}`)
  if (lead.message) {
    if (lines.length > 0) lines.push("")
    lines.push(lead.message)
  }
  return lines.length > 0 ? lines.join("\n") : null
}

export class HttpLeadGateway implements LeadGateway {
  constructor(private readonly apiUrl: string) {}

  async submit(lead: Lead): Promise<void> {
    const response = await fetch(`${this.apiUrl}/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: lead.email,
        name: lead.name || null,
        message: composeMessage(lead),
      }),
    })
    // Si no llegó, se propaga: el formulario muestra el error real en vez de
    // prometerle al visitante un contacto que nadie va a hacer.
    if (!response.ok) {
      throw new Error(`lead_not_delivered_${response.status}`)
    }
  }
}

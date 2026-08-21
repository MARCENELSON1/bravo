import type { Lead, LeadGateway } from "@/domain/ports/lead-gateway"

// Adapter sin backend: registra el lead en consola y simula un envío exitoso.
// Cuando exista el endpoint, se crea un HttpLeadGateway que cumpla el mismo puerto
// y se cambia una sola línea en el contenedor DI (OCP / DIP).
export class ConsoleLeadGateway implements LeadGateway {
  async submit(lead: Lead): Promise<void> {
    // Simula latencia de red para que la UI muestre su estado de "enviando".
    await new Promise((resolve) => setTimeout(resolve, 500))
    console.info("[lead] recibido (sin backend):", lead)
  }
}

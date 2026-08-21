import { useState } from "react"

import type { Lead } from "@/domain/ports/lead-gateway"
import { InvalidLeadError } from "@/application/use-cases/submit-lead"
import { useContainer } from "@/presentation/providers/container-provider"

type Status = "idle" | "submitting" | "success" | "error"

// Puente entre el caso de uso SubmitLead y el formulario de contacto.
export function useLeadForm() {
  const { submitLead } = useContainer()
  const [status, setStatus] = useState<Status>("idle")
  const [error, setError] = useState<string | null>(null)

  async function submit(lead: Lead) {
    setStatus("submitting")
    setError(null)
    try {
      await submitLead.execute(lead)
      setStatus("success")
    } catch (e) {
      setStatus("error")
      setError(
        e instanceof InvalidLeadError
          ? "Revisá el email ingresado."
          : "No se pudo enviar. Probá de nuevo en un momento.",
      )
    }
  }

  return { status, error, submit }
}

import { useEffect, useState } from "react"

import type { Plan } from "@/domain/entities/plan"
import { useContainer } from "@/presentation/providers/container-provider"

// Puente entre el caso de uso GetPricingPlans y React. La UI no conoce repositorios.
export function usePricingPlans() {
  const { getPricingPlans } = useContainer()
  const [plans, setPlans] = useState<readonly Plan[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    getPricingPlans
      .execute()
      .then((result) => {
        if (alive) {
          setPlans(result)
          setLoading(false)
        }
      })
      // Si la API de planes (INTL) no responde, corta el skeleton en vez de dejarlo
      // girando para siempre. AR usa datos estáticos y nunca falla.
      .catch(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [getPricingPlans])

  return { plans, loading }
}

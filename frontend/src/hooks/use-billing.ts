import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

// Planes de la región del local (AR/INTL) — moneda + riel se derivan de ahí.
export function useBillingPlans(region: string | null) {
  const { billingApi } = useServices()
  return useQuery({
    queryKey: ["billing-plans", region],
    queryFn: () => billingApi.plans(region as string),
    enabled: Boolean(region),
  })
}

export function useSubscription() {
  const { billingApi } = useServices()
  return useQuery({
    queryKey: ["billing-subscription"],
    queryFn: () => billingApi.subscription(),
  })
}

// Inicia el checkout: devuelve la URL de pago (hosteada) para redirigir.
export function useCheckout() {
  const { billingApi } = useServices()
  return useMutation({
    mutationFn: (planId: string) => billingApi.checkout(planId),
  })
}

export function useCancelSubscription() {
  const { billingApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => billingApi.cancel(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["billing-subscription"] })
    },
  })
}

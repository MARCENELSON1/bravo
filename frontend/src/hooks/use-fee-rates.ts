import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { FeeRateDTO } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

// Comisiones (slice B): tasas de comisión por método (bps).
export function useFeeRates() {
  const { paymentsApi } = useServices()
  return useQuery({
    queryKey: ["fee-rates"],
    queryFn: () => paymentsApi.getFeeRates(),
  })
}

export function useUpdateFeeRates() {
  const { paymentsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (rates: FeeRateDTO[]) => paymentsApi.updateFeeRates(rates),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["fee-rates"] })
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] })
    },
  })
}
